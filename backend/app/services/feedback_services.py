from typing import Dict, Any, List
from ..utils.file_manager import load_json_data, save_json_data
from ..schemas.feedback import ResumeFeedback, FeedbackItem
from ..core_ai.agentic_learner import AgenticLearner # Import the AgenticLearner
from ..core_ai.llm_client import LLMClient # Need LLMClient to initialize AgenticLearner

USER_PROFILE_FILE = "user_profile.json"

# Initialize LLMClient and AgenticLearner globally (or pass as dependency in a larger app)
llm_client_instance = LLMClient()
agentic_learner_instance = AgenticLearner(llm_client_instance)

def process_feedback_and_update_preferences(feedback: ResumeFeedback) -> None:
    """
    Processes user feedback and updates the learned_preferences in user_profile.json
    using the AgenticLearner.
    """
    user_profile = load_json_data(USER_PROFILE_FILE)
    current_preferences = user_profile.get("learned_preferences", {})

    # Use the AgenticLearner to update preferences
    updated_preferences = agentic_learner_instance.update_preferences_from_feedback(
        current_preferences,
        feedback.feedback_items
    )

    user_profile["learned_preferences"] = updated_preferences
    save_json_data(USER_PROFILE_FILE, user_profile)
    print(f"User preferences updated based on feedback. New preferences: {updated_preferences}")

# Example usage for direct testing (adjust as needed for module imports)
if __name__ == "__main__":
    # This block needs to be runnable outside the app context for testing.
    # The global `llm_client_instance` and `agentic_learner_instance` should work.
    example_feedback = ResumeFeedback(
        resume_version_id="test_version_002",
        feedback_items=[
            FeedbackItem(section="summary", text="This is a long summary.", comment="Make this summary much more concise and professional.", is_positive=True),
            FeedbackItem(section="experience", text="Worked on a project.", comment="Use stronger action verbs and quantify achievements.", is_positive=True)
        ]
    )

    # Make sure user_profile.json exists and has initial data for testing this directly
    try:
        current_profile = load_json_data(USER_PROFILE_FILE)
        if not current_profile.get("learned_preferences"):
            current_profile["learned_preferences"] = {}
            save_json_data(USER_PROFILE_FILE, current_profile)
    except Exception:
        # Create a minimal user_profile.json if it doesn't exist for direct testing
        save_json_data(USER_PROFILE_FILE, {"core_data": {}, "learned_preferences": {}})

    process_feedback_and_update_preferences(example_feedback)

    updated_profile = load_json_data(USER_PROFILE_FILE)
    print(f"Updated user profile after direct feedback service test: {updated_profile}")