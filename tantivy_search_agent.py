from typing import List, Dict, Any, Optional
from tantivy import Index
import logging
import os
import re

class TantivySearchAgent:
    def __init__(self, index_path: str):
        """Initialize the Tantivy search agent with the index path"""
        self.index_path = index_path
        self.logger = logging.getLogger(__name__)
        try:
            self.index = Index.open(index_path)
            self.logger.info(f"Successfully opened Tantivy index at {index_path}")
        except Exception as e:
            self.logger.error(f"Failed to open Tantivy index: {e}")
            raise

    def get_query_instructions(self) -> str:
        """Return instructions for the LLM on how to parse and construct Tantivy queries"""
        return """
Instructions for generating a Tantivy query using Tantivy's query syntax.
Here are the supported features:


1. Boolean Operators:

   - AND: term1 AND term2 (both required)
   - OR: term1 OR term2 (either term)
   - Multiple words default to OR operation
   - AND takes precedence over OR
   - Example: security AND (cloud OR network)
   - cloud network = cloud OR network

2. Required/Excluded Terms:
   - Required (+): +term (must contain)
   - Excluded (-): -term (must not contain)
   - Example: +security cloud -deprecated
   - Equivalent to: security AND cloud AND NOT deprecated

3. Phrase Search:
   - Use quotes: "exact phrase"
   - Both single/double quotes work
   - Escape quotes with \\"
   - Slop operator: "term1 term2"~N 
   - use slop operator only for terms inside quotes
   - Prefix matching: "start of phrase"*
   - Example: "cloud security"~2 
   - the above will find "cloud framework and security "

4. Set Operations:
   - IN operator: field IN [value1 value2]
   - More efficient than OR
   - Example: status IN [active pending review]

5. Wildcards:
   - ? for single character
   - * for any number of characters
   - Example: sec?rity cloud*

6. Special Features:
   - All docs: * 
   - Boost terms: term^2.0 (positive numbers only)
   - Example: security^2.0 cloud
   - the above will boost security by 2.0
   
Query Examples:
1. Basic: security AND cloud
2. Field-specific: title:security AND body:cloud
3. Phrase with slop: "security framework"~2
4. Complex: +title:"cloud security"^2.0 +(aws OR azure) -deprecated
6. Mixed: (title:security^2.0 OR description:security) AND status IN [active review]

Tips:
- Group complex expressions with parentheses
- Use quotes for exact phrases
- Add + for required terms, - for excluded terms
- Boost important terms with ^N
"""

    def search(self, query: str, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search the Tantivy index with the given query using Tantivy's query syntax"""
        try:
            # Create a searcher
            searcher = self.index.searcher()
     
            # Parse and execute the query
            try:
                # First try with lenient parsing
                query_parser = self.index.parse_query_lenient(query)
                search_results = searcher.search(query_parser[0], num_results).hits
                
            except Exception as query_error:
                self.logger.error(f"Lenient query parsing failed: {query_error}")
            
            # Process results
            results = []
            for score, doc_address in search_results:
                doc = searcher.doc(doc_address)
                text = doc.get_first("text")
                
                # Extract highlighted snippets based on query terms
                # Remove special syntax for highlighting while preserving Hebrew
                highlight_terms = re.sub(
                    r'[:"()[\]{}^~*\\]|\b(AND|OR|NOT|TO|IN)\b|[-+]', 
                    ' ', 
                    query
                ).strip()
                highlight_terms = [term for term in highlight_terms.split() if len(term) > 1]
                
                # Create regex pattern for highlighting
                if highlight_terms:
                    # Escape regex special chars but preserve Hebrew
                    patterns = [re.escape(term) for term in highlight_terms]
                    pattern = '|'.join(patterns)
                    # Get surrounding context for matches
                    matches = list(re.finditer(pattern, text, re.IGNORECASE))
                    if matches:
                        highlights = []
                        for match in matches:
                            start = max(0, match.start() - 50)
                            end = min(len(text), match.end() + 50)
                            highlight = text[start:end]
                            if start > 0:
                                highlight = f"...{highlight}"
                            if end < len(text):
                                highlight = f"{highlight}..."
                            highlights.append(highlight)
                    else:
                        highlights = [text[:100] + "..." if len(text) > 100 else text]
                else:
                    highlights = [text[:100] + "..." if len(text) > 100 else text]
                
                result = {
                    "score": float(score),
                    "title": doc.get_first("title") or os.path.basename(doc.get_first("filePath") or ""),
                    "file_path": doc.get_first("filePath"),
                    "line_number": doc.get_first("segment"),
                    "is_pdf": doc.get_first("isPdf"),
                    "text": text,
                    "highlights": highlights
                }
                results.append(result)
            
            self.logger.info(f"Found {len(results)} results for query: {query}")
            return results
            
        except Exception as e:
            self.logger.error(f"Error during search: {str(e)}")
            return []

    def validate_index(self) -> bool:
        """Validate that the index exists and is accessible"""
        try:
            # Try to create a searcher and perform a simple search
            searcher = self.index.searcher()
            query_parser = self.index.parse_query("*")
            searcher.search(query_parser, 1)
            return True
        except Exception as e:
            self.logger.error(f"Index validation failed: {e}")
            return False
