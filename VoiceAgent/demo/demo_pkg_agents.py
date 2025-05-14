from agents import Agent, WebSearchTool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions, RECOMMENDED_PROMPT_PREFIX
# The save_image_locally tool is removed from this import as generate_ad_image now handles saving.
from tools import (
    generate_image_prompt,
    generate_ad_image,
    save_ad_copy_to_markdown,
    AdContext,
)
from agents.items import MessageOutputItem, ReasoningItem
import os
import dotenv
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# --- Simplified Agent for Testing (Commented Out) ---
"""
direct_image_agent = Agent(
    name="Direct Image Generator",
    instructions=prompt_with_handoff_instructions(
        "You are an AI image generation assistant. The user will provide a prompt. "
        "Use the 'generate_ad_image' tool to create an image based on this prompt. "
        "Then, announce the full result message returned by the tool."
    ),
    model="gpt-4o-mini",
    tools=[generate_ad_image]
)

initial_agent = direct_image_agent
"""

# --- Incremental Test: Step 1 (Commented out) ---
"""
news_research_agent = Agent(
    name="News Researcher",
    instructions=prompt_with_handoff_instructions(
        "You are a news researcher. Your task is to use the WebSearchTool to find recent news relevant to the user's ad creation request. "
        "Summarize the key findings. Your response will be this summary, which then becomes available to the Ad Copywriter in the next step of the workflow."
    ),
    model="gpt-4o-mini",
    tools=[WebSearchTool()]
)

copywriting_agent = Agent(
    name="Ad Copywriter Test",
    instructions=prompt_with_handoff_instructions(
        "You will have access to a news summary from the previous step. "
        "Your ONLY task is to acknowledge this by stating clearly: 'I have received the news summary. The summary is: [ dokładnie powtórz streszczenie, które otrzymałeś z poprzedniego kroku ]'. "
        "Do nothing else. Do not add any pleasantries before or after this exact statement."
    ),
    model="gpt-4o-mini",
    tools=[],
    handoffs=[]
)

news_research_agent.handoffs = [copywriting_agent]
initial_agent = news_research_agent
"""

# --- New Two-Step Test: Prompt Generation -> Image Generation (Aligned with Example) ---

# Define the target agent first
# image_generation_test_agent = Agent(
# name="Image Generation Test Agent",
# handoff_description="Uses gpt-image-1 to turn an image prompt into a "
# "local PNG file and tells the user where it was saved.",
# instructions=prompt_with_handoff_instructions(
# "You are an AI image generation specialist. You will receive a detailed image prompt string from the previous agent's response. "
# "Use your 'generate_ad_image' tool with this received image prompt. The tool will save the image and return a message with its file path. "
# "Announce the full message returned by the tool to the user. Do not add any pleasantries before or after this exact statement from the tool."
# ),
# model="gpt-4o-mini",
# tools=[generate_ad_image]
#     # No further handoffs for this agent in this specific test
# )

# Define the initial agent, with handoff to the target agent in its constructor
# prompt_generation_test_agent = Agent(
# name="Prompt Generation Test Agent",
# instructions=prompt_with_handoff_instructions(
# "You are an AI image prompt engineer. The user describes an ad "
# "concept. Call your 'generate_image_prompt' tool with the full "
# "description. After the tool returns, **reply with ONLY that raw "
# "prompt string and then immediately hand-off to the "
# "'Image Generation Test Agent'.**"
# ),
# model="gpt-4o-mini",
# tools=[generate_image_prompt],
# handoffs=[image_generation_test_agent]
# )

# initial_agent = prompt_generation_test_agent

