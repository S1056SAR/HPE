import schedule
import time
import logging
from datetime import datetime
import threading
from scraper import NetworkDocScraper
from ingestion import DataIngestionPipeline
from environment import UPDATE_CHECK_INTERVAL
import datetime
import json
import os

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
        is_news_source  = False
        
        if doc_type == "release_notes":
            current_docs = self.scraper.parse_cisco_release_notes(url)
        elif doc_type == "config_guides":
            current_docs = self.scraper.parse_cisco_config_guides(url)
        elif doc_type == "posts": # *** ADD THIS CASE ***
            current_docs = self.scraper.parse_hacker_news(url)
            is_news_source  = True
        else:
            logger.error(f"Unknown document type: {doc_type}")
            return
        
        # if save_scraped_data and current_docs:
        #     # Define filename (e.g., hackernews_posts_scrape.json)
        #     filename = f"{vendor.lower()}_{doc_type.lower()}_scrape.json"
        #     try:
        #         # Use 'with' to ensure the file is closed properly
        #         with open(filename, 'w', encoding='utf-8') as f:
        #             json.dump(current_docs, f, ensure_ascii=False, indent=4) # [11, 13, 16]
        #         logger.info(f"Successfully saved scraped data ({len(current_docs)} items) to {filename}")
        #     except IOError as e:
        #         logger.error(f"Error saving scraped data to {filename}: {e}")
        #     except Exception as e: # Catch other potential errors during dump
        #          logger.error(f"An unexpected error occurred while saving {filename}: {e}")
        

        if is_news_source and current_docs:
            logger.info(f"Fetching content for {len(current_docs)} scraped news items...")
            enriched_docs = [] # Store docs with content
            for i, doc in enumerate(current_docs):
                try:
                    logger.info(f"Fetching content for item {i+1}/{len(current_docs)}: {doc.get('title', doc['url'])}")
                    # Use the existing extract_document_content method [6]
                    # Pass the whole 'doc' dictionary as it might be needed (like for PDF type detection)
                    content = self.scraper.extract_document_content(doc)
                    # Add the extracted content to the dictionary
                    doc['content'] = content if content else "" # Add empty string if extraction fails [10, 14, 15]
                    enriched_docs.append(doc)
                    # Optional: Add a small delay between content fetches if needed
                    # time.sleep(1) 
                except Exception as e:
                    logger.error(f"Error fetching content for {doc.get('url', 'N/A')}: {e}", exc_info=True)
                    # Add the doc even if content extraction failed, with empty content
                    doc['content'] = "" 
                    enriched_docs.append(doc)
            
            current_docs = enriched_docs # Replace original list with enriched one
            logger.info("Finished fetching content for news items.")

            # --- Save the enriched data to JSON ---
            filename = f"{vendor.lower()}_{doc_type.lower()}_scrape_with_content.json" # New filename
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(current_docs, f, ensure_ascii=False, indent=4) # [11, 13, 16]
                logger.info(f"Successfully saved enriched scraped data ({len(current_docs)} items) to {filename}")
            except IOError as e:
                logger.error(f"Error saving enriched scraped data to {filename}: {e}")
            except Exception as e: # Catch other potential errors during dump
                 logger.error(f"An unexpected error occurred while saving {filename}: {e}")



        key = f"{vendor}_{doc_type}"
        
        if key not in self.last_checked:
            # self.last_checked[key] = {doc["url"]: doc["date"] for doc in current_docs}
            # logger.info(f"Initial check for {key}: found {len(current_docs)} documents")
            # return
            self.last_checked[key] = {doc["url"]: doc.get("date", datetime.datetime.min.isoformat()) for doc in current_docs} # Use a default date if missing
            logger.info(f"Initial check for {key}: found {len(current_docs)} documents")
            # --- On initial check, process *all* found documents ---
            # Pass vendor along with doc_type
            self._process_new_documents(current_docs, vendor, doc_type) 
            return
        
        new_docs = []
        current_state = {}
        
        # for doc in current_docs:
        #     if doc["url"] not in self.last_checked[key]:
        #         new_docs.append(doc)
        #     elif doc["date"] != self.last_checked[key][doc["url"]]:
        #         # Document was updated
        #         new_docs.append(doc)
        
        # # Update the stored state
        # self.last_checked[key] = {doc["url"]: doc["date"] for doc in current_docs}
        
        for doc in current_docs:
            doc_url = doc["url"]
            # Handle cases where 'date' might be missing
            doc_date = doc.get("date", datetime.datetime.min.isoformat()) 
            current_state[doc_url] = doc_date # Build the latest state

            if doc_url not in self.last_checked[key]:
                new_docs.append(doc)
                logger.info(f"Detected new document: {doc.get('title', doc_url)}")
            # Check date only if it exists in both current doc and last checked state
            elif doc_date != datetime.datetime.min.isoformat() and \
                 doc_url in self.last_checked[key] and \
                 doc_date != self.last_checked[key][doc_url]:
                # Document was updated
                new_docs.append(doc)
                logger.info(f"Detected updated document: {doc.get('title', doc_url)}")


        # Update the stored state *after* comparison
        self.last_checked[key] = current_state


        # Process new documents if any
        if new_docs:
            logger.info(f"Found {len(new_docs)} new or updated documents for {key}")
            self._process_new_documents(new_docs, vendor, doc_type)
        else:
            logger.info(f"No new or updated documents found for {key}")
    
    def _process_new_documents(self, documents, vendor, doc_type):
        # """Process newly discovered documents"""
        # for doc in documents:
        #     try:
        #         content = self.scraper.extract_document_content(doc["url"])
        #         if not content:
        #             continue
        """Process newly discovered documents"""
        processed_count = 0
        for doc in documents:
            doc_url = doc['url']
            doc_key = f"{vendor.lower()}_{doc_type.lower()}_{doc_url}"

            if doc_key in self.ingestion_pipeline.ingested_files:
                logger.info(f"Document already ingested (according to tracking file): {doc.get('title', doc_url)}. Skipping processing.")
                continue

            logger.info(f"Processing new/updated document: {doc.get('title', doc_url)}")
            try:
                # Use the 'doc' dictionary directly for extract_document_content
                content = self.scraper.extract_document_content(doc) 
                if not content:
                    # logger.warning(f"No content extracted from {doc.get('url', 'N/A')}, skipping.")
                    logger.warning(f"No content extracted from {doc_url}, skipping.")
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
                
                elif doc_type == "posts": # *** ADD THIS CASE ***
                     metadata = {**doc}
                     chunks = self.ingestion_pipeline.processor.chunk_document(content, metadata)
                     collection_name = "hacker_news_posts"
                     if collection_name:
                         self.ingestion_pipeline.vector_store.add_documents(collection_name, chunks)
                    #      logger.info(f"Processed and stored new document to '{collection_name}': {doc.get('title', 'N/A')}")
                    #  else:
                    #     logger.warning(f"No collection specified for doc_type '{doc_type}'")
                         self.ingestion_pipeline.ingested_files[doc_key] = {
                         "timestamp": datetime.datetime.now().isoformat(),
                         "title": doc.get("title", "N/A"),
                         "url": doc_url,
                         "chunks": len(chunks)
                         }
                        # --- Save the updated tracking data ---
                         self.ingestion_pipeline._save_tracking_data() 
                         processed_count += 1
                         logger.info(f"Successfully processed and stored document to '{collection_name}': {doc.get('title', doc_url)}")
                     else:
                         logger.error(f"Could not determine collection name for doc_type '{doc_type}'. Skipping storage for: {doc_url}")

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
        schedule.every(1).minutes.do(
             self.check_for_updates,
             url="https://news.ycombinator.com/newest", # Hacker News URL
             vendor="HackerNews",               # Custom vendor name
             doc_type="posts"                  # Custom doc type
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
