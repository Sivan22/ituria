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

    def extract_keywords(self, query: str, failed_keywords: List[str] = None) -> List[str]:
        """Extract search keywords using Claude, considering previously failed keywords"""
        try:
            prompt = f"""Extract 3-5 most important search keywords from this question. 
                    Consider synonyms and related terms that might help find relevant information.
                    Return only the keywords separated by spaces, no other text.
                    IMPORTANT: Do not split individual words into letters.
                    """
            
            if failed_keywords:
                prompt += f"""
                    The following keywords were tried but found no results: {', '.join(failed_keywords)}
                    Please suggest alternative keywords that are:
                    1. Different from the failed keywords
                    2. More general or using synonyms
                    3. Related but from a different perspective
                    """
            
            prompt += f"Question: {query}"
            
            message = self.client.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=100,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            keywords = message.content[0].text.strip().split()
            if not keywords:  # If Claude returns empty or only spaces
                # Simple fallback: split by spaces and take first 5 words, excluding stop words
                stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 
                            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 
                            'to', 'was', 'were', 'will', 'with'}
                words = [word.lower() for word in query.split() 
                        if word.lower() not in stop_words and len(word) > 1]
                keywords = words[:5] if words else [query.lower()]
            
            # Remove any keywords that were already tried
            if failed_keywords:
                keywords = [k for k in keywords if k.lower() not in {w.lower() for w in failed_keywords}]
                if not keywords:  # If all new keywords were already tried
                    keywords = [query.lower()]  # Use full query as fallback
            
            self.logger.info(f"Extracted keywords: {keywords}")
            return keywords
            
        except Exception as e:
            self.logger.error(f"Error extracting keywords: {e}")
            # Improved fallback with stop words filtering
            stop_words = {'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from', 
                        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the', 
                        'to', 'was', 'were', 'will', 'with'}
            words = [word.lower() for word in query.split() 
                    if word.lower() not in stop_words and len(word) > 1]
            return words[:5] if words else [query.lower()]

    def evaluate_results(self, results: List[Dict[str, Any]], query: str) -> Tuple[bool, Optional[str], Optional[str]]:
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
            
            return is_good, new_keywords, explanation
            
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

    def search_and_answer(self, query: str) -> Dict[str, Any]:
        """Main method to process a query and return an answer with steps"""
        steps = []
        attempt = 0
        failed_keywords = []
        
        # Step 1: Extract keywords
        steps.append({
            "action": "Keyword Extraction",
            "description": "Extracting search keywords from the query...",
            "results": []
        })
        keywords = self.extract_keywords(query, failed_keywords)
        steps[-1]["description"] = f"✓ Keywords extracted"
        steps[-1]["results"] = [{"type": "keywords", "content": keywords}]

        while attempt < self.max_search_attempts:
            self.logger.info(f"Search attempt {attempt + 1} with keywords: {keywords}")
            
            try:
                # Step 2: Search documents
                steps.append({
                    "action": f"Document Search (Attempt {attempt + 1})",
                    "description": f"Searching documents with keywords: {', '.join(keywords)}...",
                    "results": []
                })
                results = self.indexer.search_documents(" ".join(keywords))
                
                if not results:
                    steps[-1]["description"] = f"⚠ No documents found"
                    steps[-1]["results"] = [{"type": "no_results", "content": f"No matches for keywords: {', '.join(keywords)}"}]
                    failed_keywords.extend(keywords)
                    if attempt == self.max_search_attempts - 1:
                        final_msg = "I couldn't find any relevant documents that match your query. Please try:\n" \
                                  "1. Using different keywords\n" \
                                  "2. Rephrasing your question\n" \
                                  "3. Checking if the topic is covered in the indexed documents"
                        return {
                            "steps": steps,
                            "answer": final_msg,
                            "sources": []
                        }
                    # Try with next set of keywords
                    attempt += 1
                    keywords = self.extract_keywords(query, failed_keywords)
                    continue
                
                steps[-1]["description"] = f"✓ Found {len(results)} documents"
                steps[-1]["results"] = [
                    {
                        "type": "document",
                        "content": {
                            "title": result.get("filename", "Untitled"),
                            "score": f"{result.get('score', 0):.2f}",
                            "highlights": result.get("highlights", [])[:1]  # Show first highlight only
                        }
                    }
                    for result in results[:3]  # Show top 3 results
                ]
                
                # Step 3: Evaluate results
                steps.append({
                    "action": "Result Evaluation",
                    "description": "Evaluating search results quality...",
                    "explanation": "",
                    "results": []
                })
                is_good, new_keywords, explanation = self.evaluate_results(results, query)
                
                if is_good:
                    steps[-1]["description"] = "✓ Search results are relevant and sufficient"
                    steps[-1]["explanation"] = explanation
                    steps[-1]["results"] = [{"type": "evaluation", "content": {"confidence": "high", "status": "accepted"}}]
                else:
                    steps[-1]["description"] = "⚠ Results need refinement"
                    steps[-1]["explanation"] = explanation
                    next_keywords = new_keywords if new_keywords else self.extract_keywords(query, failed_keywords)
                    steps[-1]["results"] = [
                        {"type": "evaluation", "content": {"confidence": "low", "status": "refining"}},
                        {"type": "next_keywords", "content": next_keywords}
                    ]
                
                if is_good:
                    # Step 4: Generate answer
                    steps.append({
                        "action": "Answer Generation",
                        "description": "Generating comprehensive answer from search results..."
                    })
                    answer = self.generate_answer(query, results)
                    steps[-1]["description"] = "Generated answer based on found information"
                    
                    return {
                        "steps": steps,
                        "answer": answer,
                        "sources": [{
                            "title": result.get("filename", "Untitled"),
                            "path": result.get("path", "Unknown"),
                            "highlights": result.get("highlights", []),
                            "score": result.get("score", 0)
                        } for result in results]
                    }
                
                failed_keywords.extend(keywords)
                keywords = new_keywords if new_keywords else self.extract_keywords(query, failed_keywords)
                
                attempt += 1
                
            except Exception as e:
                error_msg = f"An error occurred while processing your question: {str(e)}"
                steps.append({
                    "action": "Error",
                    "description": error_msg
                })
                return {
                    "steps": steps,
                    "answer": error_msg,
                    "sources": []
                }
        
        final_msg = "I couldn't find a satisfactory answer after multiple attempts. The available information might be insufficient. Please try rephrasing your question or check if the topic is covered in the documents."
        steps.append({
            "action": "Search Exhausted",
            "description": "Maximum search attempts reached without satisfactory results"
        })
        return {
            "steps": steps,
            "answer": final_msg,
            "sources": []
        }
