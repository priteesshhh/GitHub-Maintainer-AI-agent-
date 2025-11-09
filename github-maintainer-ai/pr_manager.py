#!/usr/bin/env python3

from typing import List, Optional
from github import Repository, Issue, PullRequest
from loguru import logger
from issue_analyzer import CodeFix

class PRManager:
    def __init__(self, repo: Repository):
        self.repo = repo
    
    def create_pull_request(self, issue: Issue, fixes: List[CodeFix], analysis) -> Optional[PullRequest]:
        """Creates a pull request with the generated fixes."""
        try:
            # Create branch name from issue
            branch_name = f"fix/issue-{issue.number}-{issue.title[:50].lower().replace(' ', '-')}"
            
            # Get the default branch
            default_branch = self.repo.default_branch
            
            # Create new branch from default branch
            try:
                ref = self.repo.get_git_ref(f"heads/{default_branch}")
                self.repo.create_git_ref(
                    ref=f"refs/heads/{branch_name}",
                    sha=ref.object.sha
                )
                logger.info(f"Created branch: {branch_name}")
            except Exception as e:
                logger.error(f"Error creating branch: {str(e)}")
                return None
            
            # Apply fixes
            commit_message = f"Fix issue #{issue.number}: {issue.title}\n\n"
            commit_message += "Changes made:\n"
            
            for fix in fixes:
                try:
                    # Get the file content
                    file_content = self.repo.get_contents(
                        fix.file_path,
                        ref=branch_name
                    )
                    
                    # Update content
                    new_content = file_content.decoded_content.decode('utf-8')
                    new_content = new_content.replace(fix.old_code, fix.new_code)
                    
                    # Create commit
                    self.repo.update_file(
                        path=fix.file_path,
                        message=f"Fix: {fix.description}",
                        content=new_content.encode('utf-8'),
                        sha=file_content.sha,
                        branch=branch_name
                    )
                    
                    commit_message += f"- {fix.description}\n"
                    logger.info(f"Committed fix to {fix.file_path}")
                    
                except Exception as e:
                    logger.error(f"Error applying fix to {fix.file_path}: {str(e)}")
                    continue
            
            # Add analysis details to PR body
            pr_body = f"This PR addresses issue #{issue.number}\n\n"
            pr_body += commit_message + "\n"
            
            if analysis:
                if analysis.testing_steps:
                    pr_body += "\nTesting Steps:\n"
                    for step in analysis.testing_steps:
                        pr_body += f"- {step}\n"
                
                if analysis.considerations:
                    pr_body += "\nConsiderations:\n"
                    for consideration in analysis.considerations:
                        pr_body += f"- {consideration}\n"
                
                if analysis.potential_impacts:
                    pr_body += "\nPotential Impacts:\n"
                    for impact in analysis.potential_impacts:
                        pr_body += f"- {impact}\n"
            
            # Create pull request
            try:
                pr = self.repo.create_pull(
                    title=f"Fix issue #{issue.number}: {issue.title}",
                    body=pr_body,
                    head=branch_name,
                    base=default_branch
                )
                logger.info(f"Created pull request #{pr.number}")
                
                # Add labels
                pr.set_labels("automated-fix")
                
                return pr
                
            except Exception as e:
                logger.error(f"Error creating pull request: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error in create_pull_request: {str(e)}")
            return None
            logger.info(f"Created pull request: {pr_url}")
            
            return pr_url
            
        except Exception as e:
            logger.error(f"Error processing issue #{issue_number}: {str(e)}")
            return None
    
    def _get_or_create_fork(self) -> Repository:
        """Gets or creates a fork of the repository."""
        try:
            fork = self.github.get_repo(f"{self.user.login}/{self.repo.name}")
            logger.info(f"Using existing fork: {fork.full_name}")
            return fork
        except:
            fork = self.user.create_fork(self.repo)
            logger.info(f"Created new fork: {fork.full_name}")
            return fork
    
    def _create_branch(self, fork: Repository, branch_name: str):
        """Creates a new branch in the fork."""
        try:
            # Get the default branch's HEAD
            default_branch = fork.default_branch
            default_branch_ref = fork.get_git_ref(f"heads/{default_branch}")
            
            # Check if branch exists
            try:
                existing_ref = fork.get_git_ref(f"heads/{branch_name}")
                # Branch exists - update it
                existing_ref.edit(sha=default_branch_ref.object.sha, force=True)
                logger.info(f"Updated existing branch: {branch_name}")
                return
            except:
                # Branch doesn't exist - that's fine
                pass
            
            # Create a new branch
            fork.create_git_ref(ref=f"refs/heads/{branch_name}", 
                              sha=default_branch_ref.object.sha)
            logger.info(f"Created branch: {branch_name}")
        except Exception as e:
            logger.error(f"Error creating branch: {str(e)}")
            raise
    
    def _commit_fix(self, fork: Repository, branch_name: str, fix: CodeFix):
        """Commits a fix to the branch."""
        try:
            # Get the current file
            files = fork.get_contents(fix.file_path, ref=branch_name)
            file = files if not isinstance(files, list) else files[0]
            
            # Update the content
            message = f"Fix: {fix.description}"
            fork.update_file(
                path=fix.file_path,
                message=message,
                content=fix.new_code.encode('utf-8'),  # Ensure content is encoded
                sha=file.sha,
                branch=branch_name
            )
            logger.info(f"Committed fix to {fix.file_path}")
        except Exception as e:
            logger.error(f"Error committing fix: {str(e)}")
            raise
    
    def _create_pull_request(self, issue: Issue, branch_name: str) -> str:
        """Creates a pull request with the fixes."""
        try:
            # Create the pull request
            # Get the analysis details
            analysis = self.fixer.get_analysis()
            
            # Create a detailed PR description
            pr_body = f"""# Fix for Issue #{issue.number}

## Overview
This pull request addresses {issue.title}

## Changes Made
{chr(10).join(f"- {change}" for change in analysis.changes)}

## Testing Steps
{chr(10).join(f"- {step}" for step in analysis.testing_steps)}

## Important Considerations
{chr(10).join(f"- {consideration}" for consideration in analysis.considerations)}

## Potential Impacts
{chr(10).join(f"- {impact}" for impact in analysis.potential_impacts)}

## Automated Analysis
This fix was generated by the GitHub Maintainer AI after careful analysis of the issue and codebase. Each change has been validated for:
- Syntax correctness
- Logic consistency
- Error handling
- Edge cases
- Performance implications

## Review Notes
- Please review the changes carefully
- Pay special attention to the potential impacts
- Test the changes according to the provided testing steps
- Suggest any additional considerations or improvements

Fixes #{issue.number}
"""
            
            pr = self.repo.create_pull(
                title=f"Fix for issue #{issue.number}: {issue.title}",
                body=pr_body,
                base=self.repo.default_branch,
                head=f"{self.user.login}:{branch_name}"
            )
            return pr.html_url
        except Exception as e:
            logger.error(f"Error creating pull request: {str(e)}")
            raise
