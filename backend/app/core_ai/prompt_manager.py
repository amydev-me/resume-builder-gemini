from typing import Dict, Any, List


class PromptManager:
    def __init__(self):
        # Base instructions for the LLM
        self.base_instructions = (
            "You are an expert resume writer and career coach. Your goal is to create highly effective, "
            "professional, and concise resume content. Always maintain a professional tone. "
            "Focus on achievements, quantification, and relevant skills. Avoid jargon where possible. "
            "Respond only with the resume content, no conversational filler. Format the resume clearly with distinct sections (e.g., Summary, Experience, Education, Skills)."
        )

    def generate_resume_prompt(self, user_core_data: Dict[str, Any], learned_preferences: List[Dict[str, Any]],
                               initial_request: str = "", target_job_description: str = "") -> str:
        """
        Constructs a comprehensive prompt for Gemini to generate a resume.
        Combines core data, dynamic learned preferences (rules), and specific requests.
        """

        prompt_parts = [self.base_instructions]

        # 1. User Core Data
        prompt_parts.append(f"\nHere is the candidate's core information:")
        prompt_parts.append(f"- Full Name: {user_core_data.get('full_name', 'Unknown')}")
        prompt_parts.append(
            f"- Contact: Email: {user_core_data.get('email', 'N/A')}, Phone: {user_core_data.get('phone', 'N/A')}, LinkedIn: {user_core_data.get('linkedin', 'N/A')}")

        # Add years of experience if available
        if 'years_of_experience' in user_core_data and user_core_data['years_of_experience'] is not None:
            prompt_parts.append(f"- Total Years of Experience: {user_core_data['years_of_experience']} years")

        if user_core_data.get('job_history'):
            prompt_parts.append("\n- Job History (Please summarize each responsibility using strong action verbs and quantify outcomes where appropriate):")  # <--- Add this instruction

            for job in user_core_data['job_history']:
                prompt_parts.append(
                    f"  * {job.get('title', '')} at {job.get('company', '')} ({job.get('dates', '')}): {job.get('responsibilities', '')}")

        if user_core_data.get('education'):
            prompt_parts.append("\n- Education:")

            for edu in user_core_data['education']:
                prompt_parts.append(
                    f"  * {edu.get('degree', '')} in {edu.get('major', '')} from {edu.get('institution', '')} ({edu.get('dates', '')})")

        if user_core_data.get('skills'):
            prompt_parts.append(f"\n- Skills: {', '.join(user_core_data['skills'])}")


        if user_core_data.get('certifications'):
            prompt_parts.append(f"\n- Certifications: {', '.join(user_core_data['certifications'])}")

        if user_core_data.get('projects'):
            prompt_parts.append("\n- Projects:")
            for proj in user_core_data['projects']:
                prompt_parts.append(f"  * {proj.get('name', '')}: {proj.get('description', '')}")

        # 2. Learned Preferences (Dynamic Agentic Rules)
        # Iterate over the list of rules and add them to the prompt if active

        if learned_preferences:  # Check if the list is not empty
            prompt_parts.append(
                "\nBased on previous interactions and feedback, apply the following specific guidelines and preferences:")
            for rule_obj in learned_preferences:
                if rule_obj.get("active", True):  # Only add active rules
                    rule_text = rule_obj.get("rule")
                    if rule_text:
                        prompt_parts.append(f"- {rule_text}")

        # 3. Specific Request (from frontend, e.g., target JD)
        if initial_request:
            prompt_parts.append(f"\nUser's specific instruction for this generation: {initial_request}")

        if target_job_description:
            prompt_parts.append(
                f"\nTarget Job Description (emphasize relevant skills/experience): {target_job_description}")
            prompt_parts.append(
                "Prioritize content that aligns with the job description's requirements. Look for keywords and concepts.")

        prompt_parts.append(
            "\n\nNow, generate the complete resume based on all the above information. Ensure it is formatted clearly with distinct sections (e.g., Summary, Experience, Education, Skills).")

        stylistic_rules = []
        exclusion_rules = []
        inclusion_rules = []  # For potential future "must include X" rules

        if learned_preferences:
            for rule_obj in learned_preferences:
                if rule_obj.get("active", True):
                    rule_text = rule_obj.get("rule")
                    rule_type = rule_obj.get("type", "stylistic")  # Default to stylistic if type not specified
                    if rule_text:
                        if rule_type == "stylistic":
                            stylistic_rules.append(rule_text)
                        elif rule_type == "exclusion":
                            exclusion_rules.append(rule_text)
                        elif rule_type == "inclusion":
                            inclusion_rules.append(rule_text)

        if stylistic_rules:
            prompt_parts.append(
                "\nBased on previous interactions and feedback, apply the following specific stylistic guidelines:")
            for rule_text in stylistic_rules:
                prompt_parts.append(f"- {rule_text}")

        if exclusion_rules:
            prompt_parts.append(
                "\nIMPORTANT: Adhere strictly to the following content exclusion rules. Do NOT include any information related to these topics or keywords from the provided core data:")
            for rule_text in exclusion_rules:
                prompt_parts.append(f"- {rule_text}")  # LLM will read "Do not include C# language details."

        if inclusion_rules:
            prompt_parts.append(
                "\nIMPORTANT: Ensure the generated resume explicitly highlights the following. Prioritize content that reflects these areas:")
            for rule_text in inclusion_rules:
                prompt_parts.append(f"- {rule_text}")

        return "\n".join(prompt_parts)


# Example usage (for testing this module directly)
if __name__ == "__main__":
    pm = PromptManager()

    test_core_data = {
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "years_of_experience": 9,
        "job_history": [
            {"title": "Software Engineer", "company": "Acme Inc.", "dates": "2020-2024",
             "responsibilities": "Developed backend systems."}
        ],
        "skills": ["Python", "JavaScript", "SQL"]
    }

    # Example preferences (matching the new list of rules structure)
    test_preferences_1 = [
        {"id": "pref_001", "rule": "Ensure the summary is no more than 3 sentences.", "active": True},
        {"id": "pref_002", "rule": "Every bullet point must start with a strong, impactful action verb.",
         "active": True},
        {"id": "pref_003", "rule": "Quantify achievements numerically whenever possible.", "active": True},
        {"id": "pref_004", "rule": "Maintain a professional and innovative tone.", "active": True}
    ]

    test_preferences_2 = [
        {"id": "pref_001", "rule": "Keep all sections concise.", "active": True},
        {"id": "pref_005", "rule": "Exclude references section.", "active": True}
    ]

    print("--- Prompt Example 1 (Dynamic Rules) ---")
    prompt1 = pm.generate_resume_prompt(
        test_core_data,
        test_preferences_1,
        initial_request="Create a resume optimized for a Senior Developer role.",
        target_job_description="Seeking a Senior Python Developer to lead projects and mentor junior developers."
    )
    print(prompt1)
    print("-" * 50)

    print("\n--- Prompt Example 2 (Different Dynamic Rules) ---")
    prompt2 = pm.generate_resume_prompt(
        test_core_data,
        test_preferences_2,
        initial_request="Just update the education section to be more descriptive."
    )
    print(prompt2)
    print("-" * 50)