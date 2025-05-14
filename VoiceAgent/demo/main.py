import asyncio
import os
from pathlib import Path

import numpy as np
import sounddevice as sd
import traceback

# Imports for the core agent framework
from demo_pkg_agents import ( # Assuming your agents are in demo_pkg_agents.py
    # news_research_agent,
    copywriting_agent,
    # platform_adjustment_agent,
    # image_prompt_generation_agent,
    image_generation_agent,
    # AdWorkflow # Your custom workflow
)

from my_workflow import MyWorkflow

# Correct imports for the voice pipeline based on OpenAI Agents SDK documentation
from agents.voice import AudioInput, VoicePipeline

# Ensure OPENAI_API_KEY is loaded, e.g., via dotenv or environment
from dotenv import load_dotenv
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("🔴 OPENAI_API_KEY not found. Please set it in your .env file or environment.")
    exit()

# -------------------- Configuration --------------------
SAMPLE_RATE = 24_000  # 24 kHz mono – default for the OpenAI voice endpoints
CHANNELS = 1          # mono
RECORD_SECONDS = 5    # how long to record from microphone for each turn
TTS_MODEL_NAME = "tts-1"
TTS_VOICE_NAME = "alloy"

# Ensure we are running from this directory (so relative paths work)
script_dir = Path(__file__).parent.resolve()
if Path.cwd() != script_dir:
    print(f"Changing CWD from {Path.cwd()} to {script_dir}")
    os.chdir(script_dir)

# -------------------- Voice capture --------------------
async def record_audio_turn() -> AudioInput:
    """Record `RECORD_SECONDS` of audio for one conversational turn."""
    print(f"\n[MIC] Please speak for up to {RECORD_SECONDS} seconds. Recording... (Press Ctrl+C to exit)")
    # Small pause for user to prepare, or use an input prompt
    # input("Press Enter to start recording for this turn...") 
    try:
        recording = sd.rec(int(RECORD_SECONDS * SAMPLE_RATE),
                           samplerate=SAMPLE_RATE,
                           channels=CHANNELS,
                           dtype=np.int16)
        sd.wait()  # wait until the recording is finished
        print("[MIC] Recording finished for this turn. Processing your request...")
        mono_buffer = recording.flatten()
        return AudioInput(buffer=mono_buffer)
    except Exception as e:
        print(f"[MIC] Error during recording: {e}. Returning empty audio.")
        return AudioInput(buffer=np.array([], dtype=np.int16)) # Return empty audio on error

