#  Use this tool in your AI agents (e.g. CrewAI)

import os
from typing import List, Any
from llama_index.llms.gemini import Gemini
from llama_index.core.llms import ChatMessage, ImageBlock
from llama_index.multi_modal_llms.gemini import GeminiMultiModal
from llama_index.core.program import MultiModalLLMCompletionProgram
from llama_index.core.output_parsers import PydanticOutputParser
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex, StorageContext, Settings
from llama_index.core.schema import TextNode
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.vector_stores.qdrant import QdrantVectorStore
import qdrant_client
from pydantic import BaseModel
from PIL import Image
import matplotlib.pyplot as plt
import dotenv

dotenv.load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # add your GOOGLE API key here
os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY

class GoogleRestaurant(BaseModel):
    """Data model for a Google Restaurant."""

    bank_name: str
    receiving_bank_details: str
    payment_due_date: str
    balance_due: int
    PO_number: str
    payment_terms: str
    recipient_name: str

google_image_url = "./GeminiTutorial/invoice/invoice.png"
image = Image.open(google_image_url).convert("RGB")

plt.figure(figsize=(16, 5))
plt.imshow(image)

class GeminiTool:
    def __init__(self, api_key: str, qdrant_path: str = "qdrant_gemini_12"):
        self.api_key = api_key
        os.environ["GOOGLE_API_KEY"] = api_key
        self.qdrant_path = qdrant_path
        # Get the parent directory of the tools folder
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.setup_settings()
        
    def setup_settings(self):
        """Initialize Gemini settings"""
        Settings.embed_model = GeminiEmbedding(
            model_name="models/embedding-001", 
            api_key=self.api_key
        )
        Settings.llm = Gemini(api_key=self.api_key)

    def process_invoice_pydantic(self, invoice_directory: str) -> List[Any]:
        """Process invoice images and return Pydantic objects"""
        # Convert relative path to absolute path
        abs_invoice_dir = os.path.join(self.base_dir, invoice_directory)
        if not os.path.exists(abs_invoice_dir):
            raise ValueError(f"Invoice directory not found at: {abs_invoice_dir}")
            
        prompt_template_str = """\
            summarise the invoice in the image\
            and return the answer with json format \
        """
        
        image_documents = SimpleDirectoryReader(abs_invoice_dir).load_data()
        results = []
        
        for img_doc in image_documents:
            if "invoice" in img_doc.image_path:
                pydantic_response = self._pydantic_gemini(
                    "models/gemini-2.0-flash",
                    GoogleRestaurant,
                    [img_doc],
                    prompt_template_str,
                )
                results.append(pydantic_response)
        
        return results

    def _pydantic_gemini(self, model_name, output_class, image_documents, prompt_template_str):
        """Internal method to process images with Gemini"""
        gemini_llm = GeminiMultiModal(model_name=model_name)
        llm_program = MultiModalLLMCompletionProgram.from_defaults(
            output_parser=PydanticOutputParser(output_class),
            image_documents=image_documents,
            prompt_template_str=prompt_template_str,
            multi_modal_llm=gemini_llm,
            verbose=True,
        )
        return llm_program()

    def query_invoice(self, invoice_directory: str, query: str) -> str:
        """Query processed invoice data"""
        # Convert relative path to absolute path
        abs_invoice_dir = os.path.join(self.base_dir, invoice_directory)
        if not os.path.exists(abs_invoice_dir):
            raise ValueError(f"Invoice directory not found at: {abs_invoice_dir}")
            
        # Process results into nodes
        results = self.process_invoice_pydantic(abs_invoice_dir)
        nodes = []
        for res in results:
            text_node = TextNode()
            metadata = {}
            for r in res:
                if r[0] == "description":
                    text_node.text = r[1]
                else:
                    metadata[r[0]] = r[1]
            text_node.metadata = metadata
            nodes.append(text_node)

        # Setup vector store and index
        client = qdrant_client.QdrantClient(path=self.qdrant_path)
        vector_store = QdrantVectorStore(client=client, collection_name="collection_2")
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex(nodes=nodes, storage_context=storage_context)
        
        # Query
        query_engine = index.as_query_engine(similarity_top_k=3)
        response = query_engine.query(query)
        return str(response)

def query_invoice():
    # Initialize the tool
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # add your GOOGLE API key here
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    gemini_tool = GeminiTool(api_key=GOOGLE_API_KEY)

    results = gemini_tool.process_invoice_pydantic("./invoice")
    print(results)

def query_invoice_response():
    # Initialize the tool
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # add your GOOGLE API key here
    os.environ["GOOGLE_API_KEY"] = GOOGLE_API_KEY
    gemini_tool = GeminiTool(api_key=GOOGLE_API_KEY)

    # Or query the invoice
    response = gemini_tool.query_invoice(
        "./invoice",
        "how much is the invoice directed to Tesla? What are the payment terms?"
    )
    print(response)

query_invoice()

