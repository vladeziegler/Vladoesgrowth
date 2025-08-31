import asyncio
import os
import uuid
from typing import List, Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from models import (
    FileUploadResponse, TaskResponse, TaskStatusResponse, TaskStatus,
    ClothingAnalysisResponse, WorkflowResults, GenerateQuadrantsRequest,
    AnalyzeClothingRequest
)
from services import gemini_service, file_service, reverse_search_service

app = FastAPI(
    title="Clothing Visualization API",
    description="API for generating clothing visualization and analysis",
    version="1.0.0"
)

# Enable CORS for web frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Task storage (in production, use Redis or database)
tasks: Dict[str, Dict[str, Any]] = {}


def update_task_progress(task_id: str, progress: int, message: str, results: Any = None):
    """Update task progress."""
    if task_id in tasks:
        tasks[task_id].update({
            "progress": progress,
            "message": message,
            "results": results
        })


async def process_full_workflow(
    task_id: str,
    reference_file_id: str,
    clothing_file_ids: List[str]
):
    """Background task for full workflow processing."""
    try:
        tasks[task_id]["status"] = TaskStatus.PROCESSING
        update_task_progress(task_id, 10, "Loading reference image...")
        
        # Load reference image
        reference_data = file_service.read_file(reference_file_id, 'reference')
        if not reference_data:
            raise Exception("Reference image not found")
        
        update_task_progress(task_id, 20, "Analyzing clothing items...")
        
        # Analyze all clothing items
        clothing_analyses = []
        for i, clothing_id in enumerate(clothing_file_ids):
            clothing_data = file_service.read_file(clothing_id, 'clothing')
            if not clothing_data:
                continue
                
            analysis = await gemini_service.analyze_clothing(clothing_data)
            if analysis:
                clothing_analyses.append({
                    "filename": f"clothing_{clothing_id}",
                    "file_id": clothing_id,
                    "analysis": analysis
                })
            
            progress = 20 + (30 * (i + 1) // len(clothing_file_ids))
            update_task_progress(task_id, progress, f"Analyzed {i + 1}/{len(clothing_file_ids)} items...")
        
        update_task_progress(task_id, 50, "Generating quadrant images...")
        
        # Generate quadrant images for each clothing item
        generated_images = []
        for i, clothing_id in enumerate(clothing_file_ids):
            clothing_data = file_service.read_file(clothing_id, 'clothing')
            if not clothing_data:
                continue
                
            image_data = await gemini_service.generate_quadrant_image(reference_data, clothing_data)
            if image_data:
                generated_file_id = file_service.save_generated_file(
                    image_data, 
                    f"quadrant_{clothing_id}"
                )
                generated_images.append({
                    "clothing_file_id": clothing_id,  # Changed from clothing_id to clothing_file_id
                    "generated_file_id": generated_file_id,
                    "download_url": f"/download/{generated_file_id}"
                })
            
            progress = 50 + (40 * (i + 1) // len(clothing_file_ids))
            update_task_progress(task_id, progress, f"Generated {i + 1}/{len(clothing_file_ids)} images...")
        
        # Prepare final results
        results = {
            "reference_image": reference_file_id,
            "clothing_analyses": clothing_analyses,
            "generated_images": generated_images,
            "total_processed": len(clothing_file_ids)
        }
        
        tasks[task_id].update({
            "status": TaskStatus.COMPLETED,
            "progress": 100,
            "message": "Workflow completed successfully",
            "results": results,
            "download_urls": [img["download_url"] for img in generated_images]
        })
        
    except Exception as e:
        tasks[task_id].update({
            "status": TaskStatus.FAILED,
            "progress": 0,
            "message": f"Workflow failed: {str(e)}",
            "error": str(e)
        })


@app.post("/upload-reference", response_model=FileUploadResponse)
async def upload_reference_image(file: UploadFile = File(...)):
    """Upload reference image of the person."""
    if not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    file_data = await file.read()
    file_id = file_service.save_uploaded_file(file_data, file.filename, 'reference')
    
    return FileUploadResponse(
        file_id=file_id,
        filename=file.filename,
        message="Reference image uploaded successfully"
    )


@app.post("/upload-clothing", response_model=List[FileUploadResponse])
async def upload_clothing_images(files: List[UploadFile] = File(...)):
    """Upload clothing item images."""
    responses = []
    
    for file in files:
        if not file.content_type.startswith('image/'):
            continue  # Skip non-image files
            
        file_data = await file.read()
        file_id = file_service.save_uploaded_file(file_data, file.filename, 'clothing')
        
        responses.append(FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            message="Clothing image uploaded successfully"
        ))
    
    if not responses:
        raise HTTPException(status_code=400, detail="No valid image files uploaded")
    
    return responses


@app.post("/analyze-clothing", response_model=List[ClothingAnalysisResponse])
async def analyze_clothing_items(request: AnalyzeClothingRequest):
    """Analyze clothing items and return structured data."""
    results = []
    
    for clothing_id in request.clothing_file_ids:
        clothing_data = file_service.read_file(clothing_id, 'clothing')
        if not clothing_data:
            continue
            
        analysis = await gemini_service.analyze_clothing(clothing_data)
        if analysis:
            results.append(ClothingAnalysisResponse(
                filename=f"clothing_{clothing_id}",
                file_id=clothing_id,
                analysis=analysis
            ))
    
    return results


@app.post("/generate-quadrants", response_model=TaskResponse)
async def generate_quadrant_images(
    request: GenerateQuadrantsRequest,
    background_tasks: BackgroundTasks
):
    """Generate quadrant images for clothing items."""
    # Validate that files exist
    reference_data = file_service.read_file(request.reference_file_id, 'reference')
    if not reference_data:
        raise HTTPException(status_code=404, detail="Reference image not found")
    
    for clothing_id in request.clothing_file_ids:
        if not file_service.read_file(clothing_id, 'clothing'):
            raise HTTPException(status_code=404, detail=f"Clothing image {clothing_id} not found")
    
    # Create task
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "progress": 0,
        "message": "Task queued",
        "results": None
    }
    
    # Start background processing
    background_tasks.add_task(
        process_full_workflow,
        task_id,
        request.reference_file_id,
        request.clothing_file_ids
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Quadrant generation started"
    )


