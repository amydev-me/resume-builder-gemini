from typing import Dict, Any, List,  Optional
import json # Ensure json is imported


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

        # --- Job History Section ---
        if user_core_data.get('job_history'):
            prompt_parts.append("\n- **Work Experience:**")
            # Sort jobs in reverse chronological order based on dates
            sorted_jobs = sorted(user_core_data['job_history'], key=lambda x: x.get('dates', ''), reverse=True)

            for job in sorted_jobs:
                title = job.get('title', '')
                company = job.get('company', '')
                location = job.get('location', '')
                dates = job.get('dates', '')
                responsibilities = job.get('responsibilities', '')  # This is your raw input line(s)

                prompt_parts.append(
                    f"\n  * **{title}** at {company} | {location} | {dates}\n"
                    f"    Based on the following core responsibilities provided, **expand each into 3-5 impactful, quantified bullet points**. "
                    f"Focus on the 'Problem-Action-Result' (PAR) or 'Situation-Task-Action-Result' (STAR) methodology. "
                    f"**Elaborate on technical challenges, solutions, and measurable outcomes.** "
                    f"If the input is generic or concise, **infer and add relevant details, common tasks, and achievements for such roles** (e.g., for a Full Stack Engineer (AI), think about data integration, API development, performance optimization, model deployment, and collaboration with cross-functional teams). "
                    f"Ensure each bullet point starts with a strong action verb.\n"
                    f"    **Core Responsibilities for Expansion (Analyze these):**\n"
                    f"    ```\n"
                    f"    {responsibilities}\n"  # The AI will read and expand upon this
                    f"    ```\n"
                    f"    **Generated Detailed Bullet Points (aim for 3-5 comprehensive points):**"
                    # This is where the AI will write
                )

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
            prompt_parts.append("\n\n**Overall Resume Guidelines (Apply these after generating all sections):**")
            for rule_text in stylistic_rules:
                prompt_parts.append(f"- {rule_text}")

        if exclusion_rules:
            prompt_parts.append(
                "\nIMPORTANT: Adhere strictly to the following content exclusion rules. Do NOT include any information related to these topics or keywords:")
            for rule_text in exclusion_rules:
                prompt_parts.append(f"- {rule_text}")

        if inclusion_rules:
            prompt_parts.append(
                "\nIMPORTANT: Ensure the generated resume explicitly highlights the following. Prioritize content that reflects these areas:")
            for rule_text in inclusion_rules:
                prompt_parts.append(f"- {rule_text}")

        prompt_parts.append("\n**Generate the complete resume now, strictly adhering to all the instructions, data, and preferences provided.**")
        prompt_parts.append("Format the resume in a clean, professional, and easy-to-read markdown format.")
        return "\n".join(prompt_parts)

    def generate_suggestions_prompt(self, user_core_data: Dict[str, Any], learned_preferences: List[Dict[str, Any]],
                                    target_job_description: Optional[str] = None) -> str:
        """
        Constructs a comprehensive prompt for the LLM to generate proactive resume suggestions.
        Analyzes core data, learned preferences, and an optional target job description.
        """
        core_data_json = json.dumps(user_core_data, indent=2)
        preferences_json = json.dumps(learned_preferences, indent=2)

        prompt = (
            "You are an expert career coach and resume strategist. Your primary goal is to analyze a candidate's resume data "
            "and their past learned preferences, then provide proactive, actionable suggestions for improving their resume. "
            "Focus on best practices for modern, ATS-friendly resumes (conciseness, quantification, strong action verbs, relevance).\n\n"
        )

        prompt += (
            "**Candidate's Current Core Resume Data (JSON format):**\n```json\n"
            f"{core_data_json}\n```\n\n"
        )

        if learned_preferences:
            prompt += (
                "**Candidate's Previously Learned Preferences/Rules (JSON format):**\n```json\n"
                f"{preferences_json}\n```\n"
                "When providing suggestions, acknowledge these existing preferences and do not suggest things already covered by active rules. If a rule is about an area that still needs improvement despite the rule, phrase the suggestion as a reinforcement or a deeper dive.\n\n"
            )
        else:
            prompt += "Candidate has no specific learned preferences yet.\n\n"

        if target_job_description:
            prompt += (
                f"**Target Job Description for Contextual Analysis:**\n```\n{target_job_description}\n```\n"
                "Prioritize suggestions that help align the resume more closely with this job description. Identify potential skill gaps, areas to emphasize, or experiences to rephrase for maximum relevance to this role.\n\n"
            )

        prompt += (
            "Based on the above information, provide a list of clear, concise, and professional suggestions. "
            "Focus on actionable advice. Output your suggestions as a JSON array where each object strictly follows this schema:\n"
            f"```json\n"
            f"[\n"
            f"  {{\n"
            f"    \"category\": \"string\", // Must be one of: \"Content Improvement\", \"Stylistic Tip\", \"Skill Gap\", \"Formatting\", \"Overall Strategy\"\n"
            f"    \"suggestion\": \"string\", // The natural language suggestion, e.g., \"Consider adding quantified achievements to your job history in the form of numbers and percentages.\"\n"
            f"    \"action_type\": \"string\" | null, // Optional: e.g., \"add_skill\", \"rephrase_summary\", \"quantify_experience\", \"update_section\"\n"
            f"    \"relevant_field\": \"string\" | null // Optional: e.g., \"skills\", \"summary\", \"job_history.responsibilities\", \"education\"\n"
            f"  }}\n"
            f"]\n"
            f"```\n\n"
            "Provide at least 3 to 5 distinct and valuable suggestions. Do not include any conversational text outside the JSON. Ensure the JSON is valid and complete."
        )

        return prompt

    def generate_critique_prompt(self,
                                 resume_draft: str,
                                 learned_preferences: List[Dict[str, Any]],
                                 target_job_description: Optional[str] = None) -> str:
        """
        Constructs a prompt for the LLM to critique a generated resume draft.
        """
        preferences_json = json.dumps(learned_preferences, indent=2)

        prompt = (
            "You are an expert resume reviewer and AI assistant. Your task is to critically analyze a generated resume "
            "against specific guidelines and a target job description (if provided). "
            "Identify any areas where the resume deviates from the instructions or could be improved.\n\n"
        )

        prompt += "**Resume to Critique:**\n```\n"
        prompt += resume_draft  # Use resume_draft here
        prompt += "\n```\n\n"

        if learned_preferences:
            prompt += "**Learned Preferences (Rules to enforce):**\n```json\n"
            prompt += preferences_json
            prompt += "\n```\n"
            prompt += "Strictly identify if any of these active rules have been violated. For rules with `applies_to_target_job_only: true`, only enforce them if a target job description is provided below.\n\n"

        if target_job_description:
            prompt += "**Target Job Description (to tailor the resume to):**\n```\n"
            prompt += target_job_description
            prompt += "\n```\n"
            prompt += "Assess how well the resume is tailored to this job description. Look for keyword relevance, skill alignment, and emphasis on relevant experiences.\n\n"

        prompt += (
            "Identify specific issues or areas for improvement. Be concise and actionable in your critique. "
            "Output a JSON object with two keys: `issues` (a list of critique items) and `overall_assessment` (a brief summary). "
            "Also include a `has_issues` boolean indicating if any issues were found.\n"
            "**Critique Item Schema:**\n"
            f"```json\n"
            f"{{\n"
            f"  \"issues\": [\n"
            f"    {{\n"
            f"      \"category\": \"Rule Violation\" | \"Stylistic\" | \"Content Gap\" | \"Target JD Mismatch\" | \"Best Practice\" | \"Other\",\n"
            f"      \"description\": \"Specific description of the issue, e.g., 'Summary is too long; needs to be under 3 sentences.'\",\n"
            f"      \"severity\": \"low\" | \"medium\" | \"high\",\n"
            f"      \"relevant_rule_id\": \"Optional: ID of the rule if applicable\",\n"
            f"      \"suggested_action\": \"Optional: Actionable advice to fix (e.g., 'shorten', 'add numbers', 'remove')\"\n"
            f"    }}\n"
            f"  ],\n"
            f"  \"overall_assessment\": \"A brief, overall summary of the critique.\",\n"
            f"  \"has_issues\": true | false\n"
            f"}}\n"
            f"```\n\n"
            "If no issues are found, the `issues` list should be empty and `has_issues` should be `false`."
        )
        return prompt

    def generate_refinement_prompt(self, previous_resume_content: str, critiques: List[Dict[str, Any]],
                                   user_core_data: Dict[str, Any], learned_preferences: List[Dict[str, Any]],
                                   target_job_description: Optional[str] = None) -> str:
        """
        Constructs a prompt for the LLM to refine a resume based on specific critiques.
        """
        critiques_json = json.dumps(critiques, indent=2)
        preferences_json = json.dumps(learned_preferences, indent=2)
        core_data_json = json.dumps(user_core_data, indent=2)

        prompt = (
            "You are an expert resume writer and AI assistant tasked with refining a resume. "
            "You have been provided with a previous version of a resume and a list of specific critiques. "
            "Your goal is to address *all* the critiques and generate a *new, improved version* of the resume. "
            "Ensure the refined resume still adheres to all original instructions, core data, and learned preferences.\n\n"
        )

        prompt += "**Previous Resume Version:**\n```\n"
        prompt += previous_resume_content
        prompt += "\n```\n\n"

        prompt += "**Critiques to Address:**\n```json\n"
        prompt += critiques_json
        prompt += "\n```\n\n"

        prompt += (
            "**Original User Core Data (for reference on content):**\n```json\n"
            f"{core_data_json}\n```\n\n"
        )
        prompt += (
            "**Original Learned Preferences (Rules to still enforce):**\n```json\n"
            f"{preferences_json}\n```\n\n"
        )

        if target_job_description:
            prompt += (
                "**Original Target Job Description (for continued tailoring):**\n```\n"
                f"{target_job_description}\n```\n\n"
            )

        prompt += (
            "Generate the complete, refined resume. Focus exclusively on fixing the identified issues. "
            "Ensure the output is a professional, markdown-formatted resume and contains no conversational text outside the resume content itself."
        )
        return prompt


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