# -------------------- Main Conversational Loop --------------------
async def main_conversation_loop() -> None:
    print("Initializing Conversational Ad Agent with TTS...")
    
    workflow = MyWorkflow(on_start=lambda t: print(f"[STT] Transcribed: {t!r}"))
    pipeline = VoicePipeline(workflow=workflow)

    player = sd.OutputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
    player.start()
    print("[SYSTEM] Audio player started.")

    accumulated_text_for_tts = ""
    tts_active = False        # True while a chunk is being played
    should_play_audio = False # True only when the agent is asking a question

    try:
        while True:
            print("[SYSTEM] Ready for voice input. Press Enter to start recording, then Enter again to stop.")
            # Simple blocking input to start/stop recording phase
            input("           Press Enter to start...")
            print("[SYSTEM] Recording... Press Enter to stop.")
            
            audio_input_stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16)
            audio_input_stream.start()
            
            recorded_frames = []
            
            # Record until Enter is pressed again
            # This is a simplified way to handle recording stop.
            # For a real app, more robust silence detection or a GUI button would be better.
            def record_callback(indata, frames, time, status):
                if status:
                    print(f"[AUDIO_REC_STATUS] {status}")
                recorded_frames.append(indata.copy())

            # Re-assign audio_input_stream with the callback
            # This is a bit of a workaround because sd.InputStream doesn't allow changing callback after start
            # A better approach might involve managing the stream and callback attachment more carefully.
            # For now, we re-create it if this becomes an issue. Let's assume the first one works for one recording session.
            # This part of the audio recording loop might need refinement for continuous use.
            # The key is to capture audio into `recorded_frames`.

            with sd.InputStream(samplerate=SAMPLE_RATE, channels=CHANNELS, dtype=np.int16, callback=record_callback) as mic_stream_for_input:
                input() # Wait for Enter to stop recording
                mic_stream_for_input.stop()

            print(f"[SYSTEM] Recording stopped. Processing {len(recorded_frames)} frames.")

            if not recorded_frames:
                print("[SYSTEM] No audio recorded. Waiting for new input.")
                continue

            full_recording_np = np.concatenate(recorded_frames, axis=0)
            print(f"[SYSTEM] Full recording shape: {full_recording_np.shape}, dtype: {full_recording_np.dtype}")

            audio_input = AudioInput(buffer=full_recording_np)
            print("[SYSTEM] AudioInput created. Running pipeline...")

            result = await pipeline.run(audio_input)
            print("[SYSTEM] Pipeline run initiated. Streaming events...")

            async for event in result.stream():
                # --- DETAILED EVENT LOGGING ---
                print(f"[DEBUG_EVENT_TYPE] {event.type}")
                print(f"[DEBUG_EVENT_DATA] {vars(event)}\n")
                # --- END DETAILED EVENT LOGGING ---

                if event.type == "voice_stream_event_audio" and event.data is not None:
                    if should_play_audio:
                        print(f"[TTS_PLAYER] Playing audio chunk of size: {len(event.data)}")
                        player.write(event.data)
                        tts_active = True
                    else:
                        print("[TTS_PLAYER] -- Skipping non-question audio chunk")
                elif event.type == "voice_stream_event_text_delta" and event.text_delta:
                    print(f"[AGENT_TEXT_DELTA] '{event.text_delta}'")
                    accumulated_text_for_tts += event.text_delta

                    # Detect a question → allow the next audio chunks through
                    if "?" in event.text_delta.strip():
                        should_play_audio = True
                elif event.type == "voice_stream_event_lifecycle":
                    print(f"[LIFECYCLE] Event: {event.event}")
                    if event.event == "turn_started":
                        print("[SYSTEM] Agent turn started.")
                        accumulated_text_for_tts = ""
                        tts_active = False
                        should_play_audio = False   # reset every turn
                    elif event.event == "turn_ended":
                        if accumulated_text_for_tts:
                            print(f"[SYSTEM] Agent turn ended. Full text from agent for this turn: '{accumulated_text_for_tts}'")
                            # If we were to speak the whole turn at once, it would be here.
                            # But we are streaming chunk by chunk with voice_stream_event_audio.
                        else:
                            print("[SYSTEM] Agent turn ended. No text accumulated for TTS in this turn (might be tool calls only or no output).")
                        accumulated_text_for_tts = ""
                        should_play_audio = False
                        if tts_active: # If TTS was active in this turn, wait for it to finish
                            print("[SYSTEM] Waiting for TTS to finish for this turn...")
                            # sd.wait() # This might block too long if player is continuously fed.
                            # Better to let player drain naturally. Or use player.flush() if available.
                        tts_active = False
                elif event.type == "voice_stream_event_error":
                    print(f"[ERROR_EVENT] Code: {event.code}, Message: {event.message}")
                    # Potentially stop or reset pipeline here.
                else:
                    # Catch any other event types
                    print(f"[OTHER_EVENT] Type: {event.type}, Data: {vars(event)}")


            print("[SYSTEM] End of events for this input.")
            # Ensure any final audio is played.
            # sd.wait() # This could block if player is not properly managed.
            # Consider player.stop() and player.start() per interaction if needed.

    except KeyboardInterrupt:
        print("[SYSTEM] Keyboard interrupt received. Shutting down...")
    except Exception as e:
        print(f"[SYSTEM_CRITICAL_ERROR] An unexpected error occurred in main_conversation_loop: {e}")
        print(traceback.format_exc())
    finally:
        print("[SYSTEM] Cleaning up...")
        if 'player' in locals() and player is not None:
            print("[SYSTEM] Closing audio player...")
            player.stop()
            player.close()
        if 'audio_input_stream' in locals() and audio_input_stream is not None and not audio_input_stream.closed:
            audio_input_stream.stop()
            audio_input_stream.close()
        print("[SYSTEM] Conversational Ad Agent shut down.")