@app.post("/full-workflow", response_model=TaskResponse)
async def full_workflow(
    background_tasks: BackgroundTasks,
    reference_file: UploadFile = File(...),
    clothing_files: List[UploadFile] = File(...)
):
    """Complete workflow: upload files, generate images, and analyze clothing."""
    # Upload reference image
    if not reference_file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="Reference file must be an image")
    
    reference_data = await reference_file.read()
    reference_file_id = file_service.save_uploaded_file(
        reference_data, 
        reference_file.filename, 
        'reference'
    )
    
    # Upload clothing images
    clothing_file_ids = []
    for file in clothing_files:
        if file.content_type.startswith('image/'):
            file_data = await file.read()
            file_id = file_service.save_uploaded_file(file_data, file.filename, 'clothing')
            clothing_file_ids.append(file_id)
    
    if not clothing_file_ids:
        raise HTTPException(status_code=400, detail="No valid clothing images uploaded")
    
    # Create task
    task_id = str(uuid.uuid4())
    tasks[task_id] = {
        "status": TaskStatus.PENDING,
        "progress": 0,
        "message": "Task queued",
        "results": None
    }
    
    # Start background processing
    background_tasks.add_task(
        process_full_workflow,
        task_id,
        reference_file_id,
        clothing_file_ids
    )
    
    return TaskResponse(
        task_id=task_id,
        status=TaskStatus.PENDING,
        message="Full workflow started"
    )


@app.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get the status of a background task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    task = tasks[task_id]
    return TaskStatusResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        message=task["message"],
        results=task.get("results"),
        download_urls=task.get("download_urls"),
        error=task.get("error")
    )


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    """Download a generated file."""
    file_path = file_service.get_file_path(file_id, 'generated')
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=f"generated_{file_id}.png"
    )


@app.delete("/cleanup/{task_id}")
async def cleanup_task_files(task_id: str):
    """Clean up files associated with a task."""
    if task_id not in tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get file IDs from task results if available
    task = tasks[task_id]
    file_ids = []
    
    if task.get("results"):
        results = task["results"]
        if "reference_image" in results:
            file_ids.append(results["reference_image"])
        
        for img in results.get("generated_images", []):
            file_ids.append(img.get("generated_file_id"))
        
        for analysis in results.get("clothing_analyses", []):
            file_ids.append(analysis.get("file_id"))
    
    # Clean up files
    file_service.cleanup_files(file_ids)
    
    # Remove task
    del tasks[task_id]
    
    return {"message": "Task and associated files cleaned up"}


