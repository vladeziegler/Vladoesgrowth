#!/usr/bin/env python
import os
import dotenv
dotenv.load_dotenv()
from typing import Optional, Union
import sys
import json
import streamlit as st

from pydantic import BaseModel, Field
from typing import List, Optional

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
from crew_youtube_simple import YoutubeCrew

class ValueObject(BaseModel):
    name: str = Field(
        ..., 
        description="The name of the value, e.g., 'perseverance'"
    )
    origin: str = Field(
        ..., 
        description="The origin or development of the value, e.g., 'Developed this trait when joining the army and completing the program after 3 attempts'"
    )
    impact_today: str = Field(
        ..., 
        description="How the value impacts how the creator works today, e.g., 'When cold calling people, understands the power of numbers and having to go through a lot of setbacks to get a successful call'"
    )

    # Add default constructor for error handling
    @classmethod
    def default(cls) -> 'ValueObject':
        return cls(
            name="",
            origin="",
            impact_today=""
        )

class ChallengeObject(BaseModel):
    description: str = Field(
        ..., 
        description="Description of the challenge, e.g., 'Experiencing homelessness in 2009'"
    )
    learnings: str = Field(
        ..., 
        description="The lessons the creator learned from the challenge, e.g., 'Made survival and ruthless prioritization his first priority'"
    )

    @classmethod
    def default(cls) -> 'ChallengeObject':
        return cls(
            description="",
            learnings=""
        )

class AchievementObject(BaseModel):
    description: str = Field(
        ..., 
        description="Description of the achievement, e.g., 'Founding own creative agency \"On Air\"', 'Speaking at TEDx Conferences'"
    )

    @classmethod
    def default(cls) -> 'AchievementObject':
        return cls(
            description=""
        )

class LifeEventObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name or title of the life event, e.g., 'Childhood'"
    )
    description: str = Field(
        ..., 
        description="Description of the life event, e.g., 'Grew up on a quiet island called La Désirade, in Guadeloupe'"
    )

    @classmethod
    def default(cls) -> 'LifeEventObject':
        return cls(
            name="",
            description=""
        )

class BusinessObject(BaseModel):
    name: str = Field(
        ..., 
        description="Name of the business, e.g., 'Agency \"On Air\"'"
    )
    description: str = Field(
        ..., 
        description="Description of the business, e.g., 'Marketing strategist to drive innovation in large corporates'"
    )
    genesis: str = Field(
        ..., 
        description="How the business started, e.g., 'Started as a freelancer, building out the skills to turn them into an agency in 2010'"
    )

    @classmethod
    def default(cls) -> 'BusinessObject':
        return cls(
            name="",
            description="",
            genesis=""
        )

class ContentCreatorInfo(BaseModel):
    life_events: Optional[List[LifeEventObject]] = Field(default_factory=list)
    business: Optional[BusinessObject] = None
    values: Optional[List[ValueObject]] = Field(default_factory=list)
    challenges: Optional[List[ChallengeObject]] = Field(default_factory=list)
    achievements: Optional[List[AchievementObject]] = Field(default_factory=list)
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    @classmethod
    def default(cls) -> 'ContentCreatorInfo':
        return cls(
            first_name="",
            last_name="",
            life_events=[LifeEventObject.default()],
            business=BusinessObject.default(),
            values=[ValueObject.default()],
            challenges=[ChallengeObject.default()],
            achievements=[AchievementObject.default()]
        )
    
    def update(self, new_info):
        if isinstance(new_info, ContentCreatorInfo):
                        setattr(self, field, new_value)
        else:
            # Handle updating from other types of objects if needed
            pass

