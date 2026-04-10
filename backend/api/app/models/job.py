from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

class JobStatus(str, Enum):
    PENDING     = "pending"
    QUEUED      = "queued"
    PROCESSING  = "processing"
    EXTRACTING  = "extracting_audio"
    TRANSCRIBING = "transcribing"
    ANALYZING   = "analyzing"
    CLIPPING    = "clipping"
    REFRAMING   = "reframing"
    CAPTIONING  = "captioning"
    RENDERING   = "rendering"
    UPLOADING   = "uploading"
    COMPLETED   = "completed"
    FAILED      = "failed"
    CANCELLED   = "cancelled"

class ClipResult(BaseModel):
    clip_id: str
    clip_url: str
    thumbnail_url: str
    duration: float          # seconds
    start_time: float        # in original video
    end_time: float
    transcript_snippet: str
    viral_score: float       # 0–100
    title: Optional[str] = None
    # Template-generated overlay text
    top_title: Optional[str] = None
    bottom_tag: Optional[str] = None
    template_id: Optional[str] = None

class JobCreate(BaseModel):
    video_url: Optional[str] = None      # GCS URL after upload
    youtube_url: Optional[str] = None   # YouTube link
    options: Optional[dict] = {}        # user preferences
    template_id: Optional[str] = "viral-hook"  # Selected viral template ID

class JobDB(BaseModel):
    job_id: str
    user_id: str
    video_url: Optional[str] = None
    youtube_url: Optional[str] = None
    status: JobStatus = JobStatus.PENDING
    progress: int = 0           # 0–100
    current_step: str = ""
    error_message: Optional[str] = None
    clips: List[ClipResult] = []
    options: dict = {}
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    video_duration: Optional[float] = None
    clip_count: int = 0

class JobPublic(BaseModel):
    job_id: str
    status: JobStatus
    progress: int
    current_step: str
    clips: List[ClipResult] = []
    clip_count: int
    video_duration: Optional[float] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
