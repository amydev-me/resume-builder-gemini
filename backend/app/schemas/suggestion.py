# backend/app/schemas/suggestions.py

from pydantic import BaseModel
from typing import List, Optional

class SuggestionItem(BaseModel):
    """Represents a single actionable suggestion from the AI."""
    category: str  # e.g., "Content Improvement", "Stylistic Tip", "Skill Gap", "Formatting"
    suggestion: str # The actual suggestion in natural language (e.g., "Consider adding quantified achievements to your job history.")
    action_type: Optional[str] = None # Optional: Suggests what kind of action the user might take (e.g., "add_skill", "rephrase_summary", "update_experience")
    relevant_field: Optional[str] = None # Optional: Points to the core_data field this suggestion applies to (e.g., "skills", "job_history.responsibilities", "summary")

class SuggestionsResponse(BaseModel):
    """The full response model for proactive suggestions."""
    suggestions: List[SuggestionItem]
    message: str = "Suggestions generated successfully."

# You might also want a request model for the new endpoint if it accepts parameters
class GetSuggestionsRequest(BaseModel):
    """Request model for fetching suggestions."""
    target_job_description: Optional[str] = None # Allow providing a target JD for contextual suggestions