def save_output_to_markdown(output, filename="creatorOutputSimple.md"):
    """
    Save output to a markdown file with proper error handling.
    Handles both CrewAI output and ContentCreatorInfo objects.
    """
    try:
        with open(filename, "w", encoding="utf-8") as md_file:
            md_file.write("# Creator Analysis Output\n\n")
            
            # Handle different types of output objects
            if hasattr(output, 'raw'):  # CrewAI output
                md_file.write(f"## Raw Output\n\n```\n{output.raw}\n```\n\n")
                
                if hasattr(output, 'json_dict') and output.json_dict:
                    md_file.write(f"## JSON Output\n\n```json\n{json.dumps(output.json_dict, indent=2)}\n```\n\n")
                
                if hasattr(output, 'pydantic'):
                    md_file.write(f"## Pydantic Output\n\n```\n{output.pydantic}\n```\n\n")
                
                if hasattr(output, 'tasks_output'):
                    md_file.write(f"## Tasks Output\n\n```\n{output.tasks_output}\n```\n\n")
                
                if hasattr(output, 'token_usage'):
                    md_file.write(f"## Token Usage\n\n```\n{output.token_usage}\n```\n")
            
            else:  # ContentCreatorInfo object
                try:
                    content = output.model_dump_json(indent=2)
                    md_file.write(f"## Merged Content\n\n```json\n{content}\n```\n\n")
                except AttributeError:
                    # Fallback for older Pydantic versions
                    content = json.dumps(output.dict(), indent=2)
                    md_file.write(f"## Merged Content\n\n```json\n{content}\n```\n\n")
            
        return True
    except Exception as e:
        print(f"Error saving to markdown file: {str(e)}")
        return False
# def save_output_to_markdown(crew_output, filename="creatorOutputSimple.md"):
#     """
#     Save crew output to a markdown file with proper error handling.
#     """
#     try:
#         with open(filename, "w", encoding="utf-8") as md_file:
#             md_file.write("# Creator Analysis Output\n\n")
#             md_file.write(f"## Raw Output\n\n```\n{crew_output.raw}\n```\n\n")
            
#             if crew_output.json_dict:
#                 md_file.write(f"## JSON Output\n\n```json\n{json.dumps(crew_output.json_dict, indent=2)}\n```\n\n")
            
#             if crew_output.pydantic:
#                 md_file.write(f"## Pydantic Output\n\n```\n{crew_output.pydantic}\n```\n\n")
            
#             md_file.write(f"## Tasks Output\n\n```\n{crew_output.tasks_output}\n```\n\n")
#             md_file.write(f"## Token Usage\n\n```\n{crew_output.token_usage}\n```\n")
            
#         return True
#     except Exception as e:
#         print(f"Error saving to markdown file: {str(e)}")
#         return False

# ----------------------------------------------------------------------

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

