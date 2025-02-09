import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff
from .tools.weaviate_vector_search_tool import (
    WeaviateVectorSearchTool,
)
from crewai_tools import EXASearchTool

from pydantic import BaseModel, Field
from typing import Optional, List

class AgentObject(BaseModel):
    company_activity: str = Field(
        ..., 
        description="The company activity, e.g., 'Software development'"
    )
    task: str = Field(
        ..., 
        description="The task, e.g., 'Receiving calls and handling customer complaints'"
    )
    location: str = Field(
        ..., 
        description="The location, e.g., 'New York'"
    )
    role: str = Field(
        ..., 
        description="The role, e.g., 'Sales Manager'"
    )
    hours_saved: float = Field(
        ..., 
        description="The hours saved, e.g., 10"
    )
    money_saved: float = Field(
        ..., 
        description="The money saved, e.g., 1000"
    )

    market_size: Optional[float] = Field(
        None, 
        description="The market size, e.g., 1000000"
    )

    market_category: Optional[str] = Field(
        None, 
        description="The category of the market, e.g., 'HVAC serving the B2B market in Canada'"
    )

    market_growth: Optional[float] = Field(
        None, 
        description="The yearly growth rate of the market in percentage, e.g., 10%"
    )
    market_challenges: Optional[str] = Field(
        None, 
        description="The set of key challenges the market is currently facing, e.g., 'The HVAC industry is facing a shortage of skilled workers'"
    )
    market_notes: Optional[str] = Field(
        None, 
        description="The various key information that are necessary to understand the market, e.g., 'The HVAC industry is driven by energy efficiency and sustainability measures.'"
    )


class AgentObjectList(BaseModel):
    agents: List[AgentObject] = Field(
        ..., 
        description="A list of AgentObjects"
    )
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

weaviate_vector_search_tool = WeaviateVectorSearchTool(
    weaviate_cluster_url=os.environ.get("WEAVIATE_URL"),
    weaviate_api_key=os.environ.get("WEAVIATE_API_KEY"),
    collection_name="Agents_19",
    headers={"X-OpenAI-Api-Key": os.environ.get("OPENAI_API_KEY")},
    limit=10,
)
exa_search_tool = EXASearchTool(
    api_key=os.environ.get("EXA_API_KEY"),
)


@CrewBase
class AgenticRagExample:
    """AgenticRagExample crew"""

    # Learn more about YAML configuration files here:
    # Agents: https://docs.crewai.com/concepts/agents#yaml-configuration-recommended
    # Tasks: https://docs.crewai.com/concepts/tasks#yaml-configuration-recommended
    agents_config = "config/agents.yaml"
    tasks_config = "config/tasks.yaml"

    # @before_kickoff
    # def before_kickoff_2(self) -> None:
    #     return print("Before kickoff")

    # If you would like to add tools to your agents, you can learn more about it here:
    # https://docs.crewai.com/concepts/agents#agent-tools
    @agent
    def rag_agent(self) -> Agent:
        return Agent(
            config=self.agents_config["rag_agent"],
            verbose=True,
            tools=[weaviate_vector_search_tool],
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
    def rag_task(self) -> Task:
        return Task(
            config=self.tasks_config["rag_task"],
        )

    @task
    def expand_details_task(self) -> Task:
        return Task(
            config=self.tasks_config["expand_details_task"], output_file="report.md"
        )

    @task
    def report_task(self) -> Task:
        return Task(config=self.tasks_config["report_task"], output_file="report.md")

    @crew
    def crew(self) -> Crew:
        """Creates the AgenticRagExample crew"""

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
