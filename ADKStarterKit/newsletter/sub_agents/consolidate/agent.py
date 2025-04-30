from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from newsletter.sub_agents.marketer.prompt import MARKETER_AGENT_INSTR, RESEARCH_AGENT_INSTR, USER_RESEARCH_AGENT_INSTR
from google.adk.tools.google_search_tool import google_search
# Wrapped agent
from newsletter.tools.search import google_search_grounding
from google.adk.tools import FunctionTool
from newsletter.tools.places import PlacesService
from newsletter.shared_libraries import types
from newsletter.sub_agents.content_creation.agent import writer_agent
from newsletter.sub_agents.marketer.agent import marketer_agent
from newsletter.sub_agents.consolidate.prompt import CONSOLIDATE_AGENT_INSTR
consolidate_agent = Agent(
    model="gemini-2.0-flash",
    name="consolidate_agent",
    description="""An agent who can allocate work to the subagents.""",
    instruction=CONSOLIDATE_AGENT_INSTR,
    tools=[AgentTool(agent=marketer_agent), AgentTool(agent=writer_agent)],
)