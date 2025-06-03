import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv() # Ensure .env is loaded here too for robustness

class LLMClient:
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable not set.")
        genai.configure(api_key=api_key)
        self.model_name = model_name
        self.model = genai.GenerativeModel(self.model_name)

    def generate_text(self, prompt: str, temperature: float = 0.7, max_output_tokens: int = 2048) -> str:
        """
        Generates text using the configured Gemini model.
        """
        try:
            # Use safety_settings to prevent blocking on potentially sensitive resume content
            # Adjust these based on your specific needs
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            response = self.model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                ),
                safety_settings=safety_settings
            )
            # Access the text property of the candidate, handling cases where it might not exist
            if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
                generated_text = "".join(part.text for part in response.candidates[0].content.parts)
                return generated_text.strip()
            return "No text generated or response blocked." # Fallback if no content
        except genai.types.BlockedPromptException as e:
            # Handle cases where the prompt itself is blocked by safety settings
            print(f"Prompt was blocked by safety settings: {e}")
            return "Content generation blocked due to safety concerns with the prompt."
        except Exception as e:
            print(f"Error generating content with Gemini: {e}")
            return f"Error: {str(e)}"

# Example usage (for testing this module directly)
if __name__ == "__main__":
    llm_client = LLMClient()
    test_prompt = "Tell me a fun fact about Python programming."
    generated = llm_client.generate_text(test_prompt)
    print(f"\n--- LLM Client Test ---")
    print(f"Prompt: {test_prompt}")
    print(f"Generated: {generated}")

    resume_prompt = "Write a concise summary for a software engineer with 5 years experience."
    resume_summary = llm_client.generate_text(resume_prompt, temperature=0.5)
    print(f"\n--- Resume Summary Test ---")
    print(f"Prompt: {resume_prompt}")
    print(f"Generated: {resume_summary}")