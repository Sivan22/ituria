# AI Document Search Agent

![alt text](image.png)

## Overview
This project implements an intelligent document search and question-answering system that combines:
- Elasticsearch for efficient document indexing and retrieval
- Anthropic's Claude-3 for keyword extraction, result evaluation, and answer generation
- Custom search refinement workflow for improved answer accuracy

## Features
- Smart document indexing with custom analyzer for improved search relevance
- Intelligent keyword extraction from natural language questions
- Automated search result evaluation and refinement
- Multi-attempt search strategy with confidence scoring
- Context-aware answer generation using Claude-3
- Comprehensive error handling and logging
- Support for multilingual queries and documents

## Prerequisites
- Python 3.11+
- Elasticsearch 8.x running locally
- Anthropic API Key (Claude-3 access required)

## Installation
1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up `.env` file with your credentials:
```
ANTHROPIC_API_KEY=your_anthropic_api_key
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
```

4. install elasticsearch:
```
docker run -d --name elasticsearch -p 9200:9200 -p 9300:9300 -e discovery.type=single-node -e xpack.security.enabled=false elasticsearch:8.12.1
```

## Usage
### Quick Start
Run the Flet UI to see the system in action with documents of your choice:
```bash
python flet_ui.py
```

## How It Works

### Document Indexing
- Documents are indexed using a custom Elasticsearch analyzer
- Supports automatic retry for connection handling
- Configurable index settings for optimal search performance

### Search and Answer Generation
1. **Keyword Extraction**: Uses Claude-3 to extract relevant search keywords from the question
2. **Document Search**: Performs Elasticsearch search with extracted keywords
3. **Result Evaluation**: 
   - Evaluates search results using Claude-3
   - Assigns confidence scores to determine result quality
   - Automatically refines search if confidence is low
4. **Answer Generation**: 
   - Generates comprehensive answers using relevant document contexts
   - Structures responses clearly and acknowledges any information gaps

## Configuration
- Modify `document_indexer.py` to customize Elasticsearch settings and analysis
- Adjust `agent_workflow.py` to configure:
  - Maximum search attempts
  - Confidence thresholds
  - Claude-3 parameters
  - Answer generation requirements
- Customize `demo.py` to test with different questions or document sets
- Customize `flet_ui' to fit the UX/UI to your needs

## Security
- Store API keys and sensitive data in environment variables
- Never commit `.env` file to version control
- Ensure proper access controls on Elasticsearch

## Troubleshooting
- Verify Elasticsearch is running and accessible
- Check Anthropic API key permissions and Claude-3 access
- Ensure proper file permissions for document directory
- Review logs for detailed error information

## Contributing
Contributions are welcome! Please submit pull requests or open issues for bugs and feature requests.

## License
MIT
