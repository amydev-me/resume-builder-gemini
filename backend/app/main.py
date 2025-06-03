import os
from dotenv import load_dotenv
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from pydantic import BaseModel

from .utils.file_manager import load_json_data, save_json_data
from .schemas.feedback import ResumeFeedback, ResumeContentResponse
from .services.feedback_services import  process_feedback_and_update_preferences
# Import the new core_ai modules
from .core_ai.llm_client import LLMClient
from .core_ai.prompt_manager import PromptManager
from .utils.text_processing import clean_llm_output  # For cleaning LLM output

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


@app.post("/generate-resume/")
async def generate_resume(request: GenerateResumeRequest):
    """
    Generates a resume using core data and learned preferences via PromptManager and LLMClient.
    """
    try:
        user_profile = load_json_data(USER_PROFILE_FILE)
        core_data = user_profile.get("core_data", {})
        learned_preferences = user_profile.get("learned_preferences", {})

        # Use the PromptManager to construct the full prompt
        full_prompt = prompt_manager.generate_resume_prompt(
            user_core_data=core_data,
            learned_preferences=learned_preferences,
            initial_request=request.initial_prompt,
            target_job_description=request.target_job_description
        )

        # Use the LLMClient to generate content
        generated_content = llm_client.generate_text(full_prompt)
        generated_content = clean_llm_output(generated_content)  # Clean up output

        # Prepare and save the new version
        new_version_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat() + 'Z'
        version_name = f"Resume Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"

        new_resume_entry = {
            "id": new_version_id,
            "timestamp": timestamp,
            "version_name": version_name,
            "content": generated_content,
            "feedback_summary": "Generated using learned preferences."
        }

        all_versions = load_json_data(RESUME_VERSIONS_FILE)
        if not isinstance(all_versions, list):
            all_versions = []
        all_versions.append(new_resume_entry)
        save_json_data(RESUME_VERSIONS_FILE, all_versions)

        return ResumeContentResponse(**new_resume_entry)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating resume: {str(e)}")


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