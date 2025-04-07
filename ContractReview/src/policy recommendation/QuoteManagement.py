from crewai import Agent, Crew, Process, Task
from tools.multiplicationTool import multiplication_tool 
# from langchain_openai import ChatOpenAI
# from composio_crewai import ComposioToolSet, Action, App, Trigger
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
# from composio.client.collections import TriggerEventData
import os
import time 
import dotenv  
import re
from datetime import datetime

from crewai import Agent, LLM

# from composio_crewai import ComposioToolSet, Action, App
from crewai import Agent, Task, Crew
# from langchain_openai import ChatOpenAI
from typing import Optional, List

import os
from dotenv import load_dotenv
load_dotenv()
from crewai import LLM

openai_llm_mini = LLM(
    model="gpt-4o-mini"
)
openai_llm_4o = LLM(
    model="gpt-4o"
)

# llama_llm = LLM(
#     model="huggingface/meta-llama/Llama-3.3-70B-Instruct",
#     # base_url="https://api.groq.com/openai/v1"
# )
groq_llm = LLM(
    model="groq/meta-llama/llama-4-scout-17b-16e-instruct"
    # temperature=0.3
)

o3_llm = LLM(
    model="o3-mini"
)


# llm_groq = LLM(
#     model="groq/llama-3.3-70b-versatile",
#     temperature=0.2
# )
# Fix imports for tools
import os
import sys

# Add the parent directory to Python path to make imports work properly
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(current_dir))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
timezone = datetime.now().astimezone().tzinfo

import sys

from tools.claimTool import DocumentQueryTool
from tools.insuranceTool import PolicyQueryTool
from tools.calculationTool import CalculationTool
calculation_tool = CalculationTool()
claim_tool = DocumentQueryTool()
policy_tool = PolicyQueryTool()

# Add the tools directory to Python path
tools_path = "/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/QuoteAutomation/src/recommendationenginetest"
sys.path.append(tools_path)

class Incident(BaseModel):
    # claim_number: Optional[str] = Field(description="The claim number", default=None)
    incident_description: Optional[str] = Field(description="The description of the incident", default=None)
    incident_date: Optional[float] = Field(description="The date of the incident", default=None)
    incident_date_reported: Optional[float] = Field(description="The date the incident was reported", default=None)
    claim_number: Optional[str] = Field(description="The claim number", default=None)
    policy_number: Optional[str] = Field(description="The policy number", default=None)

class Damage(BaseModel):
    damage_type: Optional[str] = Field(description="The type of damaged item (e.g. carpet, roof, fence, structure, etc.)", default=None)
    # quantity: Optional[int] = Field(description="The quantity of the damaged item (e.g. 1, 2, 3, etc.)", default=None)
    damage_description: Optional[str] = Field(description="Broken living room window and water-damaged flooring, Area rug damaged by water", default=None)
    damage_estimate: Optional[float] = Field(description="The value of the object that got damaged", default=None)
    covered: Optional[bool] = Field(description="Whether the reported damage object is covered by the policy or not", default=None)
    coverage_amount: Optional[str] = Field(description="The method to calculate the coverage amount that is allowed by the policy for the damage", default=None)
    supporting_documents: Optional[List[str]] = Field(description="The unedited text from the policy document that supports the coverage decision, coverage amount.", default=None)

class Repair(BaseModel):
    repair_type: Optional[str] = Field(description="The type of repairs done to prevent further damage (e.g. Broken windows boarded up to prevent further rain damage, etc.)", default=None)
    repair_reason: Optional[str] = Field(description="The reason for the repair (e.g. wear and tear, damage, etc.)", default=None)
    repair_description: Optional[str] = Field(description="The description of the object that needs or already got repaired", default=None)
    repair_estimate: Optional[float] = Field(description="The value of the object that needs to be repaired", default=None)
    covered: Optional[bool] = Field(description="Whether the repair is covered by the policy or not", default=None)
    coverage_amount: Optional[str] = Field(description="The method to calculate the coverage amount that is allowed by the policy for the repair", default=None)
    supporting_documents: Optional[List[str]] = Field(description="The unedited text from the policy document that supports the coverage decision, coverage amount.", default=None)

class Claim(BaseModel):
    incident: Incident
    damage: List[Damage]
    repair: List[Repair]

