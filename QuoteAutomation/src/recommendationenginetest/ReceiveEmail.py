from crewai import Agent, Crew, Process, Task
from langchain_openai import ChatOpenAI
from composio_crewai import ComposioToolSet, Action, App, Trigger
from pydantic import BaseModel, Field
from composio.client.collections import TriggerEventData
import os
import time 
import dotenv  
import re
from datetime import datetime
# from composio_llamaindex import App, ComposioToolSet, Action
# from llama_index.core.agent import FunctionCallingAgentWorker
# from llama_index.core.llms import ChatMessage
# from llama_index.llms.openai import OpenAI

from composio.client.collections import TriggerEventData

from composio_crewai import ComposioToolSet, Action, App
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Optional, List
COMPOSIO_API_KEY = "vl3aa4zgipffn4ykpmzqva"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
from crewai import LLM

openai_llm = LLM(
    model="openai/o3-mini"
)

# llm_groq = LLM(
#     model="groq/llama-3.3-70b-versatile",
#     temperature=0.2
# )

# COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
# calendar_tools = composio_toolset.get_tools(actions=[Action.GOOGLECALENDAR_FIND_FREE_SLOTS, Action.GOOGLECALENDAR_CREATE_EVENT, Action.GMAIL_CREATE_EMAIL_DRAFT])
composio_toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)
# gsheets_tools = composio_toolset.get_tools(actions=['GOOGLESHEETS_LOOKUP_SPREADSHEET_ROW'])
date_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
timezone = datetime.now().astimezone().tzinfo
tools = composio_toolset.get_tools(actions=[
    Action.GOOGLESHEETS_LOOKUP_SPREADSHEET_ROW,
    Action.GOOGLECALENDAR_FIND_FREE_SLOTS, 
    Action.GOOGLECALENDAR_CREATE_EVENT, 
    Action.GMAIL_CREATE_EMAIL_DRAFT
])
import sys

# Add the tools directory to Python path
tools_path = "/Users/vladimirdeziegler/text_crewai/Vladoesgrowth/QuoteAutomation/src/recommendationenginetest"
sys.path.append(tools_path)

from tools.pineconeTool import PineconeVectorSearchTool

database_tool = PineconeVectorSearchTool()



class Item(BaseModel):
    description: Optional[str] = Field(description="The description of the item", default=None)
    upc_code: Optional[str] = Field(description="The upc code of the item", default=None)
    quantity: Optional[int] = Field(description="The quantity of the item", default=None)

class NewItem(BaseModel):
    query: Optional[str] = Field(description="The query related to a specific item", default=None)
    quantity: Optional[int] = Field(description="The quantity of the item", default=None)

class ListOfItems(BaseModel):
    items: Optional[List[Item]] = Field(description="The list of items", default_factory=list)
    new_items: Optional[List[NewItem]] = Field(description="The list of new items", default_factory=list)

class ReturnedItem(BaseModel):
    item_description: Optional[str] = Field(description="The description of the item", default=None)
    upc_code: Optional[str] = Field(description="The upc code of the item", default=None)
    quantity_available: Optional[int] = Field(description="The quantity of the item available", default=None)
    unit_cost: Optional[float] = Field(description="The unit cost of the item", default=None)

class OrderableItems(BaseModel):
    returned_items: Optional[List[ReturnedItem]] = Field(description="The list of items", default_factory=list)

# Create a CrewAI agent
email_processor = Agent(
    role="Process Email Agent",
    goal="""You'll be parsing the email sender info to populate a list of Item objects, as ListOfItems object.""",
    backstory="You are an expert at converting messy email requests into structured Item objects.",
    verbose=True,
    tools=tools,
    llm=openai_llm
)