# Commenting out the test main() function to ensure main_conversation_loop is used.
# async def main():
#     print("🎙️ Voice Agent Demo Starting...")
#     try:
#         # Your existing workflow setup
#         # workflow = AdWorkflow(
#         #     news_agent=news_research_agent,
#         #     copy_agent=copywriting_agent,
#         #     platform_agent=platform_adjustment_agent,
#         #     img_prompt_agent=image_prompt_generation_agent,
#         #     img_gen_agent=image_generation_agent
#         # )
#         # pipeline = VoicePipeline(workflow=workflow) # If AdWorkflow is compatible
# 
#         # For now, let's try to run the example workflow structure if AdWorkflow isn't ready
#         # This uses SingleAgentVoiceWorkflow with a single agent to test the voice pipeline part.
#         # You'll need to adapt this to your multi-agent AdWorkflow.
#         # For simplicity, using image_generation_agent as a placeholder for a single agent.
#         # This is just to test if the VoicePipeline runs without the OpenAITTS import error.
#         from agents.voice import SingleAgentVoiceWorkflow # Import if using this example structure
#         from agents import Agent # Basic Agent for the example
# 
#         # Placeholder agent for testing the pipeline structure
#         test_agent = Agent(name="TestAgent", instructions="You are a helpful assistant.", model="gpt-4o-mini")
#         
#         # Using SingleAgentVoiceWorkflow for initial testing of the pipeline
#         # You will replace this with your AdWorkflow once it's confirmed to be compatible
#         # with how VoicePipeline expects a workflow.
#         pipeline = VoicePipeline(workflow=SingleAgentVoiceWorkflow(agent=test_agent))
# 
# 
#         print("🎤 Simulating audio input (3 seconds of silence)...")
#         # For simplicity, we'll just create 3 seconds of silence
#         # In reality, you'd get microphone data
#         sample_rate = 24000  # Standard sample rate for OpenAI TTS
#         duration_seconds = 3
#         buffer = np.zeros(sample_rate * duration_seconds, dtype=np.int16)
#         audio_input = AudioInput(buffer=buffer) # sample_rate might not be needed here based on previous fixes
# 
#         print("▶️ Running pipeline...")
#         # The .run() method might not take initial_input based on previous fixes.
#         # It takes the AudioInput directly.
#         result = await pipeline.run(audio_input) 
#         
#         print("🔊 Pipeline finished. Processing result...")
# 
#         # --- Handling the output ---
#         # The following is based on the SDK example for playing back audio.
#         # You'll need to adapt how you handle the final_output text
#         # and the audio stream.
# 
#         final_text_output = ""
#         audio_data_chunks = []
# 
#         player = sd.OutputStream(samplerate=sample_rate, channels=1, dtype=np.int16)
#         player.start()
#         print("🎧 Playing audio response...")
# 
#         async for event in result.stream():
#             if event.type == "workflow_event_text_delta":
#                 # print(f"Text delta: {event.data}", end="")
#                 final_text_output += event.data
#             elif event.type == "voice_stream_event_audio":
#                 # print(f"Audio data chunk received, size: {len(event.data)}")
#                 audio_data_chunks.append(event.data)
#                 player.write(event.data) # Play audio as it streams in
#             elif event.type == "workflow_event_finish":
#                 print(f"🏁 Workflow finished. Reason: {event.data.reason}")
#                 if event.data.output:
#                      final_text_output = event.data.output # Prefer final output if available
#             # else:
#                 # print(f"Received event: {event.type}")
# 
#         player.stop()
#         player.close()
#         
#         print(f"📝 Final Text Output from workflow: {final_text_output}")
# 
#         if not audio_data_chunks:
#             print("⚠️ No audio data was streamed back by the pipeline.")
#         else:
#             print("✅ Audio playback complete.")
#             # You could save the full audio if needed:
#             # full_audio_data = np.concatenate(audio_data_chunks)
#             # sd.write("output_audio.wav", full_audio_data, sample_rate)
#             # print("🎤 Full audio response saved to output_audio.wav")
# 
# 
#     except ImportError as e:
#         print(f"❌ ImportError: {e}")
#         print("   Ensure 'openai-agents[voice]' is installed and imports are correct.")
#         print(f"   PYTHONPATH: {os.getenv('PYTHONPATH')}")
#         print(f"   sys.path: {sys.path}")
#     except Exception as e:
#         print(f"❌ An error occurred: {e}")
#         print(traceback.format_exc())

if __name__ == "__main__":
    # Make sure set_tracing_disabled(True) is called if you don't want tracing
    # from agents import set_tracing_disabled
    # set_tracing_disabled(True) 
    asyncio.run(main_conversation_loop()) # Ensure main_conversation_loop is called 