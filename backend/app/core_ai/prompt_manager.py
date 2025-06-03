from typing import Dict, Any, List


class PromptManager:
    def __init__(self):
        # Base instructions for the LLM
        self.base_instructions = (
            "You are an expert resume writer and career coach. Your goal is to create highly effective, "
            "professional, and concise resume content. Always maintain a professional tone. "
            "Focus on achievements, quantification, and relevant skills. Avoid jargon where possible. "
            "Respond only with the resume content, no conversational filler."
        )

    def generate_resume_prompt(self, user_core_data: Dict[str, Any], learned_preferences: Dict[str, Any],
                               initial_request: str = "", target_job_description: str = "") -> str:
        """
        Constructs a comprehensive prompt for Gemini to generate a resume.
        Combines core data, learned preferences, and specific requests.
        """
        prompt_parts = [self.base_instructions]

        # 1. User Core Data
        prompt_parts.append(f"\nHere is the candidate's core information:")
        prompt_parts.append(f"- Full Name: {user_core_data.get('full_name', 'Unknown')}")
        prompt_parts.append(
            f"- Contact: Email: {user_core_data.get('email', 'N/A')}, Phone: {user_core_data.get('phone', 'N/A')}, LinkedIn: {user_core_data.get('linkedin', 'N/A')}")

        if user_core_data.get('job_history'):
            prompt_parts.append("\n- Job History:")
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

        # 2. Learned Preferences (Agentic Memory)
        prompt_parts.append("\nBased on previous interactions, the candidate prefers the following:")
        if learned_preferences.get("conciseness_level") == "high":
            prompt_parts.append("- Be very concise and direct. Keep sentences and bullet points short.")
        elif learned_preferences.get("conciseness_level") == "medium":
            prompt_parts.append("- Maintain a moderate level of detail.")
        elif learned_preferences.get("conciseness_level") == "low":
            prompt_parts.append("- Provide more detail and elaborate on achievements and responsibilities.")

        if learned_preferences.get("action_verb_preference") == "strong":
            prompt_parts.append(
                "- Start almost every bullet point with a strong, impactful action verb (e.g., 'Led', 'Developed', 'Managed', 'Implemented').")
        elif learned_preferences.get("action_verb_preference") == "normal":
            prompt_parts.append("- Use a good mix of action verbs, varying them to avoid repetition.")

        if learned_preferences.get("quantification_emphasis") == "high":
            prompt_parts.append(
                "- **Quantify achievements numerically whenever possible.** Provide metrics and specific results (e.g., 'Increased efficiency by 15%', 'Managed a budget of $2M').")
        elif learned_preferences.get("quantification_emphasis") == "normal":
            prompt_parts.append("- Quantify achievements where natural and impactful.")

        if learned_preferences.get("tone"):
            prompt_parts.append(f"- The preferred tone is: {learned_preferences['tone']}.")

        if learned_preferences.get("sections_to_include"):
            prompt_parts.append(
                f"- Include the following sections: {', '.join(learned_preferences['sections_to_include'])}.")

        if learned_preferences.get("preferred_keywords"):
            prompt_parts.append(
                f"- Incorporate these keywords naturally: {', '.join(learned_preferences['preferred_keywords'])}.")

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

        return "\n".join(prompt_parts)


# Example usage (for testing this module directly)
if __name__ == "__main__":
    pm = PromptManager()

    # Example core data (matching your user_profile.json structure)
    test_core_data = {
        "full_name": "Jane Doe",
        "email": "jane.doe@example.com",
        "job_history": [
            {"title": "Software Engineer", "company": "Acme Inc.", "dates": "2020-2024",
             "responsibilities": "Developed backend systems."}
        ],
        "skills": ["Python", "JavaScript", "SQL"]
    }

    # Example preferences (what might be in user_profile.json after feedback)
    test_preferences_1 = {
        "conciseness_level": "high",
        "action_verb_preference": "strong",
        "quantification_emphasis": "high",
        "tone": "impactful"
    }

    # Example preferences 2 (different feedback)
    test_preferences_2 = {
        "conciseness_level": "low",
        "action_verb_preference": "normal",
        "tone": "friendly",
        "sections_to_include": ["summary", "experience", "education", "awards"]
    }

    print("--- Prompt Example 1 (Concise, Strong, Quantified) ---")
    prompt1 = pm.generate_resume_prompt(
        test_core_data,
        test_preferences_1,
        initial_request="Create a resume optimized for a Senior Developer role.",
        target_job_description="Seeking a Senior Python Developer to lead projects and mentor junior developers."
    )
    print(prompt1)
    print("-" * 50)

    print("\n--- Prompt Example 2 (Detailed, Normal Verbs, Friendly) ---")
    prompt2 = pm.generate_resume_prompt(
        test_core_data,
        test_preferences_2,
        initial_request="Just update the education section to be more descriptive."
    )
    print(prompt2)
    print("-" * 50)