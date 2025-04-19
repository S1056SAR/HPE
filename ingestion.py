import logging
import json
import os
import datetime
from scraper import NetworkDocScraper
from document_processor import DocumentProcessor
from vector_store import VectorStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    def __init__(self):
        self.scraper = NetworkDocScraper()
        self.processor = DocumentProcessor()
        self.vector_store = VectorStore()
        
        # Create tracking directory
        self.tracking_dir = os.path.join(os.getcwd(), "tracking")
        os.makedirs(self.tracking_dir, exist_ok=True)
        self.tracking_file = os.path.join(self.tracking_dir, "ingested_files.json")
        
        # Load tracking data
        if os.path.exists(self.tracking_file):
            with open(self.tracking_file, 'r') as f:
                self.ingested_files = json.load(f)
        else:
            self.ingested_files = {}
    
    def ingest_cisco_release_notes(self, url):
        """Ingest Cisco release notes from the provided URL"""
        logger.info(f"Starting ingestion of Cisco release notes from {url}")
        
        # Get document metadata and links
        document_links = self.scraper.parse_cisco_release_notes(url)
        logger.info(f"Found {len(document_links)} release note documents")
        
        processed_count = 0
        for doc_meta in document_links:
            try:
                # Check if document was already processed
                doc_key = f"cisco_release_notes_{doc_meta['url']}"
                if doc_key in self.ingested_files:
                    logger.info(f"Document already ingested: {doc_meta['title']}. Skipping.")
                    continue
                
                # Extract content from each document
                content = self.scraper.extract_document_content(doc_meta["url"])
                if not content:
                    logger.warning(f"No content extracted from {doc_meta['url']}")
                    continue
                
                # Extract additional product info from content
                product_info = self.processor.extract_product_info(content)
                
                # Combine all metadata
                metadata = {**doc_meta, **product_info}
                
                # Chunk the document
                chunks = self.processor.chunk_document(content, metadata)
                
                # Store in vector database
                self.vector_store.add_documents("cisco", chunks)
                
                # Mark document as ingested
                self.ingested_files[doc_key] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "title": doc_meta["title"],
                    "chunks": len(chunks)
                }
                self._save_tracking_data()
                
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(document_links)}: {doc_meta['title']}")
                
            except Exception as e:
                logger.error(f"Error processing {doc_meta['url']}: {str(e)}")
        
        logger.info(f"Completed ingestion of {processed_count} release notes")
    
    def ingest_cisco_config_guides(self, url):
        """Ingest Cisco configuration guides from the provided URL"""
        logger.info(f"Starting ingestion of Cisco configuration guides from {url}")
        
        # Get document metadata and links
        document_links = self.scraper.parse_cisco_config_guides(url)
        logger.info(f"Found {len(document_links)} configuration guide documents")
        
        processed_count = 0
        for doc_meta in document_links:
            try:
                # Check if document was already processed
                doc_key = f"cisco_config_guides_{doc_meta['url']}"
                if doc_key in self.ingested_files:
                    logger.info(f"Document already ingested: {doc_meta['title']}. Skipping.")
                    continue
                
                # Extract content from each document
                content = self.scraper.extract_document_content(doc_meta["url"])
                if not content:
                    logger.warning(f"No content extracted from {doc_meta['url']}")
                    continue
                
                product_info = self.processor.extract_product_info(content)
                
                metadata = {**doc_meta, **product_info}
                
                chunks = self.processor.chunk_document(content, metadata)
                
                self.vector_store.add_documents("cisco", chunks)
                
                self.ingested_files[doc_key] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "title": doc_meta["title"],
                    "chunks": len(chunks)
                }
                self._save_tracking_data()
                
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(document_links)}: {doc_meta['title']}")
                
            except Exception as e:
                logger.error(f"Error processing {doc_meta['url']}: {str(e)}")
        
        logger.info(f"Completed ingestion of {processed_count} configuration guides")
    
    def ingest_scraped_data(self, json_file_path):
        """Ingest data from scraped_data.json file"""
        # Check if file was already processed
        file_stat = os.stat(json_file_path)
        file_key = f"scraped_data_{json_file_path}_{file_stat.st_mtime}"
        
        if file_key in self.ingested_files:
            logger.info(f"File {json_file_path} was already ingested. Skipping.")
            return
            
        logger.info(f"Ingesting data from {json_file_path}")
        
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            chunks = []
            
            metadata = {
                "vendor": "Cisco",
                "doc_type": "Error Documentation",
                "source": "scraped_data.json"
            }
            
            content = json.dumps(data)  # Convert the entire JSON to string for processing
            error_chunks = self.processor.chunk_document(content, metadata)
            chunks.extend(error_chunks)
            
            self.vector_store.add_documents("error_codes", chunks)
            
            self.ingested_files[file_key] = {
                "timestamp": datetime.datetime.now().isoformat(),
                "chunks": len(chunks)
            }
            self._save_tracking_data()
            
            logger.info(f"Ingested {len(chunks)} chunks from scraped_data.json")
            
        except Exception as e:
            logger.error(f"Error ingesting scraped data: {str(e)}")
    
    def ingest_aruba_documentation(self, url, force_scrape=False):
        """Ingest Aruba AOS-CX documentation from the provided URL"""
        # Check if URL was already processed
        url_key = f"aruba_documentation_{url}"
        if not force_scrape and url_key in self.ingested_files:
            logger.info(f"URL {url} was already ingested. Skipping.")
            return
        
        logger.info(f"Starting ingestion of Aruba AOS-CX documentation from {url}")
        
        # Initialize the enhanced scraper
        self.scraper = NetworkDocScraper()
        
        # Get document links from the main page
        document_links = self.scraper.parse_aruba_documentation(url)
        logger.info(f"Found {len(document_links)} documents on main page")
        
        # Get additional documents from dropdown options
        dropdown_links = self.scraper.scrape_dropdown_options(url)
        logger.info(f"Found {len(dropdown_links)} additional documents from dropdown options")
        
        # Combine all document links
        all_links = document_links + dropdown_links
        
        processed_count = 0
        
        # Create a list to store the content and metadata for each document
        documents_data = []
        
        for doc_meta in all_links:
            try:
                # Check if document was already processed
                doc_key = f"aruba_doc_{doc_meta['url']}"
                if not force_scrape and doc_key in self.ingested_files:
                    logger.info(f"Document already ingested: {doc_meta['title']}. Skipping.")
                    continue
                
                # Extract content using the enhanced extract_document_content method
                content = self.scraper.extract_document_content(doc_meta)
                    
                if not content:
                    logger.warning(f"No content extracted from {doc_meta['url']}")
                    continue
                
                # Store the document content and metadata in the documents_data list
                document_info = {
                    'title': doc_meta['title'],
                    'url': doc_meta['url'],
                    'content': content  # Save the content here
                }
                documents_data.append(document_info)
                
                product_info = self.processor.extract_product_info(content)
                metadata = {**doc_meta, **product_info}
                chunks = self.processor.chunk_document(content, metadata)
                self.vector_store.add_documents("aruba", chunks)
                
                self.ingested_files[doc_key] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "title": doc_meta["title"],
                    "chunks": len(chunks)
                }
                self._save_tracking_data()
                
                processed_count += 1
                logger.info(f"Processed {processed_count}/{len(all_links)}: {doc_meta['title']}")
                if processed_count == 122:
                    break
            
            except Exception as e:
                logger.error(f"Error processing {doc_meta['url']}: {str(e)}")
        
        # Save the documents_data as a JSON file
        json_file_path = 'aruba_documents_content.json'
        with open(json_file_path, 'w', encoding = 'utf-8') as json_file:
            json.dump(documents_data, json_file, ensure_ascii = False, indent = 4)
        
        # Mark URL as completely processed
        self.ingested_files[url_key] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "documents_processed": processed_count
        }
        self._save_tracking_data()
        
        logger.info(f"Completed ingestion of {processed_count} Aruba documents")


    # def ingest_juniper_documentation(self, url):
    #     """Ingest Juniper documentation from the provided URL"""
    #     # Check if URL was already processed
    #     url_key = f"juniper_documentation_{url}"
    #     if url_key in self.ingested_files:
    #         logger.info(f"URL {url} was already ingested. Skipping.")
    #         return
            
    #     logger.info(f"Starting ingestion of Juniper documentation from {url}")
        
    #     # Implementation would depend on your scraper's capabilities for Juniper
    #     # This is a placeholder for future implementation
        
    #     logger.info(f"Juniper documentation ingestion not yet implemented")
    
    # def ingest_arista_documentation(self, url):
    #     """Ingest Arista documentation from the provided URL"""
    #     # Check if URL was already processed
    #     url_key = f"arista_documentation_{url}"
    #     if url_key in self.ingested_files:
    #         logger.info(f"URL {url} was already ingested. Skipping.")
    #         return
            
    #     logger.info(f"Starting ingestion of Arista documentation from {url}")
        
    #     # Implementation would depend on your scraper's capabilities for Arista
    #     # This is a placeholder for future implementation
        
    #     logger.info(f"Arista documentation ingestion not yet implemented")

    def _load_tracking_data(self): 
        """Load tracking data from file."""
        # Use the logic already present in __init__ or _load_ingestion_tracking
        tracking_file_path = getattr(self, 'tracking_file', os.path.join(getattr(self, 'tracking_dir', './tracking'), "ingested_files.json"))
        if os.path.exists(tracking_file_path):
            try:
                with open(tracking_file_path, 'r') as f:
                    self.ingested_files = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from tracking file: {tracking_file_path}. Starting with empty tracking.")
                self.ingested_files = {}
        else:
            self.ingested_files = {}
    
    # def _save_tracking_data(self):
    #     """Save tracking data to file"""
    #     with open(self.tracking_file, 'w') as f:
    #         json.dump(self.ingested_files, f, indent=2)
    def _save_tracking_data(self):
        """Save tracking data to file"""
        # This method should already exist in ingestion.py [5]
        tracking_file_path = getattr(self, 'tracking_file', os.path.join(getattr(self, 'tracking_dir', './tracking'), "ingested_files.json"))
        tracking_dir_path = os.path.dirname(tracking_file_path)
        os.makedirs(tracking_dir_path, exist_ok=True) # Ensure directory exists
        try:
            with open(tracking_file_path, 'w') as f:
                json.dump(self.ingested_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tracking data to {tracking_file_path}: {e}")


    def run_full_ingestion(self):
        """Run the complete ingestion pipeline for all vendors"""
        # Cisco documentation
        self.ingest_cisco_release_notes("https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-release-notes-list.html")
        self.ingest_cisco_config_guides("https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-installation-and-configuration-guides-list.html")
        
        # Aruba documentation
        self.ingest_aruba_documentation("https://arubanetworking.hpe.com/techdocs/AOS-CX/Consolidated_RNs/HTML-9300/Content/PDFs.htm")
        
        # Scraped data
        if os.path.exists("scraped_data.json"):
            self.ingest_scraped_data("scraped_data.json")
        
        logger.info("Full ingestion pipeline completed")
    
    def reset_ingestion_tracking(self):
        self.ingested_files = {}
        self._save_tracking_data()
        logger.info("Ingestion tracking has been reset")



