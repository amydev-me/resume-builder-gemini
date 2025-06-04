import json
from typing import Dict, Any, List, Optional
from ..schemas.feedback import FeedbackItem
from ..core_ai.llm_client import LLMClient
from ..utils.text_processing import clean_llm_output
from ..schemas.feedback import ResumeFeedback
class AgenticLearner:
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client

    def _interpret_feedback_with_llm(self, feedback_comment: str, current_user_profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Uses the LLM to interpret a natural language feedback comment and extract
        both stylistic preferences (as dynamic rules) and suggested core data updates.
        The LLM's response should be a structured JSON indicating intent.
        """
        current_core_data_json = json.dumps(current_user_profile.get("core_data", {}), indent=2)
        current_preferences_json = json.dumps(current_user_profile.get("learned_preferences", []), indent=2)

        prompt = (
            f"You are an AI assistant tasked with interpreting user feedback on a resume. "
            f"Your goal is to extract two types of information from the user's comment:\n"
            f"1. **Stylistic Preferences (Rules/Guidelines):** How the resume should be written. Examples: 'Ensure the summary is concise.', 'Use strong action verbs in the experience section.', 'Quantify achievements whenever possible.', 'Maintain a professional tone.'\n"
            f"2. **Content Exclusion/Inclusion Rules:** What specific content or keywords from the core data should be omitted or explicitly included in the generated resume. Examples: 'Do not include C# language details.', 'Exclude projects older than 2020.', 'Ensure to highlight Python and AI skills.'\n" # <--- Add this new rule type
            f"3. **Factual Core Data Updates:** Changes or additions to the user's personal information, job history, education, skills, projects, etc.\n\n"
            f"Here is the user's current known core data:\n```json\n{current_core_data_json}\n```\n"
            f"And their current learned writing preferences (as a list of rules):\n```json\n{current_preferences_json}\n```\n\n"
            f"Based on the following user feedback, identify relevant changes. "
            f"Output a single JSON object with two main keys: `rules` and `core_data_updates`. "
            f"If no updates of a certain type are needed, the corresponding value should be an empty object or array.\n\n"
            f"**Schema for Output:**\n"
            f"```json\n"
            f"{{\n"
            f"  \"rules\": [\n"
            f"    {{\n"
            f"      \"action\": \"add\" | \"update\" | \"remove\",\n"
            f"      \"id\": \"existing_rule_id\" | null,\n"
            f"      \"rule\": \"Natural language rule/guideline or content exclusion rule\",\n" # <--- Update description
            f"      \"type\": \"stylistic\" | \"exclusion\" | \"inclusion\", // <--- NEW FIELD: rule type\n"
            f"      \"active\": true | false\n"
            f"    }},\n"
            f"    // ... more rules\n"
            f"  ],\n"
            f"  \"core_data_updates\": {{\n"
            f"**Schema for Output:**\n"
            f"```json\n"
            f"{{\n"
            f"  \"rules\": [\n"
            f"    {{\n"
            f"      \"action\": \"add\" | \"update\" | \"remove\",\n"
            f"      \"id\": \"existing_rule_id\" | null, // Only for 'update' or 'remove'\n"
            f"      \"rule\": \"Natural language rule/guideline\", // Only for 'add' or 'update'\n"
            f"      \"type\": \"stylistic\" | \"exclusion\" | \"inclusion\", // <--- NEW FIELD: rule type\n"
            f"      \"active\": true | false // Only for 'add' or 'update', default to true\n"
            f"    }},\n"
            f"    // ... more rules\n"
            f"  ],\n"
            f"  \"core_data_updates\": {{\n"
             f"    \"full_name\": \"New Name\" | null,\n"
            f"    \"email\": \"new@example.com\" | null,\n"
            f"    \"phone\": \"+1234567890\" | null,\n"
            f"    \"linkedin\": \"new_linkedin_url\" | null,\n"
            f"    \"years_of_experience\": 9 | null, "
            f"    \"job_history_add\": [{{\"title\": \"New Role\", \"company\": \"New Co\", ...}}],\n"
            f"    \"job_history_update\": [{{\"company\": \"Old Co\", \"updates\": {{\"responsibilities\": \"new responsibilities\"}}}}],\n"
            f"    \"job_history_remove\": [\"Company Name to Remove\"],\n"
            f"    \"education_add\": [{{\"degree\": \"PhD\", \"institution\": \"Uni\", ...}}],\n"
            f"    \"education_update\": [{{\"institution\": \"Old Uni\", \"updates\": {{\"degree\": \"New Degree\"}}}}],\n"
            f"    \"education_remove\": [\"Institution Name to Remove\"],\n"
            f"    \"skills_add\": [\"PostgreSQL\", \"Docker\"],\n"
            f"    \"skills_remove\": [\"OldSkill\"],\n"
            f"    \"projects_add\": [{{\"name\": \"New Project\", \"description\": \"...\"}}],\n"
            f"    \"projects_update\": [{{\"name\": \"Old Project\", \"updates\": {{\"description\": \"new desc\"}}}}],\n"
            f"    \"projects_remove\": [\"Project Name to Remove\"]\n"
            f"    // ... add more as needed for other sections\n"
            f"  }}\n"
            f"}}\n"
            f"```\n\n"
            f"Ensure all string values are enclosed in double quotes. Only provide fields that are explicitly indicated by the user feedback. Prioritize concrete, actionable changes.  For 'rules', generate concise and clear guidelines that can be directly applied during resume generation.  If a rule already exists that covers the feedback, suggest updating that rule instead of adding a new one.  If a rule is no longer relevant, suggest removing it.\n\n"
            f"User Feedback: '{feedback_comment}'\n"
            f"JSON Output:"
        )

        response_text = self.llm_client.generate_text(prompt, temperature=0.1, max_output_tokens=1024)
        cleaned_response = clean_llm_output(response_text)

        try:
            interpreted_data = json.loads(cleaned_response)
            return interpreted_data
        except json.JSONDecodeError:
            print(f"Warning: LLM did not return valid JSON for feedback '{feedback_comment}': {cleaned_response}")
            return {"rules": [], "core_data_updates": {}}

    def update_user_profile_from_feedback(self, current_user_profile: Dict[str, Any], feedback_items: List[FeedbackItem]) -> Dict[str, Any]:
        """
        Updates the user's profile (core data and learned preferences/rules) based on feedback,
        using the LLM to interpret complex natural language comments.
        """
        updated_profile = current_user_profile.copy()
        current_core_data = updated_profile.get("core_data", {})
        current_rules = updated_profile.get("learned_preferences", [])

        for item in feedback_items:
            if not item.comment:
                continue

            llm_interpretation = self._interpret_feedback_with_llm(item.comment, updated_profile)

            # --- Manage Rules (learned_preferences) ---
            extracted_rules = llm_interpretation.get("rules", [])
            for rule_action in extracted_rules:
                action = rule_action.get("action")
                if action == "add":
                    new_rule = {
                        "id": f"pref_{len(current_rules) + 1}", # Simple ID generation for now
                        "rule": rule_action.get("rule"),
                        "active": rule_action.get("active", True) # Default to active
                    }
                    current_rules.append(new_rule)
                elif action == "update":
                    rule_id = rule_action.get("id")
                    for existing_rule in current_rules:
                        if existing_rule["id"] == rule_id:
                            existing_rule["rule"] = rule_action.get("rule")
                            existing_rule["active"] = rule_action.get("active", True)
                            break # Assume only one match
                elif action == "remove":
                    rule_id = rule_action.get("id")
                    current_rules = [r for r in current_rules if r["id"] != rule_id]

            # --- Apply Core Data Updates (same as before) ---
            extracted_core_data_updates = llm_interpretation.get("core_data_updates", {})
            for key in ["full_name", "email", "phone", "linkedin", "years_of_experience"]:
                if key in extracted_core_data_updates and extracted_core_data_updates[key] is not None:
                    current_core_data[key] = extracted_core_data_updates[key]

            if "skills_add" in extracted_core_data_updates and isinstance(extracted_core_data_updates["skills_add"], list):
                existing_skills = set(current_core_data.get("skills", []))
                for skill in extracted_core_data_updates["skills_add"]:
                    if skill not in existing_skills:
                        current_core_data.setdefault("skills", []).append(skill)
                        existing_skills.add(skill)

            if "skills_remove" in extracted_core_data_updates and isinstance(extracted_core_data_updates["skills_remove"], list):
                current_core_data["skills"] = [
                    s for s in current_core_data.get("skills", []) if s not in extracted_core_data_updates["skills_remove"]
                ]

            if "job_history_add" in extracted_core_data_updates and isinstance(extracted_core_data_updates["job_history_add"], list):
                current_core_data.setdefault("job_history", []).extend(extracted_core_data_updates["job_history_add"])

            if "education_add" in extracted_core_data_updates and isinstance(extracted_core_data_updates["education_add"], list):
                current_core_data.setdefault("education", []).extend(extracted_core_data_updates["education_add"])

            if "projects_add" in extracted_core_data_updates and isinstance(extracted_core_data_updates["projects_add"], list):
                current_core_data.setdefault("projects", []).extend(extracted_core_data_updates["projects_add"])

            if extracted_core_data_updates.get("job_history_update") or extracted_core_data_updates.get("job_history_remove"):
                print("Warning: Complex job_history update/remove logic not fully implemented yet.")
            if extracted_core_data_updates.get("education_update") or extracted_core_data_updates.get("education_remove"):
                print("Warning: Complex education update/remove logic not fully implemented yet.")
            if extracted_core_data_updates.get("projects_update") or extracted_core_data_updates.get("projects_remove"):
                print("Warning: Complex projects update/remove logic not fully implemented yet.")

        updated_profile["core_data"] = current_core_data
        updated_profile["learned_preferences"] = current_rules
        return updated_profile

# Example usage (for testing this module directly)
if __name__ == "__main__":
    llm_client_for_test = LLMClient()
    learner = AgenticLearner(llm_client_for_test)

    # Initial profile data for testing (with the new rule structure)
    initial_user_profile = {
        "core_data": {
            "full_name": "Jane Doe",
            "email": "jane.doe@example.com",
            "phone": "+1 (555) 123-4567",
            "job_history": [
                {"title": "Software Engineer", "company": "Acme Inc.", "dates": "2020-2024", "responsibilities": "Developed backend systems."}
            ],
            "education": [],
            "skills": ["Python", "JavaScript"]
        },
        "learned_preferences": [
            {"id": "pref_001", "rule": "Ensure the summary is concise.", "active": True},
            {"id": "pref_002", "rule": "Use action verbs.", "active": True}
        ]
    }

    print("--- Initial Profile ---")
    print(json.dumps(initial_user_profile, indent=2))
    print("-" * 30)

    # Test Feedback 1: Add a new rule and update core data
    feedback_1 = ResumeFeedback(
        resume_version_id="dummy_id_1",
        feedback_items=[
            FeedbackItem(
                section="overall",
                text="",
                comment="The summary is still too long. Please add a rule to limit it to 3 sentences. Also, I have 9 years of experience.",
                is_positive=True
            )
        ]
    )
    print("\n--- Processing Feedback 1 ---")
    updated_profile_1 = learner.update_user_profile_from_feedback(initial_user_profile, feedback_1.feedback_items)
    print("--- After Feedback 1 ---")
    print(json.dumps(updated_profile_1, indent=2))
    print("-" * 30)

    # Test Feedback 2: Update an existing rule and add a skill
    feedback_2 = ResumeFeedback(
        resume_version_id="dummy_id_2",
        feedback_items=[
            FeedbackItem(
                section="experience",
                text="",
                comment="Update the 'Use action verbs' rule to be more specific: 'Every bullet point in the experience section must start with a strong action verb.' Also, add 'PostgreSQL' to my skills.",
                is_positive=True
            )
        ]
    )
    print("\n--- Processing Feedback 2 ---")
    updated_profile_2 = learner.update_user_profile_from_feedback(updated_profile_1, feedback_2.feedback_items)
    print("--- After Feedback 2 ---")
    print(json.dumps(updated_profile_2, indent=2))
    print("-" * 30)

    # Test Feedback 3: Remove a rule
    feedback_3 = ResumeFeedback(
        resume_version_id="dummy_id_3",
        feedback_items=[
            FeedbackItem(
                section="summary",
                text="",
                comment="The 'Ensure the summary is concise' rule is too restrictive. Please remove it.",
                is_positive=False  # This could also be used to signal removal
            )
        ]
    )
    print("\n--- Processing Feedback 3 ---")
    updated_profile_3 = learner.update_user_profile_from_feedback(updated_profile_2, feedback_3.feedback_items)
    print("--- After Feedback 3 ---")
    print(json.dumps(updated_profile_3, indent=2))
    print("-" * 30)