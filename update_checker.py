import schedule
import time
import logging
from datetime import datetime
import threading
from scraper import NetworkDocScraper
from ingestion import DataIngestionPipeline
from environment import UPDATE_CHECK_INTERVAL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
    
class UpdateChecker:
    def __init__(self):
        self.scraper = NetworkDocScraper()
        self.ingestion_pipeline = DataIngestionPipeline()
        self.last_checked = {}
        self.running = False
        self.thread = None
    
    def check_for_updates(self, url, vendor, doc_type):
        """Check if there are new documents available"""
        logger.info(f"Checking for updates: {vendor} {doc_type}")
        
        if doc_type == "release_notes":
            current_docs = self.scraper.parse_cisco_release_notes(url)
        elif doc_type == "config_guides":
            current_docs = self.scraper.parse_cisco_config_guides(url)
        else:
            logger.error(f"Unknown document type: {doc_type}")
            return
        
        key = f"{vendor}_{doc_type}"
        
        if key not in self.last_checked:
            self.last_checked[key] = {doc["url"]: doc["date"] for doc in current_docs}
            logger.info(f"Initial check for {key}: found {len(current_docs)} documents")
            return
        
        new_docs = []
        for doc in current_docs:
            if doc["url"] not in self.last_checked[key]:
                new_docs.append(doc)
            elif doc["date"] != self.last_checked[key][doc["url"]]:
                # Document was updated
                new_docs.append(doc)
        
        # Update the stored state
        self.last_checked[key] = {doc["url"]: doc["date"] for doc in current_docs}
        
        # Process new documents if any
        if new_docs:
            logger.info(f"Found {len(new_docs)} new or updated documents for {key}")
            self._process_new_documents(new_docs, doc_type)
        else:
            logger.info(f"No new documents found for {key}")
    
    def _process_new_documents(self, documents, doc_type):
        """Process newly discovered documents"""
        for doc in documents:
            try:
                content = self.scraper.extract_document_content(doc["url"])
                if not content:
                    continue
                
                # Use the ingestion pipeline to process and store the document
                if doc_type == "release_notes":
                    # Create metadata
                    metadata = {**doc}
                    # Extract product info
                    product_info = self.ingestion_pipeline.processor.extract_product_info(content)
                    metadata.update(product_info)
                    
                    # Chunk and store
                    chunks = self.ingestion_pipeline.processor.chunk_document(content, metadata)
                    self.ingestion_pipeline.vector_store.add_documents("release_notes", chunks)
                    
                elif doc_type == "config_guides":
                    # Create metadata
                    metadata = {**doc}
                    # Extract product info
                    product_info = self.ingestion_pipeline.processor.extract_product_info(content)
                    metadata.update(product_info)
                    
                    # Chunk and store
                    chunks = self.ingestion_pipeline.processor.chunk_document(content, metadata)
                    self.ingestion_pipeline.vector_store.add_documents("config_guides", chunks)
                
                logger.info(f"Processed new document: {doc['title']}")
                
            except Exception as e:
                logger.error(f"Error processing new document {doc['url']}: {str(e)}")
    
    def start(self):
        """Start the update checker as a background thread"""
        if self.running:
            logger.warning("Update checker is already running")
            return
        
        self.running = True
        
        # Schedule update checks
        schedule.every(UPDATE_CHECK_INTERVAL).hours.do(
            self.check_for_updates, 
            url="https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-release-notes-list.html",
            vendor="Cisco",
            doc_type="release_notes"
        )
        
        schedule.every(UPDATE_CHECK_INTERVAL).hours.do(
            self.check_for_updates, 
            url="https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-installation-and-configuration-guides-list.html",
            vendor="Cisco",
            doc_type="config_guides"
        )
        
        # Run in a separate thread
        def run_scheduler():
            logger.info("Starting update checker thread")
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        self.thread = threading.Thread(target=run_scheduler)
        self.thread.daemon = True
        self.thread.start()
        
        logger.info("Update checker started")
    
    def stop(self):
        """Stop the update checker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
            logger.info("Update checker stopped")
