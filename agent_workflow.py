import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dotenv import load_dotenv
from llm_providers import LLMProvider
from langchain.schema import HumanMessage
from tantivy_search_agent import TantivySearchAgent

load_dotenv()

class SearchAgent:
    def __init__(self, tantivy_agent: TantivySearchAgent, provider_name: str = "Claude"):
        """Initialize the search agent with Tantivy agent and LLM client"""
        self.tantivy_agent = tantivy_agent
        self.logger = logging.getLogger(__name__)
        
        # Initialize LLM provider
        self.llm_provider = LLMProvider()
        self.set_provider(provider_name)
        
        self.min_confidence_threshold = 0.5

    def set_provider(self, provider_name: str) -> None:
        self.llm = self.llm_provider.get_provider(provider_name)
        if not self.llm:
            raise ValueError(f"Provider {provider_name} not available")
        self.current_provider = provider_name

    def get_available_providers(self) -> list[str]:
        return self.llm_provider.get_available_providers()

    def get_query(self, query: str, failed_queries: List[str] = None) -> str:
        """Generate a Tantivy query using Claude, considering previously failed queries"""
        try:
            prompt = (
                "Create a Tantivy query for this search request using Tantivy's query syntax. "
                "Return only the Tantivy query string, no other text.\n\n"+
                self.tantivy_agent.get_query_instructions()+                
                "\n\nAdditional instructions: \n"
                "1. Use only Hebrew terms for the search query\n"
                "2. the corpus to search in is an ancient Hebrew corpus - Tora and Talmud. "
                "3. Try to use ancient Hebrew terms and or Talmudic expressions and prevent modern words that are not common in those texts \n"              
                f"the search request: {query}"
            )
            
            if failed_queries:
                prompt += (
                    f"\n\nPrevious failed queries:\n"+
                    '\n'.join(failed_queries)+
                    "\n\n"
                    "Please generate an alternative query that:\n"
                    "1. Uses different Hebrew synonyms or related terms\n"
                    "2. Tries broader or more general terms\n"
                    "3. Adjusts proximity values or uses wildcards\n"
                    "4. Simplifies complex expressions using +/- operators\n"
                    "5. Considers using IN operator for multiple alternatives"
                )
            
            response = self.llm.invoke([HumanMessage(content=prompt)])
            tantivy_query = response.content.strip()  
            self.logger.info(f"Generated Tantivy query: {tantivy_query}")
            return tantivy_query
            
        except Exception as e:
            self.logger.error(f"Error generating Tantivy query: {e}")
            # Fallback to basic quoted search
            return f'"{query}"'

    def _evaluate_results(self, results: List[Dict[str, Any]], query: str) -> Dict[str, Any]:
        """Evaluate search results using Claude with confidence scoring"""
     
       # Prepare context from results
        context = "\n".join(f"Result {i}. Source: {r.get('title',[])}\n Text: {r.get('text', [])}"
            for i, r in enumerate(results)
                )

        try:
            message = self.llm.invoke([HumanMessage(content=f"""Evaluate the search results for answering this question:
                    Question: {query}
                    
                    Search Results:
                    {context}
                    
                    Provide evaluation in this format:
                    [line 1] Confidence score (0.0 to 1.0) indicating how well the results can answer the question. this line should include only the number return, don't include '[line 1]'
                    [line 2] ACCEPT if score >= {self.min_confidence_threshold}, REFINE if score < {self.min_confidence_threshold}. return only the word ACCEPT or REFINE.
                    [line 3] Detailed explanation of what information is present or missing, don't include '[line 3]'. it should be only in Hebrew
                             """)])
            lines = message.content.strip().replace('\n\n', '\n').split('\n')
            confidence = float(lines[0])
            decision = lines[1].upper()
            explanation = lines[2]
            
            is_good = decision == 'ACCEPT'

            self.logger.info(f"Evaluation: Confidence={confidence}, Decision={decision}")
            self.logger.info(f"Explanation: {explanation}")
            
            return {
                "confidence": confidence,
                "is_sufficient": is_good,
                "explanation": explanation,
             
            }
            
        except Exception as e:
            self.logger.error(f"Error evaluating results: {e}")
            # Fallback to simple evaluation
            return {
                "confidence": 0.0,
                "is_sufficient": False,
                "explanation": "",         
            }

    def _generate_answer(self, query: str, results: List[Dict[str, Any]]) -> str:
        """Generate answer using Claude with improved context utilization"""
        if not results:
            return "I couldn't find any relevant information to answer your question."

          # Prepare context from results
        context = "\n".join(f"Result {i}. Source: {r.get('title',[])}\n Text: {r.get('text', [])}"
            for i, r in enumerate(results)
                )
        
        try:
            message = self.llm.invoke([HumanMessage(content=f"""Based on these search results, answer this question:
                    Question: {query}
                    
                    Search Results:
                    {context}
                    
                    Requirements for your answer:
                    1. Use only information from the search results
                    2. Be comprehensive but concise
                    3. Structure the answer clearly
                    4. If any aspect of the question cannot be fully answered, acknowledge this
                    5. cite sources for each fact or information you use
                    6. The answer should be only in Hebrew
                    """)])
            return message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Error generating answer: {e}")
            return f"I encountered an error generating the answer: {str(e)}"

    def search_and_answer(self, query: str, num_results: int = 10, max_iterations: int = 3) -> Dict[str, Any]:
        """Execute multi-step search process using Tantivy"""
        steps = []
        all_results = []
        
        # Step 1: Generate Tantivy query
        initial_query = self.get_query(query)
        steps.append({
            'action': 'יצירת שאילתת חיפוש',
            'description': 'נוצרה שאילתת חיפוש עבור מנוע החיפוש',
            'results': [{'type': 'query', 'content': initial_query}]
        })
        
        # Step 2: Initial search with Tantivy query
        results = self.tantivy_agent.search(initial_query, num_results)
        
        steps.append({
            'action': 'חיפוש במאגר',
            'description': f'חיפוש במאגר עבור שאילתת חיפוש: {initial_query}\n נמצאו {len(results)} תוצאות',
            'results': [{'type': 'document', 'content': {
                'title': r['title'],
                'highlights': [r['highlights'][0]],
                'score': r['score']
            }} for r in results]
        })
        
        all_results.extend(results)
        
        # Step 3: Evaluate results
        evaluation = self._evaluate_results(results, query)
        confidence = evaluation['confidence']
        is_sufficient = evaluation['is_sufficient']
        explanation = evaluation['explanation']
        
        
        steps.append({
            'action': 'דירוג תוצאות',
            'description': 'דירוג תוצאות חיפוש',
            'results': [{
                'type': 'evaluation',
                'content': {
                    'status': 'accepted' if is_sufficient else 'insufficient',
                    'confidence': confidence,
                    'explanation': explanation,
                }
            }]
        })
        
        # Step 4: Additional searches if needed
        attempt = 2
        failed_queries = []
        
        while not is_sufficient and attempt < max_iterations:

            # Mark query as failed
            failed_queries.append(query)

            # Generate new query
            new_query = self.get_query(query, failed_queries)
           
            steps.append({
                    'action': f'יצירת שאילתה מחדש (ניסיון {attempt})',
                    'description': 'נוצרה שאילתת חיפוש נוספת עבור מנוע החיפוש',
                    'results': [
                        {'type': 'new_query', 'content': new_query}
                    ]
                })
            
            # Search with new query
            results = self.tantivy_agent.search(new_query, num_results)
            
            steps.append({
                'action': f'חיפוש נוסף (ניסיון {attempt}) ',
                'description': f'מחפש במאגר עבור שאילתת חיפוש: {new_query}',
                'results': [{'type': 'document', 'content': {
                    'title': r['title'],
                    'highlights': [r['highlights']],
                    'score': r['score']
                }} for r in results]
            })
            
            all_results.extend(results)
            
            # Re-evaluate with current results
            evaluation = self._evaluate_results(results, query)
            confidence = evaluation['confidence']
            is_sufficient = evaluation['is_sufficient']
            explanation = evaluation['explanation']
            
            steps.append({
                'action': f'דירוג תוצאות (ניסיון {attempt})',
                'description': 'דירוג תוצאות חיפוש לניסיון זה',
                'explanation': explanation,
                'results': [{
                    'type': 'evaluation',
                    'content': {
                        'status': 'accepted' if is_sufficient else 'insufficient',
                        'confidence': confidence,
                        'explanation': explanation,
                    }
                }]
            })
            
            attempt += 1
        
        # Step 5: Generate final answer
        answer = self._generate_answer(query, all_results)
        
        return {
            'steps': steps,
            'answer': answer,
            'sources': [{
                'title': r['title'],
                'path': r['file_path'],
                'highlights': [r['text']],
                'score': r['score']
            } for r in all_results]
        }
