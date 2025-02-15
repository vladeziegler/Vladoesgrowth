#  This is the script to create your vector index using Qdrant
import os
from typing import List
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client
from llama_index.core.schema import ImageNode, Document
import dotenv

dotenv.load_dotenv()

class GeminiIndexTool:
    def __init__(self, api_key: str, qdrant_path: str = "qdrant_index"):
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        self.qdrant_path = qdrant_path
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setup_settings()
        
    def setup_settings(self):
        """Initialize Gemini settings"""
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001", 
            api_key=self.api_key
        )
        Settings.llm = Gemini(api_key=self.api_key)

    def create_index(self, invoice_directory: str) -> None:
        """Create and store vector index from invoice images"""
        # Convert to absolute path
        abs_path = os.path.join(self.base_dir, invoice_directory)
        if not os.path.exists(abs_path):
            raise ValueError(f"Invoice directory not found at: {abs_path}")

        # Load all images from the directory
        print(f"Loading documents from {abs_path}")
        documents = SimpleDirectoryReader(abs_path).load_data()
        
        # Setup Qdrant
        print("Setting up Qdrant vector store...")
        client = qdrant_client.QdrantClient(path=self.qdrant_path)
        vector_store = QdrantVectorStore(
            client=client, 
            collection_name="invoice_collection",
            force_recreate=True  # This ensures we start fresh
        )
        
        # Create storage context
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        
        # Create index
        print("Creating vector index...")
        index = VectorStoreIndex.from_documents(
            documents,
            storage_context=storage_context,
            show_progress=True
        )
        
        print(f"Successfully created index with {len(documents)} documents")
        return

def index_invoices():
    # Initialize the tool
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Replace with your API key
    indexer = GeminiIndexTool(api_key=GOOGLE_API_KEY)
    
    # Create the index
    indexer.create_index("invoice")
    print("Index creation completed!")

if __name__ == "__main__":
    index_invoices()