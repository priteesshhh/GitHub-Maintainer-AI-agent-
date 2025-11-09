#!/usr/bin/env python3

import sys
import os
from typing import Optional
from loguru import logger
from core.github_client import GitHubClient
from issue_analyzer import IssueAnalyzer
from code_fixer import CodeFixer
from pr_manager import PRManager
from dotenv import load_dotenv

def parse_repository_url(url: str) -> tuple[str, str]:
    """Parse a GitHub repository URL into owner and name.
    
    Supports formats:
    - https://github.com/owner/repo
    - git@github.com:owner/repo.git
    - owner/repo
    """
    import re
    
    patterns = [
        r"(?:https?://github\.com/)?([^/]+)/([^/\.]+)(?:\.git)?/?$",
        r"git@github\.com:([^/]+)/([^/\.]+)(?:\.git)?/?$"
    ]
    
    for pattern in patterns:
        match = re.match(pattern, url)
        if match:
            return match.group(1), match.group(2)
    
    raise ValueError(f"Invalid GitHub repository URL format: {url}. " 
                    "Expected format: owner/repo or https://github.com/owner/repo")

def main():
    """Main entry point for the GitHub Maintainer AI agent."""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        logger.info("Starting GitHub Maintainer AI agent")

        # Get repository URL from command line argument or environment
        repo_url = os.getenv("GITHUB_REPO_URL")
        if not repo_url and len(sys.argv) > 1:
            repo_url = sys.argv[1]
        elif not repo_url:
            logger.error("Please provide a GitHub repository URL")
            logger.error("Usage: python main.py https://github.com/owner/repository")
            logger.error("   or: set GITHUB_REPO_URL environment variable")
            sys.exit(1)
        owner, repo = parse_repository_url(repo_url)

        # Initialize configuration
        config = {
            "url": repo_url,
            "repository": f"{owner}/{repo}",
            "branch": "main",
            "labels": ["bug"],  # Focus on bugs first
            "max_issues": 10
        }

        logger.info("Configuration:")
        logger.info(f"- Repository: {config['repository']}")
        logger.info(f"- Branch: {config['branch']}")
        logger.info(f"- Labels: {config['labels']}")
        logger.info(f"- Max issues: {config['max_issues']}")

        # Initialize components
        github_client = GitHubClient()
        try:
            repo = github_client.get_repository(owner, repo)
            logger.info(f"Successfully connected to repository: {repo.full_name}")
        except Exception as e:
            logger.error(f"Failed to access repository: {str(e)}")
            sys.exit(1)

        issue_analyzer = IssueAnalyzer(repo)
        code_fixer = CodeFixer(repo)
        pr_manager = PRManager(repo)

        # Get open issues
        logger.info("Scanning for open issues...")
        issues = []
        try:
            # First get repository labels
            available_labels = [label.name for label in repo.get_labels()]
            logger.info(f"Available labels in repository: {available_labels}")
            
            # Determine which labels to use
            if config['labels']:
                # Check which configured labels exist in the repository
                valid_labels = [label for label in config['labels'] if label in available_labels]
                if not valid_labels:
                    logger.warning(f"None of the configured labels {config['labels']} exist in the repository")
                    logger.info("Will fetch all open issues without label filtering")
                    valid_labels = []
                else:
                    logger.info(f"Using labels for filtering: {valid_labels}")
            else:
                valid_labels = []
            
            # Get open issues with optional label filtering
            if valid_labels:
                open_issues = list(repo.get_issues(state='open', labels=valid_labels)[:config['max_issues']])
            else:
                open_issues = list(repo.get_issues(state='open')[:config['max_issues']])
            
            issues = open_issues
            logger.info(f"Found {len(issues)} open issues to analyze")
            
            # Only try to create sample issues if we have write access
            if not issues and repo.permissions.push:
                logger.info("No matching open issues found. Creating a sample issue for testing...")
                title = "Sample Bug Report"
                body = "This is a sample bug issue created for testing the GitHub Maintainer AI agent."
                new_issue = repo.create_issue(title=title, body=body, labels=["bug"])
                issues = [new_issue]
                logger.info(f"Created sample issue #{new_issue.number}: {new_issue.title}")
        
        except Exception as e:
            logger.error(f"Failed to fetch or create issues: {str(e)}")
            sys.exit(1)

        if not issues:
            logger.info("No open issues found to process")
            return

        # Process each issue
        for issue in issues:
            logger.info(f"Analyzing issue #{issue.number}: {issue.title}")

            try:
                # Analyze the issue and find affected files
                analysis = issue_analyzer.analyze_issue(issue)
                if isinstance(analysis, dict) and analysis.get('affected_files'):
                    logger.info(f"Identified {len(analysis['affected_files'])} affected files:")
                    for file in analysis['affected_files']:
                        logger.info(f"- {file}")
                    
                    # Generate fixes
                    logger.info(f"Generating fixes for issue #{issue.number}...")
                    fixes = code_fixer.generate_fix(issue, analysis['affected_files'])
                    
                    if fixes:
                        # Create branch name from issue
                        branch_name = f"fix/issue-{issue.number}-{issue.title.lower().replace(' ', '-')[:50]}"
                        
                        # Create pull request
                        logger.info(f"Creating pull request for issue #{issue.number}...")
                        try:
                            pr = pr_manager.create_pull_request(
                                title=f"Fix #{issue.number}: {issue.title}",
                                body=f"Automated fix for issue #{issue.number}\n\n{fixes['description']}\n\nChanges:\n{fixes['changes']}",
                                branch_name=branch_name,
                                changes=fixes['changes'],
                                base_branch=config['branch']
                            )
                            logger.info(f"Created pull request #{pr.number}: {pr.html_url}")
                            
                            # Add a comment to the issue
                            issue.create_comment(
                                f"I've created a pull request with a potential fix: {pr.html_url}\n\n"
                                f"Please review the changes and let me know if any adjustments are needed."
                            )
                        except Exception as e:
                            logger.error(f"Failed to create pull request for issue #{issue.number}: {str(e)}")
                    else:
                        logger.info(f"Could not generate fixes for issue #{issue.number}")
                        issue.create_comment(
                            "I analyzed this issue but couldn't generate a reliable fix. "
                            "This might require human intervention or more context."
                        )
                else:
                    logger.info("No files identified for this issue")
                    issue.create_comment(
                        "I analyzed this issue but couldn't identify the affected files. "
                        "Could you please provide more details about which files need to be modified?"
                    )
                    continue

            except Exception as e:
                logger.error(f"Error processing issue #{issue.number}: {str(e)}")
                continue
                logger.info("No fixes generated for this issue")
                continue

            # Create pull request
            pr = pr_manager.create_pull_request(
                issue=issue,
                fixes=fixes,
                analysis=code_fixer.get_analysis()
            )

            if pr:
                logger.info(f"Created pull request #{pr.number}: {pr.title}")
                issue.create_comment(
                    f"I've created a pull request with some suggested fixes: #{pr.number}"
                )
            else:
                logger.warning("Failed to create pull request")

    except Exception as e:
        logger.error(f"Error in main process: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
