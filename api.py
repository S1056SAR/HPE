from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import logging
import uvicorn
import json
import os
from datetime import datetime
from vector_store import VectorStore
from llm_service import LLMService
from agent import NetworkIntegrationAgent
from update_checker import UpdateChecker
from web_search import WebSearcher
from topology_generator import TopologyGenerator
from environment import ENABLE_WEB_SEARCH, MAX_SEARCH_RESULTS
from environment import GROQ_MODEL, GROQ_API_KEY

#Updated till the final DB was created
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

vector_store = VectorStore()
llm_service = LLMService(model_name=GROQ_MODEL)

web_searcher = None
if ENABLE_WEB_SEARCH:
    web_searcher = WebSearcher(max_results=MAX_SEARCH_RESULTS)

agent = NetworkIntegrationAgent(vector_store, llm_service, web_searcher)
topology_generator = TopologyGenerator(llm_service)

# Store recent queries for topology visualization
recent_queries = []
MAX_RECENT_QUERIES = 10

# Initialize templates
templates_dir = os.path.join(os.path.dirname(__file__), "templates")
templates = Jinja2Templates(directory=templates_dir)

app = FastAPI(
    title="Network Integration Assistant API",
    description="API for assisting with network equipment integration across vendors",
    version="1.0.0"
)

# Add route for index page to redirect to topology viewer
@app.get("/", include_in_schema=False)
async def index():
    return {"message": "Network Integration Assistant API", "docs": "/docs", "topology_viewer": "/topology"}

class QueryRequest(BaseModel):
    query: str
    metadata: Optional[Dict[str, Any]] = None

class QueryResponse(BaseModel):
    response: str
    analysis: Optional[Dict[str, Any]] = None
    topology_mermaid: Optional[str] = None

# Topology generation is now handled dynamically by the TopologyGenerator class

@app.post("/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process a user query and return a response"""
    try:
        analysis = agent.analyze_query(request.query)
        response = agent.generate_response(request.query)
        
        # Generate topology diagram dynamically based on response content and analysis
        topology_mermaid = topology_generator.generate_topology(response, analysis)
        
        # Create response object
        query_response = QueryResponse(
            response=response,
            analysis=analysis,
            topology_mermaid=topology_mermaid
        )
        
        # Store query for topology visualization
        query_data = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "timestamp": datetime.now().isoformat(),
            "original_query": request.query,
            "response": response[:500] + "..." if len(response) > 500 else response,  # Truncate for storage
            "source": analysis.get("source", ""),
            "target": analysis.get("target", ""),
            "intent": analysis.get("intent", ""),
            "topology_mermaid": topology_mermaid
        }
        
        # Add to recent queries and maintain max size
        global recent_queries
        recent_queries.insert(0, query_data)
        if len(recent_queries) > MAX_RECENT_QUERIES:
            recent_queries = recent_queries[:MAX_RECENT_QUERIES]
        
        return query_response
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/topology", response_class=HTMLResponse)
async def get_topology_viewer(request: Request):
    """Serve the topology viewer HTML page"""
    return templates.TemplateResponse("topology_viewer.html", {"request": request})


@app.get("/api/topology")
async def get_topology_data(query_id: str = "latest"):
    """Get topology data for visualization"""
    if not recent_queries:
        raise HTTPException(status_code=404, detail="No queries available")
    
    if query_id == "latest":
        # Return the most recent query
        return recent_queries[0]
    else:
        # Find query by ID
        for query in recent_queries:
            if query["id"] == query_id:
                return query
        
        raise HTTPException(status_code=404, detail=f"Query with ID {query_id} not found")


@app.get("/api/recent-queries")
async def get_recent_queries():
    """Get list of recent queries"""
    return {
        "queries": [{
            "id": q["id"],
            "timestamp": q["timestamp"],
            "original_query": q["original_query"],
            "source": q["source"],
            "target": q["target"],
            "intent": q["intent"]
        } for q in recent_queries]
    }
