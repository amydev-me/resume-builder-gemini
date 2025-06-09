from pydantic import BaseModel
from typing import List, Optional, Literal

class CritiqueIssue(BaseModel):
    category: Literal["Rule Violation", "Stylistic", "Content Gap", "Target JD Mismatch", "Best Practice", "Other"]
    description: str # e.g., "Summary is too long", "Missing quantification in job history", "C# mentioned despite exclusion"
    severity: Literal["low", "medium", "high"]
    relevant_rule_id: Optional[str] = None # If it violates a specific learned rule
    suggested_action: Optional[str] = None # e.g., "shorten summary", "add numbers", "remove C# details"

class ResumeCritique(BaseModel):
    issues: List[CritiqueIssue]
    overall_assessment: str # A brief overall summary of the critique
    has_issues: bool # Convenience flag, True if issues list is not empty, False otherwise