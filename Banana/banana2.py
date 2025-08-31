# To run this code you need to install the following dependencies:
# pip install google-genai

import mimetypes
import os
import json
from typing import List, Optional
from pydantic import BaseModel
from google import genai
from google.genai import types


class ClothingItem(BaseModel):
    category: str
    description: str
    condition: str
    tags: List[str]
    size: Optional[str] = None
    material: Optional[str] = None


def analyze_clothing(client, clothing_image_data):
    """Analyzes a clothing image and returns structured data."""
    prompt = """Analyze this clothing item for a Vinted listing. Return only a JSON object with these exact keys:
- "category": clothing type (e.g. "T-shirt", "Jeans", "Dress")
- "description": brief, factual description (max 50 words)
- "condition": one of "New with tags", "Very good", "Good", "Satisfactory", "Has flaws"
- "tags": array of relevant tags (color, style, occasion, season)
- "size": visible size if any (or null)
- "material": fabric/material if visible (or null)

Be concise and factual. No markdown formatting."""
    
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=[
            types.Part.from_bytes(
                data=clothing_image_data,
                mime_type='image/jpeg',
            ),
            prompt,
        ]
    )
    
    try:
        # Clean the response text to remove markdown backticks if they exist
        clean_text = response.text.strip().replace('```json', '').replace('```', '').strip()
        data = json.loads(clean_text)
        # Validate with Pydantic model
        clothing_item = ClothingItem(**data)
        return clothing_item.dict()
    except (json.JSONDecodeError, AttributeError, Exception) as e:
        print(f"Error parsing JSON from Gemini response: {e}")
        print(f"Raw response: {response.text}")
        return None


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    with open("ImageCrocPrototype.jpeg", "rb") as image_file:
        reference_image_data = image_file.read()

    clothing_dir = "clothes/"
    clothing_files = [f for f in os.listdir(clothing_dir) if f.endswith(('.jpeg', '.jpg', '.png'))]
    all_clothing_data = []

    for clothing_file in clothing_files:
        clothing_path = os.path.join(clothing_dir, clothing_file)
        with open(clothing_path, "rb") as image_file:
            clothing_image_data = image_file.read()

        # Analyze the clothing item
        analysis_data = analyze_clothing(client, clothing_image_data)
        if analysis_data:
            all_clothing_data.append({
                "filename": clothing_file,
                "details": analysis_data
            })

        model = "gemini-2.5-flash-image-preview"
        contents = [
            types.Content(
                role="user",
                parts=[
                    types.Part.from_bytes(
                        mime_type="image/jpeg",
                        data=reference_image_data,
                    ),
                    types.Part.from_bytes(
                        mime_type="image/jpeg",
                        data=clothing_image_data,
                    ),
                                         types.Part.from_text(text="""Create a sharp, high-quality image with four quadrants showing the person from the first image wearing the exact clothing item from the second image. Requirements:

1. Each quadrant shows a different angle (front, back, left side, right side)
2. The clothing must match EXACTLY: same color, texture, fit, and all details from the product image
3. Sharp focus with close-up view to clearly showcase the clothing
4. Consistent lighting and background across all quadrants
5. The clothing should fit naturally and realistically on the person
6. Maintain the exact fabric appearance, stitching, logos, and design elements
7. Professional photo quality suitable for online clothing marketplace"""),
                ],
            ),
        ]
        generate_content_config = types.GenerateContentConfig(
            response_modalities=[
                "IMAGE",
                "TEXT",
            ],
        )

        file_index = 0
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=contents,
            config=generate_content_config,
        ):
            if (
                chunk.candidates is None
                or chunk.candidates[0].content is None
                or chunk.candidates[0].content.parts is None
            ):
                continue
            if chunk.candidates[0].content.parts[0].inline_data and chunk.candidates[0].content.parts[0].inline_data.data:
                file_name = f"output_{os.path.splitext(clothing_file)[0]}_{file_index}"
                file_index += 1
                inline_data = chunk.candidates[0].content.parts[0].inline_data
                data_buffer = inline_data.data
                file_extension = mimetypes.guess_extension(inline_data.mime_type)
                save_binary_file(f"{file_name}{file_extension}", data_buffer)
            else:
                print(chunk.text)

    print("\n--- Clothing Analysis Results ---")
    print(json.dumps(all_clothing_data, indent=2))


if __name__ == "__main__":
    generate()
