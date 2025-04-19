# import chromadb
# import os

# def view_chromadb(db_path="./chroma_db"):
#     # Initialize ChromaDB client
#     client = chromadb.PersistentClient(path=db_path)
    
#     # Get all collections
#     collections = client.list_collections()
#     print(f"Found {len(collections)} collections in ChromaDB at {db_path}")
    
#     # Iterate through each collection
#     for collection in collections:
#         print(f"\n=== Collection: {collection.name} ===")
#         print(f"Metadata: {collection.metadata}")
        
#         # Get collection count
#         count = collection.count()
#         print(f"Document count: {count}")
        
#         if count > 0:
#             # Retrieve sample documents (limit to 5 for readability)
#             data = collection.get(limit=5)
            
#             # Display IDs
#             print("\nSample IDs:")
#             for id in data["ids"]:
#                 print(f"  - {id}")
            
#             # Display documents with their metadata
#             print("\nSample Documents:")
#             for i, (doc, meta) in enumerate(zip(data["documents"], data["metadatas"])):
#                 print(f"\nDocument {i+1}:")
#                 print(f"  Metadata: {meta}")
#                 # Truncate long documents for display
#                 if len(doc) > 500:
#                     print(f"  Content: {doc[:500]}...")
#                 else:
#                     print(f"  Content: {doc}")
            
#             if count > 5:
#                 print(f"\n... and {count-5} more documents")

# if __name__ == "__main__":
#     # You can specify a different path if needed
#     db_path = input("Enter ChromaDB path (default: ./chroma_db): ") or "./chroma_db"
#     view_chromadb(db_path)



import re
import chromadb
import os
import json
import sqlite3
import tempfile
import shutil
from pathlib import Path
import argparse

def explore_chromadb_collection_details(db_path):
    """
    Directly inspect a ChromaDB by examining its underlying SQLite database.
    This approach is more robust for examining problematic ChromaDB instances.
    """
    print(f"Analyzing ChromaDB at: {db_path}")
    
    # ChromaDB uses SQLite under the hood
    chroma_db_file = os.path.join(db_path, "chroma.sqlite3")
    
    if not os.path.exists(chroma_db_file):
        print(f"Error: SQLite database file not found at {chroma_db_file}")
        return
    
    # Make a temporary copy of the database to avoid locks
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "temp_chroma.sqlite3")
        shutil.copy2(chroma_db_file, temp_db_path)
        
        try:
            # Connect to the copy
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Get schema information
            print("\n=== Database Schema ===")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            for table in tables:
                print(f"Table: {table[0]}")
                cursor.execute(f"PRAGMA table_info({table[0]});")
                columns = cursor.fetchall()
                for column in columns:
                    print(f"  - {column[1]} ({column[2]})")
            
            # Get collection information
            print("\n=== Collections ===")
            try:
                cursor.execute("SELECT name, id, topic, metadata FROM collections")
                collections = cursor.fetchall()
                
                for collection in collections:
                    name, collection_id, topic, metadata_str = collection
                    try:
                        metadata = json.loads(metadata_str) if metadata_str else {}
                    except:
                        metadata = {"error": "Could not parse metadata"}
                    
                    print(f"\nCollection: {name}")
                    print(f"ID: {collection_id}")
                    print(f"Topic: {topic}")
                    print(f"Metadata: {json.dumps(metadata, indent=2)}")
                    
                    # Count embeddings for this collection
                    cursor.execute("SELECT COUNT(*) FROM embeddings WHERE collection_id = ?", (collection_id,))
                    embedding_count = cursor.fetchone()[0]
                    print(f"Embedding count: {embedding_count}")
                    
                    # Get sample embeddings
                    if embedding_count > 0:
                        cursor.execute("""
                            SELECT e.id, e.embedding_id, e.metadata, d.document, d.id as document_id
                            FROM embeddings e
                            LEFT JOIN documents d ON e.document_id = d.id
                            WHERE e.collection_id = ?
                            LIMIT 5
                        """, (collection_id,))
                        
                        embeddings = cursor.fetchall()
                        
                        if embeddings:
                            print(f"\nSample Entries (showing up to 5 of {embedding_count}):")
                            
                            for i, embedding in enumerate(embeddings):
                                e_id, embedding_id, e_metadata_str, document, document_id = embedding
                                
                                print(f"\nEntry {i+1}:")
                                print(f"  Embedding ID: {embedding_id}")
                                print(f"  Document ID: {document_id}")
                                
                                try:
                                    e_metadata = json.loads(e_metadata_str) if e_metadata_str else {}
                                    print(f"  Metadata: {json.dumps(e_metadata, indent=2)}")
                                except:
                                    print(f"  Metadata: Error parsing metadata")
                                
                                if document:
                                    if len(document) > 500:
                                        print(f"  Document: {document[:500]}...")
                                    else:
                                        print(f"  Document: {document}")
                                else:
                                    print("  Document: None (Document might be stored separately or missing)")
                            
                            if embedding_count > 5:
                                print(f"... and {embedding_count - 5} more entries")
                        else:
                            print("No embeddings found despite positive count (possible database inconsistency)")
            except Exception as e:
                print(f"Error querying collections: {e}")
                # Try alternative schema
                print("Trying alternative schema...")
                try:
                    # Get tables with embeddings or documents
                    for table_name in [t[0] for t in tables]:
                        if "embedding" in table_name.lower() or "document" in table_name.lower():
                            print(f"\nExamining table: {table_name}")
                            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                            count = cursor.fetchone()[0]
                            print(f"Row count: {count}")
                            
                            if count > 0:
                                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                                columns = [description[0] for description in cursor.description]
                                print(f"Columns: {columns}")
                                
                                rows = cursor.fetchall()
                                for i, row in enumerate(rows):
                                    print(f"\nRow {i+1}:")
                                    for col_name, value in zip(columns, row):
                                        if isinstance(value, str) and len(value) > 500:
                                            print(f"  {col_name}: {value[:500]}...")
                                        else:
                                            print(f"  {col_name}: {value}")
                except Exception as e2:
                    print(f"Error with alternative schema attempt: {e2}")
            
        except Exception as e:
            print(f"Error analyzing database: {e}")
        finally:
            conn.close()

