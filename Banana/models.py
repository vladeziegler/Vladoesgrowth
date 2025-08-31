from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ClothingItem(BaseModel):
    category: str
    description: str
    condition: str
    tags: List[str]
    size: Optional[str] = None
    material: Optional[str] = None


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    message: str


class TaskResponse(BaseModel):
    task_id: str
    status: TaskStatus
    message: str


class TaskStatusResponse(BaseModel):
    task_id: str
    status: TaskStatus
    progress: int  # 0-100
    message: str
    results: Optional[Dict[str, Any]] = None
    download_urls: Optional[List[str]] = None
    error: Optional[str] = None


class ClothingAnalysisResponse(BaseModel):
    filename: str
    file_id: str
    analysis: ClothingItem


class WorkflowResults(BaseModel):
    reference_image: str
    clothing_analyses: List[ClothingAnalysisResponse]
    generated_images: List[Dict[str, str]]  # filename -> download_url mapping
    total_processed: int


class GenerateQuadrantsRequest(BaseModel):
    reference_file_id: str
    clothing_file_ids: List[str]


class AnalyzeClothingRequest(BaseModel):
    clothing_file_ids: List[str]

