from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec
import time
import os
import dotenv

dotenv.load_dotenv()

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "agents-data-3"

def reset_index():
    """Delete and recreate the Pinecone index"""
    try:
        # Initialize Pinecone with gRPC
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists
        existing_indexes = pc.list_indexes()
        
        if INDEX_NAME in existing_indexes:
            print(f"\nDeleting existing index '{INDEX_NAME}'...")
            pc.delete_index(name=INDEX_NAME)
            print("Index deleted successfully")
            
            # Wait a bit after deletion
            print("Waiting for deletion to complete...")
            time.sleep(10)
        
        # Create new index with simplified parameters
        print(f"\nCreating new index '{INDEX_NAME}'...")
        pc.create_index(
            name=INDEX_NAME,
            dimension=1024,  # dimension for multilingual-e5-large
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        
        print("\nWaiting for index to initialize (this may take a minute)...")
        time.sleep(20)
        
        # Verify index creation
        new_index = pc.Index(name=INDEX_NAME)
        stats = new_index.describe_index_stats()
        
        print("\nIndex created successfully!")
        print("\nIndex Statistics:")
        print(f"Total vectors: {stats.total_vector_count}")
        print(f"Namespaces: {stats.namespaces}")
        
        return True
        
    except Exception as e:
        print(f"\nError during index reset: {e}")
        print(f"Type of error: {type(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("This script will delete and recreate your Pinecone index.")
    print(f"Index name: {INDEX_NAME}")
    
    confirm = input("\nAre you sure you want to proceed? This will delete all existing data (y/n): ")
    
    if confirm.lower().startswith('y'):
        success = reset_index()
        if success:
            print("\nIndex reset completed successfully!")
        else:
            print("\nIndex reset failed. Please check the error messages above.")
    else:
        print("\nOperation cancelled.")

if __name__ == "__main__":
    main()