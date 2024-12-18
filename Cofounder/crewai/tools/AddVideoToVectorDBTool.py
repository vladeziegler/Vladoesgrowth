from crewai_tools.tools.base_tool import BaseTool
from pydantic import BaseModel, Field
from typing import Any, Type
from embedchain import App
from youtube_transcript_api import YouTubeTranscriptApi
import logging
import re
from bs4 import BeautifulSoup
import requests

logger = logging.getLogger(__name__)

class AddVideoToVectorDBInput(BaseModel):
    video_url: str = Field(..., description="The URL of the YouTube video to add to the vector DB.")

class AddVideoToVectorDBOutput(BaseModel):
    success: bool = Field(..., description="Whether the video was successfully added to the vector DB.")
    error_message: str = Field(default="", description="Error message if the operation failed.")

class AddVideoToVectorDBTool(BaseTool):
    name: str = "Add Video to Vector DB"
    description: str = "Adds a YouTube video transcript to the vector database."
    args_schema: Type[AddVideoToVectorDBInput] = AddVideoToVectorDBInput
    app: Any = Field(default=None, exclude=True)
    is_initialized: bool = Field(default=False, exclude=True)

    def __init__(self, app: App, **data):
        super().__init__(**data)
        self.app = app
        self.is_initialized = False

    def initialize_for_new_creator(self):
        """Reset the vector database before starting analysis for a new creator."""
        logger.info("Initializing vector database for new creator")
        if self.app is not None:
            self.app.reset()
            logger.info("Vector database reset successfully")
        else:
            logger.error("No app instance available for reset")
        self.is_initialized = True

    def _extract_video_id(self, url: str) -> str:
        """Extract the video ID from a YouTube URL."""
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if video_id_match:
            return video_id_match.group(1)
        else:
            raise ValueError("Could not extract video ID from URL")

    def _fetch_transcript(self, video_id: str) -> str:
        """Fetch the transcript for a given YouTube video ID."""
        try:
            # First, try to get the official transcript
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            return " ".join([entry['text'] for entry in transcript])
        except Exception as e:
            logger.warning(f"Failed to fetch official transcript: {str(e)}")
            
            try:
                print("Trying to fetch auto-generated captions")
                transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr-FR', 'fr'])
                return " ".join([entry['text'] for entry in transcript])
            except Exception as e:
                logger.warning(f"Failed to fetch auto-generated captions: {str(e)}")
                
                print("Trying to scrape captions")
                return self._scrape_transcript(video_id)

    def _scrape_transcript(self, video_id: str) -> str:
        """Scrape the transcript from the YouTube video page."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        transcript_element = soup.find('div', {'class': 'ytd-transcript-renderer'})
        if transcript_element:
            return transcript_element.get_text()
        else:
            raise Exception("Could not find transcript in the video page")

    def _run(self, video_url: str) -> AddVideoToVectorDBOutput:
        if not self.is_initialized:
            self.initialize_for_new_creator()
            
        try:
            logger.info(f"Processing video: {video_url}")
            video_id = self._extract_video_id(video_url)
            transcript_text = self._fetch_transcript(video_id)
            
            logger.info(f"Adding transcript to vector DB for video ID: {video_id}")
            self.app.add(transcript_text, data_type="text", metadata={"source": video_url})
            logger.info("Transcript successfully added to vector DB")
            
            return AddVideoToVectorDBOutput(success=True)
        except Exception as e:
            error_message = f"Failed to add video transcript: {str(e)}"
            logger.error(error_message)
            return AddVideoToVectorDBOutput(success=False, error_message=error_message)

# from crewai_tools.tools.base_tool import BaseTool
# from crewai_tools.tools.base_tool import BaseTool
# from pydantic.v1 import BaseModel, Field
# from typing import Any, Type
# from embedchain import App
# from youtube_transcript_api import YouTubeTranscriptApi
# import logging
# import re
# from bs4 import BeautifulSoup
# import re
# import requests

# logger = logging.getLogger(__name__)

# logger = logging.getLogger(__name__)

# class AddVideoToVectorDBInput(BaseModel):
#     video_url: str = Field(..., description="The URL of the YouTube video to add to the vector DB.")

# class AddVideoToVectorDBOutput(BaseModel):
#     success: bool = Field(..., description="Whether the video was successfully added to the vector DB.")
#     error_message: str = Field(default="", description="Error message if the operation failed.")

# class AddVideoToVectorDBTool(BaseTool):
#     name: str = "Add Video to Vector DB"
#     description: str = "Adds a YouTube video transcript to the vector database."
#     args_schema: Type[AddVideoToVectorDBInput] = AddVideoToVectorDBInput
#     app: Any = Field(default=None, exclude=True)

#     def __init__(self, app: App, **data):
#         super().__init__(**data)
#         self.app = app

#     def _extract_video_id(self, url: str) -> str:
#         """Extract the video ID from a YouTube URL."""
#         video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
#         if video_id_match:
#             return video_id_match.group(1)
#         else:
#             raise ValueError("Could not extract video ID from URL")

#     def _fetch_transcript(self, video_id: str) -> str:
#         """Fetch the transcript for a given YouTube video ID."""
#         try:
#             # First, try to get the official transcript
#             transcript = YouTubeTranscriptApi.get_transcript(video_id)
#             return " ".join([entry['text'] for entry in transcript])
#         except Exception as e:
#             logger.warning(f"Failed to fetch official transcript: {str(e)}")
            
#             # If official transcript fails, try to get auto-generated captions
#             try:
#                 print("Trying to fetch auto-generated captions")
#                 # transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en-US', 'en'])
#                 transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['fr-FR', 'fr'])
#                 return " ".join([entry['text'] for entry in transcript])
#             except Exception as e:
#                 logger.warning(f"Failed to fetch auto-generated captions: {str(e)}")
                
#                 # If both methods fail, try to scrape the transcript
#                 print("Trying to scrape captions")
#                 return self._scrape_transcript(video_id)

#     def _scrape_transcript(self, video_id: str) -> str:
#         """Scrape the transcript from the YouTube video page."""
#         url = f"https://www.youtube.com/watch?v={video_id}"
#         response = requests.get(url)
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Look for the transcript in the page source
#         transcript_element = soup.find('div', {'class': 'ytd-transcript-renderer'})
#         if transcript_element:
#             return transcript_element.get_text()
#         else:
#             raise Exception("Could not find transcript in the video page")

#     def _run(self, video_url: str) -> AddVideoToVectorDBOutput:
#         try:
#             logger.info(f"Processing video: {video_url}")
#             video_id = self._extract_video_id(video_url)
#             transcript_text = self._fetch_transcript(video_id)
            
#             logger.info(f"Adding transcript to vector DB for video ID: {video_id}")
#             self.app.add(transcript_text, data_type="text", metadata={"source": video_url})
#             logger.info("Transcript successfully added to vector DB")
            
#             return AddVideoToVectorDBOutput(success=True)
#         except Exception as e:
#             error_message = f"Failed to add video transcript: {str(e)}"
#             logger.error(error_message)
#             return AddVideoToVectorDBOutput(success=False, error_message=error_message)