class ClaimDecision(BaseModel):
    claim_decision: Optional[str] = Field(description="The decision of the insurance company about the claim", default=None)
    claim_details: Claim
    tasks_to_investigate: Optional[List[str]] = Field(description="The list of repair and damage objects that need to be investigated further", default=None)
    amount_approved: Optional[float] = Field(description="The sum of the repair and damage objects that are covered by the policy", default=None)
    amount_to_investigate: Optional[float] = Field(description="The sum of the repair and damage objects that need to be investigated further", default=None)
    amount_rejected: Optional[float] = Field(description="The sum of the repair and damage objects that are not covered by the policy", default=None)

claim_processor = Agent(
    role="Claim Processor Agent",
    goal="""You'll use the DocumentQueryTool tool to fill out the claim information. You need to pass a query to the tool to get the claim information.
    Here are the fields you need to populate:
    - incident_description
    - incident_date
    - incident_date_reported
    - claim_number
    - policy_number

    And for each damage object (usually has a residual or market value):
    - damage_type
    - damage_description
    - damage_estimate

    And for each repair object (i.e. usually requested the intervention of a contractor):
    - repair_type
    - repair_description
    - repair_estimate

    IMPORTANT:
    - You need to make sure you're not reporting the same damage or repair object multiple times.
    You should avoid double counting at all costs. For example, if the value of damage is 1,200$, then the value of repair is 1,200$. If an action is taken to fix roof for 7,000$, then the value of repair is 7,000$. You should count the damage and the replacement. Unless explicitly stated.
    - This means you first look at all the damages and repairs, and allocate them to the right objects.
    - You need to make sure you're not skipping any of the damage or repair objects.
    - You need to think deeply about whether they fall under a damage or repair object.
        - Damages are the damage to the property or furniture. For example, a broken window, a broken door, a broken table, etc. This object usually has a market or residual value.
        - Repairs are the repairs to the property or furniture. For example, fixing a broken window, fixing a broken door, fixing a broken table, etc. This is usually done by a contractor.
        - Repairs can also be actions that were taken to prevent further damages. For example: Tarp installed over damaged areas of the roof immediately after the storm.
    """,
    backstory="You need to fill out the claim with the relevant information. You convert claim information into structured Claim objects.",
    verbose=True,
    tools=[claim_tool],
    llm=openai_llm_4o
)

remove_duplicates_agent = Agent(
    role="Remove Duplicates Agent",
    goal="""Remove duplicates from the list of damage and repair objects. If you spot an item where the value is the same, and the item is roughly equal, then it's a duplicate. When you decide on which duplicate to remove, you should figure out if it's most closely related to a damage or repair object and pick that one.
    """,
    backstory="You are an expert at removing duplicates from the list of damage and repair objects. You're incredibly experienced at assessing a claim situation against the set of policy guidelines. You can thoughtfully explain your reaosning to define whether something is covered or not, and walk through how to calculate the maximum coverage amounts.",
    llm=openai_llm_mini,
    verbose=True,
)

policy_processor = Agent(
    role="Policy Processor Agent",
    goal="""Use the PolicyQueryTool to populate the oustanding fields in the list of Repair and Damage Objects.
    Your task is to extract detailed information from the policy document to support if the damage and repair objects are covered.
    For each damage and repair object, you need to figure out 2 things:
    1. If it's covered or not.
    2. If it's covered, what is the maximum coverage amount.
    To do so, you need to:
    - Construct a query that includes the incident description, and specific damage/repair description.
    - The response from the PolicyQueryTool tool will return chunks from the insurance policy. You need to analyse it to define if the damage/repair in question is covered. If yes, you need to carefully explain in maximum coverage amount how to calculate the maximum coverage amount.
    - Coverage amount should be a detailed breakdown of the method to calculate the maximum coverage amount.
    - Supporting documents should be the chunks of text from the policy document that support the coverage decision, coverage amount. Keep it unchanged.
    Do not perform any calculations.
    """,
    backstory="You are an independent insurance adjuster expert tasked with reviewing policy documents. Your decisions must be backed by info in policy documents. Use the incident and damage details to form precise queries. You're incredibly experienced at assessing a claim situation against the set of policy guidelines. You can thoughtfully explain your reaosning to define whether something is covered or not, and walk through how to calculate the maximum coverage amounts.",
    verbose=True,
    tools=[policy_tool],
    llm=openai_llm_4o
)

