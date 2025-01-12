import logging
from typing import Optional
from youtube_transcript_api import YouTubeTranscriptApi
import re
from bs4 import BeautifulSoup
import requests
from embedchain import App
from pydantic import BaseModel, Field
import sys
import streamlit as st
OPENAI_API_KEY = "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"
# OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
# Set up detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

config = {
    'llm': {
        'provider': 'openai',
        'config': {
            'model': 'gpt-4o-mini',
            'temperature': 0.4,
            'api_key': OPENAI_API_KEY,  # Set in YouTubeAnalyzer.__init__
            # 'api_key': openai_api_key,
            'prompt': """
            Analyze the following content and answer the queries based on the content.
            Answer in a concise and actionable manner.
            Answer in bullet points. 
            Back up claims with quotes or comments from the video to support your points.
            
            Context: $context
            
            Query: $query
            
            Response:""",
            'system_prompt': """
            You are a highy experienced product manager. When answering questions, you focus on workflows, pain points, and possible solutions. You don't go beyond scope. You don't make up information. You refer to product names, people, and companies they're mentioend. Your answers are concise, actionable, and to the point. You don't use jargon, and you don't use long sentences. You answer in bullet points.
            """
        }
    }
}

class YouTubeAnalyzer:
    def __init__(self):
        logger.info("Initializing YouTubeAnalyzer...")
        print("Setting up analyzer with OpenAI API key...")
        try:
            self.app = App.from_config(config=config)
            logger.info("Successfully initialized embedchain App")
            print("✓ Analyzer setup complete")
        except Exception as e:
            logger.error(f"Failed to initialize embedchain App: {str(e)}")
            print(f"✗ Error during setup: {str(e)}")
            raise

    def _extract_video_id(self, url: str) -> str:
        """Extract video ID from YouTube URL."""
        logger.info(f"Extracting video ID from URL: {url}")
        print(f"Processing URL: {url}")
        
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
        if not video_id_match:
            logger.error("Failed to extract video ID from URL")
            print("✗ Invalid YouTube URL format")
            raise ValueError("Could not extract video ID from URL")
        
        video_id = video_id_match.group(1)
        logger.info(f"Successfully extracted video ID: {video_id}")
        print(f"✓ Found video ID: {video_id}")
        return video_id

    def _fetch_transcript(self, video_id: str) -> str:
        """Fetch transcript using multiple fallback methods."""
        logger.info(f"Attempting to fetch transcript for video ID: {video_id}")
        print("\nFetching video transcript...")

        # Try official transcript
        try:
            logger.info("Attempting to fetch official transcript")
            print("Trying official transcript...")
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
            logger.info("Successfully fetched official transcript")
            print("✓ Official transcript obtained")
            return " ".join([entry['text'] for entry in transcript])
        except Exception as e:
            logger.warning(f"Failed to fetch official transcript: {str(e)}")
            print("✗ Official transcript not available")
            
        # Try auto-generated captions
        try:
            logger.info("Attempting to fetch auto-generated captions")
            print("Trying auto-generated captions...")
            transcript = YouTubeTranscriptApi.get_transcript(
                video_id, 
                languages=['en-US', 'en', 'fr-FR', 'fr']
            )
            logger.info("Successfully fetched auto-generated captions")
            print("✓ Auto-generated captions obtained")
            return " ".join([entry['text'] for entry in transcript])
        except Exception as e:
            logger.warning(f"Failed to fetch auto-generated captions: {str(e)}")
            print("✗ Auto-generated captions not available")
            
        # Try scraping as last resort
        logger.info("Attempting to scrape transcript")
        print("Trying to scrape transcript from webpage...")
        return self._scrape_transcript(video_id)

    def _scrape_transcript(self, video_id: str) -> str:
        """Scrape transcript from YouTube page as last resort."""
        url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Scraping transcript from URL: {url}")
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            transcript_element = soup.find('div', {'class': 'ytd-transcript-renderer'})
            if not transcript_element:
                logger.error("Could not find transcript element in page")
                print("✗ No transcript found on webpage")
                raise Exception("Could not find transcript in video page")
                
            logger.info("Successfully scraped transcript from page")
            print("✓ Transcript scraped from webpage")
            return transcript_element.get_text()
            
        except Exception as e:
            logger.error(f"Failed to scrape transcript: {str(e)}")
            print(f"✗ Failed to scrape transcript: {str(e)}")
            raise

    def process_video(self, video_url: str) -> bool:
        """Process a video URL and add its transcript to the database."""
        logger.info(f"Starting video processing for URL: {video_url}")
        print(f"\nProcessing video: {video_url}")
        
        try:
            video_id = self._extract_video_id(video_url)
            transcript = self._fetch_transcript(video_id)
            
            print("\nAdding transcript to database...")
            logger.info("Adding transcript to vector database")
            
            self.app.add(transcript, data_type="text", metadata={"source": video_url})
            
            logger.info("Successfully added transcript to database")
            print("✓ Transcript successfully added to database")
            return True
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}")
            print(f"✗ Error processing video: {str(e)}")
            return False

    def query_video(self, query: str) -> str:
        """Query the video transcript database."""
        logger.info(f"Querying database with: {query}")
        print(f"\nQuerying database with: {query}")
        
        try:
            print("Processing query...")
            response = self.app.query(query)
            
            logger.info("Successfully retrieved response from database")
            print("✓ Query successful")
            
            return response
            
        except Exception as e:
            logger.error(f"Error querying database: {str(e)}")
            print(f"✗ Query failed: {str(e)}")
            return f"Error: {str(e)}"

