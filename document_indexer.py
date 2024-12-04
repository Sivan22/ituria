import os
import logging
from dotenv import load_dotenv
from elasticsearch import Elasticsearch, ConnectionError, RequestError
from typing import List, Dict, Any
import time

# Load environment variables
load_dotenv()

class DocumentIndexer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Get Elasticsearch configuration
        self.es_host = os.getenv('ELASTICSEARCH_HOST', 'localhost')
        self.es_port = int(os.getenv('ELASTICSEARCH_PORT', 9200))
        
        # Connect to Elasticsearch with retry logic
        self.es_client = self._connect_with_retry()
        
        # Create index if not exists
        self.index_name = 'document_search_index'
        self._ensure_index_exists()

    def _connect_with_retry(self, max_retries=3, retry_delay=2) -> Elasticsearch:
        """Attempt to connect to Elasticsearch with retries"""
        for attempt in range(max_retries):
            try:
                # More specific connection settings
                client = Elasticsearch(
                    [f"http://{self.es_host}:{self.es_port}"],
                    verify_certs=False,
                    request_timeout=30,
                    max_retries=3,
                    retry_on_timeout=True
                )
                
                if client.ping():
                    self.logger.info("Successfully connected to Elasticsearch")
                    return client
                    
            except ConnectionError as e:
                if attempt == max_retries - 1:
                    raise ConnectionError(f"Failed to connect to Elasticsearch after {max_retries} attempts: {str(e)}")
                self.logger.warning(f"Connection attempt {attempt + 1} failed, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise Exception(f"Unexpected error connecting to Elasticsearch: {str(e)}")
                self.logger.warning(f"Unexpected error during attempt {attempt + 1}, retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
        
        raise ConnectionError("Failed to establish connection to Elasticsearch")

    def _ensure_index_exists(self):
        """Create index if it doesn't exist"""
        try:
            if not self.es_client.indices.exists(index=self.index_name):
                self.es_client.indices.create(index=self.index_name, body={
                    'settings': {
                        'analysis': {
                            'analyzer': {
                                'custom_analyzer': {
                                    'type': 'custom',
                                    'tokenizer': 'standard',
                                    'filter': ['lowercase', 'stop']
                                }
                            }
                        },
                        'number_of_shards': 1,  # Single node setup
                        'number_of_replicas': 0  # No replicas needed for testing
                    },
                    'mappings': {
                        'properties': {
                            'content': {'type': 'text', 'analyzer': 'custom_analyzer'},
                            'filename': {'type': 'keyword'},
                            'path': {'type': 'keyword'}
                        }
                    }
                })
                self.logger.info(f"Created index: {self.index_name}")
        except RequestError as e:
            if "resource_already_exists_exception" not in str(e):
                raise
            self.logger.info(f"Index {self.index_name} already exists")

    def index_documents(self, documents_path: str) -> int:
        """
        Index documents from a given directory
        
        Args:
            documents_path (str): Path to directory containing text files
        
        Returns:
            int: Number of documents indexed
        """
        if not os.path.exists(documents_path):
            raise FileNotFoundError(f"Documents directory not found: {documents_path}")

        indexed_count = 0
        
        for root, _, files in os.walk(documents_path):
            for file in files:
                if file.endswith('.txt'):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        if not content.strip():
                            self.logger.warning(f"Skipping empty file: {filepath}")
                            continue

                        # Index document
                        doc = {
                            'content': content,
                            'filename': file,
                            'path': filepath
                        }
                        
                        self.es_client.index(
                            index=self.index_name, 
                            document=doc,
                            refresh=True  # Ensure document is immediately searchable
                        )
                        
                        indexed_count += 1
                        self.logger.info(f"Indexed: {filepath}")
                    
                    except Exception as e:
                        self.logger.error(f"Error indexing {filepath}: {e}")
                        continue
        
        if indexed_count == 0:
            self.logger.warning("No documents were indexed")
        else:
            self.logger.info(f"Successfully indexed {indexed_count} documents")
        
        return indexed_count

    def search_documents(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search indexed documents
        
        Args:
            query (str): Search query
            top_k (int): Number of top results to return
        
        Returns:
            List of top matching documents
        """
        if not query.strip():
            return []

        try:
            search_body = {
                'query': {
                    'match': {
                        'content': {
                            'query': query,
                            'analyzer': 'custom_analyzer'
                        }
                    }
                },
                'highlight': {
                    'fields': {
                        'content': {
                            'fragment_size': 300,
                            'number_of_fragments': 30,
                            'pre_tags': [''],
                            'post_tags': ['']
                        }
                    }
                }
            }
            
            results = self.es_client.search(
                index=self.index_name, 
                body=search_body, 
                size=top_k
            )
            
            formatted_results = []
            for hit in results['hits']['hits']:
                result = {
                    'filename': hit['_source']['filename'],
                    'path': hit['_source']['path'],
                    'score': hit['_score'],
                    'highlights': hit.get('highlight', {}).get('content', [])
                }
                formatted_results.append(result)
            
            return formatted_results

        except Exception as e:
            self.logger.error(f"Search error: {str(e)}")
            raise
