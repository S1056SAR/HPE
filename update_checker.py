import schedule
import time
import logging
from typing import Dict, List, Any
from datetime import datetime as dt # Alias datetime to avoid conflict
import threading
from scraper import NetworkDocScraper
from ingestion import DataIngestionPipeline # For _save_tracking_data and processor
from vector_store import VectorStore # For collection name constants
from environment import UPDATE_CHECK_INTERVAL
import json
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UpdateChecker:
    def __init__(self):
        self.scraper = NetworkDocScraper()
        # UpdateChecker might need its own VectorStore instance or access to DataIngestionPipeline's
        self.ingestion_pipeline = DataIngestionPipeline() # Provides vector_store and processor
        self.last_checked_docs = {} # Stores {url: date_string} for comparison
        self.running = False
        self.thread = None
        self._load_last_checked_state()


    def _load_last_checked_state(self):
        state_file = os.path.join(self.ingestion_pipeline.tracking_dir, "update_checker_state.json")
        if os.path.exists(state_file):
            try:
                with open(state_file, 'r') as f:
                    self.last_checked_docs = json.load(f)
                    logger.info("Loaded previous update checker state.")
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from update checker state file: {state_file}. Starting fresh.")
                self.last_checked_docs = {}
        else:
            self.last_checked_docs = {}

    def _save_last_checked_state(self):
        state_file = os.path.join(self.ingestion_pipeline.tracking_dir, "update_checker_state.json")
        os.makedirs(self.ingestion_pipeline.tracking_dir, exist_ok=True)
        try:
            with open(state_file, 'w') as f:
                json.dump(self.last_checked_docs, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save update checker state to {state_file}: {e}")


    def check_for_updates(self, url, vendor, doc_type):
        logger.info(f"Checking for updates: {vendor} {doc_type} from {url}")
        current_docs_metadata = [] # List of dicts {title, url, date, vendor, doc_type}

        if doc_type == "release_notes" and vendor.lower() == "cisco":
            current_docs_metadata = self.scraper.parse_cisco_release_notes(url)
        elif doc_type == "config_guides" and vendor.lower() == "cisco":
            current_docs_metadata = self.scraper.parse_cisco_config_guides(url)
        elif doc_type == "posts" and vendor.lower() == "hackernews": # "HackerNews" in main.py
            current_docs_metadata = self.scraper.parse_hacker_news(url)
        # Add more parsers here if needed, e.g., for Aruba updates
        # elif doc_type == "aos_cx_docs" and vendor.lower() == "aruba":
        # current_docs_metadata = self.scraper.parse_aruba_documentation(url) # Assuming this can find updates
        else:
            logger.warning(f"No specific parser for vendor '{vendor}' and doc_type '{doc_type}'. Skipping update check for this source.")
            return

        if not current_docs_metadata:
            logger.info(f"No documents found by scraper for {vendor} {doc_type} at {url}.")
            return

        new_or_updated_docs_metadata = []
        for doc_meta in current_docs_metadata:
            doc_url = doc_meta["url"]
            # Use current time as 'date' for HackerNews as it changes frequently
            # For others, rely on parsed date or a default.
            doc_date_str = doc_meta.get("date", dt.min.isoformat())
            if vendor.lower() == "hackernews": # Special handling for rapidly changing content
                 doc_date_str = dt.now().isoformat()


            if doc_url not in self.last_checked_docs:
                new_or_updated_docs_metadata.append(doc_meta)
                logger.info(f"Detected new document: {doc_meta.get('title', doc_url)}")
            elif doc_date_str != self.last_checked_docs.get(doc_url): # Check if date changed
                new_or_updated_docs_metadata.append(doc_meta)
                logger.info(f"Detected updated document: {doc_meta.get('title', doc_url)} (Date changed from {self.last_checked_docs.get(doc_url)} to {doc_date_str})")
            
            # Update the last_checked_docs with the current state for this URL
            self.last_checked_docs[doc_url] = doc_date_str
        
        self._save_last_checked_state() # Save state after each check

        if new_or_updated_docs_metadata:
            logger.info(f"Found {len(new_or_updated_docs_metadata)} new or updated documents for {vendor} {doc_type}.")
            self._process_new_documents(new_or_updated_docs_metadata, vendor, doc_type)
        else:
            logger.info(f"No new or updated documents found for {vendor} {doc_type}.")


    def _process_new_documents(self, documents_metadata: List[Dict], vendor: str, doc_type: str):
        """Process newly discovered or updated documents"""
        processed_count = 0
        for doc_meta in documents_metadata:
            doc_url = doc_meta['url']
            # Use a unique key for ingestion tracking, combining vendor, type, and URL
            # This is different from last_checked_docs key.
            ingestion_doc_key = f"{vendor.lower()}_{doc_type.lower()}_{doc_url}"
            
            # Check against the ingestion pipeline's tracking to avoid re-processing if already ingested by other means
            # However, for updates, we might want to re-ingest. This simple check prevents re-ingestion
            # if an "updated" doc was somehow ingested between the check and now.
            # A more sophisticated update strategy might involve deleting old versions.
            if ingestion_doc_key in self.ingestion_pipeline.ingested_files:
                # For a true update, you might want to remove existing chunks for this URL first.
                # For now, we'll log and potentially skip or decide to re-add.
                logger.info(f"Document {doc_meta.get('title', doc_url)} marked as updated/new, but already in ingestion tracking. Re-ingesting.")
                # Optionally: self.ingestion_pipeline.vector_store.delete_documents_by_url(doc_url) if such method exists

            logger.info(f"Processing new/updated document: {doc_meta.get('title', doc_url)}")
            try:
                content = self.scraper.extract_document_content(doc_meta) # Pass full doc_meta
                if not content:
                    logger.warning(f"No content extracted from {doc_url} during update processing, skipping.")
                    continue

                # Prepare metadata for document processor and vector store
                # The `doc_meta` from scraping already has vendor, title, url, date, doc_type.
                # `extract_product_info` will add more.
                product_info = self.ingestion_pipeline.processor.extract_product_info(content)
                final_metadata = {**doc_meta, **product_info}
                
                # Ensure 'vendor' field is consistent and lowercase for metadata filtering
                final_metadata['vendor'] = vendor.lower() 

                chunks = self.ingestion_pipeline.processor.chunk_document(content, final_metadata)
                
                collection_key_for_vs = ""
                if vendor.lower() == "hackernews":
                    collection_key_for_vs = VectorStore.HACKER_NEWS_COLLECTION_NAME
                else:
                    # For Cisco, Aruba, etc., the vendor name itself is the key
                    # which VectorStore.add_documents will use as a vendor tag for the main collection.
                    collection_key_for_vs = vendor.lower() 
                
                if chunks:
                    self.ingestion_pipeline.vector_store.add_documents(collection_key_for_vs, chunks)
                    
                    # Update ingestion tracking in the ingestion_pipeline
                    self.ingestion_pipeline.ingested_files[ingestion_doc_key] = {
                        "timestamp": dt.now().isoformat(),
                        "title": doc_meta.get("title", "N/A"),
                        "url": doc_url,
                        "chunks_added_during_update": len(chunks)
                    }
                    self.ingestion_pipeline._save_tracking_data() # Call method from ingestion_pipeline
                    processed_count += 1
                    logger.info(f"Successfully processed and stored updated/new document to '{collection_key_for_vs}': {doc_meta.get('title', doc_url)}")
                else:
                    logger.warning(f"No chunks generated for updated/new document: {doc_meta.get('title', doc_url)}")

            except Exception as e:
                logger.error(f"Error processing new/updated document {doc_url}: {str(e)}", exc_info=True)
        
        logger.info(f"Finished processing {processed_count} new/updated documents for {vendor} {doc_type}.")


    def start(self):
        if self.running:
            logger.warning("Update checker is already running")
            return
        
        self.running = True
        logger.info(f"Update checker configured to run every {UPDATE_CHECK_INTERVAL} hours (HackerNews every 1 min for test).")

        # Schedule Cisco Release Notes
        schedule.every(UPDATE_CHECK_INTERVAL).hours.do(
            self.check_for_updates,
            url="https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-release-notes-list.html",
            vendor="Cisco",
            doc_type="release_notes"
        )
        # Schedule Cisco Config Guides
        schedule.every(UPDATE_CHECK_INTERVAL).hours.do(
            self.check_for_updates,
            url="https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-installation-and-configuration-guides-list.html",
            vendor="Cisco",
            doc_type="config_guides"
        )
        # Schedule Hacker News (more frequently for testing updates)
        schedule.every(1).minutes.do( # Check every minute for testing
            self.check_for_updates,
            url="https://news.ycombinator.com/newest",
            vendor="HackerNews", # Consistent with ingestion
            doc_type="posts"
        )
        # Add Aruba check if desired
        # schedule.every(UPDATE_CHECK_INTERVAL).hours.do(
        #     self.check_for_updates,
        #     url="https://arubanetworking.hpe.com/techdocs/AOS-CX/Consolidated_RNs/HTML-9300/Content/PDFs.htm", # Example URL
        #     vendor="Aruba",
        #     doc_type="aos_cx_docs" # A new doc_type, needs a parser in scraper
        # )

        def run_scheduler():
            logger.info("Starting update checker thread...")
            # Run once immediately for each scheduled job if desired for testing
            # schedule.run_all() 
            while self.running:
                schedule.run_pending()
                time.sleep(30) # Check schedule every 30 seconds
            logger.info("Update checker thread stopped.")

        self.thread = threading.Thread(target=run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Update checker background thread started.")

    def stop(self):
        if not self.running:
            logger.info("Update checker is not running.")
            return
        
        self.running = False
        if self.thread and self.thread.is_alive():
            logger.info("Attempting to stop update checker thread...")
            self.thread.join(timeout=10) # Wait for thread to finish
            if self.thread.is_alive():
                logger.warning("Update checker thread did not stop gracefully.")
        logger.info("Update checker stopped.")

