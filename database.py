"""
Database connection module for ChromaDB
Handles both local and Docker deployments
"""

import os
import chromadb
from chromadb import HttpClient, PersistentClient
import streamlit as st

COLLECTION_NAME = "rada_chatbot_data"

def init_chroma_local(path="./chroma_db"):
    """Initialize ChromaDB from local persistent storage"""
    try:
        client = PersistentClient(path=path)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ ChromaDB collection '{COLLECTION_NAME}' initialized (Local)")
        return collection
    except Exception as e:
        print(f"❌ Local ChromaDB failed: {e}")
        return None

def init_chroma_docker(host="localhost", port=8000):
    """Initialize ChromaDB from Docker container"""
    try:
        client = HttpClient(host=host, port=port)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ ChromaDB collection '{COLLECTION_NAME}' initialized (Docker)")
        return collection
    except Exception as e:
        print(f"❌ Docker ChromaDB failed: {e}")
        return None

def init_chroma_cloud(url=None):
    """Initialize ChromaDB from Streamlit Cloud storage"""
    try:
        # For Streamlit Cloud deployment
        # We'll upload the chroma_db folder to the repo
        chroma_path = os.path.join(os.path.dirname(__file__), "chroma_db")
        
        if not os.path.exists(chroma_path):
            raise FileNotFoundError(f"ChromaDB folder not found at {chroma_path}")
        
        client = PersistentClient(path=chroma_path)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )
        print(f"✅ ChromaDB collection '{COLLECTION_NAME}' initialized (Cloud)")
        return collection
    except Exception as e:
        print(f"❌ Cloud ChromaDB failed: {e}")
        return None

@st.cache_resource
def get_vector_db():
    """
    Smart initialization - tries multiple methods
    Priority: Cloud > Local > Docker
    """
    
    # Try 1: Streamlit Cloud (from repo)
    collection = init_chroma_cloud()
    if collection:
        return collection, "cloud"
    
    # Try 2: Local persistent
    collection = init_chroma_local()
    if collection:
        return collection, "local"
    
    # Try 3: Docker
    docker_host = os.getenv("CHROMA_DOCKER_HOST", "localhost")
    docker_port = int(os.getenv("CHROMA_DOCKER_PORT", "8000"))
    collection = init_chroma_docker(docker_host, docker_port)
    if collection:
        return collection, "docker"
    
    raise RuntimeError("❌ Failed to initialize ChromaDB from any source!")

def export_chroma_for_deployment(source_path="./chroma_db", dest_path="./chroma_db_export"):
    """
    Export ChromaDB for deployment to Streamlit Cloud
    This creates a clean, portable copy of your vector database
    """
    import shutil
    
    if os.path.exists(dest_path):
        shutil.rmtree(dest_path)
    
    shutil.copytree(source_path, dest_path)
    print(f"✅ ChromaDB exported to {dest_path}")
    print(f"   Size: {get_folder_size(dest_path)} MB")
    print(f"   Ready for Git commit and Streamlit deployment!")

def get_folder_size(path):
    """Calculate folder size in MB"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            total += os.path.getsize(fp)
    return round(total / (1024 * 1024), 2)

if __name__ == "__main__":
    # Test connections
    print("Testing database connections...")
    collection, source = get_vector_db()
    print(f"✅ Successfully connected via: {source}")
    print(f"   Collection count: {collection.count()}")
