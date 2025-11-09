from typing import Dict, List
import os
from github import Github
from github.Repository import Repository
from loguru import logger

class GitHubClient:
    def __init__(self):
        """Initialize GitHub client with token from environment variables."""
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            logger.error("No GITHUB_TOKEN found in environment variables!")
            raise ValueError("GitHub token is required. Please check your .env file.")
        
        logger.info("Initializing GitHub client...")
        try:
            self.client = Github(self.token)
            # Test the token by getting the authenticated user
            user = self.client.get_user()
            logger.info(f"Successfully authenticated as: {user.login}")
        except Exception as e:
            logger.error(f"Failed to initialize GitHub client: {e}")
            raise

    def get_repository(self, owner: str, name: str) -> Repository:
        """Get the GitHub repository instance by owner and name."""
        try:
            logger.info(f"Accessing repository: {owner}/{name}")
            return self.client.get_repo(f"{owner}/{name}")
        except Exception as e:
            logger.error(f"Failed to access repository {owner}/{name}: {e}")
            raise
