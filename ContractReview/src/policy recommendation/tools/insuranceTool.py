import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List, Type, Union
from pydantic import BaseModel, Field, ConfigDict
from crewai_tools import BaseTool

# Default OpenAI API key - replace with your own or set as environment variable
import os
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Default path to the index
DEFAULT_INDEX_DIR = "/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/ContractReview/src/policy recommendation/utils/policy_index"

class DocumentQueryInput(BaseModel):
    """Schema for document query tool input"""
    query: str = Field(
        description="The question or query about the document content. It should only be one question at a time. For example: 'What is the claim number?'"
    )

class DocumentQueryOutput(BaseModel):
    """Schema for document query tool output"""
    answer: str = Field(
        description="The answer to the query based on the document content"
    )
    source_text: str = Field(
        description="The full text from the document that was used to generate the answer"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if any"
    )

class PolicyQueryTool(BaseTool):
    """Tool for querying document index using RAG with a simple interface."""
    
    name: str = "PolicyQueryTool"
    description: str = """Useful for querying information from insurance policy documents. 
    You can ask questions about policy details, coverage, deductibles, and other information contained in insurance documents."""
    args_schema: Type[BaseModel] = DocumentQueryInput
    
    # Define class attributes for custom properties
    index_dir: str = Field(default=DEFAULT_INDEX_DIR)
    similarity_top_k: int = Field(default=3)
    temperature: float = Field(default=0.5)  # Lower temperature for more deterministic answers
    model: str = Field(default="gpt-4o")  # Using OpenAI model for reliability
    openai_api_key: Optional[str] = Field(default=OPENAI_API_KEY)
    
    # Add fields for components that will be initialized later
    index: Optional[Any] = Field(default=None, exclude=True)
    llm: Optional[Any] = Field(default=None, exclude=True)
    retriever: Optional[Any] = Field(default=None, exclude=True)
    query_engine: Optional[Any] = Field(default=None, exclude=True)
    qa_template: Optional[Any] = Field(default=None, exclude=True)
    
    # Allow arbitrary types for attributes that might be set later
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(
        self, 
        index_dir: str = DEFAULT_INDEX_DIR,
        similarity_top_k: int = 3,
        temperature: float = 0.5,
        model: str = "gpt-4o",
        openai_api_key: Optional[str] = OPENAI_API_KEY
    ):
        """
        Initialize the document query tool.
        
        Args:
            index_dir: Directory where the document index is stored
            similarity_top_k: Number of most similar chunks to retrieve
            temperature: Temperature for the LLM response generation
            model: OpenAI model to use for generation
            openai_api_key: OpenAI API key
        """
        # Initialize the BaseTool first
        super().__init__()
        
        # Set attributes using the proper way for Pydantic models
        object.__setattr__(self, "index_dir", index_dir)
        object.__setattr__(self, "similarity_top_k", similarity_top_k)
        object.__setattr__(self, "temperature", temperature)
        object.__setattr__(self, "model", model)
        
        # Set OpenAI API key
        if openai_api_key:
            os.environ["OPENAI_API_KEY"] = openai_api_key
        elif "OPENAI_API_KEY" not in os.environ:
            raise ValueError("OpenAI API key not provided. Please set the OPENAI_API_KEY environment variable or pass it as a parameter.")
        
        # Initialize the index and query engine
        self._initialize_index_and_engine()
    
    def _initialize_index_and_engine(self):
        """Initialize the index and query engine."""
        try:
            from llama_index.core import StorageContext, load_index_from_storage, Settings
            from llama_index.core.query_engine import RetrieverQueryEngine
            from llama_index.llms.openai import OpenAI
            from llama_index.embeddings.openai import OpenAIEmbedding
        except ImportError:
            print("Required libraries not found. Installing them now...")
            import subprocess
            subprocess.check_call(["pip", "install", "llama-index", "llama-index-llms-openai", "llama-index-embeddings-openai"])
            
            from llama_index.core import StorageContext, load_index_from_storage, Settings
            from llama_index.core.query_engine import RetrieverQueryEngine
            from llama_index.llms.openai import OpenAI
            from llama_index.embeddings.openai import OpenAIEmbedding
        
        # Check if index exists
        index_path = Path(self.index_dir)
        if not (index_path / "docstore.json").exists():
            raise FileNotFoundError(f"Index not found at {self.index_dir}. Please create the index first.")
        
        # Set the embedding model to match what was used to create the index
        embed_model = OpenAIEmbedding(model="text-embedding-3-small")
        print(f"Setting up embedding model: {embed_model}")
        
        # Set the embedding model as the default for loading
        Settings.embed_model = embed_model
        
        # Load the index with detailed diagnostics
        print(f"Loading index from {self.index_dir}...")
        try:
            storage_context = StorageContext.from_defaults(persist_dir=self.index_dir)
            index = load_index_from_storage(storage_context)
            print("Index loaded successfully")
            
            # Debug index content
            print(f"Index type: {type(index)}")
            print(f"Number of docs in docstore: {len(index.docstore.docs)}")
            print(f"Available nodes: {list(index.docstore.docs.keys())}")
        except Exception as e:
            print(f"Error loading index: {e}")
            import traceback
            traceback.print_exc()
            raise
        
        # Configure LLM with OpenAI
        llm = OpenAI(temperature=self.temperature, model=self.model)
        print(f"Using LLM: OpenAI with model: {self.model}")
        
        # Create retriever
        retriever = index.as_retriever(similarity_top_k=self.similarity_top_k)
        print(f"Created retriever with similarity_top_k: {self.similarity_top_k}")
        
        # Set up query template
        from llama_index.core.prompts import PromptTemplate
        self.qa_template = PromptTemplate(
            """You are an expert insurance claims adjuster AI, specialized in analyzing insurance policies and coverage determination.

            Your task is to:
            1. Carefully analyze the provided policy context
            2. Evaluate the specific incident/damage described in the query
            3. Determine coverage based on both explicit and implicit policy terms
            4. Identify relevant policy sections that support your determination

            When analyzing coverage:
            - Look for both direct mentions and related terms that could apply
            - Consider exclusions and limitations that might affect coverage
            - Pay attention to specific conditions or requirements for coverage
            - Evaluate definitions that might impact coverage interpretation

            Context from the insurance policy:
            ---------------------
            {context_str}
            ---------------------

            Query about coverage: {query_str}

            Provide your response in this format:
            1. Coverage Determination: [Clear statement about whether the incident appears to be covered]
            2. Relevant Policy Sections: [Quote the specific sections from the context that support your determination]
            3. Analysis: [Explain how the policy sections apply to the specific incident]
            4. Important Conditions: [List any requirements or conditions that must be met for coverage]

            If certain aspects are unclear or need additional information, specify what details would be needed for a complete determination.
            """
        )
        
        # Create the query engine
        query_engine = RetrieverQueryEngine.from_args(
            retriever=retriever,
            llm=llm,
            text_qa_template=self.qa_template,
            response_mode="compact"
        )
        print("Query engine initialized successfully")
        
        # Store these objects as instance attributes
        object.__setattr__(self, "index", index)
        object.__setattr__(self, "llm", llm)
        object.__setattr__(self, "retriever", retriever)
        object.__setattr__(self, "query_engine", query_engine)
    
    def _parse_input(self, input_data: Union[str, Dict, Any]) -> str:
        """Parse the input data into a query string."""
        try:
            # Case 1: input is a dictionary with a query field
            if isinstance(input_data, dict) and "query" in input_data:
                return input_data["query"]
            
            # Case 2: input is a JSON string
            if isinstance(input_data, str):
                try:
                    # Try to parse as JSON
                    data = json.loads(input_data)
                    if isinstance(data, dict) and "query" in data:
                        return data["query"]
                except json.JSONDecodeError:
                    # Not a JSON string, treat as a query directly
                    return input_data
            
            # Case 3: input is any other value, convert to string
            return str(input_data)
            
        except Exception as e:
            # Fallback: if all else fails, return an error message
            error_msg = f"Error parsing input: {str(e)}"
            print(error_msg)
            return f"Error occurred while parsing input: {str(input_data)[:100]}..."
    
    def _run(self, *args, **kwargs) -> str:
        """Run a query against the document index."""
        try:
            # Debug prints to identify issues
            print(f"Using index directory: {self.index_dir}")
            print(f"Using model: {self.model}")
            
            # Parse the input based on how it was provided
            query = ""
            
            if kwargs and "query" in kwargs:
                # Case 1: Called with keyword arguments
                query = kwargs["query"]
            elif len(args) >= 1:
                # Case 2: Called with arguments
                query = self._parse_input(args[0])
            else:
                # Case 3: Called with no arguments
                return DocumentQueryOutput(
                    answer="",
                    source_text="No query provided",
                    error="No query provided"
                ).model_dump_json()
            
            print(f"Executing query: {query}")
            
            # Manually test retrieval to debug issues
            try:
                print("Testing retriever directly...")
                retriever_nodes = self.retriever.retrieve(query)
                print(f"Retrieved {len(retriever_nodes)} nodes directly from retriever")
                for i, node in enumerate(retriever_nodes):
                    print(f"Node {i+1} sample: {node.node.text[:100]}...")
            except Exception as e:
                print(f"Retriever test failed: {e}")
            
            # Execute the query with robust error handling
            try:
                print("Executing query through the query engine...")
                response = self.query_engine.query(query)
                print(f"Response received, type: {type(response)}")
            except Exception as e:
                print(f"Query execution failed: {e}")
                import traceback
                traceback.print_exc()
                raise
            
            # Extract source text from the response
            source_text = ""
            if hasattr(response, 'source_nodes') and response.source_nodes:
                print(f"Found {len(response.source_nodes)} source nodes")
                # Get the complete text from all source nodes
                source_texts = []
                for i, node in enumerate(response.source_nodes):
                    if hasattr(node, 'node') and hasattr(node.node, 'text'):
                        print(f"Adding text from node {i+1}")
                        source_texts.append(node.node.text)
                    else:
                        print(f"Node {i+1} structure: {dir(node)}")
                
                source_text = "\n\n---\n\n".join(source_texts)
                print(f"Total source text length: {len(source_text)}")
            else:
                print("No source nodes found in response")
                source_text = "No specific source text available."
            
            # Format response using output schema
            output = DocumentQueryOutput(
                answer=str(response) if response else "No answer generated",
                source_text=source_text,
                error=None
            )
            
            return output.model_dump_json()
                
        except Exception as e:
            error_msg = f"Error querying document: {str(e)}"
            print(error_msg)
            import traceback
            traceback.print_exc()
            
            # Format error response using output schema
            output = DocumentQueryOutput(
                answer="Error occurred during query processing",
                source_text="",
                error=error_msg
            )
            
            return output.model_dump_json()
        

# # For direct testing
if __name__ == "__main__":
    # Ensure API key is set
    os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
    
    # Create the tool
    print("Creating DocumentQueryTool...")
    tool = PolicyQueryTool()
    
    # Test queries
    test_queries = [
        "Is there a specified maximum coverage amount for fence damage caused by falling trees during a storm?",
        # "What is the policy number?",
        # "What damages were reported?",
        # "What was the date of loss?"
    ]
    
    for test_query in test_queries:
        print(f"\n\n=== Testing query: {test_query} ===")
        result = tool._run(test_query)
        
        # Parse and print results
        try:
            result_dict = json.loads(result)
            print(f"\nANSWER: {result_dict['answer']}")
            print(f"\nSOURCE TEXT PREVIEW: {result_dict['source_text'][:1000]}...")
        except:
            print(f"Raw result: {result}")