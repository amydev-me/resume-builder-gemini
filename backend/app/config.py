# backend/app/config.py

import os
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env file

SECRET_KEY = os.getenv("SECRET_KEY", "your-super-secret-key") # Change this in production!
ALGORITHM = "HS256" # Standard for JWTs
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # How long the access token is valid (in minutes)

# Database path (consistent with your file_manager and db setup)
SQL_DATABASE_FILE_NAME = "sql_app.db"
USER_PROFILE_JSON_FILE_NAME = "user_profile.json" # Still might be used for initial setup/migration
RESUME_VERSIONS_JSON_FILE_NAME = "resume_versions.json" # Still might be used for initial setup/migration

# Assuming DATA_DIR is relative to the backend/ directory where uvicorn is run
DATA_DIR_NAME = "data"