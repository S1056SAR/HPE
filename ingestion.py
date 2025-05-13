import logging
import json
import os
import datetime
from scraper import NetworkDocScraper
from document_processor import DocumentProcessor
from vector_store import VectorStore # Make sure this import is correct

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataIngestionPipeline:
    def __init__(self):
        self.scraper = NetworkDocScraper()
        self.processor = DocumentProcessor()
        self.vector_store = VectorStore()
        
        self.tracking_dir = os.path.join(os.getcwd(), "tracking")
        os.makedirs(self.tracking_dir, exist_ok=True)
        self.tracking_file = os.path.join(self.tracking_dir, "ingested_files.json")
        
        self._load_tracking_data()

    def ingest_json_file(self, file_path: str, vendor_name: str):
        """
        Ingests data from a specified JSON file for a given vendor.
        The JSON file can be a single large object or a list of objects.
        Each object will be treated as a document to be chunked.
        """
        logger.info(f"Starting ingestion of JSON file: {file_path} for vendor: {vendor_name}")
        
        file_stat = os.stat(file_path)
        file_key = f"json_{vendor_name.lower()}_{os.path.basename(file_path)}_{file_stat.st_mtime}"

        if file_key in self.ingested_files:
            logger.info(f"File {file_path} for vendor {vendor_name} (key: {file_key}) was already ingested. Skipping.")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            logger.error(f"JSON file not found: {file_path}")
            return
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from file {file_path}: {e}")
            return
        except Exception as e:
            logger.error(f"An unexpected error occurred while reading {file_path}: {e}")
            return

        documents_to_process = []
        if isinstance(data, list):
            documents_to_process = data
        elif isinstance(data, dict):
            documents_to_process = [data] # Treat a single dict as a list with one item
        else:
            logger.error(f"Unsupported JSON structure in {file_path}. Expected a list or a single dictionary.")
            return

        total_chunks_added = 0
        processed_item_count = 0

        for i, item in enumerate(documents_to_process):
            try:
                # Convert the JSON object (or item) to a string for content processing.
                # We'll pretty-print it to retain some structure for readability if needed,
                # but the embedding model will see it as a flat string.
                content_str = json.dumps(item, indent=2, ensure_ascii=False)
                
                # Basic metadata
                # We assume the entire file pertains to the given vendor_name.
                # If items within the JSON have their own 'title' or 'url', try to use them.
                item_metadata = {
                    "vendor": vendor_name.lower(),
                    "source_file": os.path.basename(file_path),
                    "original_source_info": item.get("url", item.get("link", item.get("source", "N/A"))), # Prioritize specific keys
                    "title": item.get("title", f"JSON item {i+1} from {os.path.basename(file_path)}"),
                    "doc_type": "json_import"
                }
                
                # Extract additional product info using the document processor
                # This might be less effective on raw JSON dumps but attempt it.
                # You might need to adapt DocumentProcessor or pre-process JSON if it contains natural language text in specific fields.
                product_info = self.processor.extract_product_info(content_str) # Pass string representation
                item_metadata.update(product_info)
                # Crucially, ensure the vendor from product_info (if found) doesn't override the explicit vendor_name
                item_metadata["vendor"] = vendor_name.lower()


                chunks = self.processor.chunk_document(content_str, item_metadata)
                
                if chunks:
                    # The `add_documents` method of VectorStore now takes the vendor name
                    # as the first argument when adding to the all_vendor_docs collection.
                    self.vector_store.add_documents(vendor_name.lower(), chunks)
                    total_chunks_added += len(chunks)
                    logger.debug(f"Added {len(chunks)} chunks for item {i+1} from {file_path} (vendor: {vendor_name}).")
                else:
                    logger.warning(f"No chunks generated for item {i+1} from {file_path}.")
                processed_item_count +=1
            except Exception as e:
                logger.error(f"Error processing item {i+1} from JSON file {file_path}: {e}", exc_info=True)
        
        if processed_item_count > 0 :
             self.ingested_files[file_key] = {
                "timestamp": datetime.datetime.now().isoformat(),
                "items_processed": processed_item_count,
                "total_chunks_added": total_chunks_added
            }
             self._save_tracking_data()
             logger.info(f"Completed ingestion of JSON file: {file_path} for vendor: {vendor_name}. Processed {processed_item_count} items, added {total_chunks_added} chunks.")
        else:
            logger.info(f"No items processed from JSON file: {file_path} for vendor: {vendor_name}.")


    def ingest_cisco_release_notes(self, url):
        """Ingest Cisco release notes from the provided URL"""
        logger.info(f"Starting ingestion of Cisco release notes from {url}")
        document_links = self.scraper.parse_cisco_release_notes(url)
        logger.info(f"Found {len(document_links)} release note documents")
        processed_count = 0
        for doc_meta in document_links:
            try:
                doc_key = f"cisco_release_notes_{doc_meta['url']}"
                if doc_key in self.ingested_files:
                    logger.info(f"Document already ingested: {doc_meta['title']}. Skipping.")
                    continue
                
                content = self.scraper.extract_document_content(doc_meta) 
                if not content:
                    logger.warning(f"No content extracted from {doc_meta['url']}")
                    continue
                
                product_info = self.processor.extract_product_info(content)
                metadata = {**doc_meta, **product_info, "vendor": "cisco"} 
                
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
        logger.info(f"Completed ingestion of {processed_count} release notes")

    def ingest_cisco_config_guides(self, url):
        """Ingest Cisco configuration guides from the provided URL"""
        logger.info(f"Starting ingestion of Cisco configuration guides from {url}")
        document_links = self.scraper.parse_cisco_config_guides(url)
        logger.info(f"Found {len(document_links)} configuration guide documents")
        processed_count = 0
        for doc_meta in document_links:
            try:
                doc_key = f"cisco_config_guides_{doc_meta['url']}"
                if doc_key in self.ingested_files:
                    logger.info(f"Document already ingested: {doc_meta['title']}. Skipping.")
                    continue
                
                content = self.scraper.extract_document_content(doc_meta) 
                if not content:
                    logger.warning(f"No content extracted from {doc_meta['url']}")
                    continue

                product_info = self.processor.extract_product_info(content)
                metadata = {**doc_meta, **product_info, "vendor": "cisco"} 
                
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
        """Ingest data from scraped_data.json file (assumed to be error codes)"""
        file_stat = os.stat(json_file_path)
        file_key = f"scraped_data_{json_file_path}_{file_stat.st_mtime}"
        if file_key in self.ingested_files:
            logger.info(f"File {json_file_path} was already ingested. Skipping.")
            return
        
        logger.info(f"Ingesting data from {json_file_path}")
        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            content_to_chunk = ""
            if isinstance(data, list): 
                content_to_chunk = "\n\n".join([json.dumps(item) for item in data])
            elif isinstance(data, dict): 
                content_to_chunk = json.dumps(data)
            else:
                logger.warning(f"Unsupported data type in {json_file_path}. Expected list or dict.")
                return

            metadata = {
                "doc_type": "Error Documentation",
                "source_file": os.path.basename(json_file_path)
                # Vendor for error codes will be 'error_codes' as per VectorStore logic
            }
            
            error_chunks = self.processor.chunk_document(content_to_chunk, metadata)
            if error_chunks:
                self.vector_store.add_documents(VectorStore.ERROR_CODES_COLLECTION_NAME, error_chunks)
                self.ingested_files[file_key] = {
                    "timestamp": datetime.datetime.now().isoformat(),
                    "chunks": len(error_chunks)
                }
                self._save_tracking_data()
                logger.info(f"Ingested {len(error_chunks)} chunks from {json_file_path} into error_codes.")
            else:
                logger.info(f"No chunks generated from {json_file_path}.")
        except Exception as e:
            logger.error(f"Error ingesting scraped data from {json_file_path}: {str(e)}")


    def ingest_aruba_documentation(self, url, force_scrape=False):
        """Ingest Aruba AOS-CX documentation from the provided URL"""
        url_key = f"aruba_documentation_{url}"
        if not force_scrape and url_key in self.ingested_files:
            logger.info(f"URL {url} was already ingested. Skipping.")
            return
        
        logger.info(f"Starting ingestion of Aruba AOS-CX documentation from {url}")
        
        document_links = self.scraper.parse_aruba_documentation(url)
        logger.info(f"Found {len(document_links)} documents on main page")
        
        dropdown_links = self.scraper.scrape_dropdown_options(url)
        logger.info(f"Found {len(dropdown_links)} additional documents from dropdown options")
        
        all_links = document_links + dropdown_links
        processed_count = 0
        documents_data = [] 

        for doc_meta in all_links:
            try:
                doc_key = f"aruba_doc_{doc_meta['url']}"
                if not force_scrape and doc_key in self.ingested_files:
                    logger.info(f"Document already ingested: {doc_meta['title']}. Skipping.")
                    continue
                
                content = self.scraper.extract_document_content(doc_meta)
                if not content:
                    logger.warning(f"No content extracted from {doc_meta['url']}")
                    continue
                
                document_info = {'title': doc_meta['title'], 'url': doc_meta['url'], 'content': content}
                documents_data.append(document_info)
                
                product_info = self.processor.extract_product_info(content)
                metadata = {**doc_meta, **product_info, "vendor": "aruba"}
                
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
                
            except Exception as e:
                logger.error(f"Error processing {doc_meta['url']}: {str(e)}")

        json_file_path = 'aruba_documents_content.json' # Save raw scraped content
        try:
            with open(json_file_path, 'w', encoding = 'utf-8') as json_file:
                json.dump(documents_data, json_file, ensure_ascii = False, indent = 4)
            logger.info(f"Saved raw Aruba content to {json_file_path}")
        except Exception as e:
            logger.error(f"Error saving raw Aruba content to {json_file_path}: {e}")


        self.ingested_files[url_key] = {
            "timestamp": datetime.datetime.now().isoformat(),
            "documents_processed": processed_count
        }
        self._save_tracking_data()
        logger.info(f"Completed ingestion of {processed_count} Aruba documents from {url}")

    def _load_tracking_data(self):
        """Load tracking data from file."""
        if os.path.exists(self.tracking_file):
            try:
                with open(self.tracking_file, 'r') as f:
                    self.ingested_files = json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from tracking file: {self.tracking_file}. Starting with empty tracking.")
                self.ingested_files = {}
        else:
            self.ingested_files = {}

    def _save_tracking_data(self):
        """Save tracking data to file"""
        os.makedirs(self.tracking_dir, exist_ok=True)
        try:
            with open(self.tracking_file, 'w') as f:
                json.dump(self.ingested_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tracking data to {self.tracking_file}: {e}")

    def run_full_ingestion(self):
        """Run the complete ingestion pipeline for all vendors"""
        self.ingest_cisco_release_notes("https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-release-notes-list.html")
        self.ingest_cisco_config_guides("https://www.cisco.com/c/en/us/support/switches/nexus-9000-series-switches/products-installation-and-configuration-guides-list.html")
        self.ingest_aruba_documentation("https://arubanetworking.hpe.com/techdocs/AOS-CX/Consolidated_RNs/HTML-9300/Content/PDFs.htm")
        
        if os.path.exists("scraped_data.json"): 
            self.ingest_scraped_data("scraped_data.json")
        logger.info("Full ingestion pipeline completed")

    def reset_ingestion_tracking(self):
        self.ingested_files = {}
        self._save_tracking_data()
        logger.info("Ingestion tracking has been reset")
