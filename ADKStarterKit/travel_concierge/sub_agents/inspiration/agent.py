from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from travel_concierge.sub_agents.inspiration.prompt import PLACE_AGENT_INSTR, NEWS_AGENT_INSTR, INSPIRATION_AGENT_INSTR
from google.adk.tools.google_search_tool import google_search
# Wrapped agent
from travel_concierge.tools.search import google_search_grounding
from google.adk.tools import FunctionTool
from travel_concierge.tools.places import PlacesService

places_tool = FunctionTool(func=PlacesService().find_place_from_text)

place_agent = Agent(
    model="gemini-2.0-flash",
    name="place_agent",
    instruction=PLACE_AGENT_INSTR,
    description="This agent suggests a few locations given some user preferences",
    tools = [places_tool]
)

news_agent = Agent(
    model="gemini-2.0-flash",
    name="news_agent",
    description="This agent suggests key events and news given some user preferences. You can use the google_search_grounding tool to search the web for information. Be explicit and give concrete names of the events and news.",
    instruction=NEWS_AGENT_INSTR,
    tools=[google_search_grounding],
       
)

inspiration_agent = Agent(
    model="gemini-2.0-flash",
    name="inspiration_agent",
    description="A travel inspiration agent who inspire users, and discover their next vacations; Provide information about places, activities, interests,",
    instruction=INSPIRATION_AGENT_INSTR,
    tools=[AgentTool(agent=place_agent), AgentTool(agent=news_agent)],
)