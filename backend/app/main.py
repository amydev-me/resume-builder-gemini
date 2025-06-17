import os
import uuid
import json
from pathlib import Path
import re

from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, HTTPException, Depends, status, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware # Import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm # For login form data

from pydantic import BaseModel, ValidationError
from sqlalchemy.orm import Session

from .utils.file_manager import load_json_data
from .utils.resume_parser import parse_resume_content # NEW Import for parsing
from .utils.text_processing import clean_llm_output
from .core_ai.llm_client import LLMClient
from .core_ai.prompt_manager import PromptManager

from .schemas.feedback import ResumeFeedback, ResumeContentResponse, SubmitFeedbackRequest
from .schemas.requests import SetupUserProfileRequest
from .schemas.suggestion import GetSuggestionsRequest, SuggestionsResponse, SuggestionItem
from .schemas.critique import ResumeCritique, CritiqueIssue
from .schemas.auth import UserCreate, UserLogin, Token, UserInDB

from .db.database import get_db, engine, Base # Import Base for table creation
from .db import models # Your database models

from .core.security import get_password_hash, verify_password
from .core.auth import authenticate_user, create_access_token, get_current_user, oauth2_scheme
from .config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, USER_PROFILE_JSON_FILE_NAME, RESUME_VERSIONS_JSON_FILE_NAME, DATA_DIR_NAME # Import config variables





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


