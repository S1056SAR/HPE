import streamlit as st
import chromadb
import pandas as pd
import numpy as np
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
import umap
import sqlite3
import tempfile
import shutil

st.set_page_config(page_title="ChromaDB Visualizer", layout="wide")

st.title("ChromaDB Visualizer")

# Sidebar for configuration
with st.sidebar:
    st.header("Configuration")
    db_path = st.text_input("ChromaDB Path", value="./chroma_db")
    
    st.subheader("Database Access Method")
    access_method = st.radio(
        "Choose method:",
        ["ChromaDB API (Standard)", "Direct SQLite Access (For problematic DBs)"]
    )
    
    st.subheader("Visualization Settings")
    viz_method = st.selectbox(
        "Dimensionality Reduction Method",
        ["PCA", "t-SNE", "UMAP"]
    )
    
    if viz_method == "t-SNE":
        perplexity = st.slider("Perplexity", 5, 50, 30)
        n_iter = st.slider("Iterations", 250, 1000, 300)
    elif viz_method == "UMAP":
        n_neighbors = st.slider("Neighbors", 2, 100, 15)
        min_dist = st.slider("Min Distance", 0.01, 0.99, 0.1)
    
    color_by = st.selectbox(
        "Color by",
        ["Collection", "Custom Field"]
    )
    
    if color_by == "Custom Field":
        color_field = st.text_input("Metadata Field Name", value="category")

# Function to load data using ChromaDB API
def load_via_api(db_path):
    try:
        client = chromadb.PersistentClient(path=db_path)
        collections = client.list_collections()
        
        all_embeddings = []
        all_documents = []
        all_metadatas = []
        all_collection_names = []
        
        for collection in collections:
            name = collection.name
            count = collection.count()
            
            if count > 0:
                try:
                    # Get all embeddings
                    data = collection.get(include=["embeddings", "documents", "metadatas"])
                    
                    if data and "embeddings" in data and data["embeddings"]:
                        embeddings = data["embeddings"]
                        documents = data["documents"]
                        metadatas = data["metadatas"]
                        
                        all_embeddings.extend(embeddings)
                        all_documents.extend(documents)
                        all_metadatas.extend(metadatas)
                        all_collection_names.extend([name] * len(embeddings))
                except Exception as e:
                    st.warning(f"Error loading data from collection {name}: {e}")
        
        return all_embeddings, all_documents, all_metadatas, all_collection_names
    except Exception as e:
        st.error(f"Error connecting to ChromaDB: {e}")
        return [], [], [], []

# Function to load data using direct SQLite access
def load_via_sqlite(db_path):
    chroma_db_file = os.path.join(db_path, "chroma.sqlite3")
    
    if not os.path.exists(chroma_db_file):
        st.error(f"SQLite database file not found at {chroma_db_file}")
        return [], [], [], []
    
    # Make a temporary copy of the database to avoid locks
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_db_path = os.path.join(temp_dir, "temp_chroma.sqlite3")
        shutil.copy2(chroma_db_file, temp_db_path)
        
        try:
            conn = sqlite3.connect(temp_db_path)
            cursor = conn.cursor()
            
            # Check if we have collections table
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='collections';")
            if not cursor.fetchone():
                st.error("Collections table not found. Database might be in a different format.")
                return [], [], [], []
            
            # Get all collections
            cursor.execute("SELECT name, id FROM collections")
            collections = cursor.fetchall()
            
            all_embeddings = []
            all_documents = []
            all_metadatas = []
            all_collection_names = []
            
            for name, collection_id in collections:
                # Get all embeddings for this collection
                cursor.execute("""
                    SELECT e.embedding, d.document, e.metadata
                    FROM embeddings e
                    LEFT JOIN documents d ON e.document_id = d.id
                    WHERE e.collection_id = ?
                """, (collection_id,))
                
                rows = cursor.fetchall()
                
                for embedding_blob, document, metadata_str in rows:
                    try:
                        # Convert blob to embedding vector
                        embedding = np.frombuffer(embedding_blob, dtype=np.float32).tolist()
                        
                        # Parse metadata
                        try:
                            metadata = json.loads(metadata_str) if metadata_str else {}
                        except:
                            metadata = {}
                        
                        all_embeddings.append(embedding)
                        all_documents.append(document or "")
                        all_metadatas.append(metadata)
                        all_collection_names.append(name)
                    except Exception as e:
                        st.warning(f"Error processing an embedding in collection {name}: {e}")
            
            conn.close()
            return all_embeddings, all_documents, all_metadatas, all_collection_names
        
        except Exception as e:
            st.error(f"Error accessing database directly: {e}")
            return [], [], [], []

