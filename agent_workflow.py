import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
import anthropic
from document_indexer import DocumentIndexer

load_dotenv()

class SearchAgent:
    def __init__(self, indexer: DocumentIndexer):
        """Initialize the search agent with document indexer and LLM client"""
        self.indexer = indexer
        self.logger = logging.getLogger(__name__)
        
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        self.client = anthropic.Client(api_key=api_key)
        
        self.max_search_attempts = 3
        self.min_confidence_threshold = 0.5

    def extract_keywords(self, query: str) -> List[str]:
        """Extract search keywords using Claude"""
        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=100,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"""Extract 3-5 most important search keywords from this question. 
                    Consider synonyms and related terms that might help find relevant information.
                    Return only the keywords separated by spaces, no other text.
                    Question: {query}"""
                }]
            )
            keywords = message.content[0].text.strip().split()
            self.logger.info(f"Extracted keywords: {keywords}")
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            # Fallback to simple word extraction
            words = query.lower().split()
            return words[:5]

    def evaluate_results(self, results: List[Dict[str, Any]], query: str) -> Tuple[bool, Optional[str]]:
        """Evaluate search results using Claude with confidence scoring"""
        if not results:
            return False, "No results found"

        # Prepare context from results
        context = "\n".join(
            f"Result {i+1}:\n" + "\n".join(r.get('highlights', []))
            for i, r in enumerate(results)
        )

        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=200,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"""Evaluate the search results for answering this question:
                    Question: {query}
                    
                    Search Results:
                    {context}
                    
                    Provide evaluation in this format:
                    Line 1: Confidence score (0.0 to 1.0) indicating how well the results can answer the question
                    Line 2: ACCEPT if score >= 0.5, REFINE if score < 0.5
                    Line 3: Detailed explanation of what information is present or missing
                    Line 4: If REFINE, suggest better search keywords (space-separated), considering missing aspects
                    """
                }]
            )
            
            lines = message.content[0].text.strip().split('\n')
            confidence = float(lines[0])
            decision = lines[1].upper()
            explanation = lines[2]
            
            is_good = decision == 'ACCEPT'
            new_keywords = lines[3].split() if not is_good and len(lines) > 3 else None
            
            self.logger.info(f"Evaluation: Confidence={confidence}, Decision={decision}")
            self.logger.info(f"Explanation: {explanation}")
            
            return is_good, new_keywords
            
        except Exception as e:
            self.logger.error(f"Error evaluating results: {e}")
            # Fallback to simple evaluation
            return len(results) >= 2, None

    def generate_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate answer using Claude with improved context utilization"""
        if not results:
            return "I couldn't find any relevant information to answer your question."

        context = "\n".join(
            f"Result {i+1}:\n" + "\n".join(r.get('highlights', []))
            for i, r in enumerate(results)
        )

        try:
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=1000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": f"""Based on these search results, answer this question:
                    Question: {query}
                    
                    Search Results:
                    {context}
                    
                    Requirements for your answer:
                    1. Use only information from the search results
                    2. Be comprehensive but concise
                    3. Structure the answer clearly
                    4. If any aspect of the question cannot be fully answered, acknowledge this
                    """
                }]
            )
            return message.content[0].text.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return f"I encountered an error generating the answer: {str(e)}"

    def search_and_answer(self, query: str) -> str:
        """Main method to process a query and return an answer"""
        attempt = 0
        keywords = self.extract_keywords(query)
        
        while attempt < self.max_search_attempts:
            self.logger.info(f"Search attempt {attempt + 1} with keywords: {keywords}")
            
            try:
                # Search documents
                results = self.indexer.search_documents(" ".join(keywords))
                
                # Evaluate results
                is_good, new_keywords = self.evaluate_results(results, query)
                
                if is_good:
                    # Generate and return answer
                    return self.generate_answer(query, results)
                
                if new_keywords:
                    keywords = new_keywords
                else:
                    # If no new keywords suggested, modify existing ones
                    keywords = keywords[1:] if len(keywords) > 1 else keywords
                
                attempt += 1
                
            except Exception as e:
                self.logger.error(f"Error during search attempt: {e}")
                return f"An error occurred while processing your question: {str(e)}"
        
        return "I couldn't find a satisfactory answer after multiple attempts. The available information might be insufficient. Please try rephrasing your question or check if the topic is covered in the documents."