def merge_content_creator_info(info1: Dict[str, Any], info2: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merges two ContentCreatorInfo dictionaries with consistent handling of all object types
    """
    def is_empty_or_none(value) -> bool:
        if value is None:
            return True
        if isinstance(value, (str, list, dict)) and not value:
            return True
        return False

    # Define default structures for each object type
    default_objects = {
        'values': {
            'name': 'Not specified',
            'origin': 'No information available',
            'impact_today': 'No information available'
        },
        'challenges': {
            'description': 'Not specified',
            'learnings': 'No information available'
        },
        'achievements': {
            'description': 'Not specified'
        },
        'life_events': {
            'name': 'Not specified',
            'description': 'No information available'
        },
        'business': {
            'name': 'Not specified',
            'description': 'No information available',
            'genesis': 'No information available'
        }
    }

    def merge_lists(list1: List, list2: List, object_type: str) -> List:
        """Merge two lists with type-specific field validation"""
        if not list1 and not list2:
            # Return a list with one default object of the appropriate type
            return [default_objects[object_type]]

        # Combine lists
        merged = list1.copy() if list1 else []
        if list2:
            merged.extend(list2)

        # If merged list is empty, add default
        if not merged:
            return [default_objects[object_type]]

        # Ensure each item has all required fields
        validated_items = []
        default_obj = default_objects[object_type]
        
        for item in merged:
            validated_item = default_obj.copy()
            validated_item.update({k: v for k, v in item.items() if v})
            validated_items.append(validated_item)

        return validated_items

    # Initialize merged result
    merged = {
        'life_events': merge_lists(
            info1.get('life_events', []),
            info2.get('life_events', []),
            'life_events'
        ),
        'values': merge_lists(
            info1.get('values', []),
            info2.get('values', []),
            'values'
        ),
        'challenges': merge_lists(
            info1.get('challenges', []),
            info2.get('challenges', []),
            'challenges'
        ),
        'achievements': merge_lists(
            info1.get('achievements', []),
            info2.get('achievements', []),
            'achievements'
        ),
        'business': default_objects['business'].copy(),
        'first_name': 'Unknown',
        'last_name': 'Unknown'
    }

    # Handle business object separately as it's not a list
    business1 = info1.get('business', {})
    business2 = info2.get('business', {})
    if business1 or business2:
        merged['business'] = default_objects['business'].copy()
        if business1:
            merged['business'].update({k: v for k, v in business1.items() if v})
        if business2:
            merged['business'].update({k: v for k, v in business2.items() if v})

    # Handle name fields
    merged['first_name'] = info1.get('first_name') or info2.get('first_name') or 'Unknown'
    merged['last_name'] = info1.get('last_name') or info2.get('last_name') or 'Unknown'

    return merged

def ensure_dict(info: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Convert string input to dictionary if needed."""
    if isinstance(info, str):
        try:
            return json.loads(info.strip('"""').strip("'''"))
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {str(e)}")
    return info

instagram_info = """{
    "life_events": [],
    "business": {
        "name": "",
        "description": "",
        "genesis": ""
    },
    "values": [],
    "challenges": [],
    "achievements": [],
    "first_name": "",
    "last_name": ""
}"""

def merge_and_validate_content(crew_result: Any, instagram_info: str) -> ContentCreatorInfo:
    """
    Merge crew result with Instagram info and validate the result.
    """
    try:
        # Convert Instagram info to dict
        instagram_dict = ensure_dict(instagram_info)

        # Initialize youtube_dict
        youtube_dict = {
            'values': [],
            'life_events': [],
            'challenges': [],
            'achievements': [],
            'business': {},
            'first_name': '',
            'last_name': ''
        }
        
        # Parse crew result
        if hasattr(crew_result, 'raw'):
            try:
                # First try to identify if there's a ContentCreatorInfo object
                if "ContentCreatorInfo(" in crew_result.raw:
                    # Parse the ContentCreatorInfo object
                    content_parts = crew_result.raw.split("ContentCreatorInfo(")[1].split(")")
                    content_str = content_parts[0]
                    
                    # Extract life_events
                    if "life_events=[" in content_str:
                        life_events = []
                        events_str = content_str.split("life_events=[")[1].split("]")[0]
                        event_items = events_str.split("LifeEventObject(")
                        for item in event_items:
                            if "name=" in item and "description=" in item:
                                name = item.split('name="')[1].split('"')[0]
                                description = item.split('description="')[1].split('"')[0]
                                life_events.append({
                                    "name": name,
                                    "description": description
                                })
                        if life_events:
                            youtube_dict['life_events'] = life_events
                    
                    # Extract business
                    if "business=BusinessObject(" in content_str:
                        business_str = content_str.split("business=BusinessObject(")[1].split(")")[0]
                        if 'name="' in business_str and 'description="' in business_str and 'genesis="' in business_str:
                            youtube_dict['business'] = {
                                "name": business_str.split('name="')[1].split('"')[0],
                                "description": business_str.split('description="')[1].split('"')[0],
                                "genesis": business_str.split('genesis="')[1].split('"')[0]
                            }
                    
                    # Extract values
                    if "values=[" in content_str:
                        values = []
                        values_str = content_str.split("values=[")[1].split("]")[0]
                        value_items = values_str.split("ValueObject(")
                        for item in value_items:
                            if "name=" in item and "origin=" in item and "impact_today=" in item:
                                name = item.split('name="')[1].split('"')[0]
                                origin = item.split('origin="')[1].split('"')[0]
                                impact = item.split('impact_today="')[1].split('"')[0]
                                values.append({
                                    "name": name,
                                    "origin": origin,
                                    "impact_today": impact
                                })
                        if values:
                            youtube_dict['values'] = values
                    
                    # Extract challenges and achievements if they exist
                    if "challenges=[" in content_str:
                        challenges = []
                        challenges_str = content_str.split("challenges=[")[1].split("]")[0]
                        challenge_items = challenges_str.split("ChallengeObject(")
                        for item in challenge_items:
                            if "description=" in item and "learnings=" in item:
                                description = item.split('description="')[1].split('"')[0]
                                learnings = item.split('learnings="')[1].split('"')[0]
                                challenges.append({
                                    "description": description,
                                    "learnings": learnings
                                })
                        if challenges:
                            youtube_dict['challenges'] = challenges
                    
                    if "achievements=[" in content_str:
                        achievements = []
                        achievements_str = content_str.split("achievements=[")[1].split("]")[0]
                        achievement_items = achievements_str.split("AchievementObject(")
                        for item in achievement_items:
                            if "description=" in item:
                                description = item.split('description="')[1].split('"')[0]
                                achievements.append({
                                    "description": description
                                })
                        if achievements:
                            youtube_dict['achievements'] = achievements
            
            except Exception as e:
                print(f"Error parsing crew result: {str(e)}")
        
        # Merge and validate
        merged_info = merge_content_creator_info(youtube_dict, instagram_dict)
        
        # Create and validate ContentCreatorInfo
        return ContentCreatorInfo(**merged_info)
        
    except Exception as e:
        print(f"Debug - Error details: {str(e)}")
        print(f"Debug - Crew result type: {type(crew_result)}")
        if hasattr(crew_result, 'raw'):
            print(f"Debug - Raw content: {crew_result.raw}")
        
        # Return a properly initialized default object
        return ContentCreatorInfo.default()
    
# def run():
#     """
#     Process YouTube and Instagram content and merge them.
#     """
#     try:
#         # Get YouTube handle
#         youtube_channel_handle = input("Please enter the YouTube channel handle to analyze:\n").strip()
        
#         if not youtube_channel_handle:
#             raise ValueError("YouTube channel handle cannot be empty")
            
#         inputs = {
#             "youtube_channel_handle": youtube_channel_handle
#         }
        
#         # Run the crew
#         crew_result = YoutubeCrew().crew().kickoff(inputs=inputs)
        
#         # Save crew output
#         if hasattr(crew_result, 'raw'):
#             save_output_to_markdown(crew_result, "crew_output.md")
        
#         # Merge and validate content
#         merged_model = merge_and_validate_content(crew_result, instagram_info)
        
#         # Save merged model
#         save_output_to_markdown(merged_model, "merged_output.md")
        
#         # Print the merged model using the new method
#         print("\nMerged Content Creator Info:")
#         print(merged_model.model_dump_json(indent=2))
        
#         return merged_model
        
#     except Exception as e:
#         print(f"An unexpected error occurred: {str(e)}")
#         # Return default object instead of exiting
#         return ContentCreatorInfo.default()

def run():
    """
    Process YouTube and Instagram content and merge them.
    """
    # Get YouTube handle
    youtube_channel_handle = input("Please enter the YouTube channel handle to analyze:\n").strip()
        
    inputs = {
        "youtube_channel_handle": youtube_channel_handle
    }
        
    # Run the crew
    YoutubeCrew().crew().kickoff(inputs=inputs)

if __name__ == "__main__":
    run()
