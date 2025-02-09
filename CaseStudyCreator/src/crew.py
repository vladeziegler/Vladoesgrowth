import time

import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff
from crewai_tools import EXASearchTool

from pydantic import BaseModel, Field
from typing import Optional, List
from tools.ResettingTool import ResetDatabaseTool
from tools.chroma_db_init import get_or_create_app_instance
from tools.AddVideoToVectorDBTool import AddVideoToVectorDBTool
from tools.QueryVectorDBTool import QueryVectorDBTool

app_instance = get_or_create_app_instance()
reset_database_tool = ResetDatabaseTool(app=app_instance)
add_video_to_vector_db_tool = AddVideoToVectorDBTool(app=app_instance)
query_vector_db_tool = QueryVectorDBTool(app=app_instance)

class ExecutiveSummary(BaseModel):
    industry: str = Field(
        ...,
        description="Client's industry, e.g., 'Healthcare'"
    )
    company_size: str = Field(
        ...,
        description="Size of the company, e.g., 'mid-sized'"
    )
    core_business: str = Field(
        ...,
        description="Main business activity of the client"
    )
    problem_snapshot: str = Field(
        ...,
        description="Brief description of the main problem"
    )
    solution_snapshot: str = Field(
        ...,
        description="Brief description of the implemented solution"
    )
    result_snapshot: str = Field(
        ...,
        description="Key results achieved"
    )

class Challenge(BaseModel):
    pain_points: List[str] = Field(
        ...,
        description="List of specific workflows causing inefficiencies"
    )
    impact: dict = Field(
        ...,
        description="Quantified losses in time, cost, and opportunities"
    )
    client_goals: List[str] = Field(
        ...,
        description="List of objectives the client aimed to achieve"
    )

class TechStack(BaseModel):
    languages: List[str] = Field(
        ...,
        description="Programming languages used"
    )
    frameworks: List[str] = Field(
        ...,
        description="Frameworks and libraries utilized"
    )
    infrastructure: List[str] = Field(
        ...,
        description="Infrastructure and cloud services used"
    )

class Solution(BaseModel):
    agent_name: str = Field(
        ...,
        description="Name of the AI agent deployed"
    )
    agent_role: str = Field(
        ...,
        description="Primary function of the AI agent"
    )
    customizations: List[str] = Field(
        ...,
        description="List of customizations made for the client"
    )
    tech_stack: TechStack = Field(
        ...,
        description="Technical components used in the solution"
    )

class Implementation(BaseModel):
    timeline: timedelta = Field(
        ...,
        description="Total implementation duration"
    )
    phases: List[dict] = Field(
        ...,
        description="List of implementation phases with durations and descriptions"
    )
    challenges_overcome: List[str] = Field(
        ...,
        description="Technical or organizational challenges that were addressed"
    )

class Results(BaseModel):
    metrics: dict = Field(
        ...,
        description="Key performance metrics and their improvements"
    )
    roi: dict = Field(
        ...,
        description="Return on investment calculations"
    )
    time_savings: dict = Field(
        ...,
        description="Time saved in various processes"
    )
    cost_savings: float = Field(
        ...,
        description="Total cost savings achieved"
    )

class CaseStudy(BaseModel):
    title: str = Field(
        ...,
        description="Case study title following the [Result] for [Client/Industry] Using [Solution] format"
    )
    executive_summary: ExecutiveSummary = Field(
        ...,
        description="Overview of the case study"
    )
    challenge: Challenge = Field(
        ...,
        description="Detailed description of the client's challenges"
    )
    solution: Solution = Field(
        ...,
        description="Technical solution implemented"
    )
    implementation: Implementation = Field(
        ...,
        description="Implementation process details"
    )
    results: Results = Field(
        ...,
        description="Quantifiable results achieved"
    )

weaviate_vector_search_tool = WeaviateVectorSearchTool(
    weaviate_cluster_url=os.environ.get("WEAVIATE_URL"),
    weaviate_api_key=os.environ.get("WEAVIATE_API_KEY"),
    collection_name="netflix_data_system_2",
    headers={"X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY")},
    limit=10,
)

exa_search_tool = EXASearchTool(
    api_key=os.environ.get("EXA_API_KEY"),
)

@CrewBase
class CaseStudyCreator:
    """CaseStudyCreator crew"""

    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"
    reset_database_tool = ResetDatabaseTool(app=app_instance)
    @agent
    def database_manager_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["database_manager_agent"],
            verbose=True,
            tools=[reset_database_tool],
        )
    @agent
    def add_video_to_vector_db_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["add_video_to_vector_db_agent"],
            verbose=True,
            tools=[add_video_to_vector_db_tool],
        )
    
    @agent
    def scrape_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["scrape_agent"],
            verbose=True,
            tools=[query_vector_db_tool],
        )
    
    @agent
    def expand_details_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["expand_details_agent"],
            verbose=True,
            tools=[exa_search_tool],
        )

    @agent
    def report_agent(self) -> Agent:
        return Agent(config=self.agents_config["report_agent"], verbose=True)

    @task
    def reset_database_task(self) -> Task:
        return Task(
            config=self.tasks_config["reset_database_task"],
            tools=[reset_database_tool]
        )
    
    @task
    def add_video_to_vector_db_task(self) -> Task:
        return Task(
            config=self.tasks_config["add_video_to_vector_db_task"],
            tools=[add_video_to_vector_db_tool]
        )
    
    @task
    def executive_summary_task(self) -> Task:
        return Task(
            config=self.tasks_config["executive_summary_task"],
            tools=[query_vector_db_tool],
            output_pydantic=ExecutiveSummary,
            output_file="executive_summary.md"
        )

    @task
    def challenge_task(self) -> Task:
        return Task(
            config=self.tasks_config["challenge_task"],
            tools=[query_vector_db_tool],
            output_pydantic=Challenge,
            output_file="challenge.md"
        )
    
    @task
    def solution_task(self) -> Task:
        return Task(
            config=self.tasks_config["solution_task"],
            tools=[query_vector_db_tool],
            output_pydantic=Solution,
            output_file="solution.md"
        )
    
    @task
    def implementation_task(self) -> Task:
        return Task(
            config=self.tasks_config["implementation_task"],
            tools=[query_vector_db_tool],
            output_pydantic=Implementation,
            output_file="implementation.md"
        )
    
    @task
    def results_task(self) -> Task:
        return Task(
            config=self.tasks_config["results_task"],
            tools=[query_vector_db_tool],
            output_pydantic=Results,
            context=[self.executive_summary_task(), self.challenge_task(), self.solution_task(), self.implementation_task()],
            output_file="results.md"
        )
    
    @task
    def report_task(self) -> Task:
        return Task(
            config=self.tasks_config["report_task"],
            tools=[query_vector_db_tool],
            output_pydantic=CaseStudy,
            context=[self.executive_summary_task(), self.challenge_task(), self.solution_task(), self.implementation_task(), self.results_task()],
            output_file="case_study.md"
        )

    @crew
    def crew(self) -> Crew:
        """Creates the CaseStudyCreator crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