insurance_adjuster_agent = Agent(
    role="Insurance Adjuster Agent",
    goal="""You are an independent insurance adjuster expert tasked with coming up with a claim decision. You gather all the details about the claim to decide whether the claim is covered, the amount approved, the amount to investigate, and the amount rejected. This means that you evaluate each damage and repair object in the Claim object.
    You will use the CalculationTool to calculate the sum of the amount approved, the amount to investigate, and the amount rejected.
    IMPORTANT: You need to add up the amount approved for the list of repair and damage objects that are covered. You need to add up the amount to investigate for the list of repair and damage objects that are not covered. You need to add up the amount rejected for the list of repair and damage objects that are not covered. Similarly, you need to add up the amount to be investigated for the list of repair and damage objects where you're not sure whether they are covered or not.
    """,
    backstory="You are an independent insurance adjuster expert tasked with coming up with claim decision. You gather all the details about the claim to decide whether the claim is covered, the amount approved, the amount to investigate, and the amount rejected.",
    verbose=True,
    tools=[calculation_tool],
    llm=openai_llm_4o
)

claim_processor_task = Task(
    description="""Fill out the claim with the relevant information. You will call the DocumentQueryTool tool to get the claim information.
    IMPORTANT: You will pass queries to the DocumentQueryTool tool to fill out the claim information.
    When you pass a query, it should only be one question at a time. For example: "What is the claim number?"
    You will pass a query to the DocumentQueryTool tool to fill out the claim information.
    A claim object contains the following:
    - details about an incident
    - a list of damage objects
    - A list of repairs            

    You need to figure out the following:
    - The claim number
    - The incident description
    - The incident date
    - The incident date reported
    - The claim status
    - The claim amount

    And for each damage object (i.e. usually has a residual or market value):
    - The damage type
    - The damage description
    - The damage estimate

    And for each repair object (i.e. usually requested the intervention of a contractor):
    - The repair type
    - The repair description
    - The repair estimate

    IMPORTANT:
    - If you have multiple damages or repairs, they should be reported as separate objects in the list of damage and repair objects.
    - You need to make sure you're not reporting the same damage or repair object multiple times.
    - You need to think deeply about the damage and repair objects, and provide the necessary description about them to be able to audit the decision making process.
    - You need to make sure you're not skipping any of the damage or repair objects.
    - You need to think deeply about whether they fall under a damage or repair object.
        - Damages are the damage to the property or furniture. For example, a broken window, a broken door, a broken table, etc. This object usually has a market or residual value.
        - Repairs are the repairs to the property or furniture. For example, fixing a broken window, fixing a broken door, fixing a broken table, etc. This is usually done by a contractor.
        - Repairs can also be actions that were taken to prevent further damages. For example: Tarp installed over damaged areas of the roof immediately after the storm.
    - If an item's value is worth 10,000$, then it's a damage object. If repairing the item costs 10,000$, then it's a repair object. It cannot be both.
    - Do not make up any information. You only use the information coming from the tool's response.
    - Do not fill out coverage, maximum coverage amount fields.
    """,
    agent=claim_processor,
    output_pydantic=Claim,
    output_file="Claim.md",
    tools=[claim_tool],
    expected_output="A Claim object"
)

remove_duplicates_task = Task(
    description="""Remove duplicates from the list of damage and repair objects. If you spot an item where the value is the same, and the item is roughly equal, then it's a duplicate. When you decide on which duplicate to remove, you should figure out if it's most closely related to a damage or repair object and pick that one.
    """,
    agent=remove_duplicates_agent,
    output_pydantic=Claim,
    output_file="Claim_duplicates_removed.md",
    expected_output="A Claim object where duplicates are removed"
)

policy_processor_task = Task(
    description="""Take the claim object from previous task, and populate the coverage, maximum coverage amount, and supporting documents for each damage and repair object.
    A claim object contains the following:
    - details about an incident
    - a list of damage objects
    - A list of repairs

    For each damage and repair object, you need to figure out:
    - Whether it's covered or not.
    - The maximum coverage amount.
    - The supporting documents that support the coverage decision, coverage amount.

    When you pass a query to the PolicyQueryTool tool, you should pass a query that includes the incident description, and specific damage/repair description and ask whether the damage/repair is covered, the maximum coverage amount, and the supporting documents.
    Very often, you need to evaluate the kind of damage or repair it is, and figure out if it falls under a specific category. It's not always clear cut. 
    For example, if you need to figure out whether hail damage on a the structure of the house is covered, you can assume it's covered if natural phenomenon such as heavy rains, snows, etc. are mentioned in the policy.
    If you find a relevant section in the policy stating, then you can set "covered" to True.
    Once you've determined that it's covered, you need to walk through exactly how to calculate the maximum coverage amount. This should be supported with information from the policy document. You need to specify exclusions, and any other things that need to be considered. Be comprehensive in your reasoning.
    For each object, you need to maintain in the supporting documents the verbatim text that supports the coverage decision, coverage amount. This is important you need to be able to go back to text. Specify the section, page or anything that could help you identify the exact text.
    So for each damage and repair object, you need to figure out 2 things:
    Repeat this process for each damage and repair object.
    Do not stop until you have evaluated each damage and repair object. Ensure you're not skipping any of them. Ensure you're not evaluated the same object multiple times.
    Use separate, specific queries for each of these aspects.
    In the end, you need to have a list of damage and repair objects with the following:
    - Whether it's covered or not.
    - The maximum coverage amount and the full detailed breakdown of the method to calculate the maximum coverage amount.
    - The supporting documents containing all the contect from the text that can help me understand the decision and audit the decision making process.

    IMPORTANT:
    - Keep the incident details unchanged from the previous task.
    - Do not make up any information. You only use the information coming from the tool's response.
    - If you don't find the relevant information, keep coverage set to None. This will be investigated further in the next task.
    - Make sure you do not report the same damage or repair object multiple times. Verify across the list of damage and repair objects to ensure you report them in the right object, and not multiple times.
    """,
    agent=policy_processor,
    output_pydantic=Claim,
    output_file="Claim_reviewed.md",
    tools=[policy_tool],
    expected_output="A Claim Object"
)

