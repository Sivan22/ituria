from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import sys
from pathlib import Path

# Add parent directory to Python path to import our modules
parent_dir = str(Path(__file__).parent.parent.parent)
sys.path.append(parent_dir)

from tantivy_search_agent import TantivySearchAgent
from agent_workflow import SearchAgent

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize search agents
INDEX_PATH = "./index"
try:
    tantivy_agent = TantivySearchAgent(INDEX_PATH)
    if tantivy_agent.validate_index():
        search_agent = SearchAgent(tantivy_agent)
    else:
        print(f"Failed to validate index at {INDEX_PATH}", file=sys.stderr)
        tantivy_agent = None
        search_agent = None
except Exception as e:
    print(f"Failed to initialize search agent: {str(e)}", file=sys.stderr)
    tantivy_agent = None
    search_agent = None

class SearchRequest(BaseModel):
    query: str
    numResults: Optional[int] = 5
    maxIterations: Optional[int] = 3

class SearchResponse(BaseModel):
    success: bool
    results: Optional[Dict[str, Any]] = None
    message: Optional[str] = None

@app.post("/api/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    if not search_agent or not tantivy_agent:
        raise HTTPException(
            status_code=500,
            detail="Search agent not properly initialized. Please check the index directory."
        )

    if not request.query:
        raise HTTPException(status_code=400, detail="No query provided")

    try:
        steps = []
        def step_callback(step):
            steps.append(step)

        result = search_agent.search_and_answer(
            query=request.query,
            num_results=request.numResults,
            max_iterations=request.maxIterations,
            on_step=step_callback
        )

        return SearchResponse(
            success=True,
            results={
                "steps": steps,
                "finalResult": result
            }
        )
    except Exception as e:
        return SearchResponse(
            success=False,
            message=str(e)
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
