import logging
from typing import Dict, List, Any, Optional
from llm_service import LLMService

logger = logging.getLogger(__name__)

class TopologyGenerator:
    """
    AI-powered topology diagram generator that creates Mermaid diagrams
    based on the content of responses and query analysis.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
    
    def generate_topology(self, response: str, analysis: Dict[str, Any]) -> Optional[str]:
        """
        Generate a Mermaid topology diagram based on the response content and query analysis.
        
        Args:
            response: The text response generated for the user
            analysis: The analysis of the user's query (contains intent, vendors, products)
            
        Returns:
            A Mermaid-formatted topology diagram or None if generation fails
        """
        try:
            # Extract key information from analysis
            intent = analysis.get("intent", "general")
            source_vendor = analysis.get("source", "")
            target_vendor = analysis.get("target", "")
            source_product = analysis.get("source_product", "")
            target_product = analysis.get("target_product", "")
            
            logger.info(f"Generating topology for intent: {intent}, source: {source_vendor}, target: {target_vendor}")
            
            # Create a prompt for the LLM to generate the topology
            prompt = self._create_topology_prompt(
                response=response,
                intent=intent,
                source_vendor=source_vendor,
                target_vendor=target_vendor,
                source_product=source_product,
                target_product=target_product
            )
            
            logger.info("Sending prompt to LLM service")
            
            # For debugging, create a fallback diagram if LLM fails
            fallback_diagram = self._create_fallback_diagram(source_vendor, target_vendor, intent)
            
            try:
                # Generate the Mermaid diagram using the LLM
                mermaid_diagram = self.llm_service.generate_text(prompt)
                logger.info(f"Received response from LLM service: {mermaid_diagram[:100]}...")
            except Exception as llm_error:
                logger.error(f"LLM service error: {str(llm_error)}")
                logger.info("Using fallback diagram")
                return fallback_diagram
            
            # Extract just the Mermaid code from the response
            mermaid_diagram = self._extract_mermaid_code(mermaid_diagram)
            
            if not mermaid_diagram:
                logger.warning("Failed to extract valid Mermaid diagram from LLM response")
                logger.info("Using fallback diagram")
                return fallback_diagram
                
            return mermaid_diagram
            
        except Exception as e:
            logger.error(f"Error generating topology diagram: {str(e)}")
            # Return a simple default diagram as fallback
            return self._create_fallback_diagram(source_vendor, target_vendor, intent)
    
    def _create_topology_prompt(
        self, 
        response: str, 
        intent: str,
        source_vendor: str,
        target_vendor: str,
        source_product: str,
        target_product: str
    ) -> str:
        """Create a prompt for the LLM to generate a topology diagram"""
        
        # Base prompt structure
        prompt = f"""
        Based on the following network integration response, create a Mermaid diagram that visualizes the network topology.
        
        RESPONSE:
        {response}
        
        CONTEXT:
        - Intent: {intent}
        - Source Vendor: {source_vendor}
        - Target Vendor: {target_vendor}
        - Source Product: {source_product}
        - Target Product: {target_product}
        
        INSTRUCTIONS:
        1. Create a Mermaid diagram in 'graph TD' format that shows the network topology
        2. Include all relevant devices mentioned in the response
        3. Use simple arrow syntax (A --> B) for connections between devices
        4. DO NOT use complex connection labels with dashes (like A -- label --> B), as this can cause syntax errors
        5. Group related devices using subgraph if appropriate
        6. Use descriptive node labels that include vendor and product names
        7. Ensure all node IDs are simple (A, B, C, etc.) and labels are in square brackets [Label]
        8. Only include the Mermaid code, nothing else
        9. Test your syntax carefully - avoid special characters in node labels
        
        EXAMPLE OF VALID SYNTAX:
        ```mermaid
        graph TD
            A[Cisco Router] --> B[Aruba Switch]
            B --> C[User Devices]
            
            subgraph Data_Center
                D[Server 1] --> E[Server 2]
            end
            
            B --> D
        ```
        
        MERMAID DIAGRAM FOR THIS RESPONSE:
        ```mermaid
        graph TD
        """
        
        return prompt
    
    def _create_fallback_diagram(self, source_vendor: str, target_vendor: str, intent: str) -> str:
        """Create a basic fallback diagram when LLM generation fails"""
        # Default to generic names if vendors not provided
        source = source_vendor if source_vendor else "Source"
        target = target_vendor if target_vendor else "Target"
        
        # Sanitize vendor names for Mermaid compatibility
        source = self._sanitize_for_mermaid(source)
        target = self._sanitize_for_mermaid(target)
        
        # Create appropriate diagram based on intent
        if intent == "migration":
            return f"graph TD\n    subgraph Before_Migration\n        A[{source} Switch] --> B[User Devices]\n        A --> E[Router]\n    end\n    subgraph After_Migration\n        C[{target} Switch] --> B\n        C --> E\n    end"
        
        elif intent == "integration":
            return f"graph TD\n    A[{source} Switch] --> B[{target} Switch]\n    A --> C[User Devices]\n    B --> D[Servers]"
        
        elif intent == "configuration":
            return f"graph TD\n    A[{source} Switch] --> B[{target} Switch]\n    A --> C[VLAN 10]\n    B --> C"
        
        elif intent == "interoperability":
            return f"graph TD\n    A[{source} Switch] --> B[{target} Switch]\n    C[Standard Protocols] --> A\n    C --> B"
        
        else:  # Default generic diagram
            return f"graph TD\n    A[{source} Device] --> B[{target} Device]"
            
    def _sanitize_for_mermaid(self, text: str) -> str:
        """Sanitize text for use in Mermaid diagrams"""
        # Replace spaces with underscores
        text = text.replace(" ", "_")
        # Remove special characters that might cause issues
        text = ''.join(c for c in text if c.isalnum() or c == '_')
        return text
    
    def _extract_mermaid_code(self, llm_response: str) -> Optional[str]:
        """Extract just the Mermaid code from the LLM response"""
        try:
            # Look for code between ```mermaid and ``` markers
            if "```mermaid" in llm_response:
                start_idx = llm_response.find("```mermaid")
                end_idx = llm_response.find("```", start_idx + 10)
                
                if end_idx > start_idx:
                    # Extract the code and remove the ```mermaid marker
                    mermaid_code = llm_response[start_idx + 10:end_idx].strip()
                    return mermaid_code
            
            # If no markers, check if the response starts with graph TD
            if "graph TD" in llm_response:
                return llm_response.strip()
                
            return None
        except Exception as e:
            logger.error(f"Error extracting Mermaid code: {str(e)}")
            return None
