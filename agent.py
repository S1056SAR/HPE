import logging
import re
import json
from typing import Dict, List, Any
from vector_store import VectorStore
from llm_service import LLMService
from web_search import WebSearcher

logger = logging.getLogger(__name__)

class NetworkIntegrationAgent:
    def __init__(self, vector_store: VectorStore, llm_service: LLMService, web_searcher: WebSearcher = None):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.web_searcher = web_searcher
    
    def extract_vendors_from_query(self, query: str) -> Dict[str, str]:
        """Extract vendor information from the user query"""
        vendors = ["Cisco", "Juniper", "Arista", "Aruba", "HPE", "Huawei", "Fortinet", "Palo Alto", "F5", "Checkpoint"]
        
        found_vendors = {}
        
        for vendor in vendors:
            if vendor.lower() in query.lower():
                if re.search(rf"from\s+{vendor}", query, re.IGNORECASE):
                    found_vendors["source"] = vendor
                elif re.search(rf"to\s+{vendor}", query, re.IGNORECASE):
                    found_vendors["target"] = vendor
                elif re.search(rf"with\s+{vendor}", query, re.IGNORECASE):
                    if "target" not in found_vendors:
                        found_vendors["target"] = vendor
                else:
                    if "source" not in found_vendors:
                        found_vendors["source"] = vendor
                    elif "target" not in found_vendors:
                        found_vendors["target"] = vendor
        
        return found_vendors
    
    def extract_product_from_query(self, query: str) -> Dict[str, str]:
        """Extract product information from the user query"""
        product_patterns = [
            r"Nexus\s+\d+",
            r"Catalyst\s+\d+",
            r"MX\s+\d+",
            r"EX\s+\d+",
            r"SRX\s+\d+",
            r"QFX\s+\d+",
            r"DCS-\d+",
            r"7\d{3}X",
            r"FortiGate\s+\d+",
            r"PA-\d+",
            r"CX\s+\d+",  # Added for Aruba CX switches
            r"AOS-CX\s+\d+\.\d+"  # Added for AOS-CX versions
        ]
        
        found_products = {}
        
        for pattern in product_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            if matches:
                for match in matches:
                    context = query[max(0, query.lower().find(match.lower()) - 20):
                               min(len(query), query.lower().find(match.lower()) + len(match) + 20)]
                    
                    if re.search(r"from|current|existing|have", context, re.IGNORECASE):
                        found_products["source_product"] = match
                    elif re.search(r"to|new|target|integrate", context, re.IGNORECASE):
                        found_products["target_product"] = match
                    else:
                        if "source_product" not in found_products:
                            found_products["source_product"] = match
                        elif "target_product" not in found_products:
                            found_products["target_product"] = match
        
        return found_products
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze the user query to extract key information"""
        analysis = {}
        
        # Extract vendors
        vendors = self.extract_vendors_from_query(query)
        analysis.update(vendors)
        
        # Extract products
        products = self.extract_product_from_query(query)
        analysis.update(products)
        
        # Determine query type/intent
        if re.search(r"how\s+to\s+integrate|integrat(e|ion)", query, re.IGNORECASE):
            analysis["intent"] = "integration"
        elif re.search(r"configur(e|ation)|setup|set\s+up", query, re.IGNORECASE):
            analysis["intent"] = "configuration"
        elif re.search(r"troubleshoot|problem|issue|error|not\s+working", query, re.IGNORECASE):
            analysis["intent"] = "troubleshooting"
        elif re.search(r"migrat(e|ion)|move\s+from", query, re.IGNORECASE):
            analysis["intent"] = "migration"
        elif re.search(r"features|capabilities|specifications", query, re.IGNORECASE):
            analysis["intent"] = "product_info"
        else:
            analysis["intent"] = "general"
        
        return analysis
    
    def retrieve_relevant_context(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant context based on the query analysis"""
        search_queries = {}
        
        if analysis.get("intent") == "integration":
            if analysis.get("source") and analysis.get("target"):
                search_queries["integration_guides"] = f"integrate {analysis.get('source')} with {analysis.get('target')}"
                if analysis.get("source_product") and analysis.get("target_product"):
                    search_queries["integration_guides"] += f" {analysis.get('source_product')} {analysis.get('target_product')}"
        
        elif analysis.get("intent") == "configuration":
            if analysis.get("target"):
                search_queries["config_guides"] = f"configure {analysis.get('target')}"
                if analysis.get("target_product"):
                    search_queries["config_guides"] += f" {analysis.get('target_product')}"
        
        elif analysis.get("intent") == "troubleshooting":
            search_queries["error_codes"] = query
        
        elif analysis.get("intent") == "product_info":
            if analysis.get("target_product"):
                search_queries["release_notes"] = f"{analysis.get('target_product')}"
                search_queries["config_guides"] = f"{analysis.get('target_product')}"
        
        # Add a general search query for release notes
        if analysis.get("target"):
            search_queries["release_notes"] = f"{analysis.get('target')}"
            if analysis.get("target_product"):
                search_queries["release_notes"] += f" {analysis.get('target_product')}"
        
        # If no specific queries were constructed, use the original query for all collections
        if not search_queries:
            for collection in self.vector_store.collections:
                search_queries[collection] = query
        
        # Retrieve context from each collection
        context_results = {}
        for collection, search_query in search_queries.items():
            if collection in self.vector_store.collections:
                results = self.vector_store.query(collection, search_query, n_results=3)
                context_results[collection] = results
        
        return context_results
    
    def _is_sufficient(self, context_results: Dict[str, Any]) -> bool:
        """Determine if the retrieved context is sufficient to answer the query"""
        total_documents = 0
        for collection, results in context_results.items():
            if 'documents' in results and results['documents']:
                total_documents += len(results['documents'][0])
        
        # If we have at least 2 relevant documents, consider it sufficient
        return total_documents >= 2
    
    def _combine_results(self, context_results: Dict[str, Any], web_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine vector store results with web search results"""
        # Create a new collection for web results if it doesn't exist
        if 'web_search' not in context_results:
            context_results['web_search'] = {
                'documents': [[]],
                'metadatas': [[]],
                'distances': [[]],
                'ids': [[]]
            }
        
        # Add web results to the context
        for result in web_results:
            context_results['web_search']['documents'][0].append(
                f"Title: {result['title']}\nSnippet: {result['snippet']}\nSource: {result['link']}"
            )
            context_results['web_search']['metadatas'][0].append({
                'title': result['title'],
                'source': result['link'],
                'doc_type': 'Web Search Result'
            })
            # Add dummy values for distances and ids
            context_results['web_search']['distances'][0].append(1.0)
            context_results['web_search']['ids'][0].append(f"web_{len(context_results['web_search']['ids'][0])}")
        
        return context_results
    
    def generate_response(self, query: str) -> str:
        """Generate a response to the user's query with web search fallback"""
        try:
            # Analyze the query
            analysis = self.analyze_query(query)
            logger.info(f"Query analysis: {json.dumps(analysis, indent=2)}")
            
            # Retrieve relevant context from vector store
            context_results = self.retrieve_relevant_context(query, analysis)
            
            # Check if the retrieved context is sufficient
            if not self._is_sufficient(context_results) and self.web_searcher:
                logger.info("Vector store results insufficient. Performing web search.")
                
                # Construct a more specific search query based on analysis
                search_query = query
                if analysis.get("target") and analysis.get("target_product"):
                    search_query = f"{analysis.get('target')} {analysis.get('target_product')} {query}"
                
                # Perform web search
                web_results = self.web_searcher.search(search_query)
                
                # Combine vector store and web search results
                context_results = self._combine_results(context_results, web_results)
                
                logger.info(f"Combined results with web search. Total web results: {len(web_results)}")
            
            # Format context for the prompt
            formatted_context = self.llm_service.format_context_for_prompt(context_results)
            
            # Create the prompt
            if 'web_search' in context_results and context_results['web_search']['documents'][0]:
                # Create a prompt that acknowledges web search results
                prompt = f"""
You are a network integration specialist assistant. Use the following context information to answer the user's question. 
Some of this information comes from our knowledge base, and some comes from recent web searches.

{formatted_context}

USER QUERY: {query}

Based on the context provided, give a detailed, accurate response that helps the user. 
If the information comes from web search results, acknowledge this in your response.
"""
            else:
                # Use the standard prompt
                prompt = self.llm_service.create_integration_prompt(query, formatted_context)
            
            # Generate response
            response = self.llm_service.generate_response(prompt)
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I encountered an error while processing your request. Please try again or rephrase your question."
