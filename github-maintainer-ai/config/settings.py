import os
from dotenv import load_dotenv

def load_config():
    """Load configuration from .env file."""
    # Load from .env file
    load_dotenv(override=True)
    
    # Get token and validate
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise ValueError("GITHUB_TOKEN not found in .env file")
    print(f"Found GitHub token: {token[:4]}...{token[-4:]}")
    
    return {
        "github": {
            "token": token,
            "username": os.getenv("GITHUB_USERNAME"),
            "repo_owner": os.getenv("REPO_OWNER"),
            "repo_name": os.getenv("REPO_NAME")
        },
        "llm": {
            "host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            "model": os.getenv("MODEL_NAME", "codellama")
        },
        "logging": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "file": os.getenv("LOG_FILE", "github_maintainer.log")
        },
        "memory": {
            "dir": os.getenv("MEMORY_DIR", "./memory")
        }
    }
