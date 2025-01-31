#!/usr/bin/env python
import sys
import warnings
from pydantic import BaseModel, Field
from typing import List, Optional
from crew import AgenticRagExample

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")


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
    ),
    market_challenges: Optional[str] = Field(
        None, 
        description="The set of key challenges the market is currently facing, e.g., 'The HVAC industry is facing a shortage of skilled workers'"
    ),
    market_notes: Optional[str] = Field(
        None, 
        description="The various key information that are necessary to understand the market, e.g., 'The HVAC industry is driven by energy efficiency and sustainability measures.'"
    )


class AgentObjectList(BaseModel):
    agents: List[AgentObject] = Field(
        ..., 
        description="A list of AgentObjects"
    )

def run():
    """
    Run the crew.
    """
    inputs = {
        "query": "Best use cases for custom voice agents"
    }
    AgenticRagExample().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        AgenticRagExample().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AgenticRagExample().crew().replay(task_id="3fa3fca6-be69-44b4-9ab0-299394c5cac0")

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        AgenticRagExample().crew().test(
            n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")
