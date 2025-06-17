from pydantic import BaseModel
from typing import List, Optional, Literal

class CritiqueIssue(BaseModel):
    category: Literal[
        "Rule Violation",
        "Stylistic",
        "Content Gap",
        "Target JD Mismatch",
        "Best Practice",
        "Other",
        "Error",  # Keep 'Error' just in case.
        "Quantification",
        "Impact vs. Responsibility",
        "Generic Phrases",
        "Action Verbs",
        "Conciseness",
        "ATS/JD Relevance"  # This was the last one that caused an error.
    ]
    severity: Literal["low", "medium", "high"]
    description: str
    suggested_action: Optional[str] = None
    relevant_rule_id: Optional[str] = None

class ResumeCritique(BaseModel):
    issues: List[CritiqueIssue]
    overall_assessment: str  # A brief overall summary of the critique
    has_issues: bool  # Convenience flag, True if issues list is not empty, False otherwise
