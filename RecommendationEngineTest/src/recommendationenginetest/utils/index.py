from pinecone import Pinecone, ServerlessSpec
import time

import os
import dotenv

dotenv.load_dotenv()

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
INDEX_NAME = "agents-data-2"

def create_index():
    """Create a new Pinecone index configured for the embedding model"""
    
    # Initialize Pinecone
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index already exists
    existing_indexes = pc.list_indexes()
    
    if INDEX_NAME not in existing_indexes:
        print(f"Creating new index: {INDEX_NAME}")
        
        # Create index with model configuration
        pc.create_index(
            name=INDEX_NAME,
            dimension=1024,  # dimension for multilingual-e5-large
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        
        print("\nIndex created successfully")
        
        # Wait for index to be ready
        print("\nWaiting for index to be ready...")
        time.sleep(20)
    else:
        print(f"\nIndex '{INDEX_NAME}' already exists")
        
    # Print index details
    index = pc.Index(INDEX_NAME)
    print("\nIndex details:")
    print(index.describe_index_stats())

if __name__ == "__main__":
    create_index()