claim_decision_task = Task(
    description="""You are an independent insurance adjuster expert tasked with coming up with claim decision.
    Here is how to come up with the claim decision:
    - For the repairs and damages where the coverage is True, you calculate the sum of the amount approved for the damages and repairs. 
    - For the repairs and damages where the coverage is not certain, you specifically explain why it's not certain, and draft a task list of repairs and damages to investigate further. You need to be action-oriented and use the specific documents to justify what and how to investigate further.
    - For the repairs and damages where the coverage is False, you calculate the sum of the amount rejected for the damages and repairs, and you justify why they are not covered.
    IMPORTANT: You should avoid double counting at all costs. For example, if damage is 7,000$, then replacement value is 7,000$. If repair is 7,000$, then repair value is 7,000$. Watch out you're not counting damage and repairs multiple times.
    You can use the CalculationTool to calculate sums. 
    To calculate total amounts covered, you need to add each repair and damage objects where covered is set to true.
    To calculate the sum of the amount not approved, you need to add each repair and damage objects where covered is set to false.
    To calculate the sum of the amount to investigate, you need to add each repair and damage objects where covered is not certain.
    You can also use the MultiplicationTool if you need to do multiplications.
    Only use the MultiplicationTool or CalculationTool if you have all the input parameters.
    You will use the appropriate tool to come up with the values in ClaimDecision object. If you need to calculate ratios, percentages, you'll use the MultiplicationTool. If you need to add, subtract to calculate sums, deductibles, etc. you'll use the CalculationTool.
    """,
    agent=insurance_adjuster_agent,
    output_file="Claim_decision.md",
    tools=[calculation_tool, multiplication_tool],
    # output_pydantic=ClaimDecision,
    context=[remove_duplicates_task, policy_processor_task],
    expected_output="""A detailed claim decision report that includes the following:
     - The summary of the claim decision and incident details
     - A list of tasks to investigate further the damages and repairs where the coverage is not certain
     - The sum of the amount approved for the damages and repairs
     - The sum of the amount to investigate for the damages and repairs
     - The sum of the amount rejected for the damages and repairs
     - The list of damages and repairs that are not covered and the justification for the coverage decision"""
)

# Create a crew with the agent
quote_management_crew = Crew(
    agents=[claim_processor, remove_duplicates_agent, policy_processor, insurance_adjuster_agent],
    tasks=[claim_processor_task, remove_duplicates_task, policy_processor_task, claim_decision_task],
    process=Process.sequential,
    # manager_agent=manager,
    verbose=True
)

def run_crew():
    print("Starting crew execution...")
    print("Environment Variables Check:")
    # print("PINECONE_HOST:", os.getenv("PINECONE_HOST"))
    # print("PINECONE_API_KEY:", "set" if os.getenv("PINECONE_API_KEY") else "not set")
    
    try:
        result = quote_management_crew.kickoff()
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in crew execution: {str(e)}")

def main():
    print("Starting main function...")
    print("Environment Variables at Start:")
    # print("PINECONE_HOST:", os.getenv("PINECONE_HOST"))
    # print("PINECONE_API_KEY:", "set" if os.getenv("PINECONE_API_KEY") else "not set")
    run_crew()

# Replace the direct execution code with this
if __name__ == "__main__":
    main()
        # Add code to label the email as important using Composio's Gmail tools

