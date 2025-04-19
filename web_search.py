import logging
from duckduckgo_search import DDGS
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class WebSearcher:
    def __init__(self, max_results=5):
        self.ddgs = DDGS()
        self.max_results = max_results
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Perform a web search using DuckDuckGo"""
        try:
            logger.info(f"Performing web search for: {query}")
            
            # Perform the search
            results = list(self.ddgs.text(
                query,
                region="wt-wt",
                safesearch="Off",
                timelimit="m",  # Last month
            ))
            
            # Limit results
            results = results[:self.max_results]
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("body", ""),
                    "link": result.get("href", ""),
                    "source": "web_search"
                })
            
            logger.info(f"Found {len(formatted_results)} web search results")
            return formatted_results
        except Exception as e:
            logger.error(f"Error performing web search: {str(e)}")
            return []
