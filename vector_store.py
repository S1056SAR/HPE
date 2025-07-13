import chromadb
import logging
from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from environment import CHROMA_PERSIST_DIRECTORY, EMBEDDING_MODEL
import os
import json
import datetime

logger = logging.getLogger(__name__)

class VectorStore:
    ALL_VENDOR_DOCS_COLLECTION_NAME = "all_vendor_docs"
    ERROR_CODES_COLLECTION_NAME = "error_codes"
    HACKER_NEWS_COLLECTION_NAME = "hacker_news_posts"

    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        
        # Get embedding dimension dynamically
        try:
            self.embedding_dimension = self.embedding_model.get_sentence_embedding_dimension()
            logger.info(f"Dynamically determined embedding dimension: {self.embedding_dimension}")
        except Exception as e:
            logger.warning(f"Could not dynamically determine embedding dimension, defaulting to 768. Error: {e}")
            self.embedding_dimension = 768

        logger.info(f"Using embedding model: {EMBEDDING_MODEL} with dimension: {self.embedding_dimension}")
        self._store_embedding_info()
        self.collections = self._initialize_collections()
        self.ingested_files = self._load_ingestion_tracking()
        
        if not self.check_embedding_consistency():
            logger.warning("Embedding dimension mismatch detected. Consider resetting the database or using the original embedding model.")

    def _store_embedding_info(self):
        """Store embedding model information"""
        info_dir = os.path.join(CHROMA_PERSIST_DIRECTORY, "metadata")
        os.makedirs(info_dir, exist_ok=True)
        info_file = os.path.join(info_dir, "embedding_info.json")
        embedding_info = {
            "model_name": EMBEDDING_MODEL,
            "dimension": self.embedding_dimension,
            "last_updated": str(datetime.datetime.now())
        }
        with open(info_file, 'w') as f:
            json.dump(embedding_info, f, indent=2)

    def _initialize_collections(self):
        """Initialize collections with enhanced error handling"""
        collections = {}
        
        # Define all required collections
        collection_configs = [
            (self.ALL_VENDOR_DOCS_COLLECTION_NAME, {"type": "vendor_documentation"}),
            (self.ERROR_CODES_COLLECTION_NAME, {"type": "error_codes"}),
            (self.HACKER_NEWS_COLLECTION_NAME, {"type": "hacker_news"}),
            ("cisco_docs", {"type": "vendor_specific", "vendor": "cisco"}),
            ("juniper_docs", {"type": "vendor_specific", "vendor": "juniper"}),
            ("aruba_docs", {"type": "vendor_specific", "vendor": "aruba"}),
            ("network_docs", {"type": "general_networking"}),
            ("default", {"type": "default_collection"})
        ]
        
        for collection_name, base_metadata in collection_configs:
            try:
                # Prepare metadata
                metadata = base_metadata.copy()
                metadata.update({
                    "embedding_dimension": self.embedding_dimension,
                    "model": EMBEDDING_MODEL,
                    "created_at": str(datetime.datetime.now())
                })
                
                # Create or get collection
                collection = self.client.get_or_create_collection(
                    name=collection_name,
                    metadata=metadata
                )
                collections[collection_name] = collection
                
                # Add placeholder document if collection is empty
                try:
                    count = collection.count()
                    if count == 0:
                        self._add_placeholder_document(collection, collection_name)
                except Exception as e:
                    logger.debug(f"Could not check/add placeholder for {collection_name}: {e}")
                
                logger.debug(f"Initialized collection: {collection_name}")
                
            except Exception as e:
                logger.warning(f"Failed to initialize collection {collection_name}: {e}")
                # Create a minimal fallback
                try:
                    collection = self.client.get_or_create_collection(name=collection_name)
                    collections[collection_name] = collection
                except Exception as fallback_error:
                    logger.error(f"Complete failure to create collection {collection_name}: {fallback_error}")
        
        logger.info(f"Successfully initialized {len(collections)} collections: {list(collections.keys())}")
        return collections

    def _add_placeholder_document(self, collection, collection_name: str):
        """Add a placeholder document to initialize empty collections"""
        try:
            placeholder_content = f"Placeholder document for {collection_name} collection. This document ensures the collection is properly initialized."
            
            # Generate embedding for placeholder
            embedding = self.embedding_model.encode(placeholder_content).tolist()
            
            collection.add(
                ids=[f"{collection_name}_placeholder"],
                documents=[placeholder_content],
                metadatas=[{
                    "type": "placeholder",
                    "collection": collection_name,
                    "created_at": str(datetime.datetime.now())
                }],
                embeddings=[embedding]
            )
            logger.debug(f"Added placeholder document to {collection_name}")
            
        except Exception as e:
            logger.warning(f"Failed to add placeholder to {collection_name}: {e}")

    def _load_ingestion_tracking(self):
        """Load ingestion tracking data"""
        tracking_file = os.path.join(CHROMA_PERSIST_DIRECTORY, "ingestion_tracking.json")
        if os.path.exists(tracking_file):
            try:
                with open(tracking_file, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logger.error(f"Error decoding JSON from tracking file: {tracking_file}. Starting with empty tracking.")
                return {}
        return {}

    def _save_tracking_data(self):
        """Save ingestion tracking data"""
        tracking_file = os.path.join(CHROMA_PERSIST_DIRECTORY, "ingestion_tracking.json")
        os.makedirs(CHROMA_PERSIST_DIRECTORY, exist_ok=True)
        try:
            with open(tracking_file, 'w') as f:
                json.dump(self.ingested_files, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save tracking data to {tracking_file}: {e}")

    def check_embedding_consistency(self):
        """Check embedding consistency across collections"""
        for name, collection in self.collections.items():
            try:
                collection_metadata = collection.metadata
                if collection_metadata and 'embedding_dimension' in collection_metadata:
                    stored_dimension = collection_metadata['embedding_dimension']
                    if stored_dimension != self.embedding_dimension:
                        logger.warning(f"Collection {name} was created with embedding dimension {stored_dimension}, but current model uses {self.embedding_dimension}")
                        return False
            except Exception as e:
                logger.warning(f"Error checking collection {name} metadata: {str(e)}")
        return True

    def add_documents(self, collection_key: str, documents: List[Dict[str, Any]]):
        """Add documents to the specified collection with enhanced error handling"""
        if not documents:
            logger.warning("No documents to add")
            return

        # Determine target collection
        actual_collection_name = self._resolve_collection_name(collection_key)
        vendor_tag_for_metadata = collection_key.lower()

        if actual_collection_name not in self.collections:
            logger.error(f"Target collection '{actual_collection_name}' not found. Available: {list(self.collections.keys())}")
            return
            
        collection = self.collections[actual_collection_name]

        ids, contents, metadatas_list = [], [], []
        for i, doc in enumerate(documents):
            # Ensure doc["content"] exists and is a string
            doc_content = doc.get("content")
            if not isinstance(doc_content, str) or not doc_content.strip():
                logger.warning(f"Document content is not a valid string, skipping: {doc.get('metadata', {}).get('title', 'Unknown title')}")
                continue

            # Generate a unique ID for the document chunk
            doc_id_base = doc.get("metadata", {}).get("url", "") + doc_content
            doc_id = str(hash(doc_id_base))[:16] + f"_{i}"
            
            ids.append(doc_id)
            contents.append(doc_content)
            
            # Prepare metadata
            doc_metadata = doc.get("metadata", {}).copy()
            doc_metadata.update({
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dimension": self.embedding_dimension,
                "added_at": str(datetime.datetime.now())
            })
            
            # Set vendor information
            if actual_collection_name == self.ALL_VENDOR_DOCS_COLLECTION_NAME:
                doc_metadata["vendor"] = doc_metadata.get("vendor", vendor_tag_for_metadata).lower()
            else:
                doc_metadata["vendor"] = vendor_tag_for_metadata

            # Standardize metadata fields
            doc_metadata["product_line"] = doc_metadata.get("product_line", "Unknown")
            doc_metadata["release"] = doc_metadata.get("release", "Unknown")
            
            # Handle list fields
            for field in ["features", "categories", "deployment"]:
                value = doc_metadata.get(field, [])
                if isinstance(value, list):
                    doc_metadata[field] = ",".join(value)
                else:
                    doc_metadata[field] = str(value) if value else ""
            
            metadatas_list.append(doc_metadata)

        if not contents:
            logger.warning("No valid documents with content to process after filtering.")
            return

        try:
            embeddings = self.embedding_model.encode(contents).tolist()
            
            collection.add(
                ids=ids,
                documents=contents,
                metadatas=metadatas_list,
                embeddings=embeddings
            )
            logger.info(f"Added {len(contents)} documents to collection '{collection.name}' (key: '{collection_key}').")
            
        except Exception as e:
            logger.error(f"Error adding documents to collection '{collection.name}': {str(e)}")

    def _resolve_collection_name(self, collection_key: str) -> str:
        """Resolve collection key to actual collection name"""
        key_lower = collection_key.lower()
        
        if key_lower == self.ERROR_CODES_COLLECTION_NAME:
            return self.ERROR_CODES_COLLECTION_NAME
        elif key_lower == self.HACKER_NEWS_COLLECTION_NAME:
            return self.HACKER_NEWS_COLLECTION_NAME
        else:
            # For vendor documents, use the main vendor collection
            return self.ALL_VENDOR_DOCS_COLLECTION_NAME

    def query(self, collection_name: str, query_text: str, n_results: int = 3, where_filter: Optional[Dict[str, Any]] = None):
        """Query a specific collection with enhanced error handling"""
        try:
            # Try exact collection name first
            if collection_name in self.collections:
                collection = self.collections[collection_name]
            else:
                # Fallback to similar collection names
                fallback_collections = [
                    self.ALL_VENDOR_DOCS_COLLECTION_NAME,
                    "network_docs",
                    "default"
                ]
                
                collection = None
                for fallback_name in fallback_collections:
                    if fallback_name in self.collections:
                        collection = self.collections[fallback_name]
                        logger.debug(f"Using fallback collection '{fallback_name}' for query '{collection_name}'")
                        break
                
                if not collection:
                    logger.error(f"No suitable collection found for '{collection_name}'. Available: {list(self.collections.keys())}")
                    return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

            embedding = self.embedding_model.encode(query_text).tolist()
            
            query_params = {
                "query_embeddings": [embedding],
                "n_results": n_results
            }
            if where_filter:
                query_params["where"] = where_filter
            
            results = collection.query(**query_params)
            logger.debug(f"Query '{query_text}' returned {len(results.get('documents', [[]])[0])} results from {collection.name}")
            return results
            
        except Exception as e:
            logger.error(f"Error querying collection '{collection_name}': {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}

    def query_all_collections(self, query_text: str, n_results: int = 3):
        """Query all initialized collections"""
        embedding = self.embedding_model.encode(query_text).tolist()
        all_results = {}
        
        for name, collection in self.collections.items():
            try:
                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=n_results
                )
                all_results[name] = results
                logger.debug(f"Queried collection {name}: {len(results.get('documents', [[]])[0])} results")
            except Exception as e:
                logger.error(f"Error querying collection {name}: {str(e)}")
                all_results[name] = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        return all_results
        
    def clear_collection(self, collection_name: str):
        """Clear a specific collection"""
        if collection_name in self.collections:
            try:
                existing_items = self.collections[collection_name].get(limit=10000)
                if existing_items and existing_items['ids']:
                    self.collections[collection_name].delete(ids=existing_items['ids'])
                    logger.info(f"Cleared collection: {collection_name}")
                else:
                    logger.info(f"Collection {collection_name} is already empty.")
            except Exception as e:
                logger.error(f"Error clearing collection {collection_name}: {str(e)}")
        else:
            logger.warning(f"Collection {collection_name} not found for clearing.")

    def reset_database(self):
        """Reset the entire database"""
        logger.info("Resetting database...")
        collection_names_to_delete = list(self.client.list_collections())
        for collection_obj in collection_names_to_delete:
            try:
                self.client.delete_collection(name=collection_obj.name)
                logger.info(f"Deleted collection: {collection_obj.name}")
            except Exception as e:
                logger.error(f"Error deleting collection {collection_obj.name} during reset: {e}")
        
        self.collections = self._initialize_collections()
        self.ingested_files = {}
        self._save_tracking_data()
        logger.info("Database reset complete. All collections re-initialized.")

    def ensure_collections_exist(self):
        """Ensure all required collections exist"""
        required_collections = [
            "cisco_docs", "juniper_docs", "aruba_docs", 
            "all_vendor_docs", "network_docs", "default"
        ]
        
        for collection_name in required_collections:
            if collection_name not in self.collections:
                try:
                    logger.info(f"Creating missing collection: {collection_name}")
                    collection = self.client.get_or_create_collection(
                        name=collection_name,
                        metadata={
                            "type": "auto_created",
                            "embedding_dimension": self.embedding_dimension,
                            "model": EMBEDDING_MODEL
                        }
                    )
                    self.collections[collection_name] = collection
                    self._add_placeholder_document(collection, collection_name)
                except Exception as e:
                    logger.warning(f"Could not create collection {collection_name}: {e}")
