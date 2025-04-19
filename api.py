from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging
import uvicorn
from vector_store import VectorStore
from llm_service import LLMService
from agent import NetworkIntegrationAgent
from update_checker import UpdateChecker
from web_search import WebSearcher
from environment import ENABLE_WEB_SEARCH, MAX_SEARCH_RESULTS
from environment import GROQ_MODEL, GROQ_API_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vector_store = VectorStore()
llm_service = LLMService(model_name=GROQ_MODEL)

web_searcher = None
if ENABLE_WEB_SEARCH:
    web_searcher = WebSearcher(max_results=MAX_SEARCH_RESULTS)

agent = NetworkIntegrationAgent(vector_store, llm_service, web_searcher)

app = FastAPI(
    title="Network Integration Assistant API",
    description="API for assisting with network equipment integration across vendors",
    version="1.0.0"
)

class QueryRequest(BaseModel):
    query: str
    metadata: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    response: str
    analysis: Optional[Dict[str, Any]] = None

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return a response"""
    try:
        analysis = agent.analyze_query(request.query)
        
        response = agent.generate_response(request.query)
        
        return QueryResponse(
            response=response,
            analysis=analysis
        )
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
