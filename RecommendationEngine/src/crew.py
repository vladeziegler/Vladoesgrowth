import os
from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task, before_kickoff
from agentic_rag_example.tools.weaviate_vector_search_tool import (
    WeaviateVectorSearchTool,
)
from crewai_tools import EXASearchTool
# If you want to run a snippet of code before or after the crew starts,
# you can use the @before_kickoff and @after_kickoff decorators
# https://docs.crewai.com/concepts/crews#example-crew-class-with-decorators

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

    # To learn more about structured task outputs,
    # task dependencies, and task callbacks, check out the documentation:
    # https://docs.crewai.com/concepts/tasks#overview-of-a-task
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
        # To learn how to add knowledge sources to your crew, check out the documentation:
        # https://docs.crewai.com/concepts/knowledge#what-is-knowledge

        return Crew(
            agents=self.agents,  # Automatically created by the @agent decorator
            tasks=self.tasks,  # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=True,
            # process=Process.hierarchical, # In case you wanna use that instead https://docs.crewai.com/how-to/Hierarchical/
        )
