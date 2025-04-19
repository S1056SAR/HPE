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
    def __init__(self):
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIRECTORY)
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self.embedding_dimension = 768  # Explicitly set to 768
        logger.info(f"Using embedding model: {EMBEDDING_MODEL} with dimension: {self.embedding_dimension}")
        
        self._store_embedding_info()
        self.collections = self._initialize_collections()
        self.ingested_files = self._load_ingestion_tracking()
        
        if not self.check_embedding_consistency():
            logger.warning("Embedding dimension mismatch detected. Consider resetting the database or using the original embedding model.")
    
    def _store_embedding_info(self):
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
        collections = {}
        vendors = ["cisco", "juniper", "aruba", "arista", "hpe"]
        for vendor in vendors:
            collection_name = f"{vendor}_docs"
            collections[vendor] = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"vendor": vendor, "embedding_dimension": self.embedding_dimension, "model": EMBEDDING_MODEL}
            )
        
        collections["error_codes"] = self.client.get_or_create_collection(
            name="error_codes",
            metadata={"type": "error_codes", "embedding_dimension": self.embedding_dimension, "model": EMBEDDING_MODEL}
        )
        collections["hacker_news_posts"] = self.client.get_or_create_collection(
            name="hacker_news_posts",
            metadata={"type": "hacker_news", "embedding_dimension": self.embedding_dimension, "model": EMBEDDING_MODEL}
        )
        
        return collections
    
    def _load_ingestion_tracking(self):
        tracking_file = os.path.join(CHROMA_PERSIST_DIRECTORY, "ingestion_tracking.json")
        if os.path.exists(tracking_file):
            with open(tracking_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_tracking_data(self):
        tracking_file = os.path.join(CHROMA_PERSIST_DIRECTORY, "ingestion_tracking.json")
        with open(tracking_file, 'w') as f:
            json.dump(self.ingested_files, f, indent=2)
    
    def check_embedding_consistency(self):
        for name, collection in self.collections.items():
            try:
                metadata = collection.metadata
                if metadata and 'embedding_dimension' in metadata:
                    stored_dimension = metadata['embedding_dimension']
                    if stored_dimension != self.embedding_dimension:
                        logger.warning(f"Collection {name} was created with embedding dimension {stored_dimension}, but current model uses {self.embedding_dimension}")
                        return False
            except Exception as e:
                logger.warning(f"Error checking collection {name}: {str(e)}")
        return True
    
    def add_documents(self, vendor: str, documents: List[Dict[str, Any]]):
        if not documents:
            logger.warning("No documents to add")
            return
        
        if vendor.lower() in self.collections:
            collection = self.collections[vendor.lower()]
        elif "error" in vendor.lower():
            collection = self.collections["error_codes"]
        else:
            collection = next(iter(self.collections.values()))
            logger.warning(f"Unknown vendor: {vendor}, using default collection")
        
        ids, contents, metadatas = [], [], []
        
        for i, doc in enumerate(documents):
            doc_id = str(hash(doc["content"]))[:16] + f"_{i}"
            ids.append(doc_id)
            contents.append(doc["content"])
            
            metadata = doc["metadata"].copy()
            metadata.update({
                "embedding_model": EMBEDDING_MODEL,
                "embedding_dimension": self.embedding_dimension,
                "vendor": vendor,
                "product_line": metadata.get("product_line", "Unknown"),
                "release": metadata.get("release", "Unknown"),
                "features": ",".join(metadata.get("features", [])),
                "categories": ",".join(metadata.get("categories", [])),
                "deployment": ",".join(metadata.get("deployment", []))
            })
            metadatas.append(metadata)
        
        embeddings = self.embedding_model.encode(contents).tolist()
        
        collection.add(
            ids=ids,
            documents=contents,
            metadatas=metadatas,
            embeddings=embeddings
        )
        
        logger.info(f"Added {len(documents)} documents to {collection.name}")

    def query_with_filter(self, query_text: str, filter_dict: Dict[str, Any], n_results: int = 3):
        embedding = self.embedding_model.encode(query_text).tolist()
        
        all_results = {}
        
        for name, collection in self.collections.items():
            try:
                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=n_results,
                    where=filter_dict
                )
                all_results[name] = results
            except Exception as e:
                logger.error(f"Error querying collection {name}: {str(e)}")
                all_results[name] = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        
        return all_results
    
    def query(self, vendor: str, query_text: str, n_results: int = 3):
        embedding = self.embedding_model.encode(query_text).tolist()
        
        if vendor.lower() in self.collections:
            collection = self.collections[vendor.lower()]
        elif "error" in vendor.lower():
            collection = self.collections["error_codes"]
        else:
            results = {}
            for name, collection in self.collections.items():
                try:
                    results[name] = collection.query(
                        query_embeddings=[embedding],
                        n_results=n_results
                    )
                except Exception as e:
                    logger.error(f"Error querying collection {name}: {str(e)}")
                    results[name] = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
            return results
        
        try:
            return collection.query(
                query_embeddings=[embedding],
                n_results=n_results
            )
        except Exception as e:
            logger.error(f"Error querying collection {vendor}: {str(e)}")
            return {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
    
    def query_all_collections(self, query_text: str, n_results: int = 3):
        embedding = self.embedding_model.encode(query_text).tolist()
        
        all_results = {}
        
        for name, collection in self.collections.items():
            try:
                results = collection.query(
                    query_embeddings=[embedding],
                    n_results=n_results
                )
                all_results[name] = results
            except Exception as e:
                logger.error(f"Error querying collection {name}: {str(e)}")
                all_results[name] = {"documents": [[]], "metadatas": [[]], "distances": [[]], "ids": [[]]}
        
        return all_results
    
    def clear_collection(self, collection_name: str):
        if collection_name in self.collections:
            try:
                results = self.collections[collection_name].get()
                if results and 'ids' in results and results['ids']:
                    self.collections[collection_name].delete(ids=results['ids'])
                    logger.info(f"Cleared collection: {collection_name}")
                else:
                    logger.info(f"Collection {collection_name} is already empty")
            except Exception as e:
                logger.error(f"Error clearing collection {collection_name}: {str(e)}")
        else:
            logger.warning(f"Collection {collection_name} not found")
    
    def reset_database(self):
        for collection_name in self.collections:
            self.clear_collection(collection_name)
        self.ingested_files = {}
        self._save_tracking_data()
        logger.info("All collections have been cleared and ingestion tracking reset")
