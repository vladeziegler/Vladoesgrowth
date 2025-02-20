#!/usr/bin/env python3
import sys
import os
import dotenv
from enum import Enum
from typing import Optional, Type, List, Union, Dict, Any

dotenv.load_dotenv()

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

class FilterOperator(str, Enum):
    """Supported Pinecone filter operators"""
    EQ = "$eq"      # Equal to
    NE = "$ne"      # Not equal to
    GT = "$gt"      # Greater than
    GTE = "$gte"    # Greater than or equal
    LT = "$lt"      # Less than
    LTE = "$lte"    # Less than or equal
    IN = "$in"      # In array
    NIN = "$nin"    # Not in array
    EXISTS = "$exists"  # Field exists
    AND = "$and"    # Logical AND
    OR = "$or"      # Logical OR

class FilterCondition(BaseModel):
    """Schema for a single filter condition"""
    field: str
    operator: FilterOperator
    value: Union[str, int, float, bool, List[Any]]

class PineconeToolSchema(BaseModel):
    """Input for PineconeTool."""
    query: str = Field(
        ...,
        description="The query to search and retrieve relevant information."
    )
    filters: Optional[List[FilterCondition]] = Field(
        default=None,
        description="List of filter conditions to apply"
    )
    top_k: Optional[int] = Field(
        default=5,
        description="Number of results to return"
    )

class PineconeVectorSearchTool(BaseTool):
    """Tool to query and filter results from a Pinecone database"""
    
    name: str = "PineconeVectorSearchTool"
    description: str = """
    A tool to search the Pinecone database with advanced filtering capabilities.
    """
    
    def _run(self, query: str, filters: Optional[Dict] = None, top_k: int = 5) -> str:
        """
        Execute the Pinecone search with filters.
        Args:
            query: The search query
            filters: Optional metadata filters dictionary
            top_k: Number of results to return
        Returns:
            Formatted string of results
        """
        try:
            pc = Pinecone(api_key=PINECONE_API_KEY)
            index = pc.Index(host=PINECONE_HOST)
            
            # Convert query to embedding
            query_embedding = pc.inference.embed(
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
                "top_k": top_k,
                "include_metadata": True
            }
            
            # Add filters if provided
            if filters:
                query_params["filter"] = filters
            
            # Execute search
            results = index.query(**query_params)
            
            # Format and print results
            output = f"\nSearch Query: '{query}'\n"
            if filters:
                output += f"Filters applied: {filters}\n"
            output += "Top Results:\n"
            
            for idx, match in enumerate(results.matches, 1):
                metadata = match.metadata
                output += f"\n{idx}. Score: {match.score:.3f}\n"
                output += f"Item Code: {metadata.get('item_code', 'N/A')}\n"
                output += f"Description: {metadata.get('item_description', 'N/A')}\n"
                output += f"Category: {metadata.get('category', 'N/A')}\n"
                output += f"Quantities - On-hand: {metadata.get('quantity_on_hand', 'N/A')}, "
                output += f"Available: {metadata.get('quantity_available', 'N/A')}\n"
                output += f"Total Inventory Value: {metadata.get('total_inventory_value', 'N/A')}\n"
            
            return output
            
        except Exception as e:
            return f"Error during search: {str(e)}"

    @staticmethod
    def create_filter(**kwargs):
        """
        Helper function to create properly structured filters
        Examples:
            create_filter(
                category=(FilterOperator.EQ, "Apparel/T-Shirts"),
                quantity_available=(FilterOperator.LT, 100)
            )
        """
        filter_dict = {}
        for field, (operator, value) in kwargs.items():
            if isinstance(operator, FilterOperator):
                filter_dict[field] = {operator.value: value}
        return filter_dict

    @staticmethod
    def create_range_filter(field, min_value=None, max_value=None):
        """
        Create a range filter for numeric fields
        Args:
            field: The field to filter on
            min_value: Minimum value (inclusive)
            max_value: Maximum value (inclusive)
        """
        conditions = {}
        if min_value is not None:
            conditions[FilterOperator.GTE.value] = min_value
        if max_value is not None:
            conditions[FilterOperator.LTE.value] = max_value
        return {field: conditions}

def main():
    tool = PineconeVectorSearchTool()
    
    # Example queries with filters
    example_queries = [
        (
            "Show all Apparel/T-Shirts inventory details",
            tool.create_filter(category=(FilterOperator.EQ, "Apparel/T-Shirts"))
        ),
        (
            "Which items are low in available stock?",
            tool.create_filter(quantity_available=(FilterOperator.LT, 100))
        ),
        (
            "List items with high inventory value",
            tool.create_filter(total_inventory_value=(FilterOperator.GT, 5000))
        ),
        (
            "Show items with quantity between 50 and 150",
            tool.create_range_filter("quantity_on_hand", 50, 150)
        )
    ]
    
    # Interactive query interface
    print("Choose a query or enter your own:")
    for idx, (query, _) in enumerate(example_queries, 1):
        print(f"{idx}. {query}")
    print("0. Enter your own query")
    
    choice = input("\nEnter your choice (0-4): ")
    
    if choice == "0":
        query_text = input("\nEnter your query: ")
        custom_filter = input("Do you want to add a metadata filter? (y/n): ").lower().startswith('y')
        if custom_filter:
            key = input("Enter metadata field key (e.g., category, quantity_on_hand): ")
            print("\nAvailable operators:")
            for op in FilterOperator:
                print(f"  {op.name}: {op.value}")
            op_name = input("Enter operator name: ").upper()
            value = input("Enter value: ")
            try:
                value = float(value)
            except ValueError:
                pass
            filters = tool.create_filter(**{key: (FilterOperator[op_name], value)})
        else:
            filters = None
    else:
        try:
            query_text, filters = example_queries[int(choice)-1]
        except (ValueError, IndexError):
            print("Invalid choice. Using default query.")
            query_text, filters = example_queries[0]
    
    # Perform the search
    result = tool.run(query=query_text, filters=filters)
    print(result)
    
    # Allow multiple queries
    while input("\nWould you like to try another query? (y/n): ").lower().startswith('y'):
        query_text = input("\nEnter your query: ")
        custom_filter = input("Do you want to add a metadata filter? (y/n): ").lower().startswith('y')
        if custom_filter:
            key = input("Enter metadata field key (e.g., category, quantity_on_hand): ")
            print("\nAvailable operators:")
            for op in FilterOperator:
                print(f"  {op.name}: {op.value}")
            op_name = input("Enter operator name: ").upper()
            value = input("Enter value: ")
            try:
                value = float(value)
            except ValueError:
                pass
            filters = tool.create_filter(**{key: (FilterOperator[op_name], value)})
        else:
            filters = None
        result = tool.run(query=query_text, filters=filters)
        print(result)

if __name__ == "__main__":
    main()