# Load data based on selected method
if st.button("Load and Visualize Data"):
    with st.spinner("Loading data from ChromaDB..."):
        if access_method.startswith("ChromaDB API"):
            embeddings, documents, metadatas, collection_names = load_via_api(db_path)
        else:
            embeddings, documents, metadatas, collection_names = load_via_sqlite(db_path)
        
        if not embeddings:
            st.error("No embeddings found or could not load data.")
            st.stop()
        
        st.success(f"Loaded {len(embeddings)} embeddings from {len(set(collection_names))} collections")
        
        # Show collection distribution
        collection_counts = pd.Series(collection_names).value_counts()
        st.subheader("Collection Distribution")
        st.bar_chart(collection_counts)
        
        # Prepare data for visualization
        with st.spinner(f"Reducing dimensionality using {viz_method}..."):
            if len(embeddings) > 10000:
                st.warning(f"Large dataset detected ({len(embeddings)} embeddings). Sampling 10,000 points for visualization.")
                # Sample 10,000 random indices
                indices = np.random.choice(len(embeddings), size=10000, replace=False)
                embeddings_sample = [embeddings[i] for i in indices]
                collection_names_sample = [collection_names[i] for i in indices]
                metadatas_sample = [metadatas[i] for i in indices]
                documents_sample = [documents[i] for i in indices]
            else:
                embeddings_sample = embeddings
                collection_names_sample = collection_names
                metadatas_sample = metadatas
                documents_sample = documents
            
            # Check if all embedding vectors have the same length
            embedding_lengths = [len(emb) for emb in embeddings_sample]
            if len(set(embedding_lengths)) > 1:
                st.error(f"Embeddings have inconsistent dimensions: {set(embedding_lengths)}")
                st.stop()
            
            # Convert to numpy array
            embeddings_array = np.array(embeddings_sample)
            
            # Apply dimensionality reduction
            if viz_method == "PCA":
                model = PCA(n_components=3)
                reduced_data = model.fit_transform(embeddings_array)
            elif viz_method == "t-SNE":
                model = TSNE(n_components=3, perplexity=perplexity, n_iter=n_iter, random_state=42)
                reduced_data = model.fit_transform(embeddings_array)
            else:  # UMAP
                reducer = umap.UMAP(n_components=3, n_neighbors=n_neighbors, min_dist=min_dist, random_state=42)
                reduced_data = reducer.fit_transform(embeddings_array)
        
        # Create DataFrame for plotting
        plot_df = pd.DataFrame({
            'x': reduced_data[:, 0],
            'y': reduced_data[:, 1],
            'z': reduced_data[:, 2],
            'collection': collection_names_sample,
            'document': [doc[:100] + "..." if len(doc) > 100 else doc for doc in documents_sample]
        })
        
        # Add metadata fields
        if metadatas_sample and all(isinstance(m, dict) for m in metadatas_sample):
            all_keys = set()
            for m in metadatas_sample:
                all_keys.update(m.keys())
            
            for key in all_keys:
                plot_df[f'metadata_{key}'] = [m.get(key, None) for m in metadatas_sample]
        
        # Determine color column
        if color_by == "Collection":
            color_column = "collection"
        else:
            metadata_key = f"metadata_{color_field}"
            if metadata_key in plot_df.columns:
                color_column = metadata_key
            else:
                st.warning(f"Metadata field '{color_field}' not found. Using 'collection' instead.")
                color_column = "collection"
        
        # Create 3D scatter plot
        st.subheader("3D Embedding Visualization")
        
        fig = px.scatter_3d(
            plot_df, x='x', y='y', z='z',
            color=color_column,
            hover_data=['document'],
            labels={'collection': 'Collection'},
            title=f"Embeddings visualized with {viz_method}"
        )
        
        fig.update_layout(height=800)
        st.plotly_chart(fig, use_container_width=True)
        
        # Create 2D scatter plot (using just x and y dimensions)
        st.subheader("2D Embedding Visualization")
        
        fig_2d = px.scatter(
            plot_df, x='x', y='y',
            color=color_column,
            hover_data=['document'],
            labels={'collection': 'Collection'},
            title=f"Embeddings visualized with {viz_method} (2D projection)"
        )
        
        fig_2d.update_layout(height=600)
        st.plotly_chart(fig_2d, use_container_width=True)
        
        # Document Explorer
        st.subheader("Document Explorer")
        
        # Collection filter
        selected_collection = st.selectbox(
            "Filter by Collection", 
            ["All Collections"] + sorted(list(set(collection_names_sample)))
        )
        
        # Text search
        search_term = st.text_input("Search in documents")
        
        filtered_df = plot_df.copy()
        
        if selected_collection != "All Collections":
            filtered_df = filtered_df[filtered_df['collection'] == selected_collection]
        
        if search_term:
            filtered_df = filtered_df[filtered_df['document'].str.contains(search_term, case=False)]
        
        st.write(f"Showing {len(filtered_df)} documents")
        
        # Show documents
        for i, row in filtered_df.head(20).iterrows():
            with st.expander(f"{row['collection']}: {row['document'][:50]}..."):
                st.write(row['document'])
                
                # Show metadata
                metadata_cols = [col for col in row.index if col.startswith('metadata_')]
                if metadata_cols:
                    st.subheader("Metadata")
                    for col in metadata_cols:
                        if pd.notna(row[col]):
                            st.write(f"**{col.replace('metadata_', '')}:** {row[col]}")
        
        if len(filtered_df) > 20:
            st.write(f"... and {len(filtered_df) - 20} more documents")

# Instructions
if not st.button:
    st.info("""
    ### Instructions:
    
    1. Enter the path to your ChromaDB in the sidebar
    2. Select the access method (use Direct SQLite Access if the standard API gives errors)
    3. Choose visualization settings
    4. Click "Load and Visualize Data"
    
    The app will display:
    - A 3D visualization of your embeddings
    - A 2D projection for easier navigation
    - Distribution of documents across collections
    - A document explorer to search and browse content
    """)