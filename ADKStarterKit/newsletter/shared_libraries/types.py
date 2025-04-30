

"""Common data schema and types for travel-concierge agents."""

from typing import Optional, Union

from google.genai import types
from pydantic import BaseModel, Field


# Convenient declaration for controlled generation.
json_response_config = types.GenerateContentConfig(
    response_mime_type="application/json"
)


class Profile(BaseModel):
    """A profile for selection."""
    motivations: list[str] = Field(
        description="Intrinsic motivations of the target audience such as: status, achievement, recognition, etc."
    )
    desires: list[str] = Field(description="Desires of the target audience such as: money, time, status, etc.")
    challenges: list[str] = Field(description="Challenges of the target audience such as: time, money, status, etc.")

class Intro(BaseModel):
    """A section of the newsletter."""
    content: str = Field(description="Content of the intro section.")

class Review(BaseModel):
    """A section of the newsletter."""
    content: str = Field(description="Content of the body section.")

class Body(BaseModel):
    """A section of the newsletter."""
    reviews: list[Review] = Field(description="List of reviews.")

class Conclusion(BaseModel):
    """A section of the newsletter."""
    content: str = Field(description="Content of the conclusion section.")

class Newsletter(BaseModel):
    """A newsletter."""
    intro: Intro = Field(description="Intro of the newsletter.")
    body: Body = Field(description="Body of the newsletter.")
    conclusion: Conclusion = Field(description="Conclusion of the newsletter.")
