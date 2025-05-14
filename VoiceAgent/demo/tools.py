import os
from agents import function_tool, RunContextWrapper
from openai import OpenAI, APIError
import openai
import base64 # Added for b64 decoding
import uuid   # Added for unique filenames
from pathlib import Path
import dotenv
from typing import Optional
from pydantic import BaseModel
# import requests # Ensure this is removed if no longer used
dotenv.load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# The search_news function has been removed as we are using the built-in WebSearchTool in agents.py

# Ensure an OpenAI client is initialized.
# It's often good practice to initialize it once, possibly outside the function
# or ensure it's passed in or accessed from a shared module.
# For simplicity here, we'll initialize it if not provided.
# Consider managing the API key via environment variables.
try:
    client = OpenAI() # Assumes OPENAI_API_KEY is set in environment
except Exception as e:
    print(f"CRITICAL: Failed to initialize OpenAI client: {e}. Image generation will fail.")
    client = None

class AdContext(BaseModel):
    ad_copy: str
    image_prompt: str
    # image_path: str

    # convenience constructor for a blank context
    @classmethod
    def empty(cls) -> "AdContext":
        return cls(ad_copy="", image_prompt="" 
                #    ,image_path=""
                   )

async def get_ad_context() -> AdContext:
    """
    Retrieves the current ad context from the user's request.
    """
    # Implement the logic to retrieve the ad context from the user's request
    # This is a placeholder implementation
    return AdContext(ad_copy="", image_prompt=""
                     # , image_path=""
                     )

