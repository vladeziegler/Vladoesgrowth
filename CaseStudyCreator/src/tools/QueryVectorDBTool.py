
from crewai_tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from typing import Type, Optional
from embedchain import App
import logging

logger = logging.getLogger(__name__)

class QueryVectorDBInput(BaseModel):
    """Input for QueryVectorDB."""
    query: str = Field(..., description="The query to search the vector database")

class QueryVectorDBOutput(BaseModel):
    """Output for QueryVectorDB."""
    reply: str = Field(..., description="The reply from the query")
    error_message: str = Field(default="", description="Error message if the operation failed")

class QueryVectorDBTool(BaseTool):
    name: str = "Query Vector DB"
    description: str = "Queries the vector database with provided input query: 'The query to search the vector database'"
    args_schema: Type[BaseModel] = QueryVectorDBInput
    
    _app: Optional[App] = PrivateAttr(default=None)

    def __init__(self, app: App):
        super().__init__()
        self._app = app

    def _run(self, query: str, **kwargs) -> QueryVectorDBOutput:
        try:
            logger.info(f"Querying vector DB with: {query}")
            
            # Enhance the query with specific instructions
            enhanced_query = f"""Please analyze the following query about the content: {query}
            Provide specific examples and relevant information from the content."""

            # Query the database
            response = self._app.query(enhanced_query)

            # Handle tuple response if necessary
            reply = response[0] if isinstance(response, tuple) else response

            # Check for empty response
            if not reply or (isinstance(reply, str) and reply.strip() == ""):
                logger.warning("No content found in vector DB")
                return QueryVectorDBOutput(
                    reply="No relevant content found in the database.",
                    error_message="No content found"
                )

            logger.info("Query completed successfully")
            return QueryVectorDBOutput(reply=reply)

        except Exception as e:
            error_message = f"Failed to query vector DB: {str(e)}"
            logger.error(error_message)
            return QueryVectorDBOutput(
                reply="Error occurred",
                error_message=error_message
            )