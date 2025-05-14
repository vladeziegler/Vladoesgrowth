# main_voice_agent.py
"""
Push-to-talk voice loop with OpenAI Agents SDK  – API-correct version
• records 5-second turns from the microphone
• sends each turn to VoicePipeline (Whisper-1  →  LLM  →  TTS-1 ‘echo’)
• streams the assistant’s PCM16 audio back through a sounddevice player
"""

import asyncio, os, traceback
from pathlib import Path

import numpy as np
import sounddevice as sd
from dotenv import load_dotenv

from agents.voice import AudioInput, VoicePipeline
from agents.voice.pipeline_config import VoicePipelineConfig          # ✅ correct import
from agents.voice.model import TTSModelSettings                       # ✅ holds the voice name

from my_workflow import MyWorkflow

# ── constants ──────────────────────────────────────────────────────────
SAMPLE_RATE   = 24_000
CHANNELS      = 1
RECORD_SEC    = 5                 # push-to-talk length per user turn
VOICE_NAME    = "echo"            # any of: alloy, ash, coral, echo, fable, onyx, nova, sage, shimmer

# ── env check ─────────────────────────────────────────────────────────
load_dotenv()
if not os.getenv("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY missing – add it to your .env")

# ── helper: record one turn from the mic ──────────────────────────────
def record_turn() -> np.ndarray:
    print(f"[MIC] Speak now… ({RECORD_SEC}s)")
    buf = sd.rec(int(RECORD_SEC * SAMPLE_RATE),
                 samplerate=SAMPLE_RATE,
                 channels=CHANNELS,
                 dtype=np.int16)
    sd.wait()
    print("[MIC] …got it.")
    return buf.flatten()

# ── main async loop ───────────────────────────────────────────────────
async def main() -> None:
    # VoicePipeline expects a config object, not a nested Config class
    pipeline = VoicePipeline(
        workflow=MyWorkflow(on_start=lambda t: print(f"[STT] {t!r}")),
        stt_model="whisper-1",
        tts_model="tts-1",
        config=VoicePipelineConfig(
            tts_settings=TTSModelSettings(voice=VOICE_NAME)  # ✅ choose voice here
        ),
    )  # VoicePipeline.__init__ spec :contentReference[oaicite:0]{index=0}  – VoicePipelineConfig :contentReference[oaicite:1]{index=1}  – TTS voices enum :contentReference[oaicite:2]{index=2}

    player = sd.OutputStream(samplerate=SAMPLE_RATE,
                             channels=CHANNELS,
                             dtype=np.int16)
    player.start()

    try:
        while True:
            # 1. capture one user turn
            pcm = record_turn()
            audio_input = AudioInput(buffer=pcm)

            # 2. run the pipeline
            result = await pipeline.run(audio_input)

            # 3. play streaming TTS chunks as they arrive
            async for event in result.stream():
                if event.type == "voice_stream_event_audio":
                    player.write(event.data)
                elif event.type == "voice_stream_event_error":
                    print(f"[ERROR] {event.code}: {event.message}")
    except KeyboardInterrupt:
        print("⏹  Stopped by user.")
    except Exception as exc:
        print("‼️  Fatal error:", exc)
        traceback.print_exc()
    finally:
        player.stop(); player.close()

if __name__ == "__main__":
    asyncio.run(main())


# import asyncio
# import os
# from pathlib import Path

# import numpy as np
# import sounddevice as sd
# import traceback
# from my_workflow import MyWorkflow
# # Correct imports for the voice pipeline based on OpenAI Agents SDK documentation
# from agents.voice import AudioInput, VoicePipeline

# # Ensure OPENAI_API_KEY is loaded, e.g., via dotenv or environment
# from dotenv import load_dotenv
# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# if not OPENAI_API_KEY:
#     print("🔴 OPENAI_API_KEY not found. Please set it in your .env file or environment.")
#     exit()

# # -------------------- Configuration --------------------
# SAMPLE_RATE = 24_000  # 24 kHz mono – default for the OpenAI voice endpoints
# CHANNELS = 1          # mono
# RECORD_SECONDS = 5    # how long to record from microphone for each turn
# TTS_MODEL_NAME = "tts-1"
# TTS_VOICE_NAME = "echo"

