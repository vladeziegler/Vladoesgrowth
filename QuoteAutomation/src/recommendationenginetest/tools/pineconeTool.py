#!/usr/bin/env python3
import sys
import os
import dotenv
from enum import Enum
from typing import Optional, Type, List, Union, Dict, Any

# Get the absolute path to the project root (QuoteAutomation directory)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
ENV_PATH = os.path.join(PROJECT_ROOT, '.env')

print("Loading environment from:", ENV_PATH)
dotenv.load_dotenv(ENV_PATH)

# Debug prints
print("Environment variables after loading:")
print(f"PINECONE_API_KEY: {'set' if os.getenv('PINECONE_API_KEY') else 'not set'}")
print(f"PINECONE_HOST: {os.getenv('PINECONE_HOST')}")

# DEBUG: Print out Python executable and sys.path for troubleshooting.
print("Python executable:", sys.executable)
print("sys.path:")
for p in sys.path:
    print("  ", p)

# Attempt the exact same import as in your working query.py
try:
    from pinecone.grpc import PineconeGRPC as Pinecone
except ModuleNotFoundError as err:
    sys.stderr.write("Error importing pinecone.grpc:\n")
    sys.stderr.write(str(err) + "\n")
    sys.stderr.write("Ensure that:\n")
    sys.stderr.write("  1. You have installed pinecone-client with gRPC support: pip install \"pinecone-client[grpc]\"\n")
    sys.stderr.write("  2. There's no local file or folder named 'pinecone' shadowing the package.\n")
    raise

from typing import Optional, Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
import json

# Configuration
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_HOST = os.getenv("PINECONE_HOST")

class FilterColumn(str, Enum):
    """Available columns for filtering"""
    UPC_CODE = "upc_code"
    QUANTITY_AVAILABLE = "quantity_available"
    UNIT_COST = "unit_cost"

class FilterSign(str, Enum):
    """Available filter operations"""
    EQUAL_TO = "eq"  # For UPC code
    GREATER_THAN = "gt"  # For quantity
    LESS_THAN = "lt"  # For unit cost

class PineconeToolInput(BaseModel):
    """Schema for tool input"""
    query: str = Field(
        description="The item description to search for"
    )
    filter_column: Optional[FilterColumn] = Field(
        default=None,
        description="Column to filter on: upc_code, quantity_available, or unit_cost"
    )
    filter_sign: Optional[FilterSign] = Field(
        default=None,
        description="Filter operation to apply"
    )
    filter_value: Optional[Union[str, int, float]] = Field(
        default=None,
        description="Value to filter by (string for UPC, number for quantity/cost)"
    )

    @property
    def get_filter(self) -> Optional[Dict]:
        """Constructs the appropriate filter based on inputs"""
        if not all([self.filter_column, self.filter_sign, self.filter_value]):
            return None

        # Validate filter combinations
        if self.filter_column == FilterColumn.UPC_CODE:
            if self.filter_sign != FilterSign.EQUAL_TO:
                raise ValueError("UPC code must use EQUAL_TO comparison")
            value = str(self.filter_value)  # Ensure UPC is string
        elif self.filter_column == FilterColumn.QUANTITY_AVAILABLE:
            if self.filter_sign != FilterSign.GREATER_THAN:
                raise ValueError("Quantity must use GREATER_THAN comparison")
            value = int(self.filter_value)
        elif self.filter_column == FilterColumn.UNIT_COST:
            if self.filter_sign != FilterSign.LESS_THAN:
                raise ValueError("Unit cost must use LESS_THAN comparison")
            value = float(self.filter_value)
        
        return {
            self.filter_column.value: {
                f"${self.filter_sign.value}": value
            }
        }

class PineconeToolOutput(BaseModel):
    """Schema for tool output"""
    item_description: Optional[str] = Field(
        default=None,
        description="The description of the item"
    )
    upc_code: Optional[str] = Field(
        default=None,
        description="The UPC code of the item"
    )
    quantity_available: Optional[int] = Field(
        default=None,
        description="The available quantity of the item"
    )
    unit_cost: Optional[float] = Field(
        default=None,
        description="The unit cost of the item"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if any"
    )

class PineconeVectorSearchTool(BaseTool):
    name: str = "PineconeVectorSearchTool"
    description: str = """Search the Pinecone database for items"""
    args_schema: Type[BaseModel] = PineconeToolInput
    pc: Optional[Any] = None
    index: Optional[Any] = None

    def __init__(self):
        super().__init__()
        # Initialize Pinecone connection
        print("Initializing PineconeVectorSearchTool...")
        print(f"PINECONE_API_KEY: {'set' if PINECONE_API_KEY else 'not set'}")
        print(f"PINECONE_HOST: {PINECONE_HOST}")
        
        # Create Pinecone client
        self.pc = Pinecone(api_key=PINECONE_API_KEY)
        self.index = self.pc.Index(host=PINECONE_HOST)
        
        print("PineconeVectorSearchTool initialized successfully")

    def _run(self, query: str, filter_column: Optional[str] = None, 
            filter_sign: Optional[str] = None, filter_value: Optional[Any] = None) -> str:
        try:
            print(f"\nPineconeVectorSearchTool executing search with:")
            print(f"  Query: {query}")
            print(f"  Filter: {filter_column}={filter_value} ({filter_sign})")
            
            # Create input model and validate
            tool_input = PineconeToolInput(
                query=query,
                filter_column=filter_column,
                filter_sign=filter_sign,
                filter_value=filter_value
            )
            
            # Convert query to embedding
            query_embedding = self.pc.inference.embed(
                model="multilingual-e5-large",
                inputs=[query],
                parameters={
                    "input_type": "query",
                    "truncate": "END"
                }
            )[0]
            
            # Prepare query parameters
            query_params = {
                "namespace": "clothing-data-2",
                "vector": query_embedding.values,
                "top_k": 2,
                "include_metadata": True
            }
            
            # Add filter if provided
            filter_dict = tool_input.get_filter
            if filter_dict:
                query_params["filter"] = filter_dict
            
            print(f"Executing Pinecone query with params: {query_params}")
            
            # Execute search
            results = self.index.query(**query_params)
            print(f"Search results: {results}")
            
            if not results.matches:
                return PineconeToolOutput(
                    error="No matches found"
                ).json()
            
            # Get the best match
            match = results.matches[0]
            metadata = match.metadata
            
            # Format response using output schema
            response = PineconeToolOutput(
                item_description=metadata.get("item_description"),
                upc_code=metadata.get("upc_code"),
                quantity_available=metadata.get("quantity_available"),
                unit_cost=metadata.get("unit_cost"),
                error=None
            )
            
            return response.json()
            
        except Exception as e:
            print(f"Error in PineconeVectorSearchTool: {str(e)}")
            return PineconeToolOutput(
                error=str(e)
            ).json()

# def main():
#     tool = PineconeVectorSearchTool()
#     # Add debug prints
#     result = tool._run(
#         query="What are your athletic clothes?", 
#         filter_column=FilterColumn.QUANTITY_AVAILABLE, 
#         filter_sign=FilterSign.GREATER_THAN, 
#         filter_value=100
#     )
#     print(result)
# if __name__ == "__main__":
#     main()

