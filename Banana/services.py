import os
import json
import uuid
import mimetypes
import requests
import http.client
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from google import genai
from google.genai import types
from models import ClothingItem

# Load environment variables from .env file
load_dotenv()


class GeminiService:
    def __init__(self):
        self.client = genai.Client(
            api_key=os.environ.get("GEMINI_API_KEY"),
        )

    async def analyze_clothing(self, clothing_image_data: bytes) -> Optional[Dict[str, Any]]:
        """Analyzes a clothing image and returns structured data."""
        prompt = """Analyze this clothing item for a Vinted listing. Return only a JSON object with these exact keys:
- "category": clothing type (e.g. "T-shirt", "Jeans", "Dress")
- "description": brief, factual description (max 50 words)
- "condition": one of "New with tags", "Very good", "Good", "Satisfactory", "Has flaws"
- "tags": array of relevant tags (color, style, occasion, season)
- "size": visible size if any (or null)
- "material": fabric/material if visible (or null)

Be concise and factual. No markdown formatting."""
        
        try:
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(
                        data=clothing_image_data,
                        mime_type='image/jpeg',
                    ),
                    prompt,
                ]
            )
            
            # Clean the response text to remove markdown backticks if they exist
            clean_text = response.text.strip().replace('```json', '').replace('```', '').strip()
            data = json.loads(clean_text)
            
            # Validate with Pydantic model
            clothing_item = ClothingItem(**data)
            return clothing_item.dict()
            
        except Exception as e:
            print(f"Error analyzing clothing: {e}")
            return None

    async def generate_quadrant_image(self, reference_image_data: bytes, clothing_image_data: bytes) -> Optional[bytes]:
        """Generates a quadrant image showing person wearing clothing item."""
        try:
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
                response_modalities=["IMAGE", "TEXT"],
            )

            for chunk in self.client.models.generate_content_stream(
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
                    inline_data = chunk.candidates[0].content.parts[0].inline_data
                    return inline_data.data
                    
        except Exception as e:
            print(f"Error generating quadrant image: {e}")
            return None


class FileService:
    def __init__(self):
        # Use absolute paths as specified by user
        base_path = "/Users/vladimirdeziegler/banana"
        self.upload_dirs = {
            'reference': f'{base_path}/uploads/reference',
            'clothing': f'{base_path}/uploads/clothing',
            'generated': f'{base_path}/uploads/generated'
        }
        self._ensure_directories()

    def _ensure_directories(self):
        """Create upload directories if they don't exist."""
        for dir_path in self.upload_dirs.values():
            os.makedirs(dir_path, exist_ok=True)

    def save_uploaded_file(self, file_data: bytes, original_filename: str, file_type: str) -> str:
        """Save uploaded file and return unique file ID."""
        file_id = str(uuid.uuid4())
        file_extension = os.path.splitext(original_filename)[1]
        
        if file_type not in self.upload_dirs:
            raise ValueError(f"Invalid file type: {file_type}")
            
        file_path = os.path.join(
            self.upload_dirs[file_type],
            f"{file_id}{file_extension}"
        )
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        return file_id

    def get_file_path(self, file_id: str, file_type: str) -> Optional[str]:
        """Get full file path from file ID."""
        if file_type not in self.upload_dirs:
            return None
            
        dir_path = self.upload_dirs[file_type]
        for filename in os.listdir(dir_path):
            if filename.startswith(file_id):
                return os.path.join(dir_path, filename)
        return None

    def read_file(self, file_id: str, file_type: str) -> Optional[bytes]:
        """Read file content by file ID."""
        file_path = self.get_file_path(file_id, file_type)
        if not file_path or not os.path.exists(file_path):
            return None
            
        with open(file_path, 'rb') as f:
            return f.read()

    def save_generated_file(self, file_data: bytes, filename: str) -> str:
        """Save generated file and return file ID."""
        file_id = str(uuid.uuid4())
        file_extension = mimetypes.guess_extension('image/png') or '.png'
        
        file_path = os.path.join(
            self.upload_dirs['generated'],
            f"{file_id}_{filename}{file_extension}"
        )
        
        with open(file_path, 'wb') as f:
            f.write(file_data)
            
        return file_id

    def get_file_path(self, file_id: str, file_type: str) -> Optional[str]:
        """Get the full file path for a given file_id and type."""
        if file_type not in self.upload_dirs:
            return None
            
        dir_path = self.upload_dirs[file_type]
        if not os.path.exists(dir_path):
            return None
            
        # Look for any file that starts with the file_id
        for filename in os.listdir(dir_path):
            if filename.startswith(file_id):
                return os.path.join(dir_path, filename)
        
        return None

    def cleanup_files(self, file_ids: List[str]):
        """Clean up temporary files."""
        for file_type in self.upload_dirs:
            dir_path = self.upload_dirs[file_type]
            if not os.path.exists(dir_path):
                continue
                
            for filename in os.listdir(dir_path):
                file_id = filename.split('_')[0]
                if file_id in file_ids:
                    file_path = os.path.join(dir_path, filename)
                    try:
                        os.remove(file_path)
                    except OSError:
                        pass  # File already deleted or permission error


class ReverseSearchService:
    def __init__(self):
        self.serper_api_key = os.environ.get("SERPER_API_KEY")
        self.imgbb_api_key = os.environ.get("IMGBB_API_KEY", "ce9c5f4c7ea3124bdb4987f210f9dbf9")  # Default API key
        if not self.serper_api_key:
            print("Warning: SERPER_API_KEY not found in environment variables")
        if not self.imgbb_api_key:
            print("Warning: IMGBB_API_KEY not found in environment variables")

    def upload_image_to_imgbb(self, file_path: str) -> Optional[str]:
        """Upload image to ImgBB and return URL"""
        try:
            with open(file_path, 'rb') as file:
                files = {'image': file}
                
                # ImgBB endpoint with API key and expiration
                url = f'https://api.imgbb.com/1/upload?expiration=600&key={self.imgbb_api_key}'
                
                response = requests.post(url, files=files)
            
            if response.status_code == 200:
                result = response.json()
                return result['data']['url']
            else:
                print(f"ImgBB upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return None
        except Exception as e:
            print(f"Error uploading to ImgBB: {e}")
            return None

    def reverse_image_search(self, image_url: str) -> Optional[Dict[str, Any]]:
        """Use Serper API for reverse image search"""
        if not self.serper_api_key:
            return None
            
        try:
            conn = http.client.HTTPSConnection("google.serper.dev")
            
            payload = json.dumps({
                "url": image_url
            })
            
            headers = {
                'X-API-KEY': self.serper_api_key,
                'Content-Type': 'application/json'
            }
            
            conn.request("POST", "/lens", payload, headers)
            res = conn.getresponse()
            data = res.read()
            return json.loads(data.decode("utf-8"))
        except Exception as e:
            print(f"Error performing reverse image search: {e}")
            return None

    def search_similar_items(self, file_path: str) -> Optional[List[Dict[str, str]]]:
        """Complete workflow: upload image and search for similar items"""
        print(f"Starting reverse search for file: {file_path}")
        
        # Step 1: Upload image to ImgBB
        image_url = self.upload_image_to_imgbb(file_path)
        if not image_url:
            print("Failed to upload image to ImgBB")
            return None
        
        print(f"Image uploaded successfully: {image_url}")

        # Step 2: Reverse image search
        search_results = self.reverse_image_search(image_url)
        if not search_results:
            print("Reverse image search returned no results")
            return None
            
        if 'organic' not in search_results:
            print(f"No organic results found. Available keys: {list(search_results.keys())}")
            return None

        # Step 3: Extract top 3 results
        organic_results = search_results.get('organic', [])
        print(f"Found {len(organic_results)} organic results")
        
        # We might need more than 3 results if some have invalid images
        max_results_to_process = min(len(organic_results), 10)  # Process up to 10 to find 3 good ones
        
        # Debug: Print the first result to see what fields are available
        if organic_results:
            print(f"Sample result keys: {list(organic_results[0].keys())}")
            print(f"Sample result: {organic_results[0]}")
        
        similar_items = []
        
        for result in organic_results[:max_results_to_process]:  # Process more results to find valid images
            # Try multiple possible image field names
            primary_image = result.get('imageUrl', '')
            thumbnail_image = result.get('thumbnailUrl', '')
            fallback_image = result.get('image_url', '') or result.get('image', '')
            
            # For social media sources, prioritize thumbnails over main images
            # as they're more likely to be accessible
            source = result.get('source', '').lower()
            if any(social in source for social in ['instagram', 'twitter', 'facebook', 'tiktok']):
                # Swap priority for social media sources
                primary_image, thumbnail_image = thumbnail_image, primary_image
            
            # Filter out problematic URLs (Instagram crawler, etc.)
            def is_valid_image_url(url):
                if not url:
                    return False
                
                # Option to bypass filtering (set to True to allow all URLs)
                bypass_filtering = os.environ.get("BYPASS_IMAGE_FILTERING", "false").lower() == "true"
                if bypass_filtering:
                    print(f"  Bypassing filter for: {url}")
                    return True
                
                # Filter out Instagram crawler URLs and other problematic sources
                blocked_patterns = [
                    'lookaside.instagram.com',
                    'crawler',
                    'widget',
                    'seo/google_widget',
                    'googleusercontent.com/proxy',  # Google proxy images
                    'google.com/imgres'  # Google image result URLs
                ]
                return not any(pattern in url.lower() for pattern in blocked_patterns)
            
            # Choose the best available image
            image_url = ''
            candidates = [primary_image, thumbnail_image, fallback_image]
            for i, candidate in enumerate(candidates):
                if candidate:
                    if is_valid_image_url(candidate):
                        image_url = candidate
                        print(f"  Selected image URL {i+1}: {candidate}")
                        break
                    else:
                        print(f"  Filtered out URL {i+1}: {candidate} (blocked pattern)")
            
            if not image_url and any(candidates):
                print(f"  No valid images found for {result.get('title', 'Unknown')}, skipping this result")
                continue  # Skip results with no valid images
            
            # Only add results that have valid images OR no candidates at all (text-only results)
            if image_url or not any(candidates):
                item = {
                    'title': result.get('title', 'Unknown Title'),
                    'link': result.get('link', ''),
                    'imageUrl': image_url,
                    'source': result.get('source', 'Unknown Source')
                }
                similar_items.append(item)
                print(f"Item {len(similar_items)}: {item['title']} - Image: {item['imageUrl'] or 'No image'}")
                
                # Stop once we have 3 good results
                if len(similar_items) >= 3:
                    break
        
        print(f"Returning {len(similar_items)} similar items")
        return similar_items


# Global service instances
gemini_service = GeminiService()
file_service = FileService()
reverse_search_service = ReverseSearchService()
