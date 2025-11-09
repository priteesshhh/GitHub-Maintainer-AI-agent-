#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from github import Github, Auth
from loguru import logger

def test_pull_request_creation():
    # Load environment variables
    load_dotenv()
    
    # Get GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: No GITHUB_TOKEN found in .env file")
        return
    
    try:
        # Initialize GitHub client with auth
        auth = Auth.Token(token)
        g = Github(auth=auth)
        
        # Test authentication
        user = g.get_user()
        print(f"Authenticated as: {user.login}")
        
        # Get the target repository
        repo_name = "TheGrayGryphon/Run8-Speed-Check"
        repo = g.get_repo(repo_name)
        print(f"\nAccessing repository: {repo_name}")
        
        # Fork the repository to your account
        try:
            fork = user.create_fork(repo)
            print(f"Created fork at: {fork.full_name}")
        except Exception as e:
            print(f"Fork already exists or couldn't be created: {str(e)}")
            # Get the existing fork
            fork = g.get_repo(f"{user.login}/Run8-Speed-Check")
            print(f"Using existing fork: {fork.full_name}")
        
        # Demonstrate creating a test branch (in this case we won't actually push changes)
        branch_name = "test-pr-creation"
        try:
            # Get the default branch's HEAD
            default_branch = fork.default_branch
            default_branch_ref = fork.get_git_ref(f"heads/{default_branch}")
            
            # Create a new branch
            fork.create_git_ref(ref=f"refs/heads/{branch_name}", 
                              sha=default_branch_ref.object.sha)
            print(f"\nCreated branch: {branch_name}")
        except Exception as e:
            print(f"Branch might already exist: {str(e)}")
        
        # Demonstrate creating a pull request (this is just a test, won't actually create one)
        print("\nSimulating pull request creation (not actually creating one):")
        print("Title: Fix speed calculation issue")
        print("Body: This PR addresses issue #2 (0 MPH Error) by fixing the speed calculation logic.")
        print(f"Base: {repo_name}:{default_branch}")
        print(f"Head: {user.login}:{branch_name}")
        
        # NOTE: Uncomment these lines to actually create a PR
        # pr = repo.create_pull(
        #     title="Fix speed calculation issue",
        #     body="This PR addresses issue #2 (0 MPH Error) by fixing the speed calculation logic.",
        #     base=default_branch,
        #     head=f"{user.login}:{branch_name}"
        # )
        # print(f"\nCreated Pull Request #{pr.number}: {pr.html_url}")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    test_pull_request_creation()