def main():
    st.title("YouTube Video Analysis for Product Insights")
    
    # openai_api_key = st.secrets["OPENAI_API_KEY"]
    youtube_url = st.text_input("Enter YouTube video URL:")
    audience = st.text_input("Enter audience:")
    
    # if not openai_api_key or not youtube_url:
        # st.warning("Please provide both OpenAI API key and YouTube URL")
        # return
        
    if st.button("Analyze Video"):
        with st.spinner("Processing video..."):
            analyzer = YouTubeAnalyzer()
            if not analyzer.process_video(youtube_url):
                return

            progress_text = st.empty()
            
            progress_text.text("Analyzing problems...")
            query_problem = f"What are the main workflow challenges that {audience} face in their day to day work?"
            response_problem = analyzer.query_video(query_problem)
            
            progress_text.text("Analyzing alternatives...")
            query_alternative = f"What are the alternatives that {audience} have tried to implement ? What tools did they try ? How did they fall short of expectations ? Be specific about the names of the tools {audience} tried."
            response_alternative = analyzer.query_video(query_alternative)
            
            progress_text.text("Analyzing ideal outcomes...")
            query_ideal_outcome = f"What are the ultimate internal motivations that drive {audience} in their work ? What kind of benefits do they seek out of adopting a new product ? "
            response_ideal_outcome = analyzer.query_video(query_ideal_outcome)
            
            progress_text.text("Analyzing gaps...")
            query_gaps = f"What are the gaps in existing solutions that prevent {audience} from achieving their ideal outcome? To establish this, you need to map out their current problems, the alternatives they have tried, their ideal outcome. You can then identify what's missing. Here is the context about their current problems: {response_problem}. Here is the context about the existing alternatives: {response_alternative}. Here is the context about their ideal outcome: {response_ideal_outcome}."
            response_gaps = analyzer.query_video(query_gaps)
            
            progress_text.text("Analyzing product benefits...")
            query_benefits = f"What are the benefits of using the product described in this video ? What gaps are they addressing to fix {audience} pain points ? For context, here are the gaps identified to meet {audience}'s needs: {response_gaps}."
            response_benefits = analyzer.query_video(query_benefits)
            
            progress_text.text("Analyzing opportunities...")
            query_opportunities = f"Based on the gaps observed to address {audience}'s pain points, and the benefits of the product described in the video, what are the oustanding opportunities ahead ? What are the gaps that remain unadressed EVEN AFTER adopting the product described, and assimilating all of the benefit. Here are the benefits from the product being discussed: {response_benefits}. Here are the gaps: {response_gaps}. Find the outstanding gaps and present them as opportunities."
            response_opportunities = analyzer.query_video(query_opportunities)
            
            progress_text.empty()
            
            sections = {
                "Problems": response_problem,
                "Alternatives": response_alternative,
                "Ideal outcome": response_ideal_outcome,
                "Gaps": response_gaps,
                "Product": response_benefits,
                "Opportunities": response_opportunities
            }
            
            for section, response in sections.items():
                with st.expander(f"📊 {section}"):
                    st.markdown(response)

if __name__ == "__main__":
    main()