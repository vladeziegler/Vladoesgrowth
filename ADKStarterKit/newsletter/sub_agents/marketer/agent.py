from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from newsletter.sub_agents.marketer.prompt import MARKETER_AGENT_INSTR, RESEARCH_AGENT_INSTR, USER_RESEARCH_AGENT_INSTR
from google.adk.tools.google_search_tool import google_search
# Wrapped agent
from newsletter.tools.search import google_search_grounding
from google.adk.tools import FunctionTool
from newsletter.tools.places import PlacesService
from newsletter.shared_libraries import types

from google.adk.tools.google_search_tool import google_search
research_agent = Agent(
    model="gemini-2.0-flash",
    name="research_agent",
    description="This agent runs research about specific industry news and key events. You always try to understand why something matters to the user. Figure out the historical context of the news and tie it back to the user's query.",
    instruction=RESEARCH_AGENT_INSTR,
    tools=[google_search],
       
)

user_research_agent = Agent(
    model="gemini-2.0-flash",
    name="user_research_agent",
    description="This agent deeply analyses the user's profile and their interests. You populate the Profile object with the user's profile.",
    instruction=USER_RESEARCH_AGENT_INSTR,
    output_schema=types.Profile,
    output_key="profile",
)

marketer_agent = Agent(
    model="gemini-2.0-flash",
    name="marketer_agent",
    description="""A marketer who knows how to tie back to his audience's profile and their interests.
    You can use the research_agent and user_research_agent as tools to help you with your research.""",
    instruction=MARKETER_AGENT_INSTR,
    tools=[AgentTool(agent=research_agent), AgentTool(agent=user_research_agent)],
)