import traceback
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from typing import List, Type, Optional
import requests
from crewai_tools.tools.base_tool import BaseTool

from pydantic import BaseModel, Field
from groq import Groq
import openai
import time
import streamlit as st

YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

class FetchRelevantVideosFromYouTubeChannelInput(BaseModel):
    youtube_handle: str = Field(
        ..., description="The YouTube channel handle (e.g., '@channelhandle')."
    )

class VideoInfo(BaseModel):
    video_id: str
    title: str
    description: str
    publish_date: datetime
    video_url: str
    category_id: str
    view_count: int
    like_count: int
    relevance_score: float = 0.0

class FetchRelevantVideosFromYouTubeChannelOutput(BaseModel):
    videos: List[VideoInfo]

class FetchRelevantVideosFromYouTubeChannelTool(BaseTool):
    name: str = "Fetch Relevant Videos for Channel"
    description: str = (
        "Fetches up to 200 latest videos for a specified YouTube channel handle, "
        "ranks them based on popularity and relevance to the creator's personal story, "
        "and returns the top 10 results, excluding short videos."
    )
    args_schema: Type[BaseModel] = FetchRelevantVideosFromYouTubeChannelInput
    return_schema: Type[BaseModel] = FetchRelevantVideosFromYouTubeChannelOutput
    
    def _run(
        self,
        youtube_handle: str,
    ) -> str:
        api_key = YOUTUBE_API_KEY
        if not api_key:
            return "YOUTUBE_API_KEY environment variable is not set"

        try:
            channel_id = self.get_channel_id(youtube_handle, api_key)
            if channel_id is None:
                return f"No channel found for handle: {youtube_handle}"
                
            all_videos = self.fetch_all_videos(channel_id, api_key)
            video_details = self.fetch_video_details(all_videos, api_key)

            videos = []
            for video_id, details in video_details.items():
                snippet = details.get("snippet", {})
                statistics = details.get("statistics", {})

                if self.is_short_video(snippet):
                    continue

                videos.append(
                    VideoInfo(
                        video_id=video_id,
                        title=snippet.get("title", ""),
                        description=snippet.get("description", ""),
                        publish_date=datetime.fromisoformat(
                            snippet.get("publishedAt", "").replace("Z", "+00:00")
                        ).astimezone(timezone.utc),
                        video_url=f"https://www.youtube.com/watch?v={video_id}",
                        category_id=snippet.get("categoryId", ""),
                        view_count=int(statistics.get("viewCount", 0)),
                        like_count=int(statistics.get("likeCount", 0))
                    )
                )

            if not videos:
                return f"No suitable videos found for channel: {youtube_handle}"

            # Sort by popularity (view count) and take top 50
            popular_videos = sorted(videos, key=lambda v: v.view_count, reverse=True)[:50]
            # popular_videos = sorted(videos, key=lambda v: v.view_count, reverse=True)[:10]
            ranked_videos = self.rank_videos(popular_videos)
            top_videos = ranked_videos[:15]
            # top_videos = ranked_videos[:2]
            # Create a summary string
            summary = f"Successfully analyzed {len(videos)} videos from {youtube_handle}.\n"
            summary += f"Top {len(top_videos)} most relevant videos:\n"
            
            for idx, video in enumerate(top_videos, 1):
                summary += f"{idx}. {video.title} - Views: {video.view_count:,}, "
                summary += f"Relevance Score: {video.relevance_score:.1f}, "
                summary += f"URL: {video.video_url}\n"

            return summary

        except Exception as e:
            error_message = f"Error processing channel {youtube_handle}: {str(e)}"
            print(error_message)
            return error_message


    def get_channel_id(self, youtube_handle: str, api_key: str) -> Optional[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "channel",
            "q": youtube_handle,
            "key": api_key,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                print(f"No channel found for handle {youtube_handle}")
                return None
            return items[0]["id"]["channelId"]
        except requests.exceptions.RequestException as e:
            print(f"Error in get_channel_id: {e}")
            print(f"Response content: {response.content}")
            return None

    def is_short_video(self, snippet: dict) -> bool:
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()
        return "#shorts" in title or "#shorts" in description or snippet.get("categoryId") == "22"

    def fetch_all_videos(self, channel_id: str, api_key: str) -> List[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "id",
            "channelId": channel_id,
            "maxResults": 50,
            "order": "date",
            "type": "video",
            "key": api_key,
        }

        all_video_ids = []
        page_token = None
        try:
            while len(all_video_ids) < 200:
            # while len(all_video_ids) < 20:
                if page_token:
                    params["pageToken"] = page_token

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                new_video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
                all_video_ids.extend(new_video_ids)

                page_token = data.get("nextPageToken")
                if not page_token or len(new_video_ids) == 0:
                    break

                time.sleep(1)

            # return all_video_ids[:200]
            return all_video_ids[:20]
        except requests.exceptions.RequestException as e:
            print(f"Error in fetch_all_videos: {e}")
            print(f"Response content: {response.content}")
            raise

    def fetch_video_details(self, video_ids: List[str], api_key: str, batch_size: int = 50) -> dict:
        video_details = {}
        url = "https://www.googleapis.com/youtube/v3/videos"

        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            params = {
                "part": "snippet,statistics",
                "id": ",".join(batch),
                "key": api_key,
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                batch_details = {item["id"]: item for item in response.json()["items"]}
                video_details.update(batch_details)

                time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error in fetch_video_details: {e}")
                print(f"Response content: {response.content}")
                raise

        return video_details

import traceback
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
from typing import List, Type, Optional
import requests
from crewai_tools.tools.base_tool import BaseTool

from pydantic import BaseModel, Field
from groq import Groq
import openai
import time
import streamlit as st

YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

class FetchRelevantVideosFromYouTubeChannelInput(BaseModel):
    youtube_handle: str = Field(
        ..., description="The YouTube channel handle (e.g., '@channelhandle')."
    )

class VideoInfo(BaseModel):
    video_id: str
    title: str
    description: str
    publish_date: datetime
    video_url: str
    category_id: str
    view_count: int
    like_count: int
    relevance_score: float = 0.0

class FetchRelevantVideosFromYouTubeChannelOutput(BaseModel):
    videos: List[VideoInfo]

class FetchRelevantVideosFromYouTubeChannelTool(BaseTool):
    name: str = "Fetch Relevant Videos for Channel"
    description: str = (
        "Fetches up to 200 latest videos for a specified YouTube channel handle, "
        "ranks them based on popularity and relevance to the creator's personal story, "
        "and returns the top 10 results, excluding short videos."
    )
    args_schema: Type[BaseModel] = FetchRelevantVideosFromYouTubeChannelInput
    return_schema: Type[BaseModel] = FetchRelevantVideosFromYouTubeChannelOutput
    
    def _run(
        self,
        youtube_handle: str,
    ) -> str:
        api_key = YOUTUBE_API_KEY
        if not api_key:
            return "YOUTUBE_API_KEY environment variable is not set"

        try:
            channel_id = self.get_channel_id(youtube_handle, api_key)
            if channel_id is None:
                return f"No channel found for handle: {youtube_handle}"
                
            all_videos = self.fetch_all_videos(channel_id, api_key)
            video_details = self.fetch_video_details(all_videos, api_key)

            videos = []
            for video_id, details in video_details.items():
                print(f"Video ID: {video_id}")
                print(f"Details keys: {details.keys()}")
                snippet = details.get("snippet", {})
                print(f"Snippet keys: {snippet.keys()}")
                
                # Then try to access description
            # videos = []
            # for video_id, details in video_details.items():
                snippet = details.get("snippet", {})
                statistics = details.get("statistics", {})

                if self.is_short_video(snippet):
                    continue

                description = snippet.get("description", "")
                print(f"Description: {description[:100]}...")  # Print first 100
                videos.append(
                    VideoInfo(
                        video_id=video_id,
                        title=snippet.get("title", ""),
                        description=snippet.get("description", ""),
                        publish_date=datetime.fromisoformat(
                            snippet.get("publishedAt", "").replace("Z", "+00:00")
                        ).astimezone(timezone.utc),
                        video_url=f"https://www.youtube.com/watch?v={video_id}",
                        category_id=snippet.get("categoryId", ""),
                        view_count=int(statistics.get("viewCount", 0)),
                        like_count=int(statistics.get("likeCount", 0))
                    )
                )

            if not videos:
                return f"No suitable videos found for channel: {youtube_handle}"

            # Sort by popularity (view count) and take top 50
            # popular_videos = sorted(videos, key=lambda v: v.view_count, reverse=True)[:50]
            popular_videos = sorted(videos, key=lambda v: v.view_count, reverse=True)[:10]
            ranked_videos = self.rank_videos(popular_videos)
            # top_videos = ranked_videos[:15]
            top_videos = ranked_videos[:2]
            # Create a summary string
            summary = f"Successfully analyzed {len(videos)} videos from {youtube_handle}.\n"
            summary += f"Top {len(top_videos)} most relevant videos:\n"
            
            for idx, video in enumerate(top_videos, 1):
                summary += f"{idx}. {video.title} - Views: {video.view_count:,}, "
                summary += f"Relevance Score: {video.relevance_score:.1f}, "
                summary += f"URL: {video.video_url}\n"

            return summary

        except Exception as e:
            error_message = f"Error processing channel {youtube_handle}: {str(e)}"
            print(f"Full error details: {type(e).__name__}: {str(e)}")
            print(f"Details at error: {details}")  # This will show us the exact state of the data
            return error_message

    def get_channel_id(self, youtube_handle: str, api_key: str) -> Optional[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "type": "channel",
            "q": youtube_handle,
            "key": api_key,
        }
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json().get("items", [])
            if not items:
                print(f"No channel found for handle {youtube_handle}")
                return None
            return items[0]["id"]["channelId"]
        except requests.exceptions.RequestException as e:
            print(f"Error in get_channel_id: {e}")
            print(f"Response content: {response.content}")
            return None

    def is_short_video(self, snippet: dict) -> bool:
        title = snippet.get("title", "").lower()
        description = snippet.get("description", "").lower()
        return "#shorts" in title or "#shorts" in description or snippet.get("categoryId") == "22"

    def fetch_all_videos(self, channel_id: str, api_key: str) -> List[str]:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "id",
            "channelId": channel_id,
            "maxResults": 50,
            "order": "date",
            "type": "video",
            "key": api_key,
        }

        all_video_ids = []
        page_token = None
        try:
            while len(all_video_ids) < 200:
            # while len(all_video_ids) < 20:
                if page_token:
                    params["pageToken"] = page_token

                response = requests.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                new_video_ids = [item["id"]["videoId"] for item in data.get("items", [])]
                all_video_ids.extend(new_video_ids)

                page_token = data.get("nextPageToken")
                if not page_token or len(new_video_ids) == 0:
                    break

                time.sleep(1)

            return all_video_ids[:200]
            # return all_video_ids[:20]
        except requests.exceptions.RequestException as e:
            print(f"Error in fetch_all_videos: {e}")
            print(f"Response content: {response.content}")
            raise

    def fetch_video_details(self, video_ids: List[str], api_key: str, batch_size: int = 50) -> dict:
        video_details = {}
        url = "https://www.googleapis.com/youtube/v3/videos"

        for i in range(0, len(video_ids), batch_size):
            batch = video_ids[i:i + batch_size]
            params = {
                "part": "snippet,statistics",
                "id": ",".join(batch),
                "key": api_key,
            }
            try:
                response = requests.get(url, params=params)
                response.raise_for_status()
                batch_details = {item["id"]: item for item in response.json()["items"]}
                video_details.update(batch_details)

                time.sleep(1)
            except requests.exceptions.RequestException as e:
                print(f"Error in fetch_video_details: {e}")
                print(f"Response content: {response.content}")
                raise

        return video_details

    def rank_videos(self, videos: List[VideoInfo]) -> List[VideoInfo]:
        groq_client = Groq(api_key=GROQ_API_KEY)
        
        for video in videos:
            prompt = f"""
            Rate how likely this video is to cover the personal story of its creator. Respond with a single number from 0 to 10, where 0 means not at all likely and 10 means extremely likely.

            A score of 1 means it's purely promotional or unrelated to personal stories.
            A score of 10 means it's a deep, meaningful personal story or reflection.

            Title: {video.title}
            Description: {video.description}

            Rating (0-10):
            Respond with ONLY a single number between 1 and 10, with no additional text, explanation, or newlines.
            Example correct response: 7
            """

            try:
                response = groq_client.chat.completions.create(
                    model="llama-3.1-8b-instant",
                    messages=[
                        {"role": "system", "content": "You are an AI that rates videos based on their relevance to the creator's personal story. You must respond with only a single number from 0 to 10, nothing else."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=5,
                    temperature=0.1
                )

                score_text = response.choices[0].message.content.strip()
                # Add debug print
                print(f"Raw score for video '{video.title}': '{score_text}'")
                
                # Try to extract just the number if there's extra text
                import re
                number_match = re.search(r'\d+(?:\.\d+)?', score_text)
                if number_match:
                    score = float(number_match.group())
                    if 0 <= score <= 10:
                        video.relevance_score = score * 10
                    else:
                        print(f"Score out of range for video {video.title}: {score}")
                        video.relevance_score = 0
                else:
                    print(f"No valid number found in response for video {video.title}")
                    video.relevance_score = 0
                    
            except Exception as e:
                print(f"Error with Groq API for video {video.title}: {str(e)}")
                video.relevance_score = 0

        return sorted(videos, key=lambda v: v.relevance_score, reverse=True)