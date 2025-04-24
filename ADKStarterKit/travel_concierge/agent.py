from google.adk.agents import Agent

from travel_concierge.sub_agents.inspiration.agent import inspiration_agent

# Example 1: Simple built-in tool
from google.adk.tools.google_search_tool import google_search

# google_search_tool = FunctionTool(func=google_search)

# Example 2: Agent as a tool
from travel_concierge.tools.search import google_search_grounding

# Example 3: Function tool
from travel_concierge.tools.places import PlacesService
from google.adk.tools import FunctionTool
places_tool = FunctionTool(func=PlacesService().find_place_from_text)
from travel_concierge.prompt import ROOT_AGENT_INSTR

from travel_concierge.sub_agents.inspiration.agent import place_agent, news_agent
root_agent = Agent(
    model="gemini-2.0-flash-001",
    name="root_agent",
    description="A Travel concierge",
    instruction=ROOT_AGENT_INSTR,
    tools=[places_tool],
    sub_agents=[
        inspiration_agent
    ]
    # tools = [google_search_tool]
    # tools = [google_search_grounding],
    # tools=[places_tool]
    # sub_agents=[
    #     inspiration_agent
    # ]
)