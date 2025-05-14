# filename: agents_setup.py
"""
Agent definitions with streaming enabled.
"""

from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from agents.items import MessageOutputItem, ReasoningItem, ToolCallOutputItem, ItemHelpers
from tools import (
    generate_image_prompt,
    generate_ad_image,
    save_ad_copy_to_markdown,
    AdContext,
)

from agents import Agent
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
from tools import (
    AdContext,
    generate_ad_image,
    generate_image_prompt,
    save_ad_copy_to_markdown,
)

# # ── helper text that is appended to every specialist prompt
# COMMON_PREFIX = (
#     "If anything is unclear, ask clarifying questions. "
#     "Think out loud via ReasoningItem, then yield MessageOutputItem('Done!'). "
#     "Never reveal the item names to the user."
# )

# # ── 1. Copywriter ────────────────────────────────────────────────────────────
# copywriting_agent = Agent[AdContext](
#     name="Ad Copywriter",
#     handoff_description="Writes or rewrites ad copy and saves it to Markdown.",
#     instructions=prompt_with_handoff_instructions(
#         f"{COMMON_PREFIX}\nYou are an expert ad copywriter."
#     ),
#     model="gpt-4o-mini",
#     tools=[save_ad_copy_to_markdown],
# )

# # ── 2. Image-prompt engineer ────────────────────────────────────────────────
# prompt_generation_agent = Agent[AdContext](
#     name="Image Prompt Generator",
#     handoff_description="Turns the ad concept into a DALL·E-style prompt.",
#     instructions=prompt_with_handoff_instructions(
#         f"{COMMON_PREFIX}\nYou are an image-prompt engineer."
#     ),
#     model="gpt-4o-mini",
#     tools=[generate_image_prompt],
# )

# # ── 3. Image generator ───────────────────────────────────────────────────────
# image_generation_agent = Agent[AdContext](
#     name="Ad Image Generator",
#     handoff_description="Generates the final image from the prompt.",
#     instructions=prompt_with_handoff_instructions(
#         f"{COMMON_PREFIX}\nYou are an image-generation specialist. "
#         "NEVER reveal the local image path."
#     ),
#     model="gpt-4o-mini",
#     tools=[generate_ad_image],
# )

# # ── Triage / entry point ────────────────────────────────────────────────────
# triage_agent = Agent[AdContext](
#     name="Ad Triage Agent",
#     handoff_description="Routes the user to the right specialist.",
#     instructions=(
#         "You’re the creative director. Gather the user’s ad goals, "
#         "then delegate in this order:\n"
#         "1. Copywriter → 2. Prompt Generator → 3. Image Generator.\n"
#         "If the user asks to tweak something, hand off accordingly."
#     ),
#     model="gpt-4o-mini",
#     handoffs=[
#         copywriting_agent,
#         prompt_generation_agent,
#         image_generation_agent,
#     ],
# )

# # Make every specialist able to return control to triage
# for ag in (copywriting_agent, prompt_generation_agent, image_generation_agent):
#     if triage_agent not in ag.handoffs:
#         ag.handoffs.append(triage_agent)


# from agents import Agent, WebSearchTool
# from agents.extensions.handoff_prompt import prompt_with_handoff_instructions, RECOMMENDED_PROMPT_PREFIX
# # The save_image_locally tool is removed from this import as generate_ad_image now handles saving.
# from tools import (
#     generate_image_prompt,
#     generate_ad_image,
#     save_ad_copy_to_markdown,
#     AdContext,
# )
# from agents.items import MessageOutputItem, ReasoningItem, ToolCallOutputItem, ItemHelpers
# import os
# import dotenv
# dotenv.load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# # initial_agent = prompt_generation_test_agent

