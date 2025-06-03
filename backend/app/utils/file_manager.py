import json
from pathlib import Path
import os

# Get the base directory of the 'app' module
APP_BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = APP_BASE_DIR / "data"

# Ensure the data directory exists
DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_json_data(file_name: str):
    """Loads JSON data from a specified file within the data directory."""
    file_path = DATA_DIR / file_name
    if not file_path.exists():
        # Create an empty file if it doesn't exist, useful for new files
        with open(file_path, 'w') as f:
            json.dump({}, f)  # Empty dict for user_profile, empty list for resume_versions
        return {}  # Or [] depending on expected structure

    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json_data(file_name: str, data):
    """Saves data to a specified JSON file within the data directory."""
    file_path = DATA_DIR / file_name
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)  # Use indent for readability


# Example usage (for testing this module directly)
if __name__ == "__main__":
    # Test loading/saving user profile
    profile_data = load_json_data("user_profile.json")
    print(f"Loaded user profile: {profile_data}")

    profile_data["core_data"]["full_name"] = "Jane Doe"  # Example modification
    save_json_data("user_profile.json", profile_data)
    print("User profile updated and saved.")

    # Test loading/saving resume versions
    versions_data = load_json_data("resume_versions.json")
    print(f"Loaded resume versions: {versions_data}")

    # Add a new version (simplified)
    new_version = {
        "id": "test_version_002",
        "timestamp": "2024-06-03T15:30:00Z",  # Replace with actual time
        "version_name": "Test Save",
        "content": "This is a new test resume content.",
        "feedback_summary": "Saved after initial edits."
    }
    if not isinstance(versions_data, list):  # Ensure it's a list for appending
        versions_data = []
    versions_data.append(new_version)
    save_json_data("resume_versions.json", versions_data)
    print("New resume version added and saved.")