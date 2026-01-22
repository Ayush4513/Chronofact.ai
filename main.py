"""
Chronofact.ai - Main Entry Point

AI-powered fact-based news service that constructs accurate and verifiable
event timelines from X (Twitter) data using Qdrant vector database and BAML.

Usage:
    python main.py                    # Start API server
    python -m src.cli                 # Show CLI help
    python -m src.cli init            # Initialize system
    python -m src.cli query "topic"   # Generate timeline

For full documentation, see README.md
"""

from src.cli import app
from typer.testing import CliRunner

runner = CliRunner()


def main():
    app()


if __name__ == "__main__":
    main()
