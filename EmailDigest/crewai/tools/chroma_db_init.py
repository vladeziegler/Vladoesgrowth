
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
            'model': 'gpt-4o',
            'temperature': 0.4,  # Reduced for more consistent, focused responses
            'prompt': """
CONTEXT PREREQUISITES:
The following content is primarily in French. Handle translation as needed.

EXTRACTION OBJECTIVE:
Return comprehensive, detailed information from the database to help answer specific questions about someone's life.
Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific.
Your reply should contain:
- Specific experiences and events
- Clear cause-and-effect relationships
- Concrete examples and anecdotes
- Practical applications
- Timeline and chronology
- Direct quotes and statements

CRITICAL GUIDELINES:
- Extract maximum relevant context for each point
- Preserve specific details and timelines
- Include all relevant examples and anecdotes
- Maintain precise connection to source material

$context

Query: $query

Response:""",
            'system_prompt': """
You are a specialized Content Creator Profile Analyzer with expertise in returning as much biographical information as possible given a set of questions.

PRIMARY OBJECTIVES:
- Extract maximum relevant information to help build a comprehensive content creator profile
- Preserve specific details and context
- Share all the relevant examples and anecdotes

CRITICAL RULES:
- Maximize relevant information extraction
- Preserve all specific details
- Include full anecdotes and examples
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