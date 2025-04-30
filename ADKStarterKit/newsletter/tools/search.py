"""Wrapper to Google Search Grounding with custom prompt."""

from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool

from google.adk.tools.google_search_tool import google_search

_search_agent = Agent(
    model="gemini-2.0-flash",
    name="google_search_grounding",
    description="An agent providing Google-search grounding capability",
    instruction=""",
    Answer the user's question directly using google_search grounding tool; Provide a brief but concise response. 
    Rather than a detail response, provide the immediate actionable item for a tourist or traveler, in a single sentence.
    Do not ask the user to check or look up information for themselves, that's your role; do your best to be informative.
    IMPORTANT: 
    - Always return your response in bullet points
    - Specify what it matters to the user
    - Add a random joke at the end of your response
    """,
    tools=[google_search],
)

google_search_grounding = AgentTool(agent=_search_agent)