from document_indexer import DocumentIndexer
from agent_workflow import SearchAgent
import os
import logging
import sys
from elasticsearch import ConnectionError

def setup_logging():
    """Configure logging settings"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def main():
    logger = setup_logging()
    
    try:
        # Initialize components
        logger.info("Initializing document indexer...")
        indexer = DocumentIndexer()
        
        # Get the absolute path to the documents directory
        current_dir = os.path.dirname(os.path.abspath(__file__))
        documents_path = os.path.join(current_dir, 'documents')
        
        if not os.path.exists(documents_path):
            logger.error(f"Documents directory not found: {documents_path}")
            return
        
        try:
            indexed_docs = indexer.index_documents(documents_path)
            logger.info(f"Successfully indexed {indexed_docs} documents")
        except ConnectionError as e:
            logger.error(f"Failed to connect to Elasticsearch: {str(e)}")
            logger.error("Please ensure Elasticsearch is running and accessible")
            return
        except Exception as e:
            logger.error(f"Error during document indexing: {str(e)}")
            return
            
        if indexed_docs == 0:
            logger.warning("No documents were indexed. Please check your documents directory.")
            return
        
        logger.info("Initializing search agent...")
        agent = SearchAgent(indexer)
        
        # Demo search capabilities
        logger.info("\nDemonstrating search and answer capabilities:\n")
        print("="*80)
        
        # Hebrew questions about Israeli history and culture
        questions = [
            "מתי הוקמה מדינת ישראל ומי הכריז על הקמתה?",
            "איך התפתחה ישראל מבחינה טכנולוגית וכלכלית?",
            "מהם המאפיינים העיקריים של התרבות הישראלית?",
            "איך השפיעו גלי העלייה השונים על התפתחות המדינה?",
            "מהם המאפיינים הייחודיים של המטבח הישראלי?"
        ]
        
        for i, query in enumerate(questions, 1):
            print(f"\nQuestion {i}: {query}")
            print("-"*80)
            
            try:
                answer = agent.search_and_answer(query)
                print(f"\nAnswer: {answer}\n")
            except Exception as e:
                logger.error(f"Error processing question: {str(e)}")
            
            print("="*80)

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    main()
