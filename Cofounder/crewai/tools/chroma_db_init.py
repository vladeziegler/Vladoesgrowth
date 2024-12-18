
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
# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

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

# config = {
#     'app': {
#         'config': {
#             'name': 'full-stack-app'
#         }
#     },
#         'llm': {
#         'provider': 'openai',
#         'config': {
#             'model': 'gpt-4o',
#             'temperature': 0.4,
#             # 'max_tokens': 2000,
#             'prompt': (
#                 "The following context is primarily in French.\n"
#                 "If the query is in English, translate it to French before searching.\n"
#                 "Once you find relevant information in French, translate it back to English before answering.\n\n"
#                 "Provide relevant answers back in the query's language."
#                 "Be comprehensive, accurate and precise. Share as much information as possible.\n"
#                 "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
#                 "Always try to extract the actionable practical advice from the content.\n"
#                 "Give the context within which every story is set.\n"
#                 "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
#                 "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
#                 "In each section, you should provide a clear claim, backstory/context, anecdote/story that you can retrieve from the content to exemplify your claim.\n"
#                 "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
#                 "IMPORTANT: If you don't know the answer, don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
#                 "Always end your reply with a summary of the main points you covered in the reply.\n"
#                 "Always translate the quotes back to English.\n"
#                 "Act as a potential customer of the protagonist. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
#                 "$context\n\nQuery: $query\n\nHelpful Answer:"
#             ),
#             'system_prompt': (
#                 "Act as a translator and answer finder for a multilingual audience.\n"
#                 "You are a helpful assistant that can answer questions about the content creator and their content with comprehensive and precise answers.\n"
#                 "You don't make up answers, and you don't give generic best practices.\n"
#                 "But you're smart and can find the answer in the context provided.\n"
#                 "If a question is in a different language from the content, translate the query to match the content language.\n"
#                 "Provide relevant answers back in the query's language."
#                 "Be comprehensive, accurate and precise. Share as much information as possible.\n"
#                 "Everytime you answer a question, figure out why it matters to the audience, and why it matters to the protagonist, and where/how he developed this trait, and how he's using it in practice in his life and business. Be specific\n"
#                 "Always try to extract the actionable practical advice from the content.\n"
#                 "Give the context within which every story is set.\n"
#                 "Always keep the storytelling part that's relevant to the query. Keep ALL the details of the story as accurate and precise as possible.\n"
#                 "For every reply, you should respond in sections, where each section is a single idea/concept/lesson/value/motivation/belief/etc.\n"
#                 "In each section, you should provide a clear claim, backstory/context, anecdote/story that you can retrieve from the content to exemplify your claim.\n"
#                 "For every section, you should provide 1-3 hyper actionable and practical advice, tips that can be derived and executed from this insight.\n"
#                 "IMPORTANT: If you don't know the answer, don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
#                 "Always end your reply with a summary of the main points you covered in the reply.\n"
#                 "Always translate the quotes back to English.\n"
#                 "Act as a potential customer of the protagonist. Interpret the answers based on what's in it for you. You want to learn practical advice that you can apply in your own personal or professional life. You know the importance of author's advice and takeaways, and real-lifestorytelling to absorb lessons."
#                 "IMPORTANT: If you don't know the answer, LEAVE IT BLANK, and move on. Don't try to make up an answer. Don't try to give a generic answer. Don't try to give generic best practices.\n"
#             ),
#             'api_key': OPENAI_API_KEY,
#         }
#     },
#     'vectordb': {
#         'provider': 'chroma',
#         'config': {
#             # 'dir': db_path,
#             'dir': get_chroma_db_path(),
#             'allow_reset': True
#         }
#     },
#     'embedder': {
#         'provider': 'openai',
#         'config': {
#             'model': 'text-embedding-ada-002',
#             'api_key': OPENAI_API_KEY,
#         }
#     },
#     'chunker': {
#         'chunk_size': 1000,
#         'chunk_overlap': 500,
#         'length_function': 'len',
#         'min_chunk_size': 501
#     },
# }

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