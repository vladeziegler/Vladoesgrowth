from google.adk.agents import Agent

from newsletter.sub_agents.marketer.agent import marketer_agent
# Example 1: Simple built-in tool
from google.adk.tools.google_search_tool import google_search
# google_search_tool = FunctionTool(func=google_search)

# Example 2: Agent as a tool
from newsletter.tools.search import google_search_grounding

# Example 3: Function tool
from newsletter.tools.places import PlacesService
from google.adk.tools import FunctionTool
places_tool = FunctionTool(func=PlacesService().find_place_from_text)
from newsletter.prompt import ROOT_AGENT_INSTR
from newsletter.shared_libraries import types
from google.adk.tools.agent_tool import AgentTool
from newsletter.sub_agents.consolidate.agent import consolidate_agent

from newsletter.sub_agents.content_creation.agent import writer_agent
root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="root_agent",
    description="A newsletter content creator",
    instruction=ROOT_AGENT_INSTR,
    sub_agents=[
        consolidate_agent
    ],
    # include_contents='none',
    # sub_agents=[
    #     consolidate_agent],
    # tools=[AgentTool(agent=consolidate_agent)],
    # tools = [google_search_tool]
    # tools = [google_search_grounding],
    # tools=[places_tool]
    # sub_agents=[
    #     inspiration_agent
    # ]
)