#  This is the script to query your vector database
import os
from typing import Dict, Any, List
from llama_index.llms.gemini import Gemini
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
from llama_index.core.program import MultiModalLLMCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client
from pydantic import BaseModel
from llama_index.core.schema import TextNode
import os 
import dotenv

dotenv.load_dotenv()

class InvoiceData(BaseModel):
    """Data model for Invoice Information"""
    bank_name: str
    receiving_bank_details: str
    payment_due_date: str
    balance_due: int
    PO_number: str
    payment_terms: str
    recipient_name: str

class GeminiQueryProcessor:
    def __init__(self, api_key: str, qdrant_path: str = "qdrant_index"):
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        self.qdrant_path = qdrant_path
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setup_settings()
        
        # Connect to existing Qdrant store
        self.client = qdrant_client.QdrantClient(path=self.qdrant_path)
        self.vector_store = QdrantVectorStore(
            client=self.client, 
            collection_name="invoice_collection"
        )
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        
    def setup_settings(self):
        """Initialize Gemini settings"""
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001", 
            api_key=self.api_key
        )
        Settings.llm = Gemini(api_key=self.api_key)

    def get_json_output(self, invoice_directory: str) -> List[Dict[str, Any]]:
        """Process invoice images and return JSON data"""
        abs_path = os.path.join(self.base_dir, invoice_directory)
        if not os.path.exists(abs_path):
            raise ValueError(f"Invoice directory not found at: {abs_path}")
            
        documents = SimpleDirectoryReader(abs_path).load_data()
        results = []
        
        for doc in documents:
            if "invoice" in doc.image_path:
                # Setup Gemini for image processing
                gemini_llm = GeminiMultiModal(model_name="models/gemini-2.0-flash")
                prompt = "Summarize the invoice in the image and return the answer in JSON format"
                
                # Process the image
                llm_program = MultiModalLLMCompletionProgram.from_defaults(
                    output_parser=PydanticOutputParser(InvoiceData),
                    image_documents=[doc],
                    prompt_template_str=prompt,
                    multi_modal_llm=gemini_llm,
                    verbose=True,
                )
                
                result = llm_program()
                results.append(result.model_dump())  # Updated from dict() to model_dump()
                
        return results

    def query_index(self, query: str) -> str:
        """Query the existing invoice index"""
        # First get the JSON data
        results = self.get_json_output("invoice")
        
        # Create text nodes from the JSON data
        nodes = []
        for result in results:
            # Create a readable text content from the JSON data
            text_content = (
                f"Invoice Details:\n"
                f"Bank Name: {result['bank_name']}\n"
                f"Receiving Bank Details: {result['receiving_bank_details']}\n"
                f"Payment Due Date: {result['payment_due_date']}\n"
                f"Balance Due: ${result['balance_due']:,}\n"
                f"PO Number: {result['PO_number']}\n"
                f"Payment Terms: {result['payment_terms']}\n"
                f"Recipient Name: {result['recipient_name']}"
            )
            
            # Create text node with metadata
            node = TextNode(text=text_content, metadata=result)
            nodes.append(node)

        # Create index with the text nodes
        index = VectorStoreIndex(
            nodes=nodes,
            storage_context=self.storage_context,
        )
        
        # Query
        query_engine = index.as_query_engine(similarity_top_k=3)
        response = query_engine.query(query)
        return str(response)

def example_usage():
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    processor = GeminiQueryProcessor(api_key=GOOGLE_API_KEY)
    
    # Get JSON output
    json_results = processor.get_json_output("invoice")
    print("\nJSON Output:")
    for result in json_results:
        print(f"\nInvoice for {result['recipient_name']}:")
        for key, value in result.items():
            print(f"{key}: {value}")
    
    # Query the index
    print("\nQuery Response:")
    query_response = processor.query_index(
        "What is the total amount due on the invoice and what are the payment terms?"
    )
    print(query_response)

if __name__ == "__main__":
    example_usage()