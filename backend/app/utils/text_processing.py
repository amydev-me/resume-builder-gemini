import difflib

def get_text_diff(old_text: str, new_text: str) -> str:
    """
    Generates a unified diff of two text strings.
    Useful for analyzing how a user edited a generated resume.
    """
    d = difflib.unified_diff(
        old_text.splitlines(keepends=True),
        new_text.splitlines(keepends=True),
        lineterm='', # Avoid extra newlines
        fromfile='original',
        tofile='edited'
    )
    return ''.join(d)

def clean_llm_output(text: str) -> str:
    """
    Cleans common issues in LLM output (e.g., Markdown code blocks, extra whitespace).
    """
    # Remove markdown code block fences if present
    if text.startswith("```") and text.endswith("```"):
        text = text.strip("`").strip()
        # If it's a python code block, remove "python" or "json" etc.
        if text.startswith(('python', 'json', 'text')):
            text = text[text.find('\n')+1:].strip()
    return text.strip()

if __name__ == "__main__":
    # Test get_text_diff
    text1 = "Line 1\nLine 2\nLine 3"
    text2 = "Line A\nLine 2\nLine 3 updated"
    diff = get_text_diff(text1, text2)
    print("--- Text Diff Example ---")
    print(diff)
    print("-" * 20)

    # Test clean_llm_output
    llm_output_example = "```text\nThis is an example.\n```"
    cleaned = clean_llm_output(llm_output_example)
    print(f"Original LLM Output:\n'{llm_output_example}'")
    print(f"Cleaned LLM Output:\n'{cleaned}'")

    llm_output_code = "```json\n{\n\"key\": \"value\"\n}\n```"
    cleaned_code = clean_llm_output(llm_output_code)
    print(f"Original LLM Output (Code):\n'{llm_output_code}'")
    print(f"Cleaned LLM Output (Code):\n'{cleaned_code}'")