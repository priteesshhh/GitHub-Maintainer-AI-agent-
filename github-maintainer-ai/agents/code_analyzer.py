from typing import Dict, List
from core.github_client import GitHubClient
from core.logger import get_logger
from core.local_model import LocalModel

logger = get_logger(__name__)

class CodeAnalyzer:
    def __init__(self):
        self.github_client = GitHubClient()
        self.model = LocalModel()
        
    def analyze_repository(self, context: Dict) -> Dict:
        """Analyze repository code based on the given context."""
        try:
            issue = context.get('issue', {})
            logger.info(f"Analyzing code for issue #{issue.get('id')}")
            logger.info(f"Issue title: {issue.get('title')}")
            logger.info(f"Issue description: {issue.get('body', 'No description')}")
            
            files = self.github_client.get_relevant_files(context)
            if not files:
                logger.info("No relevant files found for this issue")
                return {}
                
            logger.info(f"Found {len(files)} relevant files to analyze")
            analysis_result = self._analyze_code_files(files, context)
            
            if analysis_result:
                logger.info("Analysis complete. Found potential improvements.")
                for file_path, analysis in analysis_result.items():
                    logger.info(f"File: {file_path}")
                    if analysis.get('suggestions'):
                        logger.info("Suggested improvements:")
                        for suggestion in analysis['suggestions']:
                            logger.info(f"  - {suggestion}")
            else:
                logger.info("Analysis complete. No immediate improvements needed.")
                
            return analysis_result
        except Exception as e:
            logger.error(f"Error analyzing repository: {e}")
            return {}
    
    def _analyze_code_files(self, files: List[Dict], context: Dict) -> Dict:
        """Analyze code files for patterns and potential solutions."""
        analysis = {}
        for file in files:
            analysis[file["path"]] = {
                "complexity": self._calculate_complexity(file["content"]),
                "suggestions": self._generate_suggestions(file, context)
            }
        return analysis
    
    def _calculate_complexity(self, code: str) -> Dict:
        """Calculate code complexity metrics."""
        # Add complexity calculation logic here
        return {"cyclomatic": 0, "cognitive": 0}
    
    def _generate_suggestions(self, file: Dict, context: Dict) -> List[str]:
        """Generate code improvement suggestions using the local model."""
        return self.model.generate_suggestions(file, context)
