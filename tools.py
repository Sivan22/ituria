from langchain_core.tools import tool
from sefaria import get_text as sefaria_get_text, get_commentaries as sefaria_get_commentaries
from tantivy_search import TantivySearch
from typing import Optional
from pydantic import BaseModel, Field

from app import INDEX_PATH

class ReadTextArgs(BaseModel):
        reference: str = Field(description="The reference to retrieve the text for. examples: בראשית א פרק א, Genesis 1:1")

class SearchArgs(BaseModel):
        query: str = Field(description="""the query for the search.
    Instructions for generating a query:

    1. Boolean Operators:

    - AND: term1 AND term2 (both required)
    - OR: term1 OR term2 (either term)
    - Multiple words default to OR operation (cloud network = cloud OR network)
    - AND takes precedence over OR
    - Example: Shabath AND (walk OR go)

    2. Field-specific Terms:
    - Field-specific terms: field:term
    - Example: text:אדם AND reference:בראשית
    - available fields: text, reference, topics
    - text contains the text of the document
    - reference contains the citation of the document, e.g. בראשית, פרק א
    - topics contains the topics of the document. available topics includes: תנך, הלכה, מדרש, etc.

    3. Required/Excluded Terms:
    - Required (+): +term (must contain)
    - Excluded (-): -term (must not contain)
    - Example: +security cloud -deprecated
    - Equivalent to: security AND cloud AND NOT deprecated

    4. Phrase Search:
    - Use quotes: "exact phrase"
    - Both single/double quotes work
    - Escape quotes with \\"
    - Slop operator: "term1 term2"~N 
    - Example: "cloud security"~2 
    - the above will find "cloud framework and security "
    - Prefix matching: "start of phrase"*

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
    1. Basic: +שבת +חולה +אסור
    2. Field-specific: text:סיני AND topics:תנך
    3. Phrase with slop: "security framework"~2
    4. Complex: +reference:בראשית +text:"הבל"^2.0 +(דמי OR דמים) -הבלים
    6. Mixed: (text:"רבנו משה"^2.0 OR reference:"משנה תורה") AND topics:הלכה) AND text:"תורה המלך"~3 AND NOT topics:מדרש

    Tips:
    - Group complex expressions with parentheses
    - Use quotes for exact phrases
    - Add + for required terms, - for excluded terms
    - Boost important terms with ^N
    - use field-specific terms for better results. 
    - the corpus to search in is an ancient Hebrew corpus: Tora and Talmud. so Try to use ancient Hebrew terms and or Talmudic expressions and prevent modern words that are not common in talmudic texts
    """)
        num_results: int = Field(description="the maximum number of results to return. Default: 10", default=10)



index_path = INDEX_PATH
try:
    tantivy = TantivySearch(index_path)
    tantivy.validate_index()    
except Exception as e:
    raise Exception(f"failed to create index: {e}")
        
            
    
@tool(args_schema=SearchArgs)
def search( query: str, num_results: int = 10):
    """Searches the index for the given query."""
    results = tantivy.search(query, num_results)
    formatted_results = []
    for result in results:
        formatted_results.append({
            'text': result.get('text', 'N/A'),
            'reference': result.get('reference', 'N/A')
        })
            
    return formatted_results


@tool(args_schema=ReadTextArgs)
def read_text(reference: str )->str:
    """Retrieves the text for a given reference.  
    """
    text = sefaria_get_text(reference)
    return {
        'text': str(text),
        'reference': reference
    }

@tool
def get_commentaries(reference: str, num_results: int = 10)->str:
    """Retrieves references to all available commentaries on the given verse."""
    commentaries = sefaria_get_commentaries(reference)
    return {
        'text': '\n'.join(commentaries) if isinstance(commentaries, list) else str(commentaries),
        'reference': f"Commentaries on {reference}"
    }
    
