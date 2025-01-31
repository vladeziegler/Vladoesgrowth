import json
import os
from typing import Any, Optional, Type

try:
    import weaviate
    from weaviate.classes.config import Configure, Vectorizers
    from weaviate.classes.init import Auth

    WEAVIATE_AVAILABLE = True
except ImportError:
    WEAVIATE_AVAILABLE = False
    weaviate = Any  # type placeholder
    Configure = Any
    Vectorizers = Any
    Auth = Any

from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from weaviate.classes.query import Filter


class WeaviateToolSchema(BaseModel):
    """Input for WeaviateTool."""

    query: str = Field(
        ...,
        description="The query to search retrieve relevant information from the Weaviate database. Pass only the query, not the question.",
    )
    filter_by: Optional[str] = Field(
        default=None,
        description="Filter by properties. Pass only the properties, not the question.",
    )
    filter_value: Optional[str] = Field(
        default=None,
        description="Filter by value. Pass only the value, not the question.",
    )


class WeaviateVectorSearchTool(BaseTool):
    """Tool to query, and if needed filter results from a Weaviate database"""

    model_config = {"arbitrary_types_allowed": True}  # Add this line

    name: str = "WeaviateVectorSearchTool"
    description: str = "A tool to search the Weaviate database for relevant information on internal documents."
    args_schema: Type[BaseModel] = WeaviateToolSchema
    query: Optional[str] = None
    filter_by: Optional[str] = None
    filter_value: Optional[str] = None
    filters: Optional[Filter] = None
    vectorizer: Optional[Vectorizers] = None
    generative_model: Optional[str] = None
    collection_name: Optional[str] = None
    limit: Optional[int] = Field(default=3)
    headers: Optional[dict] = None
    weaviate_cluster_url: str = Field(
        ...,
        description="The URL of the Weaviate cluster",
    )
    weaviate_api_key: str = Field(
        ...,
        description="The API key for the Weaviate cluster",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if WEAVIATE_AVAILABLE:
            openai_api_key = os.environ.get("OPENAI_API_KEY")
            if not openai_api_key:
                raise ValueError(
                    "OPENAI_API_KEY environment variable is required for WeaviateVectorSearchTool and it is mandatory to use the tool."
                )
            self.headers = {"X-OpenAI-Api-Key": openai_api_key}
            self.vectorizer = self.vectorizer or Configure.Vectorizer.text2vec_openai(
                model="text-embedding-3-small",
            )
            self.generative_model = (
                self.generative_model
                or Configure.Generative.openai(
                    model="gpt-4o",
                )
            )

    def _run(
        self,
        query: str,
        filter_by: Optional[str] = None,
        filter_value: Optional[str] = None,
    ) -> str:
        if not WEAVIATE_AVAILABLE:
            raise ImportError(
                "The 'weaviate-client' package is required to use the WeaviateVectorSearchTool. "
                "Please install it with: uv add weaviate-client"
            )
        if filter_by and filter_value:
            self.filters = Filter.by_property(filter_by).equal(filter_value)
        else:
            self.filters = None

        if not self.weaviate_cluster_url or not self.weaviate_api_key:
            raise ValueError("WEAVIATE_URL or WEAVIATE_API_KEY is not set")

        client = weaviate.connect_to_weaviate_cloud(
            cluster_url=self.weaviate_cluster_url,
            auth_credentials=Auth.api_key(self.weaviate_api_key),
            headers=self.headers,
        )
        netflix_data_system = client.collections.get(self.collection_name)

        response = netflix_data_system.generate.near_text(
            query=query,
            limit=self.limit,
            filters=self.filters,
        )
        json_response = ""
        for obj in response.objects:
            json_response += json.dumps(obj.properties, indent=2)

        client.close()
        return json_response


if __name__ == "__main__":
    tool = WeaviateVectorSearchTool(
        weaviate_cluster_url=os.environ.get("WEAVIATE_URL"),
        weaviate_api_key=os.environ.get("WEAVIATE_API_KEY"),
        collection_name="YOUR_COLLECTION_NAME",
    )
    result = tool.run("Find me the best use cases for AI agents?")
    print("result", result)
