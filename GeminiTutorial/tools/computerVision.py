import os
import google.generativeai as genai
from PIL import Image, ImageDraw, ImageFont, ImageColor
from pydantic import BaseModel, Field
from typing import List
import json
import re
import os
import dotenv

dotenv.load_dotenv()

# Set API key and configure
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

class BoundingBox(BaseModel):
    box_2d: List[int] = Field(description="Array of 4 numbers [y1, x1, y2, x2] representing normalized coordinates (0-1000)")
    label: str = Field(description="Description of the detected item")

class ImageAnalysis(BaseModel):
    boxes: List[BoundingBox] = Field(description="List of detected objects and their bounding boxes")

def parse_json(text: str) -> str:
    """Extract JSON from text, handling potential markdown or text wrapping"""
    match = re.search(r'\[.*\]', text, re.DOTALL)
    if match:
        return match.group()
    return text

def analyze_image_with_boxes(image_path: str, custom_prompt: str = None) -> tuple[Image.Image, ImageAnalysis]:
    """
    Analyzes an image and returns both the annotated image and structured data.
    
    Args:
        image_path (str): Path to the image file
        custom_prompt (str, optional): Custom prompt for analysis
        
    Returns:
        tuple: (annotated_image, structured_data)
    """
    # Load and resize image
    im = Image.open(image_path)
    im.thumbnail([640, 640], Image.Resampling.LANCZOS)
    
    # Default prompt if none provided
    if not custom_prompt:
        custom_prompt = """Analyze this image and identify key objects.
        Return a JSON array where each object has:
        - box_2d: array of 4 numbers [y1, x1, y2, x2] representing normalized coordinates (0-1000)
        - label: description of the item
        
        Example format:
        [
            {
                "box_2d": [100, 200, 300, 400],
                "label": "Object Description"
            }
        ]"""
    
    # Generate analysis
    model = genai.GenerativeModel('gemini-2.0-flash')
    response = model.generate_content([custom_prompt, im])
    
    # Parse response
    json_str = parse_json(response.text)
    boxes_data = json.loads(json_str)
    structured_data = ImageAnalysis(boxes=boxes_data)
    
    # Create annotated image
    annotated_image = plot_bounding_boxes(im, json_str)
    
    return annotated_image, structured_data

def plot_bounding_boxes(im: Image.Image, response_text: str) -> Image.Image:
    """
    Plots bounding boxes on an image with markers for each name.
    """
    # Create a copy of the image to draw on
    img = im.copy()
    width, height = img.size
    draw = ImageDraw.Draw(img)
    
    # Define colors
    colors = [
        'red', 'green', 'blue', 'yellow', 'orange', 'pink', 'purple',
        'brown', 'gray', 'beige', 'turquoise', 'cyan', 'magenta',
    ]

    # Use system font with fallback
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", 14)
    except:
        font = ImageFont.load_default()

    try:
        # Parse the JSON response
        json_str = parse_json(response_text)
        boxes = json.loads(json_str)

        # Iterate over the bounding boxes
        for i, box in enumerate(boxes):
            color = colors[i % len(colors)]
            
            # Get coordinates
            coords = box.get("box_2d", [])
            if len(coords) != 4:
                continue

            # Convert normalized coordinates to pixel coordinates
            y1, x1, y2, x2 = coords
            abs_x1 = int((x1 * width) / 1000)
            abs_y1 = int((y1 * height) / 1000)
            abs_x2 = int((x2 * width) / 1000)
            abs_y2 = int((y2 * height) / 1000)

            # Draw rectangle
            draw.rectangle(
                [(abs_x1, abs_y1), (abs_x2, abs_y2)],
                outline=color,
                width=3
            )

            # Add label
            if "label" in box:
                draw.text(
                    (abs_x1, abs_y1 - 20),
                    box["label"],
                    fill=color,
                    font=font
                )

    except Exception as e:
        print(f"Error processing response: {e}")
    
    return img

# Example usage
if __name__ == "__main__":
    image_path = "./GeminiTutorial/Spatial/cupcakes.jpg"
    
    try:
        # Example 1: Basic analysis
        annotated_image, analysis = analyze_image_with_boxes(image_path)
        annotated_image.show()  # Display the image
        print("\nDetected Objects:")
        for box in analysis.boxes:
            print(f"- {box.label}")
            
        # Example 2: Custom prompt for specific detection
        custom_prompt = """Analyze this image and identify specific objects of interest.
        Return a JSON array where each object has:
        - box_2d: array of 4 numbers [y1, x1, y2, x2] representing normalized coordinates (0-1000)
        - label: detailed description of the detected object
        """
        custom_image, custom_analysis = analyze_image_with_boxes(image_path, custom_prompt)
        custom_image.show()  # Display the image
        print("\nDetected Objects (Custom Analysis):")
        for box in custom_analysis.boxes:
            print(f"- {box.label}")
            
    except Exception as e:
        print(f"Error: {e}")

