from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from .critique import ResumeCritique # <--- Ensure this NEW IMPORT is at the top

class FeedbackItem(BaseModel):
    section: str  # e.g., "summary", "experience", "skills"
    text: str       # The specific text the feedback refers to
    comment: str    # User's textual feedback (e.g., "Make this more concise")
    is_positive: bool = True # Whether the feedback is generally positive or negative
    highlight_range: Optional[List[int]] = None # [start_index, end_index] of highlighted text

class ResumeFeedback(BaseModel):
    resume_version_id: str
    feedback_items: List[FeedbackItem]

# --- Pydantic Models for Request/Response Bodies ---
class GenerateResumeRequest(BaseModel):
    # For now, we'll just send a dummy prompt text for initial generation
    # Later, this will be more sophisticated.
    initial_prompt: str = "Generate a professional resume based on user profile."

class ResumeContentResponse(BaseModel):
    id: str
    version_name: str
    content: str
    timestamp: str
    feedback_summary: str

    # --- NEW FIELDS FOR AGENTIC FEATURES ---
    core_data_used: Optional[Dict[str, Any]] = None
    learned_preferences_used: Optional[List[Dict[str, Any]]] = None
    target_job_description_used: Optional[str] = None
    critique: Optional[ResumeCritique] = None  # <--- The critical new field for self-critique