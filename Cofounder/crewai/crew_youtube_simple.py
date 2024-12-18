from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task

from crewai import LLM
import sys
import os

from tools.chroma_db_init import app_instance

from tools.FetchRelevantVideosFromYouTubeChannelTool import FetchRelevantVideosFromYouTubeChannelTool
from tools.AddVideoToVectorDBTool import AddVideoToVectorDBTool
from tools.QueryVectorDBTool import QueryVectorDBTool

from    tools.FetchToAddInstagramAudioTool import FetchToAddInstagramAudioTool
from tools.QueryInstagramDBTool import QueryInstagramDBTool

from tools.PromptingRagTool import PromptingRagTool

from crewai_tools import SerperDevTool
from typing import List, Optional

from crewai import Agent, Crew, Process, Task
from crewai_tools import FirecrawlSearchTool
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
# Load environment variables
load_dotenv()

# from pydantic import BaseModel, Field
from typing import List, Optional
from crewai_tools.tools.base_tool import BaseTool

# from pydantic import BaseModel, Field
from typing import List, Optional

import streamlit as st
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]

fetch_relevant_videos_tool = FetchRelevantVideosFromYouTubeChannelTool()
add_video_to_vector_db_tool = AddVideoToVectorDBTool(app=app_instance)
fire_crawl_search_tool = FirecrawlSearchTool()
rag_tool = QueryVectorDBTool(app=app_instance)
fetch_to_add_instagram_audio_tool = FetchToAddInstagramAudioTool(app=app_instance)
query_instagram_db_tool = QueryInstagramDBTool(app=app_instance)
query_vector_db_tool = QueryVectorDBTool(app=app_instance)

from tools.InputValidationTool import InputValidationTool
input_validation_tool = InputValidationTool()

from tools.ResettingTool import ResetDatabaseTool
reset_database_tool = ResetDatabaseTool(app=app_instance)

from typing import List, Optional, Dict
from pydantic import BaseModel
from crewai import Agent, Crew, Process

from groq import Groq

GROQ_API_KEY=st.secrets["GROQ_API_KEY"]
groq = LLM(model="groq/llama-3.3-70b-versatile")
# groq_client = Groq(api_key=GROQ_API_KEY, model="llama-3.3-70b-versatile")

class ValueObject(BaseModel):
    name: str = Field(
        ..., 
        description="The name of the value, e.g., 'perseverance'"
    )
    origin: str = Field(
        ..., 
        description="The origin or development of the value, e.g., 'Developed this trait when joining the army and completing the program after 3 attempts'"
    )
    impact_today: str = Field(
        ..., 
        description="How the value impacts how the creator works today, e.g., 'When cold calling people, understands the power of numbers and having to go through a lot of setbacks to get a successful call'"
    )

    # Add default constructor for error handling
    @classmethod
    def default(cls) -> 'ValueObject':
        return cls(
            name="",
            origin="",
            impact_today=""
        )

class ChallengeObject(BaseModel):
    description: str = Field(
        ..., 
        description="Description of the challenge, e.g., 'Experiencing homelessness in 2009'"
    )
    learnings: str = Field(
        ..., 
        description="The lessons the creator learned from the challenge, e.g., 'Made survival and ruthless prioritization his first priority'"
    )

    @classmethod
    def default(cls) -> 'ChallengeObject':
        return cls(
            description="",
            learnings=""
        )

class AchievementObject(BaseModel):
    description: str = Field(
        ..., 
        description="Description of the achievement, e.g., 'Founding own creative agency \"On Air\"', 'Speaking at TEDx Conferences'"
    )

    @classmethod
    def default(cls) -> 'AchievementObject':
        return cls(
            description=""
        )

class LifeEventObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name or title of the life event, e.g., 'Childhood'"
    )
    description: str = Field(
        ..., 
        description="Description of the life event, e.g., 'Grew up on a quiet island called La Désirade, in Guadeloupe'"
    )

    @classmethod
    def default(cls) -> 'LifeEventObject':
        return cls(
            name="",
            description=""
        )

class BusinessObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name of the business, e.g., 'Agency \"On Air\"'"
    )
    description: str = Field(
        ..., 
        description="Description of the business, e.g., 'Marketing strategist to drive innovation in large corporates'"
    )
    genesis: str = Field(
        ..., 
        description="How the business started, e.g., 'Started as a freelancer, building out the skills to turn them into an agency in 2010'"
    )

    @classmethod
    def default(cls) -> 'BusinessObject':
        return cls(
            name="",
            description="",
            genesis=""
        )

