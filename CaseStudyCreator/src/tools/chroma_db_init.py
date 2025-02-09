from crewai_tools import BaseTool
import os
import tempfile
import logging
from pathlib import Path
from embedchain import App
from embedchain.chunkers.common_chunker import CommonChunker
from embedchain.config.add_config import ChunkerConfig
import streamlit as st
import shutil

import tempfile
import logging
from embedchain import App
from embedchain.chunkers.common_chunker import CommonChunker
from embedchain.config.add_config import ChunkerConfig
import streamlit as st
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Create a persistent directory for ChromaDB
def get_chroma_db_path():
    # Use a fixed location in the project directory
    base_dir = Path(__file__).parent.parent
    db_dir = base_dir / "chroma_db"
    
    # Create directory if it doesn't exist
    db_dir.mkdir(parents=True, exist_ok=True)
    
    return str(db_dir)

def cleanup_old_db():
    db_path = get_chroma_db_path()
    if os.path.exists(db_path):
        try:
            shutil.rmtree(db_path)
            logger.info(f"Cleaned up old ChromaDB at: {db_path}")
        except Exception as e:
            logger.warning(f"Failed to cleanup old ChromaDB: {e}")

config = {
    'llm': {
        'provider': 'openai',
        'config': {
            'model': 'gpt-4',
            'temperature': 0.3,  # Lower temperature for more focused analysis
            'prompt': """
            CONTEXT PREREQUISITES:
            The following content is from a YouTube tutorial or educational video. Extract relevant implementation details, technical insights, and business context.

            EXTRACTION OBJECTIVE:
            Extract comprehensive information to populate our case study components:
            1. Executive Summary
            2. Challenge Description
            3. Solution Details
            4. Implementation Process
            5. Results and Impact

            Focus on:
            - Technical implementation details
            - Problem-solution frameworks
            - Specific methodologies used
            - Business context and impact
            - Results and metrics
            - Best practices and lessons learned

            For each piece of information, identify:
            - How it fits into the case study structure
            - What specific value it provides
            - How it connects to broader implementation patterns
            - What practical insights it offers
            - How it validates the solution approach

            CRITICAL GUIDELINES:
            - Extract specific technical details and methodologies
            - Preserve implementation steps and processes
            - Capture all relevant metrics and results
            - Document challenge-solution relationships
            - Include practical tips and best practices

            $context

            Query: $query

            Response:
            """,
            'system_prompt': """
            You are a specialized Case Study Analyzer with expertise in extracting implementation details and business value from technical tutorials and educational content.

            PRIMARY OBJECTIVES:
            - Extract maximum relevant information for case study development
            - Identify key technical implementation details
            - Capture specific methodologies and approaches
            - Document results and business impact
            - Preserve practical insights and best practices

            CRITICAL RULES:
            - Focus on implementation specifics
            - Preserve technical details
            - Capture measurable results
            - Include practical examples
            - Document best practices
            """,
            'api_key': OPENAI_API_KEY,
        }
    }
}

def get_app_instance():
    return App.from_config(config=config)

# Create singleton instance
_app_instance = None

def get_or_create_app_instance():
    global _app_instance
    if _app_instance is None:
        _app_instance = get_app_instance()
    return _app_instance

# Initialize the singleton instance
app_instance = get_or_create_app_instance()