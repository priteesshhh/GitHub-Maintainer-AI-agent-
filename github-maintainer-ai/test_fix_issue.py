#!/usr/bin/env python3

import os
from dotenv import load_dotenv
from loguru import logger
from pr_manager import PullRequestManager

def main():
    # Load environment variables
    load_dotenv()
    
    # Get GitHub token
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("ERROR: No GITHUB_TOKEN found in .env file")
        return
    
    try:
        # Initialize the PR manager
        repo_name = "TheGrayGryphon/Run8-Speed-Check"
        manager = PullRequestManager(token, repo_name)
        
        # Process issue #2 (the 0 MPH Error issue)
        print(f"Processing issue #2...")
        pr_url = manager.process_issue(2)
        
        if pr_url:
            print(f"Created pull request: {pr_url}")
        else:
            print("Could not create pull request - see logs for details")
            
    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise

if __name__ == "__main__":
    main()