@function_tool
def save_ad_copy_to_markdown(
    context: RunContextWrapper[AdContext],
    title: str,
    subtitle: str,
    paragraph: str,
) -> str:
    """
    Saves the provided ad copy (title, subtitle, paragraph) to a Markdown file.
    The filename will be derived from the title.
    Returns a message indicating success or failure.
    """
    try:
        # Persist in context so downstream agents can read it
        context.context.ad_copy = f"{title}\n{subtitle}\n{paragraph}"
        # Sanitize title for filename (simple example)
        safe_title = "".join(c if c.isalnum() or c in " _-" else "_" for c in title)[:50]
        if not safe_title:
            safe_title = "ad_copy" # Default filename if title is empty or all non-alphanum
        
        # Ensure the filename ends with .md
        filename_stem = safe_title
        filename = Path.cwd() / f"{filename_stem}.md"
        
        md_content = f"# {title}\n\n"
        if subtitle: # Only include subtitle if provided and not empty
            md_content += f"## {subtitle}\n\n"
        md_content += f"{paragraph}\n"
        
        print(f"[save_ad_copy_to_markdown_tool] Attempting to save to: {filename.resolve()}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(md_content)
        
        success_message = f"Ad copy successfully saved to {str(filename.resolve())}"
        print(f"[save_ad_copy_to_markdown_tool] {success_message}")
        return success_message
    except Exception as e:
        error_message = f"Error saving ad copy to Markdown: {str(e)}"
        print(f"[save_ad_copy_to_markdown_tool] ERROR: {error_message}")
        return error_message

@function_tool
def generate_image_prompt(
    context: RunContextWrapper[AdContext], full_ad_concept: str
) -> str:
    """Generate an image prompt for ad generation based on a full ad concept string."""
    print(f"[generate_image_prompt_tool] Received full_ad_concept: {full_ad_concept[:150]}...")
    # Simple prompt construction; can be made more sophisticated if needed
    # This version expects the input `full_ad_concept` to contain all necessary details.
    generated_prompt = f"Create an advertising image based on the following concept: '{full_ad_concept}'. Ensure the image is engaging, high-quality, and directly relevant to the core message. Avoid text in the image."
    print(f"[generate_image_prompt_tool] Generated image prompt: {generated_prompt[:150]}...")

    # Persist in context
    context.context.image_prompt = generated_prompt
    return generated_prompt

@function_tool
def generate_ad_image(
    context: RunContextWrapper[AdContext], image_prompt: str
) -> str:
    """
    Generates an ad image using OpenAI's gpt-image-1 model, expecting b64_json response format,
    saves it locally from the base64 encoded response, and returns the local file path.
    If gpt-image-1 does not support response_format="b64_json", this will likely error.
    """
    if not client:
        error_message = "OpenAI client is not initialized. Cannot generate image."
        print(f"❌ [generate_ad_image] {error_message}")
        return f"Error: ClientInitialization - {error_message}"

    print(f"🎨 [generate_ad_image] Attempting to generate image with 'gpt-image-1' and response_format='b64_json'. Prompt: {image_prompt[:100]}...")
    try:
        response = client.images.generate(
            model="gpt-image-1", 
            prompt=image_prompt,
            n=1,
            size="1024x1024", 
             # Using b64_json as per user's explicit request
        )

        if not response.data or not response.data[0].b64_json:
            error_message = "No image data (b64_json) received from OpenAI API."
            print(f"❌ [generate_ad_image] {error_message}")
            # Log details if available, especially if a URL is present unexpectedly
            if response.data and len(response.data) > 0:
                if hasattr(response.data[0], 'url') and response.data[0].url:
                    print(f"    WARNING: b64_json was not found, but a URL was present: {response.data[0].url}. This indicates an issue with gpt-image-1 supporting b64_json.")
                else:
                    print(f"    API Response Data[0]: {response.data[0]}")                    
            else:
                print(f"    API Response: {response}")
            return f"Error: NoB64JSONData - {error_message}"

        image_data_b64 = response.data[0].b64_json
        
        print("🖼️ [generate_ad_image] Image data received, decoding base64...")
        image_data_bytes = base64.b64decode(image_data_b64)

        save_dir = "generated_images"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"📁 [generate_ad_image] Created directory: {os.path.abspath(save_dir)}")

        image_filename = f"ad_image_{uuid.uuid4()}.png"
        image_path = os.path.join(save_dir, image_filename)
        absolute_image_path = os.path.abspath(image_path)

        # print(f"💾 [generate_ad_image] Saving image to: {absolute_image_path}")
        with open(absolute_image_path, "wb") as f:
            f.write(image_data_bytes)

        # success_message = f"Image successfully generated and saved to {absolute_image_path}"
        # context.context.image_path = absolute_image_path   # persist
        # print(f"✅ [generate_ad_image] {success_message}")
        return absolute_image_path

    except APIError as e:
        error_message = f"OpenAI API error during image generation: {e}"
        print(f"❌ [generate_ad_image] {error_message}")
        error_type = "APIError"
        if hasattr(e, 'status_code') and e.status_code:
            print(f"    Status Code: {e.status_code}")
            error_type = f"APIError_HTTP{e.status_code}"
        if hasattr(e, 'request_id'): 
            print(f"    Request ID: {e.request_id}")
        if hasattr(e, 'body') and e.body: 
             print(f"    Error Body: {e.body}")
        return f"Error: {error_type} - {str(e)}"
    except base64.B64DecodeError as e:
        error_message = f"Failed to decode base64 image data: {e}"
        print(f"❌ [generate_ad_image] {error_message}")
        return f"Error: B64DecodeError - {error_message}"
    except IOError as e:
        error_message = f"Failed to save image to disk: {e}"
        print(f"❌ [generate_ad_image] {error_message}")
        return f"Error: FileIOError - {error_message}"
    except Exception as e:
        error_message = f"An unexpected error occurred in generate_ad_image: {e.__class__.__name__} - {e}"
        print(f"❌ [generate_ad_image] {error_message}")
        return f"Error: Unexpected - {error_message}"

# Removed save_image_locally as its functionality is integrated into generate_ad_image
# def save_image_locally(image_data_b64: str, filename_prefix: str = "ad_image") -> str:
# ... (old implementation)

