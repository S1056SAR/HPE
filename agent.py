import logging
import re
import json
from typing import Dict, List, Any, Optional

from vector_store import VectorStore 
from llm_service import LLMService
from web_search import WebSearcher 

logger = logging.getLogger(__name__)

class NetworkIntegrationAgent:
    def __init__(self, vector_store: VectorStore, llm_service: LLMService, web_searcher: Optional[WebSearcher] = None):
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.web_searcher = web_searcher

    def extract_vendors_from_query(self, query: str) -> Dict[str, str]:
        """Extract vendor information from the user query"""
        
        vendors = ["Cisco", "Juniper", "Arista", "Aruba", "HPE", "Huawei", "Fortinet", "Palo Alto", "F5", "Checkpoint"]
        found_vendors = {}
        
        
        from_to_match = re.search(r"(?:from|integrate)\s+([A-Za-z0-9-]+)\s+(?:to|with)\s+([A-Za-z0-9-]+)", query, re.IGNORECASE)
        if from_to_match:
            source_candidate = from_to_match.group(1)
            target_candidate = from_to_match.group(2)
            for v in vendors:
                if v.lower() == source_candidate.lower():
                    found_vendors["source"] = v
                if v.lower() == target_candidate.lower():
                    found_vendors["target"] = v
            if "source" in found_vendors and "target" in found_vendors:
                return found_vendors

        
        for vendor in vendors:
            if vendor.lower() in query.lower():
                
                if "source" not in found_vendors: # and not re.search(rf"to\s+{vendor}", query, re.IGNORECASE):
                    found_vendors["source"] = vendor
                elif "target" not in found_vendors: # and not re.search(rf"from\s+{vendor}", query, re.IGNORECASE):
                    found_vendors["target"] = vendor
                else: 
                    pass 
        return found_vendors


    def extract_product_from_query(self, query: str) -> Dict[str, str]:
        """Extract product information from the user query"""
        product_patterns = [
            r"Nexus\s+\d+[A-Za-z0-9-]*", r"Catalyst\s+\d+[A-Za-z0-9-]*",
            r"MX\s*\d+[A-Za-z0-9-]*", r"EX\s*\d+[A-Za-z0-9-]*", r"SRX\s*\d+[A-Za-z0-9-]*", r"QFX\s*\d+[A-Za-z0-9-]*",
            r"DCS-\d+[A-Za-z0-9-]*", r"7\d{3}X[A-Za-z0-9-]*",
            r"FortiGate\s+\d+[A-Za-z0-9-]*", r"PA-\d+[A-Za-z0-9-]*",
            r"CX\s+\d+[A-Za-z0-9-]*",  # Aruba CX
            r"AOS-CX\s+\d+\.\d+"     # AOS-CX versions
        ]
        found_products = {}
        
        for pattern in product_patterns:
            matches = re.findall(pattern, query, re.IGNORECASE)
            for match in matches:
                
                if "source_product" not in found_products:
                    found_products["source_product"] = match
                elif "target_product" not in found_products:
                    found_products["target_product"] = match
                break 
            if "source_product" in found_products and "target_product" in found_products:
                break
        return found_products

    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze the user query to extract key information"""
        analysis = {"original_query": query}
        
        vendors = self.extract_vendors_from_query(query)
        analysis.update(vendors)
        
        products = self.extract_product_from_query(query)
        analysis.update(products)
        
        if re.search(r"how\s+to\s+integrate|integrat(e|ion)", query, re.IGNORECASE):
            analysis["intent"] = "integration"
        elif re.search(r"configur(e|ation)|setup|set\s+up", query, re.IGNORECASE):
            analysis["intent"] = "configuration"
        elif re.search(r"troubleshoot|problem|issue|error|not\s+working", query, re.IGNORECASE):
            analysis["intent"] = "troubleshooting"
        elif re.search(r"migrat(e|ion)|move\s+from", query, re.IGNORECASE):
            analysis["intent"] = "migration"
        elif re.search(r"features|capabilities|specifications|compare", query, re.IGNORECASE):
            analysis["intent"] = "product_info"
        else:
            analysis["intent"] = "general"
            
        
        if "source" not in analysis and "target" not in analysis:
            all_vendors = ["Cisco", "Juniper", "Arista", "Aruba", "HPE"] 
            for v_name in all_vendors:
                if v_name.lower() in query.lower():
                    analysis["target"] = v_name 
                    break
        return analysis

    def retrieve_relevant_context(self, query: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve relevant context based on the query analysis using single vendor collection"""
        context_results = {}
        
        
        filter_vendor = analysis.get("target", analysis.get("source")) 
        
        search_text = query 
        
        
        if analysis.get("intent") == "troubleshooting":
            
            error_results = self.vector_store.query(
                collection_name=VectorStore.ERROR_CODES_COLLECTION_NAME,
                query_text=query,
                n_results=3
            )
            if error_results and error_results.get('documents') and error_results['documents'][0]:
                 context_results[VectorStore.ERROR_CODES_COLLECTION_NAME] = error_results

            
            if filter_vendor:
                 search_text_vendor_troubleshoot = f"{filter_vendor} {analysis.get('target_product','')} troubleshooting {query}"
                 vendor_troubleshoot_results = self.vector_store.query(
                    collection_name=VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME,
                    query_text=search_text_vendor_troubleshoot,
                    n_results=2,
                    where_filter={"vendor": filter_vendor.lower()}
                )
                 if vendor_troubleshoot_results and vendor_troubleshoot_results.get('documents') and vendor_troubleshoot_results['documents'][0]:
                    
                    if VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME in context_results:
                       
                        context_results[VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME + "_troubleshooting"] = vendor_troubleshoot_results
                    else:
                        context_results[VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME] = vendor_troubleshoot_results
            return context_results 

        
        if filter_vendor:
            
            if analysis.get("target_product"):
                search_text = f"{filter_vendor} {analysis.get('target_product')} {analysis.get('intent')} {query}"
            elif analysis.get("source_product") and analysis.get("intent") == "migration":
                 search_text = f"migrate from {analysis.get('source')} {analysis.get('source_product')} to {filter_vendor} {query}"
            else:
                search_text = f"{filter_vendor} {analysis.get('intent')} {query}"

            vendor_docs_results = self.vector_store.query(
                collection_name=VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME,
                query_text=search_text,
                n_results=3,
                where_filter={"vendor": filter_vendor.lower()}
            )
            if vendor_docs_results and vendor_docs_results.get('documents') and vendor_docs_results['documents'][0]:
                context_results[VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME] = vendor_docs_results
        
        
        if not context_results or analysis.get("intent") == "general":
            
            if not context_results.get(VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME):
                general_vendor_results = self.vector_store.query(
                    collection_name=VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME,
                    query_text=query, 
                    n_results=2
                )
                if general_vendor_results and general_vendor_results.get('documents') and general_vendor_results['documents'][0]:
                    context_results[VectorStore.ALL_VENDOR_DOCS_COLLECTION_NAME] = general_vendor_results
            
            

        return context_results

    def _is_sufficient(self, context_results: Dict[str, Any]) -> bool:
        """Determine if the retrieved context is sufficient to answer the query"""
        total_documents = 0
        if not context_results: return False

        for collection_name, results_data in context_results.items():
            # ChromaDB query results are nested, documents are in results_data['documents'][0]
            if isinstance(results_data, dict) and \
               'documents' in results_data and \
               isinstance(results_data['documents'], list) and \
               len(results_data['documents']) > 0 and \
               isinstance(results_data['documents'][0], list):
                total_documents += len(results_data['documents'][0])
        
        # If we have at least 1-2 relevant documents, consider it sufficient for now.
        # This threshold might need adjustment.
        is_sufficient = total_documents >= 1 
        logger.debug(f"Context sufficiency check: {total_documents} documents found. Sufficient: {is_sufficient}")
        return is_sufficient


    def _combine_results(self, context_results: Dict[str, Any], web_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine vector store results with web search results into context_results structure."""
        if not web_results:
            return context_results

        # Prepare web results in a format similar to ChromaDB's output for one "collection"
        web_search_collection_key = "web_search_results" # Or VectorStore.WEB_SEARCH_COLLECTION_NAME if defined
        
        web_docs = []
        web_metadatas = []
        web_ids = []
        web_distances = [] # Dummy distances

        for i, result in enumerate(web_results):
            web_docs.append(f"Title: {result.get('title', '')}\nSnippet: {result.get('snippet', '')}\nSource: {result.get('link', '')}")
            web_metadatas.append({
                'title': result.get('title', ''),
                'source': result.get('link', ''),
                'doc_type': 'Web Search Result',
                'vendor': 'web_search' # Generic vendor tag for web results
            })
            web_ids.append(f"web_{i}")
            web_distances.append(1.0) # Assign a dummy distance

        if web_docs:
            context_results[web_search_collection_key] = {
                'documents': [web_docs],
                'metadatas': [web_metadatas],
                'ids': [web_ids],
                'distances': [web_distances]
            }
        return context_results

    def generate_response(self, query: str) -> str:
        """Generate a response to the user's query with web search fallback"""
        try:
            analysis = self.analyze_query(query)
            logger.info(f"Query analysis: {json.dumps(analysis, indent=2)}")

            context_results = self.retrieve_relevant_context(query, analysis)
            
            if not self._is_sufficient(context_results) and self.web_searcher:
                logger.info("Vector store results insufficient or empty. Performing web search.")
                # Construct a more specific search query
                search_query_for_web = query
                if analysis.get("target"):
                    search_query_for_web = f"{analysis.get('target')} "
                    if analysis.get("target_product"):
                        search_query_for_web += f"{analysis.get('target_product')} "
                    search_query_for_web += query # Append original query for context
                
                web_search_items = self.web_searcher.search(search_query_for_web)
                if web_search_items:
                    logger.info(f"Found {len(web_search_items)} results from web search.")
                    context_results = self._combine_results(context_results, web_search_items)
                else:
                    logger.info("No results found from web search.")
            
            formatted_context = self.llm_service.format_context_for_prompt(context_results)
            
            prompt_to_llm = self.llm_service.create_integration_prompt(query, formatted_context)
            
            response = self.llm_service.generate_response(prompt_to_llm)
            return response

        except Exception as e:
            logger.error(f"Error in NetworkIntegrationAgent.generate_response: {str(e)}", exc_info=True)
            return "I encountered an error while processing your request. Please try again or rephrase your question."
