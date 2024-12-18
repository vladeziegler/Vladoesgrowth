# from crewai_tools.tools.base_tool import BaseTool
# from pydantic import BaseModel, Field, PrivateAttr
# from typing import Type, Optional, Union
# from embedchain import App
# import logging
# import requests
# import streamlit as st

# logger = logging.getLogger(__name__)

# class QueryVectorDBInput(BaseModel):
#     """Input for QueryVectorDB."""
#     query: str = Field(..., description="The query to search the vector database")
#     youtube_channel_handle: Optional[str] = Field(
#         None, 
#         description="Optional YouTube channel handle to query content from"
#     )

# class QueryVectorDBOutput(BaseModel):
#     """Output for QueryVectorDB."""
#     reply: str = Field(..., description="The reply from the query")
#     error_message: str = Field(default="", description="Error message if the operation failed")

# class QueryVectorDBTool(BaseTool):
#     name: str = "Query Vector DB"
#     description: str = "Queries the vector database with provided input query and optional YouTube channel handle"
#     args_schema: Type[BaseModel] = QueryVectorDBInput
    
#     _app: Optional[App] = PrivateAttr(default=None)

#     def __init__(self, app: App):
#         super().__init__()
#         self._app = app

#     def _check_channel_exists(self, youtube_channel_handle: str) -> bool:
#         """Check if a YouTube channel exists using YouTube Data API."""
#         try:
#             api_key = st.secrets["YOUTUBE_API_KEY"]
#             url = "https://www.googleapis.com/youtube/v3/search"
#             params = {
#                 "part": "id",
#                 "q": youtube_channel_handle,
#                 "type": "channel",
#                 "key": api_key
#             }
            
#             response = requests.get(url, params=params)
#             response.raise_for_status()
#             data = response.json()
            
#             # Check if any channels were found
#             return bool(data.get("items", []))
            
#         except Exception as e:
#             logger.error(f"Error checking YouTube channel: {str(e)}")
#             return False

#     def _run(
#         self, 
#         query: Union[str, dict],
#         youtube_channel_handle: Optional[str] = None
#     ) -> Union[QueryVectorDBOutput, None]:
#         try:
#             # Handle dictionary input
#             if isinstance(query, dict):
#                 youtube_channel_handle = query.get('youtube_channel_handle', youtube_channel_handle)
#                 query = query.get('query', '')

#             logger.info(f"Querying vector DB with: {query}")
            
#             # Check if YouTube channel exists when provided
#             if youtube_channel_handle:
#                 if not self._check_channel_exists(youtube_channel_handle):
#                     logger.warning(f"YouTube channel not found: {youtube_channel_handle}")
#                     return None

#             # Enhance the query with channel context if provided
#             if youtube_channel_handle:
#                 enhanced_query = f"""Please analyze the following query about the content from {youtube_channel_handle}: {query}
#                 Provide specific examples and relevant information from the content."""
#             else:
#                 enhanced_query = f"""Please analyze the following query about the content: {query}
#                 Provide specific examples and relevant information from the content."""

#             # Query the database
#             response = self._app.query(enhanced_query)
            
#             # Handle tuple response if necessary
#             reply = response[0] if isinstance(response, tuple) else response

#             # Check for empty response
#             if not reply or (isinstance(reply, str) and reply.strip() == ""):
#                 logger.warning("No content found in vector DB")
#                 return QueryVectorDBOutput(
#                     reply="No relevant content found in the database.",
#                     error_message="No content found"
#                 )

#             logger.info("Query completed successfully")
#             formatted_reply = f"""Answer: {reply}\n\nNote: This response is based on the content{
#                 f' from YouTube channel {youtube_channel_handle}' if youtube_channel_handle else ''}."""
            
#             return QueryVectorDBOutput(reply=formatted_reply)

#         except Exception as e:
#             error_message = f"Failed to query vector DB: {str(e)}"
#             logger.error(error_message)
#             return QueryVectorDBOutput(
#                 reply="Error occurred",
#                 error_message=error_message
#             )

#     def __str__(self):
#         """String representation of the tool output"""
#         try:
#             result = self._run("")
#             if result is None:
#                 return "Channel not found"
#             return result.reply
#         except Exception as e:
#             return str(e)

from crewai_tools.tools.base_tool import BaseTool
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