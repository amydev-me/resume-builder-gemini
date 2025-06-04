import json
from typing import Dict, Any, List
from ..utils.file_manager import load_json_data, save_json_data
from ..schemas.feedback import ResumeFeedback, FeedbackItem
from ..core_ai.agentic_learner import AgenticLearner
from ..core_ai.llm_client import LLMClient # Need LLMClient to initialize AgenticLearner

USER_PROFILE_FILE = "user_profile.json"

# Initialize LLMClient and AgenticLearner globally for robustness
llm_client_instance = LLMClient()
agentic_learner_instance = AgenticLearner(llm_client_instance)

def process_feedback_and_update_preferences(feedback: ResumeFeedback) -> None:
    """
    Processes user feedback and updates the entire user_profile.json (core data and preferences)
    using the AgenticLearner.
    """
    current_user_profile = load_json_data(USER_PROFILE_FILE)

    # Use the AgenticLearner to update the entire profile
    updated_profile = agentic_learner_instance.update_user_profile_from_feedback(
        current_user_profile,
        feedback.feedback_items
    )

    save_json_data(USER_PROFILE_FILE, updated_profile)
    print(f"User profile updated based on feedback. New profile:\n{json.dumps(updated_profile, indent=2)}")