# --- Full Multi-Agent Setup ---
RECOMMENDED_SUBPROMPT_PREFIX = """
If anything is unclear, ask clarifying questions. If you need to think, yield a ReasoningItem(e.g. 'Thinking about the best ad copy...') before you start writing. Once you are done with your task, yield a MessageOutputItem('Done!') to indicate that you are done.
IMPORTANT: Never mention terms like ReasoningItem, ToolCallItem, MessageOutputItem, Reasoning, etc. in your response. They are for internal use only.
"""

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
        "1. Before calling `save_ad_copy_to_markdown`, yield a ReasoningItem.\n"
        "2. Call `save_ad_copy_to_markdown` with the three parts.\n"
        "3. As soon as the ad copy is saved, yield a MessageOutputItem.\n"
        "4. If you need clarification, yield MessageOutputItem('Could you clarify ...?').\n"
        "5. Hand off back to **Triage Agent**.\n"
        "Always stream ReasoningItem and MessageOutputItem in real time to keep the user engaged.\n"
    ),
    model="gpt-4o-mini",
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
        "1. Before calling `generate_image_prompt`, yield a ReasoningItem.\n"
        "2. Call `generate_image_prompt` with the ad concept.\n"
        "3. As soon as the prompt is ready, yield a MessageOutputItem.\n"
        "4. If you need clarification, yield a MessageOutputItem('Could you clarify ...?').\n"
        "5. Hand off back to **Triage Agent**.\n"
        "Always stream ReasoningItem and MessageOutputItem in real time to keep the user engaged.\n"
    ),
    model="gpt-4o-mini",
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
        "1. Before calling `generate_ad_image`, yield a ReasoningItem.\n"
        "2. Call `generate_ad_image` with the provided prompt.\n"
        "3. As soon as the image is ready, yield a MessageOutputItem.\n"
        "4. If you need clarification, yield a MessageOutputItem('Could you clarify ...?').\n"
        "5. Ask an open question like 'What would you like next?'\n"
        "6. Hand off back to **Triage Agent** once you have finished your task.\n"
        "Always stream ReasoningItem and MessageOutputItem in real time to keep the user engaged.\n"
        "IMPORTANT: DO NOT MENTION THE IMAGE PATH IN YOUR RESPONSE. IT WILL BE SAVED LOCALLY."
    ),
    model="gpt-4o-mini",
    tools=[generate_ad_image],
    handoffs=[],         # will be filled later
)

# -------------------------------------------------------------------
# TRIAGE AGENT
RECOMMENDED_PROMPT_PREFIX = """Your an ad creative director. You are responsible for overseeing the creation of an ad. You need to gather information from the copywriter to come up with an ad concept. From then on, you need to write a prompt that encapsulates the ad concept. Finally, you need to generate an image that captures the ad concept. You have a team working with you, so you need to delegate tasks to them. start by asking a question to the user to clarify the user's ad goals with a ReasoningItem to be streamed to the user.
Always stream ReasoningItem and MessageOutputItem in real time to keep the user engaged.

IMPORTANT: Never mention terms like ReasoningItem, ToolCallItem, MessageOutputItem, Reasoning, etc. in your response. They are for internal use only."""
# -------------------------------------------------------------------
triage_agent = Agent[AdContext](
    name="Ad Triage Agent",
    handoff_description="Routes user requests to the correct specialist.",
    instructions=(
        f"{RECOMMENDED_PROMPT_PREFIX}\n"
        "You are the conversation entry point.\n"
        "Start off by welcoming the user and by asking a question to clarify the user's ad goals with a ReasoningItem to be streamed to the user.\n"
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

# async def stream_events(result):
#     async for ev in result.stream_events():
#         if ev.type != "run_item_stream_event":
#             continue

#         item = ev.item

#         if isinstance(item, ReasoningItem):
#             reason = ItemHelpers.extract_last_content(item.raw_item).strip()
#             if reason:
#                 yield f"{reason}"  # Speak reasoning/progress

#         elif isinstance(item, MessageOutputItem):
#             msg = ItemHelpers.text_message_output(item).strip()
#             yield f"{msg}"  # Speak all user-facing messages

#         elif isinstance(item, ToolCallOutputItem):
#             # Optionally, summarize tool output for the user
#             summary = ItemHelpers.extract_last_content(item.raw_item).strip()
#             if summary:
#                 yield f"{summary}"

#         # Do not yield HandoffOutputItem unless you want to announce agent switches