# # Ensure we are running from this directory (so relative paths work)
# script_dir = Path(__file__).parent.resolve()
# if Path.cwd() != script_dir:
#     print(f"Changing CWD from {Path.cwd()} to {script_dir}")
#     os.chdir(script_dir)

# # -------------------- Voice capture --------------------
# async def record_audio_turn() -> AudioInput:
#     """Record `RECORD_SECONDS` of audio for one conversational turn."""
#     print(f"\n[MIC] Please speak for up to {RECORD_SECONDS} seconds. Recording... (Press Ctrl+C to exit)")
#     # Small pause for user to prepare, or use an input prompt
#     # input("Press Enter to start recording for this turn...") 
#     try:
#         recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE),
#                            samplerate=SAMPLE_RATE,
#                            channels=CHANNELS,
#                            dtype=np.int16)
#         sd.wait()  # wait until the recording is finished
#         print("[MIC] Recording finished for this turn. Processing your request...")
#         mono_buffer = recording.flatten()
#         return AudioInput(buffer=mono_buffer)
#     except Exception as e:
#         print(f"[MIC] Error during recording: {e}. Returning empty audio.")
#         return AudioInput(buffer=np.array([], dtype=np.int16)) # Return empty audio on error

# # -------------------- Main Conversational Loop --------------------
# async def main_conversation_loop() -> None:
#     print("Initializing Conversational Ad Agent with TTS...")
    
#     workflow = MyWorkflow(on_start=lambda t: print(f"[STT] Transcribed: {t!r}"))
#     pipeline = VoicePipeline(workflow=workflow)

#     player = sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
#     player.start()
#     print("[SYSTEM] Audio player started.")

#     tts_active = False

#     try:
#         while True:
#             # Prompt user and record audio
#             print("[SYSTEM] You can speak now. What would you like to do next?")
#             print("[SYSTEM] Recording for your turn...")
#             recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE),
#                                samplerate=SAMPLE_RATE,
#                                channels=CHANNELS,
#                                dtype=np.int16)
#             sd.wait()
#             print("[SYSTEM] Recording finished for this turn. Processing your request...")
#             mono_buffer = recording.flatten()
#             audio_input = AudioInput(buffer=mono_buffer)
#             print("[SYSTEM] AudioInput created. Running pipeline...")

#             result = await pipeline.run(audio_input)
#             print("[SYSTEM] Pipeline run initiated. Streaming events...")

#             async for event in result.stream():
#                 print(f"[DEBUG_EVENT_TYPE] {event.type}")
#                 print(f"[DEBUG_EVENT_DATA] {vars(event)}\n")

#                 if event.type == "voice_stream_event_audio" and event.data is not None:
#                     if len(event.data) > 500:
#                         player.write(event.data)
#                         tts_active = True
#                 elif event.type == "voice_stream_event_lifecycle":
#                     print(f"[LIFECYCLE] Event: {event.event}")
#                     if event.event == "turn_started":
#                         print("[SYSTEM] Agent turn started.")
#                         tts_active = False
#                     elif event.event == "turn_ended":
#                         if tts_active:
#                             print("[SYSTEM] Waiting for TTS to finish for this turn...")
#                         tts_active = False
#                 elif event.type == "voice_stream_event_error":
#                     print(f"[ERROR_EVENT] Code: {event.code}, Message: {event.message}")
#                 else:
#                     print(f"[OTHER_EVENT] Type: {event.type}, Data: {vars(event)}")

#             print("[SYSTEM] End of events for this input.")

#     except KeyboardInterrupt:
#         print("[SYSTEM] Keyboard interrupt received. Shutting down...")
#     except Exception as e:
#         print(f"[SYSTEM_CRITICAL_ERROR] An unexpected error occurred in main_conversation_loop: {e}")
#         print(traceback.format_exc())
#     finally:
#         print("[SYSTEM] Cleaning up...")
#         if 'player' in locals() and player is not None:
#             print("[SYSTEM] Closing audio player...")
#             player.stop()
#             player.close()
#         print("[SYSTEM] Conversational Ad Agent shut down.")


# if __name__ == "__main__":
#     # Make sure set_tracing_disabled(True) is called if you don't want tracing
#     # from agents import set_tracing_disabled
#     # set_tracing_disabled(True) 
#     asyncio.run(main_conversation_loop()) # Ensure main_conversation_loop is called 