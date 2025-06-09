import os
from pathlib import Path

from dotenv import load_dotenv
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from pydantic import BaseModel, ValidationError

from .utils.file_manager import load_json_data, save_json_data, save_resume_version
from .schemas.feedback import ResumeFeedback, ResumeContentResponse
from .services.feedback_services import  process_feedback_and_update_preferences
# Import the new core_ai modules
from .core_ai.llm_client import LLMClient
from .core_ai.prompt_manager import PromptManager
from .utils.text_processing import clean_llm_output  # For cleaning LLM output
from .schemas.suggestion import GetSuggestionsRequest, SuggestionsResponse, SuggestionItem # <--- Make sure these are imported
from .schemas.critique import ResumeCritique, CritiqueIssue # <--- NEW IMPORTS
from sqlalchemy.orm import Session # Import Session
from .db.database import engine, get_db, Base # Import Base as well
from .db import models # Import your models

import json
# Load environment variables
load_dotenv()

# --- Configuration ---
# The API key is now handled by LLMClient internally, but we can keep this check for startup
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

# Initialize LLMClient and PromptManager globally for the app
llm_client = LLMClient(model_name="gemini-1.5-flash")  # Use the preferred model
prompt_manager = PromptManager()

USER_PROFILE_FILE = "user_profile.json"
RESUME_VERSIONS_FILE = "resume_versions.json"

# Define the maximum number of times the agent will try to refine the resume internally.
# This means 1 initial generation + MAX_REFINEMENT_ITERATIONS attempts to refine.
MAX_REFINEMENT_ITERATIONS = 2 # Set to 0 for no refinement, 1 for one pass, etc.



# --- FastAPI App Setup ---
app = FastAPI(
    title="Agentic Resume Builder (Full Brain)",
    description="Full API with enhanced agentic learning and structured prompting.",
    version="0.4.0",
)

# --- CORS Configuration ---
# Define allowed origins (where your frontend is running)
origins = [
    "http://localhost",
    "http://localhost:3000",  # Your React development server
    "http://127.0.0.1:3000", # Sometimes localhost resolves to 127.0.0.1
    # Add other origins if you deploy your frontend elsewhere, e.g.,
    # "https://your-deployed-frontend.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True, # Allow cookies and authorization headers
    allow_methods=["*"],    # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],    # Allow all headers
)

# --- NEW: Function to create database tables ---
def create_db_tables():
    models.Base.metadata.create_all(bind=engine)

# In your FastAPI app startup event (before the routes)
@app.on_event("startup")
async def startup_event():
    # Create the 'data' directory if it doesn't exist for SQLite DB file
    if not Path("./data").exists():
        Path("./data").mkdir(parents=True, exist_ok=True)
    create_db_tables()
    print("Database tables created/checked.")
    # Initialize your LLM client here if not already done

# --- Pydantic Models (retained for clarity and type safety) ---
class GenerateRequest(BaseModel):
    prompt_text: str


class GenerateResumeRequest(BaseModel):
    initial_prompt: Optional[str] = None
    target_job_description: Optional[str] = None