class ContentCreatorInfo(BaseModel):
    life_events: List[LifeEventObject] = Field(
        ..., 
        description="List of significant life events that shaped the creator's journey"
    )
    business: BusinessObject = Field(
        ..., 
        description="Information about the creator's business or primary professional venture"
    )
    values: List[ValueObject] = Field(
        ..., 
        description="List of the creator's core values that guide their work and life"
    )
    challenges: List[ChallengeObject] = Field(
        ..., 
        description="List of significant challenges faced by the creator and how they overcame them"
    )
    achievements: List[AchievementObject] = Field(
        ..., 
        description="List of the creator's notable achievements and milestones"
    )
    first_name: Optional[str] = Field(
        None, 
        description="The first name of the content creator"
    )
    last_name: Optional[str] = Field(
        None, 
        description="The last name of the content creator"
    )

    @classmethod
    def default(cls) -> 'ContentCreatorInfo':
        return cls(
            first_name="",
            last_name="",
            life_events=[LifeEventObject.default()],
            business=BusinessObject.default(),
            values=[ValueObject.default()],
            challenges=[ChallengeObject.default()],
            achievements=[AchievementObject.default()]
        )

@CrewBase
class YoutubeCrew():
    """Youtube crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks_youtube_simple.yaml"

    @agent
    def database_manager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['database_manager_agent'],
            tools=[reset_database_tool],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o")
            # llm=groq
        )

    @agent
    def scrape_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['scrape_agent'],
            tools=[FetchRelevantVideosFromYouTubeChannelTool(result_as_answer=True)],  # Example of custom tool, loaded on the beginning of file
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o")
            # llm=groq
        )

    @agent
    def vector_db_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['vector_db_agent'],
            tools=[add_video_to_vector_db_tool],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o")
            # llm=groq
        )
    
    @agent
    def general_research_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['general_research_agent'],
            tools=[rag_tool, query_instagram_db_tool],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o")
            # llm=groq
        )
    
    @agent
    def merge_results_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['merge_results_agent'],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o")
            # llm=groq
        )
    
    @agent
    def follow_up_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['follow_up_agent'],
            tools=[rag_tool, query_instagram_db_tool],
            verbose=True,
            allow_delegation=False,
            # llm=ChatOpenAI(model="gpt-4o-mini")
            llm=groq
        )
    
    @agent
    def prompting_rag_agent(self) -> Agent:
        return Agent(
            config=self.agents_config['prompting_rag_agent'],
            verbose=True,
            allow_delegation=False,
            llm=ChatOpenAI(model="gpt-4o")
            # llm=groq
        )

    @task
    def database_manager_task(self) -> Task:
        return Task(
            config=self.tasks_config['database_manager_task'],
            tools=[reset_database_tool]
        )

    @task
    def scrape_youtube_channel_task(self) -> Task:
        return Task(
            config=self.tasks_config['scrape_youtube_channel_task'],
            tools=[FetchRelevantVideosFromYouTubeChannelTool(result_as_answer=True)]
        )

    @task
    def process_video_task(self) -> Task:
        return Task(
            config=self.tasks_config['process_video_task'],
            tools=[add_video_to_vector_db_tool]
        )

    @task
    def find_achievements_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_achievements_task'],
            tools=[query_vector_db_tool],
            output_pydantic=ContentCreatorInfo,
            output_file="achievements_output.md"
        )
    
    @task
    def find_challenges_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_challenges_task'],
            tools=[query_vector_db_tool],
            output_pydantic=ContentCreatorInfo,
            output_file="challenges_output.md"
        )

    @task
    def find_life_events_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_life_events_task'],
            tools=[query_vector_db_tool],
            output_pydantic=ContentCreatorInfo,
            output_file="life_events_output.md"
            # async_execution=True
        )
    
    @task
    def find_business_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_business_task'],
            tools=[query_vector_db_tool],
            output_pydantic=ContentCreatorInfo,
            output_file="business_output.md"
            # output_file="youtube_simple_output.md"
            # async_execution=True
        )
    
    @task
    def find_values_task(self) -> Task:
        return Task(
            config=self.tasks_config['find_values_task'],
            tools=[query_vector_db_tool],
            # output_pydantic=ContentCreatorInfo,
            output_pydantic=ContentCreatorInfo,
            output_file="values_output.md"
            # async_execution=True
        )

    @task
    def merge_results_task(self) -> Task:
        return Task(
            config=self.tasks_config['merge_results_task'],
            output_pydantic=ContentCreatorInfo,
            output_file="pydanticYoutubeSimple.md",
            context=[self.find_business_task(), self.find_values_task(), self.find_achievements_task(), self.find_challenges_task(), self.find_life_events_task()]
        )
    
    @task
    def prompting_rag_task(self) -> Task:
        return Task(
            config=self.tasks_config['prompting_rag_task'],
            # tools=[rag_tool, query_instagram_db_tool],
            context=[self.merge_results_task()],
            # output_pydantic=ContentCreatorInfo,
            output_file="rag_output.md"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the Youtube Simple crew"""
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
            full_output=True
        )