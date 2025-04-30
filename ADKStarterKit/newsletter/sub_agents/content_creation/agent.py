from google.adk.agents import SequentialAgent, LlmAgent
# from google.adk.agents import Agent, SequentialAgent, LlmAgent
from google.adk.tools.agent_tool import AgentTool

from google.adk.tools.google_search_tool import google_search
# Wrapped agent
from newsletter.tools.search import google_search_grounding
from google.adk.tools import FunctionTool
# from travel_concierge.tools.places import PlacesService
from newsletter.sub_agents.content_creation.prompt import INTRO_AGENT_INSTR, REVIEW_AGENT_INSTR, BODY_AGENT_INSTR, CONCLUSION_AGENT_INSTR, WRITER_AGENT_INSTR, NEWSLETTER_AGENT_INSTR
# places_tool = FunctionTool(func=PlacesService().find_place_from_text)
from newsletter.shared_libraries import types
from google.adk.agents import Agent


intro_agent = Agent(
    model="gemini-2.0-flash",
    name="intro_agent",
    instruction=INTRO_AGENT_INSTR,
    description="This agent crafts the intro of the newsletter based on the info provided by newsletter_agent.",
    output_schema=types.Intro,
    output_key="intro",
)

review_agent = Agent(
    model="gemini-2.0-flash",
    name="review_agent",
    description="This agent crafts the review of the newsletter based on the info provided by newsletter_agent.",
    instruction=REVIEW_AGENT_INSTR,
    output_schema=types.Review,
    output_key="review",
)

body_agent = Agent(
    model="gemini-2.0-flash",
    name="body_agent",
    description="This agent crafts the body of the newsletter based on the info provided by newsletter_agent.",
    instruction=BODY_AGENT_INSTR,
    output_schema=types.Body,
    output_key="body",
)

conclusion_agent = Agent(
    model="gemini-2.0-flash",
    name="conclusion_agent",
    description="This agent crafts the conclusion of the newsletter based on the info provided by newsletter_agent.",
    instruction=CONCLUSION_AGENT_INSTR,
    output_schema=types.Conclusion,
    output_key="conclusion",
)

# newsletter_agent = Agent(
#     model="gemini-2.0-flash",
#     name="newsletter_agent",
#     description="This agent crafts all the sections of the newsletter based on the info provided.",
#     instruction=NEWSLETTER_AGENT_INSTR,
#     output_schema=types.Newsletter,
#     output_key="newsletter",
# )

writer_agent = SequentialAgent(
    # model="gemini-2.0-flash",
    name="writer_agent",
    # instruction=WRITER_AGENT_INSTR,
    # output_schema=types.Newsletter,
    sub_agents=[
        intro_agent,
        review_agent,
        body_agent,
        conclusion_agent,
    ],
)

# intro_agent = Agent(
#     model="gemini-2.0-flash",
#     name="intro_agent",
#     instruction=INTRO_AGENT_INSTR,
#     description="This agent crafts the intro of the newsletter based on the info provided by newsletter_agent.",
#     output_schema=types.Intro,
#     output_key="intro",
# )

# review_agent = Agent(
#     model="gemini-2.0-flash",
#     name="review_agent",
#     description="This agent crafts the review of the newsletter based on the info provided by newsletter_agent.",
#     instruction=REVIEW_AGENT_INSTR,
#     output_schema=types.Review,
#     output_key="review",
# )

# body_agent = Agent(
#     model="gemini-2.0-flash",
#     name="body_agent",
#     description="This agent crafts the body of the newsletter based on the info provided by newsletter_agent.",
#     instruction=BODY_AGENT_INSTR,
#     output_schema=types.Body,
#     output_key="body",
# )

# conclusion_agent = Agent(
#     model="gemini-2.0-flash",
#     name="conclusion_agent",
#     description="This agent crafts the conclusion of the newsletter based on the info provided by newsletter_agent.",
#     instruction=CONCLUSION_AGENT_INSTR,
#     output_schema=types.Conclusion,
#     output_key="conclusion",
# )

# newsletter_agent = Agent(
#     model="gemini-2.0-flash",
#     name="newsletter_agent",
#     description="This agent crafts all the sections of the newsletter based on the info provided.",
#     instruction=NEWSLETTER_AGENT_INSTR,
#     output_schema=types.Newsletter,
#     output_key="newsletter",
# )

# writer_agent = Agent(
#     model="gemini-2.0-flash",
#     name="writer_agent",
#     description="A writer agent who writes a newsletter based on the info provided by newsletter_agent that populates all the sections of the newsletter.",
#     instruction=WRITER_AGENT_INSTR,
#     tools=[AgentTool(agent=newsletter_agent)],
# )