@app.post("/reverse-search/{file_id}")
async def reverse_search_image(file_id: str):
    """Find similar items using reverse image search."""
    try:
        # Check if SERPER_API_KEY is available
        if not reverse_search_service.serper_api_key:
            return {
                "success": False,
                "message": "SERPER_API_KEY not configured. Please add it to your environment variables.",
                "similar_items": []
            }
        
        # Try to get the clothing image first (for original clothing items)
        file_path = file_service.get_file_path(file_id, 'clothing')
        
        # If not found in clothing, try generated (for backward compatibility)
        if not file_path or not os.path.exists(file_path):
            file_path = file_service.get_file_path(file_id, 'generated')
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"Image not found for file_id: {file_id}")
        
        # Perform reverse image search
        similar_items = reverse_search_service.search_similar_items(file_path)
        
        if similar_items is None:
            return {
                "success": False,
                "message": "Could not find similar items. This might be due to upload issues or no similar items found.",
                "similar_items": []
            }
        
        return {
            "success": True,
            "message": f"Found {len(similar_items)} similar items",
            "similar_items": similar_items
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": f"Error performing reverse search: {str(e)}",
            "similar_items": []
        }


@app.get("/image-proxy")
async def image_proxy(url: str):
    """Proxy images to bypass CORS restrictions."""
    try:
        import requests
        response = requests.get(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        if response.status_code == 200:
            return Response(
                content=response.content,
                media_type=response.headers.get('content-type', 'image/jpeg'),
                headers={
                    "Cache-Control": "public, max-age=3600",
                    "Access-Control-Allow-Origin": "*"
                }
            )
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")

@app.post("/download-all")
async def download_all_images(file_ids: List[str]):
    """Create a zip file with all generated images."""
    import zipfile
    import io
    
    try:
        # Create a zip file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for i, file_id in enumerate(file_ids):
                file_path = file_service.get_file_path(file_id, 'generated')
                if file_path and os.path.exists(file_path):
                    # Add file to zip with a clean name
                    zip_file.write(file_path, f"generated_image_{i+1}_{file_id}.png")
        
        zip_buffer.seek(0)
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename=clothing_images_{len(file_ids)}_items.zip"
            }
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create zip file: {str(e)}")

@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables."""
    import os
    return {
        "serper_api_key_exists": bool(os.environ.get("SERPER_API_KEY")),
        "serper_api_key_value": os.environ.get("SERPER_API_KEY", "NOT_SET")[:10] + "..." if os.environ.get("SERPER_API_KEY") else "NOT_SET",
        "imgbb_api_key_exists": bool(os.environ.get("IMGBB_API_KEY")),
        "imgbb_api_key_value": os.environ.get("IMGBB_API_KEY", "DEFAULT_USED")[:10] + "..." if os.environ.get("IMGBB_API_KEY") else "DEFAULT_USED",
        "gemini_api_key_exists": bool(os.environ.get("GOOGLE_API_KEY")),
        "generated_dir_exists": os.path.exists("/Users/vladimirdeziegler/banana/uploads/generated"),
        "generated_files": os.listdir("/Users/vladimirdeziegler/banana/uploads/generated") if os.path.exists("/Users/vladimirdeziegler/banana/uploads/generated") else []
    }

@app.get("/")
async def root():
    """API health check."""
    return {
        "message": "Clothing Visualization API",
        "status": "healthy",
        "endpoints": {
            "upload_reference": "POST /upload-reference",
            "upload_clothing": "POST /upload-clothing", 
            "analyze_clothing": "POST /analyze-clothing",
            "generate_quadrants": "POST /generate-quadrants",
            "full_workflow": "POST /full-workflow",
            "reverse_search": "POST /reverse-search/{file_id}",
            "debug_env": "GET /debug/env", 
            "task_status": "GET /status/{task_id}",
            "download": "GET /download/{file_id}",
            "download_all": "POST /download-all",
            "cleanup": "DELETE /cleanup/{task_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
