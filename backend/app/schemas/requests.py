# backend/app/schemas/requests.py

from pydantic import BaseModel
from typing import Dict, Any, List, Optional # Ensure these are imported

# Your existing request schemas should be here too, e.g., GenerateResumeRequest, SubmitFeedbackRequest

class SetupUserProfileRequest(BaseModel):
    """
    Schema for updating or setting up the user's core profile data.
    """
    core_data: Dict[str, Any]
    # In the future, if you wanted to allow setting initial learned preferences via this request,
    # you could add: learned_preferences: Optional[List[Dict[str, Any]]] = None