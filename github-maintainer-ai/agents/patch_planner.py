from typing import Dict, List
from core.github_client import GitHubClient
from core.logger import get_logger
from core.local_model import LocalModel

logger = get_logger(__name__)

class PatchPlanner:
    def __init__(self):
        self.github_client = GitHubClient()
        self.model = LocalModel()
    
    def plan_patches(self, analysis: Dict, context: Dict) -> List[Dict]:
        """Plan patches based on code analysis and context."""
        try:
            issue = context.get('issue', {})
            logger.info(f"Planning patches for issue #{issue.get('id')}")
            
            if not analysis:
                logger.info("No analysis results to plan patches from")
                return []
            
            logger.info("Generating patch plans...")
            patch_plans = self._generate_patch_plans(analysis, context)
            
            if patch_plans:
                logger.info(f"Generated {len(patch_plans)} patch plans")
                for i, patch in enumerate(patch_plans, 1):
                    logger.info(f"Patch {i}:")
                    logger.info(f"  File: {patch['file_path']}")
                    logger.info(f"  Priority: {patch.get('priority', 'medium')}")
                    if patch.get('estimated_impact'):
                        logger.info(f"  Risk Level: {patch['estimated_impact'].get('risk_level', 'unknown')}")
            else:
                logger.info("No patches needed or could not generate appropriate patches")
            
            return patch_plans
        except Exception as e:
            logger.error(f"Error planning patches: {e}")
            return []
    
    def _generate_patch_plans(self, analysis: Dict, context: Dict) -> List[Dict]:
        """Generate detailed patch plans for each file."""
        patch_plans = []
        for file_path, file_analysis in analysis.items():
            patch = self._create_patch_plan(file_path, file_analysis, context)
            if patch:
                patch_plans.append(patch)
        return patch_plans
    
    def _create_patch_plan(self, file_path: str, analysis: Dict, context: Dict) -> Dict:
        """Create a specific patch plan for a file."""
        return {
            "file_path": file_path,
            "changes": self.model.generate_changes(analysis, context),
            "priority": self._calculate_priority(analysis),
            "estimated_impact": self._estimate_impact(analysis)
        }
    
    def _calculate_priority(self, analysis: Dict) -> str:
        """Calculate priority of the patch."""
        # Add priority calculation logic here
        return "medium"
    
    def _estimate_impact(self, analysis: Dict) -> Dict:
        """Estimate the potential impact of the patch."""
        return {
            "risk_level": "low",
            "affected_components": [],
            "testing_requirements": []
        }