# --- Endpoints ---
@app.post("/test-gemini/")
async def test_gemini(request: GenerateRequest):
    """
    Tests the Gemini API by sending a basic text prompt using the LLMClient.
    """
    try:
        generated_text = llm_client.generate_text(request.prompt_text)
        return {"success": True, "generated_text": generated_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM Client Error: {str(e)}")


@app.get("/user-profile/")
async def get_user_profile():
    try:
        profile = load_json_data(USER_PROFILE_FILE)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading user profile: {str(e)}")


@app.post("/generate-resume/", response_model=ResumeContentResponse)
async def generate_resume(request: GenerateResumeRequest):
    """
    Generates a resume, performs self-critique, and iteratively refines it.
    """
    try:
        user_profile = load_json_data(USER_PROFILE_FILE) # Assuming USER_PROFILE_FILE is defined
        core_data = user_profile.get("core_data", {})
        learned_preferences = user_profile.get("learned_preferences", [])

        current_resume_draft = ""
        current_version_name = "Initial Draft"
        final_critique_results: Optional[ResumeCritique] = None # To hold the critique of the *final* version

        # Loop for initial generation and subsequent refinements
        # Iteration 0 is for initial generation, subsequent iterations are for refinement.
        for iteration in range(MAX_REFINEMENT_ITERATIONS + 1):
            print(f"--- Generation/Refinement Iteration {iteration} ---")

            if iteration == 0:
                # First pass: Generate the initial resume
                print("Generating initial resume draft...")
                resume_prompt = prompt_manager.generate_resume_prompt(
                    user_core_data=core_data,
                    learned_preferences=learned_preferences,
                    initial_request=request.initial_prompt,
                    target_job_description=request.target_job_description
                )
                raw_generated_content = llm_client.generate_text(resume_prompt, temperature=0.7)
                current_version_name = f"Resume Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                # Subsequent passes: Refine based on the last critique
                if not final_critique_results or not final_critique_results.has_issues:
                    # This should ideally not happen if loop broke correctly, but as a safeguard
                    print("No issues found in previous iteration or critique missing. Skipping refinement.")
                    break

                print(f"Refining based on previous critiques (Iteration {iteration})...")
                # Pass the issues from the last critique for refinement
                refinement_prompt = prompt_manager.generate_refinement_prompt(
                    previous_resume_content=current_resume_draft, # The draft from the previous iteration
                    critiques=[c.model_dump() for c in final_critique_results.issues], # Pass the issues list
                    user_core_data=core_data, # Provide context for the LLM
                    learned_preferences=learned_preferences, # Provide context for the LLM
                    target_job_description=request.target_job_description # Provide context for the LLM
                )
                raw_generated_content = llm_client.generate_text(refinement_prompt, temperature=0.7)
                current_version_name = f"Refined Draft {datetime.now().strftime('%Y-%m-%d %H:%M')} (Iter {iteration})"


            # --- Clean the markdown code block from generated content ---
            cleaned_content = clean_llm_output(raw_generated_content) # Re-using your clean_llm_output
            current_resume_draft = cleaned_content # Update the draft for the next iteration/final output

            # --- Critique the current draft (after generation or refinement) ---
            print(f"Critiquing the current draft (Iteration {iteration})...")
            critique_prompt = prompt_manager.generate_critique_prompt(
                resume_draft=current_resume_draft, # Critique the *current* draft
                learned_preferences=learned_preferences,
                target_job_description=request.target_job_description
            )
            raw_critique_json = llm_client.generate_text(critique_prompt, temperature=0.1) # Low temp for deterministic critique

            # Clean markdown from critique JSON
            cleaned_critique_json = raw_critique_json.strip()
            if cleaned_critique_json.startswith("```json"):
                cleaned_critique_json = cleaned_critique_json[len("```json"):].strip()
            if cleaned_critique_json.endswith("```"):
                cleaned_critique_json = cleaned_critique_json[:-len("```")].strip()

            try:
                critique_data = json.loads(cleaned_critique_json)
                final_critique_results = ResumeCritique(**critique_data) # Store for current/next iteration check
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                print(f"ERROR: Failed to parse critique JSON in iteration {iteration}: {e}")
                print(f"Raw critique output: {raw_critique_json}")
                # If critique itself is malformed, we can't trust it. Treat as no issues to break loop.
                final_critique_results = ResumeCritique(
                    issues=[CritiqueIssue(category="Error", description=f"Critique parsing failed: {e}", severity="high")],
                    overall_assessment="Critique generation failed/malformed. Cannot trust assessment.",
                    has_issues=False # Forcing False to break loop if critique is unusable
                )

            # Check if further refinement is needed
            if not final_critique_results.has_issues:
                print(f"No issues found in Iteration {iteration}. Breaking refinement loop.")
                break # Exit loop if no issues are detected

            # If we are in the last allowed iteration, and there are still issues,
            # we will return this version as it's the best we could do.
            if iteration == MAX_REFINEMENT_ITERATIONS:
                print(f"Max refinement iterations ({MAX_REFINEMENT_ITERATIONS}) reached. Returning current draft.")
                break # Exit loop if max iterations reached


        # --- Save the Final Generated/Refined Resume Version ---
        # This will be the last 'current_resume_draft' and its 'final_critique_results'
        resume_version_id = str(uuid.uuid4())
        timestamp_str = datetime.now().isoformat() + 'Z'

        save_resume_version(
            resume_id=resume_version_id,
            version_name=current_version_name, # Name reflects the last action (initial or refined)
            content=current_resume_draft,
            core_data_used=core_data,
            learned_preferences_used=learned_preferences,
            target_job_description_used=request.target_job_description,
            critique_data=final_critique_results.model_dump() if final_critique_results else None # Save the critique of the *final* version
        )

        # --- Return the Final Refined Resume and its Critique ---
        return ResumeContentResponse(
            id=resume_version_id,
            version_name=current_version_name,
            content=current_resume_draft,
            timestamp=timestamp_str,
            feedback_summary="Generated with agentic self-correction.",
            core_data_used=core_data,
            learned_preferences_used=learned_preferences,
            target_job_description_used=request.target_job_description,
            critique=final_critique_results # Pass the critique of the final version
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during resume generation: {str(e)}")




@app.post("/setup-user-profile/")
async def setup_user_profile(profile_data: dict):
    try:
        current_profile = load_json_data(USER_PROFILE_FILE)
        if "core_data" in profile_data:
            current_profile["core_data"].update(profile_data["core_data"])
        if "learned_preferences" in profile_data:
            current_profile["learned_preferences"].update(profile_data["learned_preferences"])

        save_json_data(USER_PROFILE_FILE, current_profile)
        return {"success": True, "message": "User profile updated successfully!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error setting up user profile: {str(e)}")


@app.post("/submit-feedback/")
async def submit_feedback(feedback: ResumeFeedback):
    """
    Receives user feedback and updates learned preferences using the feedback service.
    """
    try:
        process_feedback_and_update_preferences(feedback)  # This now uses AgenticLearner
        return {"success": True, "message": "Feedback processed and preferences updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

@app.post("/get-suggestions/", response_model=SuggestionsResponse)
async def get_suggestions(request: GetSuggestionsRequest):
    """
    Generates proactive suggestions for resume improvement based on user data
    and an optional target job description.
    """
    try:
        # CORRECTED: Use load_json_data directly as implemented
        user_profile = load_json_data(USER_PROFILE_FILE)
        core_data = user_profile.get("core_data", {})
        learned_preferences = user_profile.get("learned_preferences", [])

        # Generate the prompt for suggestions using the new method
        suggestions_prompt = prompt_manager.generate_suggestions_prompt(
            user_core_data=core_data,
            learned_preferences=learned_preferences,
            target_job_description=request.target_job_description
        )

        # Get raw suggestions (JSON string) from the LLM
        raw_suggestions_json = llm_client.generate_text(suggestions_prompt, temperature=0.6)

        # --- NEW: Clean the raw_suggestions_json to remove markdown code block ---
        cleaned_suggestions_json = raw_suggestions_json.strip()
        if cleaned_suggestions_json.startswith("```json"):
            cleaned_suggestions_json = cleaned_suggestions_json[len("```json"):].strip()
        if cleaned_suggestions_json.endswith("```"):
            cleaned_suggestions_json = cleaned_suggestions_json[:-len("```")].strip()
        # --- END NEW ---
        # Parse and validate the suggestions
        try:
            suggestions_data = json.loads(cleaned_suggestions_json)  # <--- USE CLEANED STRING
            if not isinstance(suggestions_data, list):
                raise ValueError("LLM did not return a list of suggestions.")
            validated_suggestions = [SuggestionItem(**s) for s in suggestions_data]
        except (json.JSONDecodeError, ValueError, ValidationError) as e:
            print(f"Error parsing/validating LLM suggestions JSON: {e}")
            print(f"Raw LLM output for suggestions: {raw_suggestions_json}")
            raise HTTPException(status_code=500, detail=f"AI returned malformed suggestions: {str(e)}. Raw output: {raw_suggestions_json[:200]}...")

        return SuggestionsResponse(suggestions=validated_suggestions)

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred while getting suggestions: {str(e)}")