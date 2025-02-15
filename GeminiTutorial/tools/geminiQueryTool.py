import os
from typing import Dict, Any
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
from llama_index.core.schema import ImageNode

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

class GeminiQueryTool:
    def __init__(self, api_key: str, qdrant_path: str = "qdrant_simple"):
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        self.qdrant_path = qdrant_path
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setup_settings()
        self.client = qdrant_client.QdrantClient(path=self.qdrant_path)
        self.vector_store = QdrantVectorStore(
            client=self.client, 
            collection_name="invoice_collection"
        )
        # Create the index during initialization
        self.storage_context = StorageContext.from_defaults(vector_store=self.vector_store)
        self.index = None  # Will be set after processing documents
        
    def setup_settings(self):
        """Initialize Gemini settings"""
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001", 
            api_key=self.api_key
        )
        Settings.llm = Gemini(api_key=self.api_key)

    def json_output(self, image_path: str) -> Dict[str, Any]:
        """Extract JSON data from an invoice image"""
        abs_path = os.path.join(self.base_dir, image_path)
        if not os.path.exists(abs_path):
            raise ValueError(f"Image not found at: {abs_path}")
            
        # Load the image
        documents = SimpleDirectoryReader(abs_path).load_data()
        
        # Setup Gemini for image processing
        gemini_llm = GeminiMultiModal(model_name="models/gemini-2.0-flash")
        prompt = "Summarize the invoice in the image and return the answer in JSON format"
        
        # Process the image
        llm_program = MultiModalLLMCompletionProgram.from_defaults(
            output_parser=PydanticOutputParser(InvoiceData),
            image_documents=documents,
            prompt_template_str=prompt,
            multi_modal_llm=gemini_llm,
            verbose=True,
        )
        
        # Get the result
        result = llm_program()
        
        # Create a TextNode with the invoice information
        text_content = (
            f"Invoice Details:\n"
            f"Bank Name: {result.bank_name}\n"
            f"Receiving Bank Details: {result.receiving_bank_details}\n"
            f"Payment Due Date: {result.payment_due_date}\n"
            f"Balance Due: ${result.balance_due:,}\n"
            f"PO Number: {result.PO_number}\n"
            f"Payment Terms: {result.payment_terms} days\n"
            f"Recipient Name: {result.recipient_name}"
        )
        
        node = TextNode(text=text_content)
        
        # Create index with the text node
        self.index = VectorStoreIndex.from_documents(
            [node],
            storage_context=self.storage_context,
        )
        
        return result

    def query(self, question: str) -> str:
        """Query the stored invoice data"""
        if self.index is None:
            raise ValueError("No documents have been processed yet. Call json_output first.")
            
        query_engine = self.index.as_query_engine(similarity_top_k=3)
        response = query_engine.query(question)
        return str(response)

def example_usage():
    # Initialize the tool
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    tool = GeminiQueryTool(api_key=GOOGLE_API_KEY)
    
    # Extract JSON data from invoice
    result = tool.json_output("invoice")
    print("JSON Output:", result)
    
    # Query the invoice data
    answer = tool.query("What is the total amount due on the invoice? What are the payment terms?")
    print("Query Response:", answer)

if __name__ == "__main__":
    example_usage()