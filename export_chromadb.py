"""
Export ChromaDB from Docker to local folder for Streamlit Cloud deployment
Run this script before deploying to Streamlit Cloud
"""

import os
import shutil
import chromadb
from chromadb import HttpClient
from tqdm import tqdm

DOCKER_HOST = "localhost"
DOCKER_PORT = 8000
COLLECTION_NAME = "rada_chatbot_data"
EXPORT_PATH = "./chroma_db"

def export_from_docker():
    """
    Export ChromaDB from Docker container to local folder
    This makes it portable for Streamlit Cloud deployment
    """
    
    print("="*60)
    print("🚀 CHROMADB EXPORT FOR STREAMLIT DEPLOYMENT")
    print("="*60)
    
    # Connect to Docker ChromaDB
    print(f"\n📡 Connecting to ChromaDB in Docker ({DOCKER_HOST}:{DOCKER_PORT})...")
    try:
        docker_client = HttpClient(host=DOCKER_HOST, port=DOCKER_PORT)
        docker_collection = docker_client.get_collection(name=COLLECTION_NAME)
        total_records = docker_collection.count()
        print(f"✅ Connected! Found {total_records} records")
    except Exception as e:
        print(f"❌ Failed to connect to Docker ChromaDB: {e}")
        print("\n💡 Make sure ChromaDB is running in Docker:")
        print("   docker run -p 8000:8000 chromadb/chroma")
        return False
    
    # Prepare local export folder
    print(f"\n📁 Preparing export folder: {EXPORT_PATH}")
    if os.path.exists(EXPORT_PATH):
        print("   ⚠️ Folder exists, removing...")
        shutil.rmtree(EXPORT_PATH)
    os.makedirs(EXPORT_PATH)
    
    # Create local ChromaDB
    print(f"\n💾 Creating local ChromaDB...")
    local_client = chromadb.PersistentClient(path=EXPORT_PATH)
    local_collection = local_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )
    
    # Export data in batches
    print(f"\n📤 Exporting {total_records} records...")
    batch_size = 500
    
    for i in tqdm(range(0, total_records, batch_size), desc="Exporting"):
        # Get batch from Docker
        results = docker_collection.get(
            limit=batch_size,
            offset=i,
            include=["embeddings", "documents", "metadatas"]
        )
        
        # Add to local
        if results['ids']:
            local_collection.upsert(
                ids=results['ids'],
                embeddings=results['embeddings'],
                documents=results['documents'],
                metadatas=results['metadatas']
            )
    
    # Verify export
    local_count = local_collection.count()
    print(f"\n✅ Export complete!")
    print(f"   Docker records: {total_records}")
    print(f"   Local records: {local_count}")
    
    if local_count == total_records:
        print("   ✅ All records exported successfully!")
    else:
        print(f"   ⚠️ Warning: Record count mismatch!")
        return False
    
    # Calculate size
    total_size = get_folder_size(EXPORT_PATH)
    print(f"\n📊 Export Statistics:")
    print(f"   Location: {os.path.abspath(EXPORT_PATH)}")
    print(f"   Size: {total_size:.2f} MB")
    print(f"   Records: {local_count}")
    
    if total_size > 100:
        print(f"\n   ⚠️ Warning: ChromaDB is large ({total_size:.2f} MB)")
        print("   Consider using Git LFS or external hosting for deployment")
    
    print("\n" + "="*60)
    print("✅ EXPORT COMPLETE - READY FOR DEPLOYMENT!")
    print("="*60)
    print("\n📝 Next Steps:")
    print("   1. Commit the chroma_db folder to your Git repository")
    print("   2. Push to GitHub")
    print("   3. Deploy to Streamlit Cloud")
    print("   4. The app will automatically use the local chroma_db\n")
    
    return True

def get_folder_size(path):
    """Calculate folder size in MB"""
    total = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.exists(fp):
                total += os.path.getsize(fp)
    return total / (1024 * 1024)

def create_gitignore():
    """Create .gitignore if it doesn't exist"""
    gitignore_path = ".gitignore"
    gitignore_content = """
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
*.egg-info/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Streamlit
.streamlit/secrets.toml

# Local ChromaDB (if using Docker in development)
# Uncomment if you only want deployed version:
# chroma_db/

# Feedback file
feedback.txt
"""
    
    if not os.path.exists(gitignore_path):
        with open(gitignore_path, 'w') as f:
            f.write(gitignore_content.strip())
        print(f"✅ Created {gitignore_path}")

if __name__ == "__main__":
    success = export_from_docker()
    
    if success:
        create_gitignore()
        print("\n🎉 All done! Your app is ready for Streamlit Cloud deployment.")
    else:
        print("\n❌ Export failed. Please check the errors above.")
