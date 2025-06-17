from typing import Dict, Any, List, Optional
import json  # Ensure json is imported


class PromptManager:
    def __init__(self):
        # Base instructions for the LLM
        self.base_instructions = (
            """
                You are an AI-powered Senior Resume Writer and Applicant Tracking System (ATS) Optimization Specialist. Your mission is to craft a highly tailored, professional, and impactful resume in Markdown format.

                Adhere strictly to the following core guidelines for ALL resume sections:
                1.  **Professional & Unique Tone (AVOID GENERICS):** Use formal, concise, and compelling language. **ABSOLUTELY DO NOT use overused, generic, or 'AI-sounding' phrases.** This includes, but is not limited to: 'leveraged', 'utilized', 'synergistic', 'paradigm shift', 'cutting-edge', 'state-of-the-art', 'robust solution', 'driving force', 'proven track record', 'results-driven', 'responsible for', 'played a key role in', 'spearheaded'. Find more descriptive, unique, and powerful alternatives. Vary sentence structure and vocabulary to ensure the resume stands out with human-like prose.
                2.  **Action Verbs:** Start EVERY bullet point in the 'Work Experience' and 'Projects' sections with a strong, quantifiable action verb (e.g., "Developed," "Managed," "Implemented," "Achieved," "Optimized," "Reduced," "Increased," "Streamlined," "Led," "Pioneered").
                3.  **Quantify Achievements (CRITICAL):** For each achievement, **mandatorily quantify the impact with specific numbers, percentages, financial values, or time savings (e.g., 'Increased sales by 15%', 'Reduced operational costs by $10K', 'Managed a team of 5 engineers', 'Streamlined data processing, saving 10 hours/week')**. If exact numbers are NOT provided in the user's data for a responsibility, **you MUST infer plausible, industry-standard, and impactful numerical outcomes that are common for that type of role and industry.** Do not use placeholders like 'X%' or 'Y dollars'. Make these inferred numbers sound concrete and realistic. Focus on 'Problem-Action-Result' (PAR) or 'Situation-Task-Action-Result' (STAR) methodology.
                4.  **ATS Optimization & Relevance (PRIMARY FOCUS if JD Provided):**
                    * Analyze the provided TARGET JOB DESCRIPTION thoroughly.
                    * Seamlessly integrate key skills, responsibilities, and keywords from the JD into the resume, particularly in the summary, skills, and experience sections. This must feel natural and not 'stuffed'.
                    * **Prioritize and reframe** information from the candidate's profile that directly aligns with the target job description. Rephrase existing bullet points from the candidate's work history to emphasize relevant skills and achievements for this specific role.
                    * If the job description mentions specific tools or technologies, ensure they are prominently highlighted if present in the candidate's skills/experience.
                5.  **Conciseness & Length:** Aim for a 1-2 page resume. Be concise and impactful. Every word should add value.
                6.  **Formatting:** Use clear Markdown headings (e.g., `##` for main sections, `###` for sub-sections like job titles). Use bullet points for lists. Ensure clean, professional spacing and readability.

                **Resume Structure:**
                * **Contact Information:** Full Name, Phone, Email, LinkedIn (if provided).
                * **Summary/Objective:** A concise (3-5 sentences) powerful paragraph tailored *specifically* to the target job description and highlighting the candidate's unique value proposition and career goals.
                * **Skills:** Categorized (e.g., Technical Skills, Soft Skills, Tools, Languages) and highly relevant to the JD.
                * **Work Experience:** Reverse chronological order. For each role: Job Title, Company, Dates (Month Year - Month Year or Present). Use 3-5 concise, achievement-oriented bullet points per role. Expand on provided responsibilities with inferred impact and outcomes if not explicit.
                * **Education:** Reverse chronological. Degree, Major, University, Graduation Date. Include relevant coursework, honors, or significant projects if impactful.
                * **Certifications/Awards (Optional):** List relevant certifications or notable awards.
                * **Projects (Optional):** If provided, describe relevant projects with their impact, technologies used, and outcomes.
                """
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
        # Ensure job_history is a list before processing
        if user_core_data.get('job_history') and isinstance(user_core_data['job_history'], list):
            prompt_parts.append("\n- **Work Experience:**")
            # Sort jobs in reverse chronological order based on start_date
            # Use '9999-01' as a very late date string to ensure jobs without start_date are pushed to the end
            # when sorting in reverse (latest first).
            sorted_jobs = sorted(user_core_data['job_history'], key=lambda x: x.get('start_date', '9999-01'),
                                 reverse=True)

            for job in sorted_jobs:
                title = job.get('title', 'N/A')
                company = job.get('company', 'N/A')
                # Assuming location is not collected from frontend, you might remove this or infer from company
                # For now, keep it as empty if not provided.
                location = job.get('location', '')  # Your frontend does not collect 'location'

                start_date = job.get('start_date', '')
                end_date = job.get('end_date', 'Present')  # Default to 'Present' if end_date is not provided
                dates_str = f"{start_date} - {end_date}" if start_date else ""

                # Ensure responsibilities is a list, then join with newlines for the prompt
                responsibilities_list = job.get('responsibilities', [])
                if not isinstance(responsibilities_list, list):  # Fallback if for some reason it's not a list
                    responsibilities_list = [str(responsibilities_list)]  # Convert to list with single string
                responsibilities_prompt = "\n".join(
                    responsibilities_list) if responsibilities_list else "No responsibilities provided."

                prompt_parts.append(
                    f"\n  * **{title}** at {company} | {dates_str}\n"
                    f"    **Expand the following core responsibilities into 3-5 distinct, highly impactful, and MANDATORILY QUANTIFIED bullet points.** Each bullet point MUST start with a strong action verb and explicitly state a measurable outcome. **If the input is generic or lacks specific numbers, you are required to INFER plausible, industry-standard numerical achievements that would be typical for this role and industry.** For example, if 'Managed projects' is given, infer 'Managed 5 complex software projects, delivering 90% on-time and 10% under budget, leading to 15% improvement in team efficiency.' Focus on 'Problem-Action-Result' (PAR) or 'Situation-Task-Action-Result' (STAR) methodology. Prioritize impact and quantify every statement."
                    f"    **Core Responsibilities for Expansion:**\n"
                    f"    ```\n"
                    f"    {responsibilities_prompt}\n"
                    f"    ```\n"
                    f"    **Generated Detailed Bullet Points (3-5 points):**"
                    # Changed to make it clearer for the LLM what to output
                )
        else:
            prompt_parts.append("\n- **Work Experience:** No work experience provided.")

        # --- Education Section ---
        # Ensure education is a list before processing
        if user_core_data.get('education') and isinstance(user_core_data['education'], list):
            prompt_parts.append("\n- Education:")
            for edu in user_core_data['education']:
                degree = edu.get('degree', 'N/A')
                institution = edu.get('institution', 'N/A')
                field_of_study = edu.get('field_of_study', '')  # Using field_of_study from frontend
                start_date = edu.get('start_date', '')
                end_date = edu.get('end_date', 'Present')  # Default to 'Present' if end_date is not provided
                edu_dates_str = f"({start_date} - {end_date})" if start_date else ""
                description = edu.get('description', '')  # Optional description/notes

                edu_line = f"  * {degree}"
                if field_of_study:
                    edu_line += f" in {field_of_study}"
                edu_line += f" from {institution} {edu_dates_str}"
                if description:
                    edu_line += f"\n    - Notes: {description}"  # Add notes if available
                prompt_parts.append(edu_line)
        else:
            prompt_parts.append("\n- Education: No education information provided.")

        # --- Skills Section ---
        # Ensure skills is a list of strings
        if user_core_data.get('skills') and isinstance(user_core_data['skills'], list):
            # Filter out any non-string items or empty strings, then join
            clean_skills = [s for s in user_core_data['skills'] if isinstance(s, str) and s.strip()]
            if clean_skills:
                prompt_parts.append(f"\n- Skills: {', '.join(clean_skills)}")
            else:
                prompt_parts.append("\n- Skills: No skills provided.")
        else:
            prompt_parts.append("\n- Skills: No skills provided.")

        # --- Certifications Section ---
        # Ensure certifications is a list of strings
        if user_core_data.get('certifications') and isinstance(user_core_data['certifications'], list):
            # Filter out any non-string items or empty strings, then join
            clean_certs = [c for c in user_core_data['certifications'] if isinstance(c, str) and c.strip()]
            if clean_certs:
                prompt_parts.append(f"\n- Certifications: {', '.join(clean_certs)}")
            else:
                prompt_parts.append("\n- Certifications: No certifications provided.")
        else:
            prompt_parts.append("\n- Certifications: No certifications provided.")

        # --- Projects Section (if you have one) ---
        # Ensure projects is a list of dictionaries
        if user_core_data.get('projects') and isinstance(user_core_data['projects'], list):
            prompt_parts.append("\n- Projects:")
            for proj in user_core_data['projects']:
                if isinstance(proj, dict):  # Ensure project item is a dictionary
                    prompt_parts.append(f"  * {proj.get('name', 'N/A')}: {proj.get('description', 'No description.')}")
                else:
                    prompt_parts.append(f"  * Invalid project entry: {str(proj)}")  # Handle malformed entry
        else:
            prompt_parts.append("\n- Projects: No project information provided.")

        # 2. Learned Preferences (Dynamic Agentic Rules)
        # Iterate over the list of rules and add them to the prompt if active
        if learned_preferences and isinstance(learned_preferences, list):
            prompt_parts.append(
                "\nBased on previous interactions and feedback, apply the following specific guidelines and preferences:")
            for rule_obj in learned_preferences:
                if isinstance(rule_obj, dict) and rule_obj.get("active", True):  # Only add active rules
                    rule_text = rule_obj.get("rule")
                    if rule_text and isinstance(rule_text, str):
                        prompt_parts.append(f"- {rule_text}")

        # 3. Specific Request (from frontend, e.g., target JD)
        if initial_request:
            prompt_parts.append(f"\nUser's specific instruction for this generation: {initial_request}")

        if target_job_description:
            prompt_parts.append(
                f"\n**TARGET JOB DESCRIPTION (THIS IS THE MOST IMPORTANT CONTEXT FOR TAILORING):**\n```\n{target_job_description}\n```\n")

            prompt_parts.append(
                f"**Your highest priority is to integrate keywords, skills, and responsibilities from this JD throughout the resume. Systematically go through EACH section (Summary, Skills, Experience, Education, Projects) and ensure maximum alignment.** Rephrase and reorder content from the candidate's profile to explicitly match the phrasing and requirements of the job description. Identify and emphasize skills and experiences that directly address the JD's demands, even if they were minor in the original profile. Do not simply list, but actively demonstrate how the candidate meets the JD's criteria.")

        prompt_parts.append(
            "\n\nNow, generate the complete resume based on all the above information. Ensure it is formatted clearly with distinct sections (e.g., Summary, Experience, Education, Skills).")

        stylistic_rules = []
        exclusion_rules = []
        inclusion_rules = []  # For potential future "must include X" rules

        if learned_preferences and isinstance(learned_preferences, list):
            # Ensure proper parsing of learned_preferences here
            clean_learned_preferences = []
            for rule_obj in learned_preferences:
                if isinstance(rule_obj, dict):
                    rule_text = rule_obj.get("rule")
                    rule_type = rule_obj.get("type", "stylistic")
                    if rule_text and isinstance(rule_text, str):
                        clean_learned_preferences.append(rule_obj)
                        if rule_type == "stylistic":
                            stylistic_rules.append(rule_text)
                        elif rule_type == "exclusion":
                            exclusion_rules.append(rule_text)
                        elif rule_type == "inclusion":
                            inclusion_rules.append(rule_text)
                elif isinstance(rule_obj, str):  # Handle cases where preferences might just be strings
                    stylistic_rules.append(rule_obj)

            if clean_learned_preferences:  # Only add if there are actual preferences
                prompt_parts.append(
                    "\nBased on previous interactions and feedback, **strictly apply the following specific guidelines and preferences**:"
                )
                for rule_text in stylistic_rules:
                    prompt_parts.append(f"- {rule_text}")

                if exclusion_rules:
                    prompt_parts.append(
                        "\nIMPORTANT: **Adhere strictly to the following content exclusion rules.** Do NOT include any information related to these topics or keywords:"
                    )
                    for rule_text in exclusion_rules:
                        prompt_parts.append(f"- {rule_text}")

                if inclusion_rules:
                    prompt_parts.append(
                        "\nIMPORTANT: **Ensure the generated resume explicitly highlights the following.** Prioritize content that reflects these areas:"
                    )
                    for rule_text in inclusion_rules:
                        prompt_parts.append(f"- {rule_text}")

        if initial_request:
            prompt_parts.append(f"\nUser's specific instruction for this generation: {initial_request}")

        if target_job_description:
            prompt_parts.append(
                f"\n**TARGET JOB DESCRIPTION (CRITICAL FOR TAILORING):**\n```\n{target_job_description}\n```\n"
                f"**Integrate keywords, skills, and responsibilities from this JD throughout the resume, especially in the summary and experience bullet points.** "
                f"Prioritize and rephrase content that directly aligns with the job description's requirements. Look for specific keywords and concepts to emphasize."
            )
        else:
            prompt_parts.append(
                "\n**No specific Target Job Description provided. Generate a strong general resume.**")

        prompt_parts.append(
            "\n\n**Generate the COMPLETE resume now, strictly adhering to all the instructions, candidate data, preferences, and the target job description (if provided).**"
            "\nYour output MUST be in a clean, professional, and easy-to-read Markdown format."
            "\nDouble-check for conciseness, impact, quantification, and ATS compatibility."
            "\nEnsure the resume is distinct and unique, avoiding generic phrasing common to AI-generated text."
        )

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
            "You are an expert resume reviewer and highly critical AI assistant. Your task is to perform a rigorous quality assurance check on the provided resume draft against best practices, the candidate's core data, and the target job description (if provided). **Your critique must be extremely specific, actionable, and focus on the quantitative and relevance aspects.**\n\n"
        )

        prompt += "**Resume to Critique:**\n```\n"
        prompt += resume_draft  # Use resume_draft here
        prompt += "\n```\n\n"

        prompt += (
            "**Specific Areas to Rigorously Check:**\n"
            "-   **Quantification:** Is every achievement in the experience section quantified with a number, percentage, or measurable outcome? If not, identify *exactly which bullet points* lack quantification and suggest specific, plausible numbers to add.\n"
            "-   **Generic Phrases:** Are any of the forbidden generic phrases present (e.g., 'leveraged', 'utilized', 'results-driven')? List them specifically.\n"
            "-   **ATS/JD Relevance:** How well does the resume integrate keywords and concepts from the Target Job Description? Point out specific instances where better keyword integration or rephrasing for relevance is needed.\n"
            "-   **Impact vs. Responsibility:** Does each bullet point focus on the *impact* and *achievement* rather than just a *responsibility*? Identify bullet points that read too much like a job description.\n"
            "-   **Conciseness:** Is any section unnecessarily verbose? Suggest specific areas for shortening.\n"
            "-   **Action Verbs:** Does every bullet point start with a strong action verb?\n"
            "-   **Coherence & Flow:** Does the resume tell a clear, compelling story? Are there any logical gaps?\n\n"
        )

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
            f"      \"category\": \"Rule Violation\" | \"Stylistic\" | \"Content Gap\" | \"Target JD Mismatch\" | \"Best Practice\" | \"Other\" | \"Quantification\" | \"Impact vs. Responsibility\" | \"Generic Phrases\" | \"Action Verbs\" | \"Conciseness\" | \"ATS/JD Relevance\",\n"  # Ensure ALL categories are here
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
            "If no issues are found, the `issues` list should be empty and `has_issues` should be `false`. **STRICTLY ADHERE TO THE SPECIFIED CATEGORY VALUES ONLY.**"
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
            "Your goal is to address *all* the critiques and generate a *new, significantly improved version* of the resume. "
            "Ensure the refined resume still adheres to all original instructions, core data, and learned preferences.\n\n"
            "**Strictly follow these refinement rules:**\n"
            "-   Do NOT just rephrase. Actively implement the 'suggested_action' for each critique.\n"
            "-   For 'Quantification' issues, add specific, plausible numbers, percentages, or monetary values. DO NOT use placeholders like 'X%'.\n"
            "-   For 'Generic Phrases' issues, replace the identified phrases with strong, specific, and impactful action verbs and descriptive language.\n"
            "-   For 'Impact vs. Responsibility' issues, rewrite the bullet point to clearly demonstrate the *result* or *outcome* of the action, using the STAR/PAR method.\n"
            "-   For 'ATS/JD Relevance' issues, aggressively integrate keywords and rephrase content from the resume to directly match the target job description. Prioritize JD relevance.\n"
            "-   For 'Conciseness' issues, shorten sentences and paragraphs without losing critical information, focusing on impact.\n"
            "-   For 'Action Verbs' issues, ensure every bullet point starts with a powerful and distinct action verb.\n"
            "-   Maintain the overall professional and concise tone. Avoid any conversational text in the final output.\n\n"
        )

        prompt += "**Previous Resume Version (to be refined):**\n```\n"
        prompt += previous_resume_content
        prompt += "\n```\n\n"

        prompt += "**Critiques to Address (MANDATORY TO FIX EACH):**\n"
        # Iterate through critiques to make them more prominent and actionable
        for i, critique_item in enumerate(critiques):
            prompt += f"- **Issue {i + 1}: {critique_item.get('category')} ({critique_item.get('severity')})**\n"
            prompt += f"  **Description:** {critique_item.get('description')}\n"
            if critique_item.get('suggested_action'):
                prompt += f"  **Action Required:** {critique_item.get('suggested_action')}\n"
            if critique_item.get('relevant_rule_id'):
                prompt += f"  (Related Rule ID: {critique_item.get('relevant_rule_id')})\n"
            prompt += "\n"  # Add a newline for readability between critiques

        prompt += (
            "**Original User Core Data (for reference on factual content - adhere strictly to this data):**\n```json\n"
            f"{core_data_json}\n```\n\n"
        )
        prompt += (
            "**Original Learned Preferences (Rules to still enforce - ensure the refined resume respects these):**\n```json\n"
            f"{preferences_json}\n```\n\n"
        )

        if target_job_description:
            prompt += (
                "**Original Target Job Description (for continued tailoring - this is paramount):**\n```\n"
                f"{target_job_description}\n```\n\n"
            )

        prompt += (
            "**Generate the complete, REFINED resume in Markdown format.** "
            "Ensure all identified issues from the 'Critiques to Address' section have been concretely fixed. "
            "The output must be ONLY the resume content, with no introductory or conversational text."
        )
        return prompt

    def generate_core_data_extraction_prompt(self, resume_text: str) -> str:
        """
        Generates a prompt to extract structured core data from a resume text.
        """
        prompt = f"""
        You are an expert resume parser and data extractor. Your task is to extract key personal, experience, education, and skill information from the provided resume text.
        Extract the following fields into a JSON object. If a field is not found, use an empty string for text fields, an empty list for list fields, or 0 for numeric fields.

        **Output JSON structure (strictly follow this):**
        ```json
        {{
            "full_name": "string",
            "email": "string",
            "phone": "string",
            "linkedin": "string",
            "years_of_experience": 0,
            "job_history": [
                {{
                    "title": "string",
                    "company": "string",
                    "start_date": "YYYY-MM or YYYY",
                    "end_date": "YYYY-MM or YYYY or 'Present'",
                    "responsibilities": ["string", "string"]
                }}
            ],
            "education": [
                {{
                    "degree": "string",
                    "major": "string",
                    "university": "string",
                    "graduation_date": "YYYY-MM or YYYY"
                }}
            ],
            "skills": ["string", "string"],
            "certifications": ["string", "string"]
        }}
        ```

        **Important Notes:**
        - For `job_history`, extract 'title', 'company', 'start_date', 'end_date', and a concise list of 2-4 key 'responsibilities' for each role.
        - For `education`, extract 'degree', 'major', 'university', and 'graduation_date'.
        - `years_of_experience` should be an integer, estimated based on job history, or 0 if no experience.
        - Ensure all lists (job_history, education, skills, certifications, responsibilities) are proper JSON arrays.
        - Dates should be in "YYYY-MM" or "YYYY" format. For current roles, `end_date` should be "Present".
        - Do not include any text or explanation outside the JSON object.

        **Resume Text to Parse:**
        ---
        {resume_text}
        ---

        Extracted JSON:
        """
        return prompt

    def generate_refinement_prompt(self, previous_resume_content: str, critiques: List[Dict[str, Any]],
                                   user_core_data: Dict[str, Any], learned_preferences: List[Dict[str, Any]],
                                   target_job_description: str = "") -> str:
        """
        Constructs a prompt for Gemini to refine a resume based on previous critiques.
        """
        prompt_parts = [
            "You are an expert resume writer. Your task is to refine the provided resume draft based on the critical feedback and specific issues identified. Your goal is to produce a significantly improved version that directly addresses each critique point while also adhering to all original resume generation guidelines.",
            "\n**Original Candidate Core Data:**",
            json.dumps(user_core_data, indent=2),  # Pass core data again for context
            "\n**Previously Generated Resume Draft (to be refined):**",
            "```markdown",
            previous_resume_content,
            "```",
            "\n**Critiques to Address (MANDATORY TO FIX EACH):**"
        ]

        # Convert critiques from Pydantic model_dump to a readable list for LLM
        for i, critique_item in enumerate(critiques):  # This line is correct
            prompt_parts.append(
                f"- Issue {i + 1} (Category: {critique_item.get('category')}, Severity: {critique_item.get('severity')}):")
            prompt_parts.append(f"  Description: {critique_item.get('description')}")
            if critique_item.get('suggested_action'):
                # CORRECTED LINE:
                prompt_parts.append(
                    f"  Suggested Action: {critique_item.get('suggested_action')}")  # Changed critrite_item to critique_item
            if critique_item.get('relevant_rule_id'):
                prompt_parts.append(f"  Relevant Rule ID: {critique_item.get('relevant_rule_id')}")
            prompt_parts.append("")  # Empty line for readability

        if learned_preferences:
            prompt_parts.append("\n**Learned Preferences (Strictly adhere to these during refinement):**")
            for rule_obj in learned_preferences:
                if isinstance(rule_obj, dict) and rule_obj.get("active", True) and rule_obj.get("rule"):
                    prompt_parts.append(f"- {rule_obj['rule']}")

        if target_job_description:
            prompt_parts.append(
                f"\n**Target Job Description (Maintain strong relevance):**\n```\n{target_job_description}\n```")
            prompt_parts.append("Ensure refinement enhances alignment with this job description.")

        prompt_parts.append(
            "\n\n**Based on the original draft, the identified critiques, and all guidelines/preferences, generate the REFINED resume. Your output must be ONLY the complete, improved resume in Markdown format.** Ensure all critique points have been addressed and the resume is polished, quantified, and tailored."
        )
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