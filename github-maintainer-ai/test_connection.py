#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from github import Github, Auth
from loguru import logger

def test_github_connection():
    # Load environment variables
    load_dotenv()
    
    # Get GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: No GITHUB_TOKEN found in .env file")
        return
    
    print(f"Found token (first/last 4 chars): {token[:4]}...{token[-4:]}")
    
    try:
        # Initialize GitHub client with newer auth method
        auth = Auth.Token(token)
        g = Github(auth=auth)
        
        # Test authentication
        user = g.get_user()
        print(f"Successfully authenticated as: {user.login}")
        
        # Test repository access
        repo_url = "TheGrayGryphon/Run8-Speed-Check"
        print(f"\nTesting access to repository: {repo_url}")
        repo = g.get_repo(repo_url)
        print(f"Repository details:")
        print(f"- Name: {repo.name}")
        print(f"- Owner: {repo.owner.login}")
        print(f"- Description: {repo.description}")
        
        # Test issues access
        print("\nFetching issues...")
        issues = list(repo.get_issues(state="open"))
        print(f"Found {len(issues)} open issues")
        for issue in issues:
            print(f"- #{issue.number}: {issue.title}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    test_github_connection()
