# filename: my_workflow.py
"""
Streaming workflow that feeds agents with full history every turn.
"""

from __future__ import annotations
import asyncio
from collections.abc import AsyncIterator
from typing import Callable

from agents import Agent, Runner, TResponseInputItem
from agents.voice import VoiceWorkflowBase
from agents.items import (
    ItemHelpers,
    ReasoningItem,
    MessageOutputItem,
    ToolCallOutputItem,
)
from agents.result import RunResultStreaming
from tools import AdContext
from demo_pkg_agents import triage_agent  # ← import from previous file

__all__ = ["MyWorkflow"]


class MyWorkflow(VoiceWorkflowBase):
    """
    Hands VoicePipeline transcriptions → runs the agent chain → yields bot text.
    """

    def __init__(self, on_start: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self._history: list[TResponseInputItem] = []
        self._current_agent: Agent = triage_agent
        self._context = AdContext.empty()
        self._on_start = on_start or (lambda x: None)

    # Called by VoicePipeline when VAD decides the user finished speaking
    async def run(self, transcription: str) -> AsyncIterator[str]:
        self._on_start(transcription)
        self._history.append({"role": "user", "content": transcription})

        # Run the active agent and stream items as they arrive
        result: RunResultStreaming = Runner.run_streamed(
            self._current_agent,
            self._history,
            context=self._context,
        )

        async for ev in result.stream_events():
            if ev.type != "run_item_stream_event":
                continue

            item = ev.item
            if isinstance(item, ReasoningItem):            # thinking updates
                txt = ItemHelpers.extract_last_content(item.raw_item).strip()
                if txt:
                    yield txt
            elif isinstance(item, MessageOutputItem):      # user-facing text
                txt = ItemHelpers.text_message_output(item).strip()
                if txt:
                    yield txt
            elif isinstance(item, ToolCallOutputItem):     # tool results
                summary = ItemHelpers.extract_last_content(item.raw_item).strip()
                if summary:
                    yield summary

        # Persist conversation state
        self._history = result.to_input_list()
        self._current_agent = result.last_agent

# from __future__ import annotations

# import random
# from collections.abc import AsyncIterator
# from typing import Callable

# from agents import Agent, Runner, TResponseInputItem
# from agents.voice import VoiceWorkflowBase
# from agents.items import (
#     ItemHelpers,
#     ReasoningItem,
#     MessageOutputItem,
#     HandoffOutputItem,
#     ToolCallItem,
#     ToolCallOutputItem,
# )
# from agents.result import RunResultStreaming  # for typing
# from tools import save_ad_copy_to_markdown, generate_image_prompt, generate_ad_image, AdContext

# from demo_pkg_agents import (
#     copywriting_agent,
#     prompt_generation_agent,
#     image_generation_agent,
#     triage_agent,
# )

# __all__ = ["MyWorkflow"]


# def _should_speak(msg: str) -> bool:
#     """Heuristic: speak only if message clearly requests more input."""
#     msg = msg.strip()
#     return (
#         msg.endswith("?")
#         or msg.lower().startswith(("could you", "would you", "can you", "please"))
#         or "what would you like" in msg.lower()
#     )


# # ENGAGING_TOOL_START = [
# #     "Let me get started on that for you.",
# #     "I'm working on it—hang tight!",
# #     "Let's make something great. Starting now!",
# #     "Give me a moment while I work my magic.",
# # ]

# # ENGAGING_REASONING = [
# #     "Thinking through the best approach...",
# #     "Let me consider the options.",
# #     "I'm brainstorming ideas for you.",
# #     "Analyzing your request to find the best solution.",
# # ]

# # ENGAGING_RESULT = [
# #     "Here's what I came up with!",
# #     "All done! Take a look:",
# #     "Finished! Here are the results:",
# #     "Here's the outcome:",
# # ]

# # ENGAGING_CLARIFICATION = [
# #     "Could you tell me a bit more?",
# #     "I need a little more info to get this just right.",
# #     "Can you clarify your preferences?",
# #     "What would you like to focus on next?",
# # ]


# class MyWorkflow(VoiceWorkflowBase):
#     """Workflow that chains our ad-generation agents.
#     Supports multi-turn conversation by maintaining history.

#     Flow (first turn):
#     1. Copywriting agent —> hand-offs to → 2. Prompt Generation agent —> hand-offs to → 3. Image Generation agent.
#     Subsequent turns will depend on user input and agent logic.

#     The workflow keeps an *input_history* list that is passed to the runner each turn, so the
#     LLM has full context. After each agent turn we update the history and remember the
#     `last_agent` returned by `Runner` so the chain can continue next turn.
#     """

#     def __init__(self, on_start: Callable[[str], None] | None = None) -> None:
#         super().__init__()
#         self._input_history: list[TResponseInputItem] = []
#         self._current_agent: Agent = triage_agent
#         self._on_start = on_start or (lambda x: print(f"[MyWorkflow - on_start_stub] STT: {x}"))
#         self._context = AdContext.empty()
#         self._first_turn = True

#     async def run(self, transcription: str) -> AsyncIterator[str]:
#         if self._first_turn and not self._input_history:
#             self._first_turn = False
#             yield "Hi! What are your goals or intentions for this ad? Tell me what you want to achieve, and I'll help you every step of the way."
#             return

#         print(f"[MyWorkflow] run() called. Current agent: {self._current_agent.name if self._current_agent else 'None'}. Transcription: {transcription!r}")
#         if not self._current_agent:
#             print("[MyWorkflow] Error: _current_agent is not set. Cannot proceed.")
#             yield "I'm sorry, there's an issue with my internal state. Please restart."
#             return

#         # Notify caller that STT finished and we are starting workflow run
#         self._on_start(transcription)

#         # Add current user message to the existing history
#         self._input_history.append({"role": "user", "content": transcription})
#         print(f"[MyWorkflow] Input history updated with user message. History length: {len(self._input_history)}")

#         # ------------------------------------------------------
#         #  ⏩  Low-latency: stream as the agent reasons / calls tools
#         # ------------------------------------------------------
#         print(f"[MyWorkflow] Calling Runner.run_streamed for agent: {self._current_agent.name}")
#         result: RunResultStreaming = Runner.run_streamed(
#             self._current_agent,
#             self._input_history,
#             context=self._context,
#         )

#         async for ev in result.stream_events():
#             if ev.type != "run_item_stream_event":
#                 continue

#             item = ev.item

#             # 1️⃣ ReasoningItem (thinking/progress)
#             if isinstance(item, ReasoningItem):
#                 reason = ItemHelpers.extract_last_content(item.raw_item).strip()
#                 if reason:
#                     yield f"{reason}"

#             # # 2️⃣ ToolCallItem (tool about to run)
#             # elif isinstance(item, ToolCallItem):
#             #     tool_name = getattr(item.raw_item, "name", "a tool")
#             #     yield f"{random.choice(ENGAGING_TOOL_START)} (Running {tool_name})"

#             # 3️⃣ MessageOutputItem (results, clarifications, confirmations)
#             elif isinstance(item, MessageOutputItem):
#                 msg = ItemHelpers.text_message_output(item).strip()
#                 if not msg:
#                     continue
#                 # Heuristic: is this a question/clarification?
#                 if msg.endswith("?") or "clarify" in msg.lower():
#                     yield f"{msg}"
#                 else:
#                     yield f"{msg}"

#             # 4️⃣ ToolCallOutputItem (tool results summary)
#             elif isinstance(item, ToolCallOutputItem):
#                 summary = ItemHelpers.extract_last_content(item.raw_item).strip()
#                 if summary:
#                     yield f"Done! {summary}"

#             # Do not yield HandoffOutputItem or technical status

#         # ── Run is done, update conversation state
#         self._input_history = result.to_input_list()
#         self._current_agent = result.last_agent
#         print(f"[MyWorkflow] Turn complete. Next agent: {self._current_agent.name if self._current_agent else 'None'}") 