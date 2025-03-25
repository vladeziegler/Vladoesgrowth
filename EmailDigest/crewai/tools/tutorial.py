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
from llama_index.core.agent import FunctionCallingAgentWorker
from llama_index.core.llms import ChatMessage
from llama_index.llms.openai import OpenAI

from composio.client.collections import TriggerEventData

from composio_crewai import ComposioToolSet, Action, App
from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
from typing import Optional, List
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# COMPOSIO_API_KEY = os.getenv("COMPOSIO_API_KEY")
COMPOSIO_API_KEY = "TO_ADD"
composio_toolset = ComposioToolSet(api_key=COMPOSIO_API_KEY)

calendar_tools = composio_toolset.get_tools(actions=[Action.GOOGLECALENDAR_FIND_FREE_SLOTS, Action.GOOGLECALENDAR_CREATE_EVENT, Action.GMAIL_CREATE_EMAIL_DRAFT])
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

class Result(BaseModel):
    email: str = Field(description="The email found in the sheet")
    recall_date: str = Field(description="The date the recall meeting was scheduled for")
    is_present: bool = Field(description="Whether the email is present in the sheet")
    message: str = Field(description="A message indicating whether the email was found")
    last_appointment_session: str = Field(description="The last appointment session")

class Event(BaseModel):
    summary: str = Field(description="Title of the event")
    start_datetime: str = Field(description="Start time in format like 'UTC+5:30, 3:00 PM' or '2024-03-20T15:00:00Z'")
    event_duration_hour: int = Field(description="Duration in hours (0-24)", ge=0, le=24)
    event_duration_minutes: int = Field(description="Duration in minutes (0-59)", ge=0, le=59)
    attendees: List[str] = Field(description="List of attendee email addresses")
    description: Optional[str] = Field(description="Event description", default=None)
    calendar_id: Optional[str] = Field(description="Calendar ID, usually 'primary'", default="primary")
    timezone: Optional[str] = Field(description="IANA timezone like 'Asia/Kolkata'", default=None)
    create_meeting_room: Optional[bool] = Field(description="Whether to create Google Meet", default=True)
    send_updates: Optional[bool] = Field(description="Whether to send updates to attendees", default=True)

# class Event(BaseModel):
#     summary: str = Field(description="The summary of the event")
#     start_datetime: str = Field(description="The start date and time of the event in ISO format")
#     event_duration_hour: int = Field(description="The duration of the event in hours")
#     event_duration_minutes: int = Field(description="The duration of the event in minutes")
#     attendees: list = Field(description="List of attendees' email addresses")
#     description: str = Field(description="The description of the event")
#     timezone: str = Field(description="The timezone of the event")
#     calendar_id: str = Field(description="The ID of the calendar where the event will be created")

# Create a CrewAI agent
email_processor = Agent(
    role="Process Email Agent",
    goal="""You'll be parsing the email sender info to extract the email and checking if an email exists in a googlesheet""",
    backstory=(
        "You are an expert at parsing the email sender info to extract the email and checking if an email exists in a googlesheet"
    ),
    verbose=True,
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o"),
)

scheduler_agent = Agent(
    role="Calendar Scheduler Agent",
    goal=f""" You are an AI assistant specialized in creating calendar events based on email information. 
                Current DateTime: {date_time} and timezone {timezone}. All the conversations happen in IST timezone.
                Analyze email, and create event on calendar depending on the email content and result of the previous task.
                When creating an event, ensure you pass the parameters as per the Event object.""",
    backstory=(
        "You are AI agent that is responsible for scheduling events on the calendar"
    ),
    verbose=True,
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o"),
)

email_draft_agent = Agent(
    role="Email Draft Agent",
    goal="You are an AI assistant specialized in drafting emails based on the email content and result of the previous task.",
    backstory=(
        "You are an AI assistant specialized in drafting emails based on the email content and result of the previous task."
    ),
    verbose=True,
    tools=tools,
    llm=ChatOpenAI(model="gpt-4o"),
)

# Create a task for the agent
process_email_task = Task(
    description=(
        "{sender_mail} is the email of the sender of the email."
        "Convert the email you find in {sender_mail} to a valid email address that you can pass to Result object."
        "https://docs.google.com/spreadsheets/d/1Uxncu0L4aWUgG_v5roOwC0c-YXmkxCqmijmp2Y_8UzY/edit#gid=0"
        "Check if the email '{sender_mail}' exists in the sheet 'Sheet1!F:F'"
        "Look in range 'Sheet1!F:F' for the email"
        "Look in range 'Sheet1!E:E' for the recall date"
        "Look in range 'Sheet1!C:C' for the last_appointment_session"
        "Return a Result object with all the fields."
    ),
    agent=email_processor,
    output_pydantic=Result,
    tools=tools,
    expected_output="A Result object with all the Result fields"
)
schedule_task = Task(
    description="""
    1. Create an event if email field in Result object is_present is True. You can tell from output of previous task.
    2. If creating an event:
       a) Find a free slot using GOOGLECALENDAR_FIND_FREE_SLOTS
       b) Create event using GOOGLECALENDAR_CREATE_EVENT with these REQUIRED parameters:
          - summary: Clear title for the meeting
          - start_datetime: Format like "UTC+5:30, 3:00 PM" or ISO format
          - event_duration_hour: Integer 0-24
          - event_duration_minutes: Integer 0-59
          - attendees: Must be list of strings, e.g., ["{sender_mail}"]
          - calendar_id: Use "primary"
       
       Optional parameters:
          - description: Meeting details
          - create_meeting_room: true to include Google Meet
          - send_updates: true to notify attendees
          - timezone: IANA format (e.g., "Asia/Kolkata")

        All these fields make up an Event object.
    """,
    agent=scheduler_agent,
    output_pydantic=Event,
    tools=tools,
    expected_output="An Event object with all the Event fields",
    context=[process_email_task]
)

email_draft_task = Task(
    description=
        "Draft an email based on the email content and result of the previous task."
        "{sender_mail} is the email of the sender of the email."
        "If you cannot fetch the user profile, you may also find the email field in the Result object from process_email_task."
        "If the Result object is_present is False, draft an email to inform the user that he should call the doctor for an onboarding."
        "If the Result object is_present is True, draft an email to inform the user that the event was created and the invite was sent to the sender."
        "Use the {message} to draft an email that is consistent with what the sender of the email is saying."
        "Check the thread id {thread_id} to send the email to the correct thread.",
    agent=email_draft_agent,
    tools=tools,
    expected_output="Email draft",
    context=[process_email_task, schedule_task]
)

# Create a crew with the agent
scheduler_crew = Crew(
    agents=[email_processor, scheduler_agent, email_draft_agent],
    tasks=[process_email_task, schedule_task, email_draft_task],
    process=Process.sequential,
    verbose=True
)

listener = composio_toolset.create_trigger_listener()
@listener.callback(filters={"trigger_name": "GMAIL_NEW_GMAIL_MESSAGE"})
def callback_function(event: TriggerEventData) -> None:
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
print("Waiting for email")
listener.wait_forever()
        # Add code to label the email as important using Composio's Gmail tools

