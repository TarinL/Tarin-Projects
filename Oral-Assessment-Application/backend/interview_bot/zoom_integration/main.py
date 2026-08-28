"""
main.py — Entry point for the Zoom interview bot.

Usage:
    python main.py "https://zoom.us/j/123456789?pwd=..."
"""

import sys
from pathlib import Path

# Load .env from project root before any other imports
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parents[3] / ".env")
except ImportError:
    pass

from session import run_zoom_interview


def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python main.py <zoom_url>")
        sys.exit(1)

    zoom_url = sys.argv[1]
    run_zoom_interview(zoom_url)


if __name__ == "__main__":
    main()
