from agents import Agent, WebSearchTool
from agents.extensions.handoff_prompt import prompt_with_handoff_instructions
# The save_image_locally tool is removed from this import as generate_ad_image now handles saving.
from tools import generate_image_prompt, generate_ad_image, save_ad_copy_to_markdown
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

# Agent 3: Ad Image Generator (Final Agent in the ad-creation chain for a turn)
image_generation_agent = Agent(
    name="Ad Image Generator",
    instructions=prompt_with_handoff_instructions(
        "You are an AI image generation specialist. "
        "INPUTS YOU RECEIVE: You will receive the image prompt string AND a status message about Markdown saving from the 'Image Prompt Generator'."
        "YOUR TASK: Use your 'generate_ad_image' tool with the received image prompt. This tool will save the image locally and return a message including its file path. "
        "YOUR FINAL RESPONSE TO THE USER: After the image is generated and saved, your response to the user MUST clearly state: "
        "  1. The success message (including the image file path) from the 'generate_ad_image' tool. "
        "  2. The image prompt string you received and used. "
        "  3. The status message about Markdown file saving. "
        "After presenting these three pieces of information, you MUST ask an open-ended question to continue the conversation, for example: 'What would you like to do next?' or 'Is there anything else I can help you with today?' "
        "Do NOT attempt any handoffs yourself unless the user explicitly asks for a capability that requires a different specialized agent you know about."
    ),
    model="gpt-4o",
    tools=[generate_ad_image]
)

# Agent 2: Image Prompt Generator
prompt_generation_agent = Agent(
    name="Image Prompt Generator",
    handoff_description="Generates a detailed image prompt based on ad copy and the markdown save status, then passes the prompt and save status to the Ad Image Generator.",
    instructions=prompt_with_handoff_instructions(
        "You are an AI image prompt engineer. "
        "INPUTS YOU RECEIVE: You will receive from the 'Ad Copywriter': "
        "  1. The ad copy (title, subtitle, paragraph) OR a clarifying question from the Copywriter if it couldn't proceed. "
        "  2. A status message about whether the ad copy was saved as a Markdown file (this may be absent if the Copywriter asked a question). "
        "YOUR TASK: "
        "  - If you received a clarifying question from the Copywriter, your ONLY action is to repeat that exact question to the user. Do not use tools or attempt to generate a prompt. Wait for the user's answer in the next turn. "
        "  - If you received ad copy: Based on the ad copy (title, subtitle, paragraph), create a detailed image prompt. "
        "    This prompt should synthesize the ad copy into a coherent visual concept. "
        "    IMPORTANT: Your generated image prompt should include details like: text to add to the image (complementary to the ad copy, not a duplicate), a description of what should be in the image, the desired style of the image, and any preferred font or style for the text in the image. "
        "    After crafting this detailed prompt string, you MUST call your 'generate_image_prompt' tool, passing this crafted prompt string as the 'full_ad_concept' argument. "
        "YOUR OUTPUT FOR NEXT AGENT (only if you generated a prompt): After your 'generate_image_prompt' tool returns its result, your entire response, which will be handed off to the 'Ad Image Generator', MUST contain: "
        "  - The image prompt string returned by your 'generate_image_prompt' tool. "
        "  - The status message about the Markdown file saving that you received from the 'Ad Copywriter'. "
        "Then, **immediately hand-off to the 'Ad Image Generator'.**"
    ),
    model="gpt-4o",
    tools=[generate_image_prompt], 
    handoffs=[image_generation_agent]
)

# Agent 1: Ad Copywriter (Initial Agent for ad creation flow - now interactive)
copywriting_agent = Agent(
    name="Ad Copywriter",
    handoff_description="Creates ad copy (possibly after asking clarifying questions), saves it to Markdown, then passes copy and save status to the Image Prompt Generator.",
    instructions=prompt_with_handoff_instructions(
        "You are an expert ad copywriter. Your goal is to generate compelling ad copy (Title, Subtitle, Paragraph)."
        "CONVERSATION HISTORY: You have access to the full conversation history. Review it carefully. "
        "YOUR TASK - DECISION POINT:"
        "1. ASSESS USER INPUT: Look at the user's most recent request and any previous answers they provided to your questions. "
        "2. DO YOU HAVE ENOUGH INFO?: Based on this, decide if you have ALL the necessary details to write effective ad copy (e.g., product/service, target audience, key message/unique selling points, desired tone)."
        "YOUR ACTIONS - BASED ON DECISION:"
        "  A. IF NOT ENOUGH INFO: Your *entire response for this turn* MUST be a polite and specific question to the user to obtain ONLY the missing information. Phrase it clearly. Example: 'To write the best ad, could you please tell me more about [specific missing detail e.g., the target audience]?' Do NOT generate any ad copy or call any tools if you are asking a question. You will get the answer in the next turn. "
        "  B. IF SUFFICIENT INFO: Proceed to: "
        "     i. Create compelling ad copy: a catchy Title, an engaging Subtitle, and a persuasive Paragraph. "
        "     ii. After crafting the copy, you MUST call the 'save_ad_copy_to_markdown' tool. Provide the 'title', 'subtitle', and 'paragraph' you created as distinct arguments to this tool. "
        "     iii. YOUR OUTPUT FOR NEXT AGENT (after tool call): Your entire response, which will be handed off to the 'Image Prompt Generator', MUST contain TWO distinct pieces of information: "
        "         - The ad copy (title, subtitle, and paragraph) that you generated. "
        "         - The result message (a string indicating success or failure) returned by the 'save_ad_copy_to_markdown' tool. "
        "     iv. Then, **immediately hand-off to the 'Image Prompt Generator'.**"
    ),
    model="gpt-4o",
    tools=[save_ad_copy_to_markdown, WebSearchTool()], 
    handoffs=[prompt_generation_agent]
)

initial_agent = copywriting_agent # This is the entry point for the ad creation flow.
# If the conversation continues, MyWorkflow._current_agent will track the active agent.