def dump_all_direct(db_path, output_dir="./chroma_dump_direct"):
    """
    Dump all documents from ChromaDB by directly accessing the SQLite database.
    This is more reliable for problematic ChromaDB instances.
    """
    print(f"Dumping ChromaDB data from: {db_path}")
    
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)
    
    # ChromaDB uses SQLite under the hood
    chroma_db_file = os.path.join(db_path, "chroma.sqlite3")
    
    if not os.path.exists(chroma_db_file):
        print(f"Error: SQLite database file not found at {chroma_db_file}")
        return
    
    # Make a temporary copy of the database to avoid locks
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "temp_chroma.sqlite3")
        shutil.copy2(chroma_db_file, temp_db_path)
        
        try:
            # Connect to the copy
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Check if collections table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collections';")
            if not cursor.fetchone():
                print("Error: Collections table not found. Database might be in a different format.")
                # Dump general database info
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = cursor.fetchall()
                
                db_info = {
                    "tables": [t[0] for t in tables],
                    "schema": {}
                }
                
                for table in tables:
                    cursor.execute(f"PRAGMA table_info({table[0]});")
                    columns = cursor.fetchall()
                    db_info["schema"][table[0]] = [
                        {"name": col[1], "type": col[2]} for col in columns
                    ]
                
                with open(os.path.join(output_dir, "db_structure.json"), 'w') as f:
                    json.dump(db_info, f, indent=2)
                
                return
            
            # Get all collections
            cursor.execute("SELECT name, id, metadata FROM collections")
            collections = cursor.fetchall()
            
            for collection in collections:
                name, collection_id, metadata_str = collection
                
                # Create collection directory
                collection_dir = os.path.join(output_dir, name)
                os.makedirs(collection_dir, exist_ok=True)
                
                # Save collection metadata
                try:
                    metadata = json.loads(metadata_str) if metadata_str else {}
                except:
                    metadata = {"error": "Could not parse metadata"}
                
                with open(os.path.join(collection_dir, "collection_metadata.json"), 'w') as f:
                    json.dump(metadata, f, indent=2)
                
                # Get all embeddings for this collection with associated documents
                cursor.execute("""
                    SELECT e.id, e.embedding_id, e.metadata, d.document, d.id as document_id
                    FROM embeddings e
                    LEFT JOIN documents d ON e.document_id = d.id
                    WHERE e.collection_id = ?
                """, (collection_id,))
                
                embeddings = cursor.fetchall()
                embedding_count = len(embeddings)
                
                print(f"Collection '{name}': Found {embedding_count} entries")
                
                # Save all entries
                for i, embedding in enumerate(embeddings):
                    if i % 100 == 0 and i > 0:
                        print(f"  Processed {i}/{embedding_count} entries")
                    
                    e_id, embedding_id, e_metadata_str, document, document_id = embedding
                    
                    # Create a unique filename
                    filename_base = f"{i+1:04d}_{embedding_id}"
                    
                    # Save metadata
                    try:
                        e_metadata = json.loads(e_metadata_str) if e_metadata_str else {}
                    except:
                        e_metadata = {"error": "Could not parse metadata"}
                    
                    with open(os.path.join(collection_dir, f"{filename_base}_metadata.json"), 'w') as f:
                        metadata_output = {
                            "embedding_id": embedding_id,
                            "document_id": document_id,
                            "metadata": e_metadata
                        }
                        json.dump(metadata_output, f, indent=2)
                    
                    # Save document if it exists
                    if document:
                        with open(os.path.join(collection_dir, f"{filename_base}_document.txt"), 'w', encoding='utf-8') as f:
                            f.write(document)
                
                print(f"  Completed saving {embedding_count} entries for collection '{name}'")
            
            print(f"\nAll data dumped to {output_dir}")
            
        except Exception as e:
            print(f"Error dumping database: {e}")
        finally:
            conn.close()

def main():
    parser = argparse.ArgumentParser(description="ChromaDB Direct Explorer - Access ChromaDB data directly")
    parser.add_argument("--path", default="./chroma_db", help="Path to ChromaDB directory")
    parser.add_argument("--dump", action="store_true", help="Dump all documents to files")
    parser.add_argument("--output", default="./chroma_dump_direct", help="Directory to save dumped files")
    
    args = parser.parse_args()
    
    if os.path.basename(parser.prog) == "__main__.py":
        print("ChromaDB Direct Explorer")
        print("-" * 30)
        print("Choose operation mode:")
        print("1. Explore collections (direct DB access)")
        print("2. Dump all data (direct DB access)")
        mode = input("Enter mode (1/2): ") or "1"
        
        db_path = input("Enter ChromaDB path (default: ./chroma_db): ") or "./chroma_db"
        
        if mode == "1":
            explore_chromadb_collection_details(db_path)
        elif mode == "2":
            output_dir = input("Output directory (default: ./chroma_dump_direct): ") or "./chroma_dump_direct"
            dump_all_direct(db_path, output_dir)
        else:
            print("Invalid mode selected.")
    else:
        if args.dump:
            dump_all_direct(args.path, args.output)
        else:
            explore_chromadb_collection_details(args.path)

if __name__ == "__main__":
    main()