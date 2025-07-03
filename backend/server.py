from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime
import yt_dlp
import tempfile
import asyncio
from concurrent.futures import ThreadPoolExecutor
import json
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Thread pool for yt-dlp operations
executor = ThreadPoolExecutor(max_workers=3)

# Define Models
class VideoInfoRequest(BaseModel):
    url: str

class VideoFormat(BaseModel):
    format_id: str
    ext: str
    quality: str
    filesize: Optional[int] = None
    format_note: Optional[str] = None

class VideoInfo(BaseModel):
    title: str
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    uploader: Optional[str] = None
    view_count: Optional[int] = None
    formats: List[VideoFormat] = []
    url: str

class DownloadRequest(BaseModel):
    url: str
    format_id: str

# Helper function to validate YouTube URL
def is_valid_youtube_url(url: str) -> bool:
    """Validate if the URL is a valid YouTube URL"""
    youtube_regex = re.compile(
        r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return bool(youtube_regex.match(url))

# Helper function to extract video info
def extract_video_info(url: str) -> Dict[str, Any]:
    # Validate YouTube URL first
    if not is_valid_youtube_url(url):
        raise HTTPException(status_code=400, detail="Invalid YouTube URL format")
    
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if not info:
                raise HTTPException(status_code=404, detail="Video not found or unavailable")
            return info
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Video unavailable" in error_msg or "not available" in error_msg:
            raise HTTPException(status_code=404, detail="Video not found or unavailable")
        elif "Private video" in error_msg:
            raise HTTPException(status_code=403, detail="Video is private")
        elif "This video is not available" in error_msg:
            raise HTTPException(status_code=404, detail="Video not available")
        else:
            raise HTTPException(status_code=400, detail=f"Error extracting video info: {error_msg}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

# Helper function to download video
def download_video(url: str, format_id: str, output_path: str) -> str:
    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            return output_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading video: {str(e)}")

@api_router.get("/")
async def root():
    return {"message": "YouTube Downloader API"}

@api_router.post("/video-info", response_model=VideoInfo)
async def get_video_info(request: VideoInfoRequest):
    """Get video information including available formats"""
    try:
        # Run yt-dlp in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(executor, extract_video_info, request.url)
        
        # Extract formats
        formats = []
        if 'formats' in info:
            for fmt in info['formats']:
                if fmt.get('vcodec') != 'none' and fmt.get('acodec') != 'none':  # Video with audio
                    quality = fmt.get('height', 'Unknown')
                    quality_str = f"{quality}p" if quality != 'Unknown' else fmt.get('format_note', 'Unknown')
                    
                    formats.append(VideoFormat(
                        format_id=fmt['format_id'],
                        ext=fmt.get('ext', 'mp4'),
                        quality=quality_str,
                        filesize=fmt.get('filesize'),
                        format_note=fmt.get('format_note')
                    ))
        
        # Sort formats by quality (highest first)
        formats.sort(key=lambda x: int(x.quality.replace('p', '')) if x.quality.replace('p', '').isdigit() else 0, reverse=True)
        
        return VideoInfo(
            title=info.get('title', 'Unknown'),
            duration=info.get('duration'),
            thumbnail=info.get('thumbnail'),
            uploader=info.get('uploader'),
            view_count=info.get('view_count'),
            formats=formats,
            url=request.url
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

@api_router.post("/download")
async def download_video_endpoint(request: DownloadRequest):
    """Download video with specified format"""
    try:
        # Create temporary file
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, f"%(title)s.%(ext)s")
        
        # Run download in thread pool
        loop = asyncio.get_event_loop()
        downloaded_file = await loop.run_in_executor(
            executor, 
            download_video, 
            request.url, 
            request.format_id, 
            output_path
        )
        
        # Get the actual filename
        files = os.listdir(temp_dir)
        if not files:
            raise HTTPException(status_code=500, detail="Download failed - no file created")
        
        actual_file = os.path.join(temp_dir, files[0])
        
        # Stream the file
        def iterfile():
            with open(actual_file, mode="rb") as file_like:
                yield from file_like
        
        # Get file info for headers
        file_size = os.path.getsize(actual_file)
        filename = os.path.basename(actual_file)
        
        headers = {
            'Content-Disposition': f'attachment; filename="{filename}"',
            'Content-Length': str(file_size)
        }
        
        return StreamingResponse(
            iterfile(),
            media_type='application/octet-stream',
            headers=headers
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()