#!/usr/bin/env python
import sys
import warnings
from pydantic import BaseModel, Field
from typing import List, Optional
from crew import CaseStudyCreator

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import timedelta
from crew import CaseStudyCreator

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

def run():
    """
    Run the crew.
    """
    inputs = {
        "youtube_url": "https://youtu.be/0uBen8fizg0?si=qzNnCCQvvIG_dagc"
    }
    CaseStudyCreator().crew().kickoff(inputs=inputs)


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        CaseStudyCreator().crew().train(
            n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        CaseStudyCreator().crew().replay(task_id="3fa3fca6-be69-44b4-9ab0-299394c5cac0")

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {"topic": "AI LLMs"}
    try:
        CaseStudyCreator().crew().test(
            n_iterations=int(sys.argv[1]), openai_model_name=sys.argv[2], inputs=inputs
        )

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


if __name__ == "__main__":
    run()