database_checker = Agent(
    role="Database Checker Agent",
    goal="""You are an AI assistant specialized in searching the inventory database using the PineconeVectorSearchTool.
    You must properly handle both regular items and new items.""",
    backstory="""You are an expert at:
    1. Using PineconeVectorSearchTool with proper input format:
       - For items with UPC code: Use both query and filter with the UPC code and eq sign
       - For new items: Use query, and pick the filter and sign depending on the email message.
    2. Processing the tool's output into a ReturnedItem object to form the OrderableItems object""",
    verbose=True,
    tools=[database_tool],
    llm=ChatOpenAI(model="gpt-4o")
)

# Create a task for the agent
process_email_task = Task(
    description=(
        "Convert the information in {message} to a ListOfItems object."
        "{message} can contain multiple items, and you should be able to parse them all."
        "{message} may or may not contain all the field for each Item object in the ListOfItems object."
        "Return a ListOfItems object with all the fields."
    ),
    agent=email_processor,
    output_pydantic=ListOfItems,
    output_file="SalesOrder.md",
    tools=tools,
    expected_output="A ListOfItems object with all the Item fields"
)

check_database_task = Task(
    description="""Search the database for items in the ListOfItems object.

    IMPORTANT: You will receive a ListOfItems object as input. You must process each item in it.
    Here is how you should pass the input parameters to the PineconeVectorSearchTool:

    For regular items (from items list):
    query="description of the item"
    filter_column="filter to apply to the metadata"
    filter_sign="the desired sign of the filter"
    filter_value="value to apply to the filter"

    Here is the list of filter you can apply to the metadata:
    - "upc_code"

    Here are the possible filter signs:
    - "eq"

    For new items (from new_items list):
    query="description of the new item"
    filter_column="filter to apply to the metadata"
    filter_sign="the desired sign of the filter"
    filter_value="value to apply to the filter"
    
    Here is the list of filter you can apply to the metadata:
    - "unit_cost"
    - "quantity_available"

    Here are the possible filter signs:
    - "eq"
    - "gt"
    - "lt"

    The tool returns a JSON string that looks like this:
    "item_description":"Athletic Socks Black Small 3-Pack","upc_code":"843956178265","quantity_available":440,"unit_cost":8.25,"error":null

    For each successful search:
    1. Create a ReturnedItem with the exact values from the response
    2. Add it to the list of ReturnedItems to form the OrderableItems object

    Make sure to:
    1. Process EVERY item from the input ListOfItems
    2. Keep the exact values returned by the tool (don't modify them)
    3. Return a valid OrderableItems object even if no items are found
    """,
    agent=database_checker,
    output_pydantic=OrderableItems,
    output_file="OrderableItems.md",
    tools=[database_tool],
    expected_output="An OrderableItems object containing all found items"
)

# Create a crew with the agent
scheduler_crew = Crew(
    agents=[email_processor, database_checker],
    tasks=[process_email_task, check_database_task],
    process=Process.sequential,
    verbose=True
)

listener = composio_toolset.create_trigger_listener()
@listener.callback(filters={"trigger_name": "GMAIL_NEW_GMAIL_MESSAGE"})
def callback_function(event: TriggerEventData) -> None:
    # Debug environment variables
    print("Environment Variables Check:")
    print("PINECONE_HOST:", os.getenv("PINECONE_HOST"))
    print("PINECONE_API_KEY:", "set" if os.getenv("PINECONE_API_KEY") else "not set")
    
    print("here in the function")
    payload = event.payload
    thread_id = payload.get("threadId")
    message = payload.get("messageText")
    sender_mail = payload.get("sender")
    
    if sender_mail is None:
        print("No sender email found")
        return
    print(sender_mail)
    
    try:
        # Match the working notebook format for inputs
        result = scheduler_crew.kickoff(
            inputs={
                "sender_mail": sender_mail,
                "message": message,
                "thread_id": thread_id
            }
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error in crew execution: {str(e)}")

print("Listener started!")
print("Environment Variables at Start:")
print("PINECONE_HOST:", os.getenv("PINECONE_HOST"))
print("PINECONE_API_KEY:", "set" if os.getenv("PINECONE_API_KEY") else "not set")
print("Waiting for email")
listener.wait_forever()
        # Add code to label the email as important using Composio's Gmail tools

