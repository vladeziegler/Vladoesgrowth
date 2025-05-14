from __future__ import annotations

import random
from collections.abc import AsyncIterator
from typing import Callable

from agents import Agent, Runner, TResponseInputItem
from agents.voice import VoiceWorkflowBase
from agents.items import (
    ItemHelpers,
    ReasoningItem,
    MessageOutputItem,
    HandoffOutputItem,
)
from agents.result import RunResultStreaming  # for typing
from tools import save_ad_copy_to_markdown, generate_image_prompt, generate_ad_image, AdContext

from demo_pkg_agents import (
    copywriting_agent,
    prompt_generation_agent,
    image_generation_agent,
    triage_agent,
)

__all__ = ["MyWorkflow"]


def _should_speak(msg: str) -> bool:
    """Heuristic: speak only if message clearly requests more input."""
    msg = msg.strip()
    return (
        msg.endswith("?")
        or msg.lower().startswith(("could you", "would you", "can you", "please"))
        or "what would you like" in msg.lower()
    )


class MyWorkflow(VoiceWorkflowBase):
    """Workflow that chains our ad-generation agents.
    Supports multi-turn conversation by maintaining history.

    Flow (first turn):
    1. Copywriting agent —> hand-offs to → 2. Prompt Generation agent —> hand-offs to → 3. Image Generation agent.
    Subsequent turns will depend on user input and agent logic.

    The workflow keeps an *input_history* list that is passed to the runner each turn, so the
    LLM has full context. After each agent turn we update the history and remember the
    `last_agent` returned by `Runner` so the chain can continue next turn.
    """

    def __init__(self, on_start: Callable[[str], None] | None = None) -> None:
        super().__init__()
        self._input_history: list[TResponseInputItem] = []
        # Start with the copywriting agent for the first interaction,
        # or a more general conversational agent if the ad-gen is a one-off task.
        # For now, assumes the first interaction is always to create an ad.
        self._current_agent: Agent = triage_agent
        self._on_start = on_start or (lambda x: print(f"[MyWorkflow - on_start_stub] STT: {x}"))
        self._context = AdContext.empty()

    async def run(self, transcription: str) -> AsyncIterator[str]:
        """Run the agent chain for a single user utterance.
        Maintains conversation history across calls.

        The pipeline does STT and passes the transcription string here. We append it to
        the input history, run the current agent (which may hand-off internally) and
        stream its output back to the caller as chunks of text (TTS or console).
        """
        print(f"[MyWorkflow] run() called. Current agent: {self._current_agent.name if self._current_agent else 'None'}. Transcription: {transcription!r}")
        if not self._current_agent:
            print("[MyWorkflow] Error: _current_agent is not set. Cannot proceed.")
            yield "I'm sorry, there's an issue with my internal state. Please restart."
            return

        # Notify caller that STT finished and we are starting workflow run
        self._on_start(transcription)

        # Add current user message to the existing history
        self._input_history.append({"role": "user", "content": transcription})
        print(f"[MyWorkflow] Input history updated with user message. History length: {len(self._input_history)}")

        # ------------------------------------------------------
        #  ⏩  Low-latency: stream as the agent reasons / calls tools
        # ------------------------------------------------------
        print(f"[MyWorkflow] Calling Runner.run_streamed for agent: {self._current_agent.name}")
        result: RunResultStreaming = Runner.run_streamed(
            self._current_agent,
            self._input_history,
            context=self._context,
        )

        async for ev in result.stream_events():
            # ── We only care about *semantic* events (ignore raw token deltas)
            if ev.type != "run_item_stream_event":
                continue

            item = ev.item

            # 1️⃣  Reasoning – short "thinking" or progress snippets (these are spoken)
            if isinstance(item, ReasoningItem):
                reason = ItemHelpers.extract_last_content(item.raw_item).strip()
                if reason:
                    yield reason  # Speak reasoning/progress naturally

            # 2️⃣  Status after each hand-off (do not yield or speak)
            elif isinstance(item, HandoffOutputItem):
                continue  # Do not yield handoff status

            # 3️⃣  Actual user-facing messages: only yield if it's a progress update or action
            elif isinstance(item, MessageOutputItem):
                msg = ItemHelpers.text_message_output(item).strip()
                # Only speak if it's a progress/action update, not a question or info
                if not _should_speak(msg):
                    # Heuristic: treat as progress update if not a question
                    yield msg  # Speak progress/action
                # Otherwise, skip (do not yield clarifications/questions)

        # ── Run is done, update conversation state
        self._input_history = result.to_input_list()
        self._current_agent = result.last_agent
        print(f"[MyWorkflow] Turn complete. Next agent: {self._current_agent.name if self._current_agent else 'None'}") 