# --- Full Multi-Agent Setup ---
RECOMMENDED_SUBPROMPT_PREFIX = "If anything is unclear, ask clarifying questions. If you need to think, yield a ReasoningItem('Thinking about the best ad copy...') before you start writing. Once you are done with your task, yield a MessageOutputItem('Done!') to indicate that you are done and go back to triage agent."
# -------------------------------------------------------------------
# SPECIALIST AGENTS (first, because triage needs to reference them)
# -------------------------------------------------------------------
# 1. Ad Copywriter
copywriting_agent = Agent[AdContext](
    name="Ad Copywriter",
    handoff_description="Writes or rewrites ad copy and saves it to Markdown.",
    instructions=prompt_with_handoff_instructions(
        f"{RECOMMENDED_SUBPROMPT_PREFIX}\n"
        "You are an expert ad copywriter.\n"
        "# Routine\n"
        "1. If you still need information, ask a *single clear question*.\n"
        "2. Otherwise, write Title / Subtitle / Paragraph copy.\n"
        "3. Call `save_ad_copy_to_markdown` with the three parts.\n"
        "4. Hand off back to **Triage Agent**.\n"
        "# Streaming\n"
        "- As you think, yield ReasoningItem('Thinking about the best ad copy...') before you start writing.\n"
        "- If you need clarification, yield MessageOutputItem('Can you clarify the target audience?') immediately.\n"
    ),
    model="gpt-4o",
    tools=[save_ad_copy_to_markdown],
    handoffs=[],         # will be filled later
)

# 2. Image Prompt Generator
prompt_generation_agent = Agent[AdContext](
    name="Image Prompt Generator",
    handoff_description="Creates a DALL·E style prompt from the ad copy.",
    instructions=prompt_with_handoff_instructions(
        f"{RECOMMENDED_SUBPROMPT_PREFIX}\n"
        "You are an image-prompt engineer.\n"
        "# Routine\n"
        "1. If the previous agent asked a question, repeat that question verbatim.\n"
        "2. Else, craft a detailed image prompt and call `generate_image_prompt`.\n"
        "3. Hand off back to **Triage Agent**."
    ),
    model="gpt-4o",
    tools=[generate_image_prompt],
    handoffs=[],         # will be filled later
)

# 3. Ad Image Generator
image_generation_agent = Agent[AdContext](
    name="Ad Image Generator",
    handoff_description="Generates the final image from an image prompt.",
    instructions=prompt_with_handoff_instructions(
        f"{RECOMMENDED_SUBPROMPT_PREFIX}\n"
        "You are an image generation specialist.\n"
        "# Routine\n"
        "1. Use `generate_ad_image` with the provided prompt.\n"
        "2. Return the success message with the file path.\n"
        "3. Ask an open question like 'What would you like next?'\n"
        "4. Hand off back to **Triage Agent** if the user's next request is not purely image-related."
    ),
    model="gpt-4o",
    tools=[generate_ad_image],
    handoffs=[],         # will be filled later
)

# -------------------------------------------------------------------
# TRIAGE AGENT
RECOMMENDED_PROMPT_PREFIX = "Your an ad creative director. You are responsible for overseeing the creation of an ad. You need to gather information from the copywriter to come up with an ad concept. From then on, you need to write a prompt that encapsulates the ad concept. Finally, you need to generate an image that captures the ad concept. You have a team working with you, so you need to delegate tasks to them."
# -------------------------------------------------------------------
triage_agent = Agent[AdContext](
    name="Ad Triage Agent",
    handoff_description="Routes user requests to the correct specialist.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the conversation entry point.\n"
        "ROUTINE"
        "Firt generate the ad copy. Then generate the image prompt. Then generate the image. Then refine the image prompt if needed. Then generate another image."
        "If user wants to refine any of the results, you can handoff to the appropriate agent."
        "# Delegation rules\n"
        "• If the user asks for *new* copy or copy changes → **Ad Copywriter**\n"
        "• If the user asks to refine the image prompt → **Image Prompt Generator**\n"
        "• If the user asks for *new* image or image changes → **Ad Image Generator**"
        "Traditional sequence is to first gather ad copy from Ad Copywriter, then generate an image prompt, then generate an image, then refine the image prompt if needed, and then generate another image."
    ),
    model="gpt-4o",
    tools=[],
    handoffs=[copywriting_agent, prompt_generation_agent, image_generation_agent]
)

initial_agent = triage_agent # This is the entry point for the ad creation flow.
# If the conversation continues, MyWorkflow._current_agent will track the active agent.

# Ensure *all* specialist <-> triage links exist exactly once
for ag in (copywriting_agent, prompt_generation_agent, image_generation_agent):
    if triage_agent not in ag.handoffs:
        ag.handoffs.append(triage_agent)