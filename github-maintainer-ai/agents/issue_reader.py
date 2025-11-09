from typing import List, Dict
from core.github_client import GitHubClient
from core.logger import get_logger

logger = get_logger(__name__)

class IssueReader:
    def __init__(self, repo_url):
        """Initialize IssueReader with a repository URL.
        
        Args:
            repo_url (str): HTTPS clone URL of the repository
        """
        self.github_client = GitHubClient({'url': repo_url})
        
    def get_open_issues(self) -> List[Dict]:
        """Fetch and analyze open issues from the repository."""
        try:
            issues = self.github_client.get_open_issues()
            return self._analyze_issues(issues)
        except Exception as e:
            logger.error(f"Error fetching open issues: {e}")
            return []
    
    def _analyze_issues(self, issues: List[Dict]) -> List[Dict]:
        """Analyze issues and extract relevant information."""
        analyzed_issues = []
        for issue in issues:
            # Add issue analysis logic here
            analyzed_issues.append({
                "id": issue["id"],
                "title": issue["title"],
                "body": issue["body"],
                "labels": issue["labels"],
                "priority": self._determine_priority(issue)
            })
        return analyzed_issues
    
    def _determine_priority(self, issue: Dict) -> str:
        """Determine issue priority based on labels and content."""
        # Add priority determination logic here
        return "medium"