@app.post("/register", response_model=UserInDB, status_code=status.HTTP_201_CREATED)
async def register_user(user_create: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.username == user_create.username).first()
    if db_user:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered")

    hashed_password = get_password_hash(user_create.password)
    db_user = models.User(username=user_create.username, email=user_create.email, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Automatically create an empty user profile for the new user
    user_profile = models.UserProfile(owner_id=db_user.id, core_data_json=json.dumps({}))
    db.add(user_profile)
    db.commit()
    db.refresh(user_profile)

    return db_user

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me/", response_model=UserInDB)
async def read_users_me(current_user: models.User = Depends(get_current_user)):
    # This is a protected route, accessible only with a valid token
    return current_user

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


# @app.get("/user-profile/")
# async def get_user_profile():
#     try:
#         profile = load_json_data(USER_PROFILE_FILE)
#         return profile
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error loading user profile: {str(e)}")
# --- Modify existing routes to require authentication ---
# Replace your current `get_user_profile` with this version
@app.get("/user-profile/", response_model=dict)  # Adjust response model if you create a UserProfile schema
async def get_user_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # Load user profile from the database, associated with the current_user
    db_profile = db.query(models.UserProfile).filter(models.UserProfile.owner_id == current_user.id).first()
    if not db_profile or not db_profile.core_data_json:
        # Return an empty profile if not found, or create a default one
        return {"core_data": {}, "learned_preferences": []}

    core_data = json.loads(db_profile.core_data_json)

    # Load learned preferences from the database
    db_preferences = db.query(models.LearnedPreference).filter(
        models.LearnedPreference.owner_id == current_user.id).all()
    learned_preferences = [json.loads(p.preference_data_json) for p in db_preferences]

    return {"core_data": core_data, "learned_preferences": learned_preferences}


# Replace your current `setup_user_profile` with this version
@app.post("/setup-user-profile/")
async def setup_user_profile(
        request: SetupUserProfileRequest,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # Retrieve or create the user profile in the database
    db_profile = db.query(models.UserProfile).filter(models.UserProfile.owner_id == current_user.id).first()
    if db_profile:
        db_profile.core_data_json = json.dumps(request.core_data)
        # Assuming learned preferences are managed separately or appended
    else:
        db_profile = models.UserProfile(owner_id=current_user.id, core_data_json=json.dumps(request.core_data))
        db.add(db_profile)

    db.commit()
    db.refresh(db_profile)
    return {"message": "User profile updated successfully."}

# @app.post("/generate-resume/", response_model=ResumeContentResponse)
# async def generate_resume(request: GenerateResumeRequest):
#     """
#     Generates a resume, performs self-critique, and iteratively refines it.
#     """
#     try:
#         user_profile = load_json_data(USER_PROFILE_FILE) # Assuming USER_PROFILE_FILE is defined
#         core_data = user_profile.get("core_data", {})
#         learned_preferences = user_profile.get("learned_preferences", [])
#
#         current_resume_draft = ""
#         current_version_name = "Initial Draft"
#         final_critique_results: Optional[ResumeCritique] = None # To hold the critique of the *final* version
#
#         # Loop for initial generation and subsequent refinements
#         # Iteration 0 is for initial generation, subsequent iterations are for refinement.
#         for iteration in range(MAX_REFINEMENT_ITERATIONS + 1):
#             print(f"--- Generation/Refinement Iteration {iteration} ---")
#
#             if iteration == 0:
#                 # First pass: Generate the initial resume
#                 print("Generating initial resume draft...")
#                 resume_prompt = prompt_manager.generate_resume_prompt(
#                     user_core_data=core_data,
#                     learned_preferences=learned_preferences,
#                     initial_request=request.initial_prompt,
#                     target_job_description=request.target_job_description
#                 )
#                 raw_generated_content = llm_client.generate_text(resume_prompt, temperature=0.7)
#                 current_version_name = f"Resume Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"
#             else:
#                 # Subsequent passes: Refine based on the last critique
#                 if not final_critique_results or not final_critique_results.has_issues:
#                     # This should ideally not happen if loop broke correctly, but as a safeguard
#                     print("No issues found in previous iteration or critique missing. Skipping refinement.")
#                     break
#
#                 print(f"Refining based on previous critiques (Iteration {iteration})...")
#                 # Pass the issues from the last critique for refinement
#                 refinement_prompt = prompt_manager.generate_refinement_prompt(
#                     previous_resume_content=current_resume_draft, # The draft from the previous iteration
#                     critiques=[c.model_dump() for c in final_critique_results.issues], # Pass the issues list
#                     user_core_data=core_data, # Provide context for the LLM
#                     learned_preferences=learned_preferences, # Provide context for the LLM
#                     target_job_description=request.target_job_description # Provide context for the LLM
#                 )
#                 raw_generated_content = llm_client.generate_text(refinement_prompt, temperature=0.7)
#                 current_version_name = f"Refined Draft {datetime.now().strftime('%Y-%m-%d %H:%M')} (Iter {iteration})"
#
#
#             # --- Clean the markdown code block from generated content ---
#             cleaned_content = clean_llm_output(raw_generated_content) # Re-using your clean_llm_output
#             current_resume_draft = cleaned_content # Update the draft for the next iteration/final output
#
#             # --- Critique the current draft (after generation or refinement) ---
#             print(f"Critiquing the current draft (Iteration {iteration})...")
#             critique_prompt = prompt_manager.generate_critique_prompt(
#                 resume_draft=current_resume_draft, # Critique the *current* draft
#                 learned_preferences=learned_preferences,
#                 target_job_description=request.target_job_description
#             )
#             raw_critique_json = llm_client.generate_text(critique_prompt, temperature=0.1) # Low temp for deterministic critique
#
#             # Clean markdown from critique JSON
#             cleaned_critique_json = raw_critique_json.strip()
#             if cleaned_critique_json.startswith("```json"):
#                 cleaned_critique_json = cleaned_critique_json[len("```json"):].strip()
#             if cleaned_critique_json.endswith("```"):
#                 cleaned_critique_json = cleaned_critique_json[:-len("```")].strip()
#
#             try:
#                 critique_data = json.loads(cleaned_critique_json)
#                 final_critique_results = ResumeCritique(**critique_data) # Store for current/next iteration check
#             except (json.JSONDecodeError, ValidationError, ValueError) as e:
#                 print(f"ERROR: Failed to parse critique JSON in iteration {iteration}: {e}")
#                 print(f"Raw critique output: {raw_critique_json}")
#                 # If critique itself is malformed, we can't trust it. Treat as no issues to break loop.
#                 final_critique_results = ResumeCritique(
#                     issues=[CritiqueIssue(category="Error", description=f"Critique parsing failed: {e}", severity="high")],
#                     overall_assessment="Critique generation failed/malformed. Cannot trust assessment.",
#                     has_issues=False # Forcing False to break loop if critique is unusable
#                 )
#
#             # Check if further refinement is needed
#             if not final_critique_results.has_issues:
#                 print(f"No issues found in Iteration {iteration}. Breaking refinement loop.")
#                 break # Exit loop if no issues are detected
#
#             # If we are in the last allowed iteration, and there are still issues,
#             # we will return this version as it's the best we could do.
#             if iteration == MAX_REFINEMENT_ITERATIONS:
#                 print(f"Max refinement iterations ({MAX_REFINEMENT_ITERATIONS}) reached. Returning current draft.")
#                 break # Exit loop if max iterations reached
#
#
#         # --- Save the Final Generated/Refined Resume Version ---
#         # This will be the last 'current_resume_draft' and its 'final_critique_results'
#         resume_version_id = str(uuid.uuid4())
#         timestamp_str = datetime.now().isoformat() + 'Z'
#
#         save_resume_version(
#             resume_id=resume_version_id,
#             version_name=current_version_name, # Name reflects the last action (initial or refined)
#             content=current_resume_draft,
#             core_data_used=core_data,
#             learned_preferences_used=learned_preferences,
#             target_job_description_used=request.target_job_description,
#             critique_data=final_critique_results.model_dump() if final_critique_results else None # Save the critique of the *final* version
#         )
#
#         # --- Return the Final Refined Resume and its Critique ---
#         return ResumeContentResponse(
#             id=resume_version_id,
#             version_name=current_version_name,
#             content=current_resume_draft,
#             timestamp=timestamp_str,
#             feedback_summary="Generated with agentic self-correction.",
#             core_data_used=core_data,
#             learned_preferences_used=learned_preferences,
#             target_job_description_used=request.target_job_description,
#             critique=final_critique_results # Pass the critique of the final version
#         )
#
#     except HTTPException:
#         raise
#     except Exception as e:
#         import traceback
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"An unexpected error occurred during resume generation: {str(e)}")




# @app.post("/setup-user-profile/")
# async def setup_user_profile(profile_data: dict):
#     try:
#         current_profile = load_json_data(USER_PROFILE_FILE)
#         if "core_data" in profile_data:
#             current_profile["core_data"].update(profile_data["core_data"])
#         if "learned_preferences" in profile_data:
#             current_profile["learned_preferences"].update(profile_data["learned_preferences"])
#
#         save_json_data(USER_PROFILE_FILE, current_profile)
#         return {"success": True, "message": "User profile updated successfully!"}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error setting up user profile: {str(e)}")


# @app.post("/submit-feedback/")
# async def submit_feedback(feedback: ResumeFeedback):
#     """
#     Receives user feedback and updates learned preferences using the feedback service.
#     """
#     try:
#         process_feedback_and_update_preferences(feedback)  # This now uses AgenticLearner
#         return {"success": True, "message": "Feedback processed and preferences updated."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error processing feedback: {str(e)}")

# Modify `submit_feedback` to use the database and current_user

# Modify `generate_resume` to use the database for data and associate resume with user

def clean_core_data_for_llm(core_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cleans and pre-processes core_data to remove or modify generic placeholders
    before sending to the LLM.
    """
    cleaned_data = core_data.copy()

    # Define common placeholder patterns
    placeholder_patterns = [
        r"placeholder\s*role", r"placeholder\s*company", r"n/a", r"not\s*applicable",
        r"example\s*job", r"test\s*role", r"job\s*title\s*\d+", r"company\s*name\s*\d+",
        r"description\s*of\s*responsibilities", r"lorem\s*ipsum", r"your\s*role",
        r"your\s*company", r"no\s*responsibilities\s*provided"
    ]
    # Compile regex for efficiency
    compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in placeholder_patterns]

    def is_placeholder(text: str) -> bool:
        if not text or not text.strip():
            return True
        for pattern in compiled_patterns:
            if pattern.search(text):
                return True
        return False

    # Clean Job History
    if 'job_history' in cleaned_data and isinstance(cleaned_data['job_history'], list):
        filtered_job_history = []
        for job in cleaned_data['job_history']:
            clean_job = job.copy()
            # Check title and company - if both are placeholders, skip the job
            if is_placeholder(clean_job.get('title', '')) and is_placeholder(clean_job.get('company', '')):
                continue

            # Clean individual fields within the job
            if is_placeholder(clean_job.get('title', '')):
                clean_job['title'] = "Experienced Professional" # Generic but not a placeholder
            if is_placeholder(clean_job.get('company', '')):
                clean_job['company'] = "Undisclosed Company" # Generic but not a placeholder

            if 'responsibilities' in clean_job and isinstance(clean_job['responsibilities'], list):
                # Filter out placeholder responsibilities
                clean_job['responsibilities'] = [
                    resp for resp in clean_job['responsibilities'] if not is_placeholder(resp)
                ]
                # If all responsibilities were placeholders, add a default
                if not clean_job['responsibilities']:
                    clean_job['responsibilities'] = ["Managed key projects and delivered impactful results."] # Provide a generic for LLM to expand

            filtered_job_history.append(clean_job)
        cleaned_data['job_history'] = filtered_job_history
        # If no valid jobs remain, signal this to the LLM later
        if not filtered_job_history:
            cleaned_data['has_meaningful_job_history'] = False
        else:
            cleaned_data['has_meaningful_job_history'] = True


    # Clean Education
    if 'education' in cleaned_data and isinstance(cleaned_data['education'], list):
        filtered_education = []
        for edu in cleaned_data['education']:
            clean_edu = edu.copy()
            if is_placeholder(clean_edu.get('degree', '')) and is_placeholder(clean_edu.get('institution', '')):
                continue
            if is_placeholder(clean_edu.get('degree', '')): clean_edu['degree'] = "Degree/Certification"
            if is_placeholder(clean_edu.get('institution', '')): clean_edu['institution'] = "Reputable Institution"
            filtered_education.append(clean_edu)
        cleaned_data['education'] = filtered_education

    # Clean Skills
    if 'skills' in cleaned_data and isinstance(cleaned_data['skills'], list):
        cleaned_data['skills'] = [skill for skill in cleaned_data['skills'] if not is_placeholder(skill)]
        if not cleaned_data['skills']:
            cleaned_data['skills'] = ["Problem Solving", "Communication", "Teamwork"] # Default skills

    # Clean Certifications
    if 'certifications' in cleaned_data and isinstance(cleaned_data['certifications'], list):
        cleaned_data['certifications'] = [cert for cert in cleaned_data['certifications'] if not is_placeholder(cert)]

    # Clean Projects
    if 'projects' in cleaned_data and isinstance(cleaned_data['projects'], list):
        filtered_projects = []
        for proj in cleaned_data['projects']:
            if isinstance(proj, dict) and not is_placeholder(proj.get('name', '')):
                if is_placeholder(proj.get('description', '')):
                    proj['description'] = "Successfully completed a significant project."
                filtered_projects.append(proj)
        cleaned_data['projects'] = filtered_projects


    # Add a flag if core data seems very sparse/placeholder-filled overall
    if not cleaned_data.get('full_name') or is_placeholder(cleaned_data.get('full_name', '')):
        cleaned_data['full_name'] = "Valued Candidate"
    if not cleaned_data.get('email') or is_placeholder(cleaned_data.get('email', '')):
        cleaned_data['email'] = "contact@example.com"


    return cleaned_data

@app.post("/generate-resume/", response_model=ResumeContentResponse)
async def generate_resume(
        request: GenerateResumeRequest,
        current_user: models.User = Depends(get_current_user),  # <--- PROTECT THIS ROUTE
        db: Session = Depends(get_db)  # <--- Inject database session
):
    """
    Generates a resume, performs self-critique, and iteratively refines it.
    """
    try:
        # Load user profile and learned preferences from the database for the current_user
        db_profile = db.query(models.UserProfile).filter(models.UserProfile.owner_id == current_user.id).first()
        core_data = json.loads(db_profile.core_data_json) if db_profile and db_profile.core_data_json else {}

        cleaned_core_data = clean_core_data_for_llm(core_data)


        db_preferences = db.query(models.LearnedPreference).filter(
            models.LearnedPreference.owner_id == current_user.id).all()
        learned_preferences = [json.loads(p.preference_data_json) for p in db_preferences]

        current_resume_draft = ""
        current_version_name = "Initial Draft"
        final_critique_results: Optional[ResumeCritique] = None

        for iteration in range(MAX_REFINEMENT_ITERATIONS + 1):
            print(f"--- Generation/Refinement Iteration {iteration} ---")

            # ... (Rest of your generate_resume logic, it remains largely the same) ...
            # The only difference is `save_resume_version` call at the end:
            if iteration == 0:
                print("Generating initial resume draft...")
                resume_prompt = prompt_manager.generate_resume_prompt(
                    user_core_data=cleaned_core_data,
                    learned_preferences=learned_preferences,
                    initial_request=request.initial_prompt,
                    target_job_description=request.target_job_description
                )
                raw_generated_content = llm_client.generate_text(resume_prompt, temperature=0.8)
                current_version_name = f"Resume Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            else:
                if not final_critique_results or not final_critique_results.has_issues:
                    print("No issues found in previous iteration or critique missing. Skipping refinement.")
                    break
                print(f"Refining based on previous critiques (Iteration {iteration})...")
                refinement_prompt = prompt_manager.generate_refinement_prompt(
                    previous_resume_content=current_resume_draft,
                    critiques=[c.model_dump() for c in final_critique_results.issues],
                    user_core_data=cleaned_core_data,
                    learned_preferences=learned_preferences,
                    target_job_description=request.target_job_description
                )
                raw_generated_content = llm_client.generate_text(refinement_prompt, temperature=0.7)
                current_version_name = f"Refined Draft {datetime.now().strftime('%Y-%m-%d %H:%M')} (Iter {iteration})"

            cleaned_content = clean_llm_output(raw_generated_content)
            current_resume_draft = cleaned_content

            print(f"Critiquing the current draft (Iteration {iteration})...")
            critique_prompt = prompt_manager.generate_critique_prompt(
                resume_draft=current_resume_draft,
                learned_preferences=learned_preferences,
                target_job_description=request.target_job_description
            )
            raw_critique_json = llm_client.generate_text(critique_prompt, temperature=0.1)

            cleaned_critique_json = raw_critique_json.strip()
            if cleaned_critique_json.startswith("```json"):
                cleaned_critique_json = cleaned_critique_json[len("```json"):].strip()
            if cleaned_critique_json.endswith("```"):
                cleaned_critique_json = cleaned_critique_json[:-len("```")].strip()

            try:
                critique_data = json.loads(cleaned_critique_json)
                final_critique_results = ResumeCritique(**critique_data)
            except (json.JSONDecodeError, ValidationError, ValueError) as e:
                print(f"ERROR: Failed to parse critique JSON in iteration {iteration}: {e}")
                print(f"Raw critique output: {raw_critique_json}")
                final_critique_results = ResumeCritique(
                    issues=[
                        CritiqueIssue(category="Error", description=f"Critique parsing failed: {e}", severity="high")],
                    overall_assessment="Critique generation failed/malformed. Cannot trust assessment.",
                    has_issues=False
                )

            if not final_critique_results.has_issues:
                print(f"No issues found in Iteration {iteration}. Breaking refinement loop.")
                break

            if iteration == MAX_REFINEMENT_ITERATIONS:
                print(f"Max refinement iterations ({MAX_REFINEMENT_ITERATIONS}) reached. Returning current draft.")
                break

        # --- Save the Final Generated/Refined Resume Version to the DATABASE ---
        db_resume_version = models.ResumeVersion(
            owner_id=current_user.id,  # Link to the authenticated user
            resume_uuid=str(uuid.uuid4()),  # Still keep a UUID if you want for external reference
            version_name=current_version_name,
            content=current_resume_draft,
            core_data_used_json=json.dumps(core_data),  # Store as JSON string
            learned_preferences_used_json=json.dumps(learned_preferences),  # Store as JSON string
            target_job_description_used=request.target_job_description,
            critique_data_json=json.dumps(final_critique_results.model_dump()) if final_critique_results else None
        )
        db.add(db_resume_version)
        db.commit()
        db.refresh(db_resume_version)  # Refresh to get the database-assigned ID

        # Return the final refined resume and its critique (using Pydantic model)
        return ResumeContentResponse(
            id=str(db_resume_version.id),  # Return DB ID as string for consistency
            version_name=db_resume_version.version_name,
            content=db_resume_version.content,
            timestamp=db_resume_version.timestamp.isoformat() + 'Z',  # Convert datetime to string
            feedback_summary="Generated with agentic self-correction and multi-user support.",
            core_data_used=json.loads(db_resume_version.core_data_used_json),
            learned_preferences_used=json.loads(db_resume_version.learned_preferences_used_json),
            target_job_description_used=db_resume_version.target_job_description_used,
            critique=final_critique_results
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred during resume generation: {str(e)}")


@app.post("/submit-feedback/")
async def submit_feedback(
        feedback_request: SubmitFeedbackRequest,
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    # 1. Update Learned Preferences based on feedback (in DB)
    for feedback_item in feedback_request.feedback_items:
        # For simplicity, we'll store each feedback item as a new learned preference.
        # In a real app, you'd process/aggregate this into existing preferences.
        new_preference_data = {
            "type": "user_feedback",
            "comment": feedback_item.comment,
            "is_positive": feedback_item.is_positive,
            "related_to_version_id": feedback_request.resume_version_id,
            "target_job_description": feedback_request.target_job_description  # Store for context
        }
        db_preference = models.LearnedPreference(
            owner_id=current_user.id,
            preference_data_json=json.dumps(new_preference_data)
        )
        db.add(db_preference)

    db.commit()

    # 2. Implement logic to generate a new refined preference list for this user
    # This part would be more complex and involve the AI processing the new feedback
    # and previous preferences. For now, simply adding new preference entry.
    # In a more advanced system, you'd feed this back to your prompt_manager logic.

    return {"message": "Feedback submitted successfully. Learned preferences updated."}


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


# Add a new route to get all resume versions for the current user
@app.get("/resume-versions/", response_model=List[ResumeContentResponse])
async def get_all_resume_versions(
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    db_resume_versions = db.query(models.ResumeVersion).filter(
        models.ResumeVersion.owner_id == current_user.id).order_by(models.ResumeVersion.timestamp.desc()).all()

    response_versions = []
    for rv in db_resume_versions:
        critique = None
        if rv.critique_data_json:
            try:
                critique = ResumeCritique(**json.loads(rv.critique_data_json))
            except (json.JSONDecodeError, ValidationError):
                print(f"Warning: Could not parse critique for resume version {rv.id}")

        response_versions.append(
            ResumeContentResponse(
                id=str(rv.id),
                version_name=rv.version_name,
                content=rv.content,
                timestamp=rv.timestamp.isoformat() + 'Z',
                feedback_summary="Loaded from database.",
                core_data_used=json.loads(rv.core_data_used_json) if rv.core_data_used_json else {},
                learned_preferences_used=json.loads(
                    rv.learned_preferences_used_json) if rv.learned_preferences_used_json else [],
                target_job_description_used=rv.target_job_description_used,
                critique=critique
            )
        )
    return response_versions


@app.post("/upload-resume/")
async def upload_resume(
        file: UploadFile = File(...),
        current_user: models.User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    if not file.filename.endswith(('.pdf', '.docx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Only PDF and DOCX are allowed."
        )

    try:
        file_content = await file.read()
        extracted_text = parse_resume_content(file_content, file.filename)

        if not extracted_text:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to extract text from the uploaded resume. Ensure it's a valid PDF or DOCX."
            )

        # Use LLM to extract structured data
        extraction_prompt = prompt_manager.generate_core_data_extraction_prompt(extracted_text)
        raw_extracted_json = llm_client.generate_text(extraction_prompt,
                                                      temperature=0.1)  # Low temp for data extraction

        # Clean markdown from JSON response
        cleaned_json = raw_extracted_json.strip()
        if cleaned_json.startswith("```json"):
            cleaned_json = cleaned_json[len("```json"):].strip()
        if cleaned_json.endswith("```"):
            cleaned_json = cleaned_json[:-len("```")].strip()

        try:
            extracted_data = json.loads(cleaned_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM extracted JSON: {e}")
            print(f"Raw LLM output: {raw_extracted_json}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"AI failed to extract valid JSON data from resume. Error: {e}"
            )

        # Update user profile in the database
        db_profile = db.query(models.UserProfile).filter(models.UserProfile.owner_id == current_user.id).first()
        if not db_profile:
            # This case should ideally not happen if user registration creates a profile
            db_profile = models.UserProfile(owner_id=current_user.id, core_data_json="{}")
            db.add(db_profile)
            db.commit()  # Commit to get an ID for the new profile if needed
            db.refresh(db_profile)

        # Merge extracted data with existing profile data (if any)
        current_profile_data = json.loads(db_profile.core_data_json) if db_profile.core_data_json else {}

        # Simple merge: new data overwrites old. For lists, you might want to append/deduplicate.
        merged_profile_data = {**current_profile_data, **extracted_data}

        # Convert complex lists (job_history, education, skills, certifications) back to JSON strings
        # before storing in the single core_data_json field.
        for key in ['job_history', 'education', 'skills', 'certifications']:
            if key in merged_profile_data and isinstance(merged_profile_data[key], list):
                merged_profile_data[key] = merged_profile_data[key]  # Keep as list for JSON.dumps

        db_profile.core_data_json = json.dumps(merged_profile_data)
        db.commit()
        db.refresh(db_profile)

        return {"message": "Resume uploaded and profile updated successfully!", "extracted_data": extracted_data}

    except HTTPException:
        raise  # Re-raise FastAPI HTTP exceptions
    except Exception as e:
        import traceback
        traceback.print_exc()  # Print full traceback to console
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An unexpected error occurred during resume upload or processing: {str(e)}"
        )