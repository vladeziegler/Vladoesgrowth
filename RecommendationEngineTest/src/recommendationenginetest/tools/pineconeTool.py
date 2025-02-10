#!/usr/bin/env python3
import sys
import os
import dotenv

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

class PineconeToolSchema(BaseModel):
    """Input for PineconeTool."""
    query: str = Field(
        ...,
        description="The query to search and retrieve relevant information from the Pinecone database."
    )
    filter_by: Optional[str] = Field(
        default=None,
        description="Filter by location. Pass only the location name, not the question."
    )

class PineconeVectorSearchTool(BaseTool):
    """Tool to query and filter results from a Pinecone database"""
    
    name: str = "PineconeVectorSearchTool"
    description: str = "A tool to search the Pinecone database for relevant information about AI agent use cases."
    args_schema: Type[BaseModel] = PineconeToolSchema
    
    def _run(self, query: str, filter_by: Optional[str] = None) -> str:
        """
        Execute the Pinecone search.
        Args:
            query: The search query.
            filter_by: Optional location to filter by.
        Returns:
            JSON string of results.
        """
        try:
            # Initialize Pinecone with gRPC
            pc = Pinecone(api_key=PINECONE_API_KEY)
            # Get the index using host
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
                "namespace": "agents-namespace",
                "vector": query_embedding.values,
                "top_k": 5,
                "include_metadata": True
            }
            
            # Add location filter if provided
            if filter_by:
                query_params["filter"] = {"location": {"$eq": filter_by}}
            
            # Execute search
            results = index.query(**query_params)
            
            # Format results
            formatted_results = []
            for match in results.matches:
                result = {
                    "score": float(match.score),
                    "role": match.metadata.get("role", "N/A"),
                    "location": match.metadata.get("location", "N/A"),
                    "company_activity": match.metadata.get("company_activity", "N/A"),
                    "task": match.metadata.get("task", "N/A"),
                    "hours_saved": match.metadata.get("hours_saved", "N/A"),
                    "money_saved": float(match.metadata.get("money_saved", 0))
                }
                formatted_results.append(result)
            
            return json.dumps(formatted_results, indent=2)
            
        except Exception as e:
            return f"Error during search: {str(e)}"

    def _arun(self, query: str, filter_by: Optional[str] = None):
        """Async version of _run (not implemented)"""
        raise NotImplementedError("Async version not implemented")


if __name__ == "__main__":
    # Example usage
    tool = PineconeVectorSearchTool()
    print("\nTesting search without filter...")
    result = tool.run("roles where voice agents are most prevalent?")
    print(result)