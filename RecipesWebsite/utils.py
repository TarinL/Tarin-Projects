from pathlib import Path

def get_project_root() -> Path:
    return Path(__file__).parent

# Helper function to find out whether the name string includes the substring.
# Case insensitive search.
def search_string(name: str, substring: str):
    return substring.strip().lower() in name.lower()