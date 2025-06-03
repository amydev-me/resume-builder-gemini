from typing import Dict, Any, List
from ..schemas.feedback import FeedbackItem
from ..core_ai.llm_client import LLMClient  # Import the LLMClient
from ..utils.text_processing import clean_llm_output


class AgenticLearner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _extract_preferences_with_llm(self, feedback_comment: str) -> Dict[str, Any]:
        """
        Uses the LLM to intelligently extract structured preferences from a natural language feedback comment.
        """
        prompt = (
            f"Analyze the following user feedback comment on a resume section. "
            f"Identify any implied preferences regarding conciseness, action verbs, quantification, tone, "
            f"or specific keywords/sections. "
            f"Output the preferences as a JSON object with keys like 'conciseness_level' (high/medium/low), "
            f"'action_verb_preference' (strong/normal), 'quantification_emphasis' (high/normal), 'tone' (e.g., professional, innovative, friendly), "
            f"'preferred_keywords' (list of strings), 'sections_to_include' (list of strings). "
            f"If a preference is not explicitly mentioned, omit it. "
            f"Example: 'Make it shorter and more impactful' -> {{'conciseness_level': 'high', 'action_verb_preference': 'strong', 'tone': 'impactful'}} "
            f"Example: 'Needs more numbers and metrics' -> {{'quantification_emphasis': 'high'}} "
            f"Example: 'Sound more professional.' -> {{'tone': 'professional'}} "
            f"Feedback: '{feedback_comment}'"
        )

        # Use a lower temperature for more deterministic output
        response_text = self.llm_client.generate_text(prompt, temperature=0.1, max_output_tokens=256)

        # Clean the output (remove markdown blocks if LLM adds them)
        cleaned_response = clean_llm_output(response_text)

        try:
            # Attempt to parse the JSON output from the LLM
            extracted_prefs = json.loads(cleaned_response)
            return extracted_prefs
        except json.JSONDecodeError:
            print(f"Warning: LLM did not return valid JSON for feedback '{feedback_comment}': {cleaned_response}")
            return {}  # Return empty dict if parsing fails

    def update_preferences_from_feedback(self,
                                         current_preferences: Dict[str, Any],
                                         feedback_items: List[FeedbackItem]) -> Dict[str, Any]:
        """
        Updates the user's learned preferences based on feedback items.
        Uses LLM to interpret complex feedback.
        """
        updated_preferences = current_preferences.copy()

        for item in feedback_items:
            if item.comment:
                llm_extracted_prefs = self._extract_preferences_with_llm(item.comment)
                # Merge LLM-extracted preferences. LLM-extracted take precedence or are added.
                # You can implement more sophisticated merging logic if needed.
                updated_preferences.update(llm_extracted_prefs)

                # Simple explicit keyword mapping (can coexist with LLM extraction)
                comment_lower = item.comment.lower()
                if "concise" in comment_lower or "shorter" in comment_lower:
                    if item.is_positive:
                        updated_preferences["conciseness_level"] = "high"
                    elif "too" in comment_lower or "overly" in comment_lower:
                        updated_preferences["conciseness_level"] = "medium"  # E.g., "too concise" might mean medium
                    else:  # Negative feedback for conciseness
                        updated_preferences["conciseness_level"] = "medium"  # Default negative

                if "action verb" in comment_lower or "impactful" in comment_lower:
                    updated_preferences["action_verb_preference"] = "strong"

                if "quantify" in comment_lower or "numbers" in comment_lower or "metrics" in comment_lower:
                    updated_preferences["quantification_emphasis"] = "high"

                # Add more rules as needed for common terms or patterns

        return updated_preferences


import json  # Ensure json is imported for direct testing

# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Ensure LLMClient is initialized for the test
    llm_client_for_test = LLMClient()
    learner = AgenticLearner(llm_client_for_test)

    initial_prefs = {
        "conciseness_level": "medium",
        "action_verb_preference": "normal",
        "quantification_emphasis": "normal",
        "tone": "professional"
    }

    print(f"Initial Preferences: {initial_prefs}")

    # Example 1: User wants more conciseness and impact
    feedback_1 = ResumeFeedback(
        resume_version_id="dummy_id_1",
        feedback_items=[
            FeedbackItem(section="summary", text="old text",
                         comment="Make this summary much shorter and more impactful.", is_positive=True)
        ]
    )
    updated_prefs_1 = learner.update_preferences_from_feedback(initial_prefs, feedback_1.feedback_items)
    print("\n--- After Feedback 1 (shorter, impactful) ---")
    print(updated_prefs_1)

    # Example 2: User wants more numbers and a friendlier tone
    feedback_2 = ResumeFeedback(
        resume_version_id="dummy_id_2",
        feedback_items=[
            FeedbackItem(section="experience", text="old text",
                         comment="Need more numbers and metrics here. Also, can the overall tone be a bit friendlier?",
                         is_positive=True)
        ]
    )
    updated_prefs_2 = learner.update_preferences_from_feedback(updated_prefs_1, feedback_2.feedback_items)
    print("\n--- After Feedback 2 (numbers, friendlier) ---")
    print(updated_prefs_2)

    # Example 3: User says something non-standard or negative
    feedback_3 = ResumeFeedback(
        resume_version_id="dummy_id_3",
        feedback_items=[
            FeedbackItem(section="skills", text="old text",
                         comment="I don't like the generic phrasing of the soft skills.", is_positive=False)
        ]
    )
    updated_prefs_3 = learner.update_preferences_from_feedback(updated_prefs_2, feedback_3.feedback_items)
    print("\n--- After Feedback 3 (negative, general) ---")
    print(
        updated_prefs_3)  # This might not change much based on simple keyword extraction, but LLM could infer "avoid generic phrases"