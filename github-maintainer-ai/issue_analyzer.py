#!/usr/bin/env python3

from dataclasses import dataclass
from typing import List, Optional, Set
import re
from github import Github, Auth, Issue, Repository
from loguru import logger

@dataclass
class CodeFix:
    file_path: str
    old_code: str
    new_code: str
    description: str

class IssueAnalysis:
    def __init__(self):
        self.affected_files: Set[str] = set()
        self.key_concepts: Set[str] = set()
        self.error_patterns: Set[str] = set()
        self.suggested_fixes: List[str] = []
        self.confidence_score: float = 0.0

class IssueAnalyzer:
    def __init__(self, repo: Repository):
        self.repo = repo
    
    def analyze_issue(self, issue: Issue) -> Optional[List[str]]:
        """Analyzes an issue to determine if it's fixable and what needs to be fixed."""
        try:
            # Create analysis object
            analysis = IssueAnalysis()
            
            # Get the issue title and body
            title = issue.title.lower()
            body = issue.body.lower() if issue.body else ""
            
            # Extract key concepts and patterns
            self._extract_concepts(title, body, analysis)
            
            # Determine issue type
            if self._is_bug_report(analysis):
                logger.info(f"Issue #{issue.number} appears to be a bug report")
                return self._analyze_bug_report(issue, analysis)
            elif self._is_feature_request(analysis):
                logger.info(f"Issue #{issue.number} appears to be a feature request")
                return self._analyze_feature_request(issue, analysis)
            else:
                logger.info(f"Issue #{issue.number} type cannot be determined")
                return None
            
        except Exception as e:
            logger.error(f"Error analyzing issue #{issue.number}: {str(e)}")
            return None
    
    def _extract_concepts(self, title: str, body: str, analysis: IssueAnalysis):
        """Extracts key concepts and patterns from issue text."""
        combined_text = f"{title}\n{body}".lower()
        
        # Technical patterns to look for
        patterns = [
            # Error patterns
            (r'\b\w+error\b', 'error_pattern'),
            (r'\berror\b', 'error_pattern'),  # Catch standalone "error"
            (r'\b\w+exception\b', 'exception_pattern'),
            (r'\b\w+bug\b', 'bug_pattern'),
            (r'\bbug\b', 'bug_pattern'),  # Catch standalone "bug"
            (r'\b\w+crash\b', 'crash_pattern'),
            
            # Speed-related patterns
            (r'\b0\s*mph\b', 'zero_speed'),
            (r'\b0\s*speed\b', 'zero_speed'),
            (r'\bspeed\s*=\s*0\b', 'zero_speed'),
            (r'\bspeed.*incorrect\b', 'speed_error'),
            (r'\bincorrect.*speed\b', 'speed_error'),
            (r'\bspeed\b', 'speed_related'),
            (r'\bvelocity\b', 'speed_related'),
            (r'\bmph\b', 'speed_related'),
            (r'\bkm/h\b', 'speed_related'),
            (r'\bmemory\b', 'memory_related'),
            (r'\bperformance\b', 'performance_related'),
            (r'\bfunction\s+(\w+)\b', 'function_name'),
            (r'\bmethod\s+(\w+)\b', 'method_name'),
            (r'\bclass\s+(\w+)\b', 'class_name'),
            (r'\bfile\s+[\'"]([\w/.]+)[\'"]', 'file_reference'),
            (r'\b([\w/.]+\.(?:py|js|cpp|h))\b', 'code_file')
        ]
        
        for pattern, category in patterns:
            matches = re.finditer(pattern, combined_text)
            for match in matches:
                if len(match.groups()) > 0:
                    analysis.key_concepts.add(f"{category}:{match.group(1)}")
                else:
                    analysis.key_concepts.add(f"{category}:{match.group()}")
    
    def _is_bug_report(self, analysis: IssueAnalysis) -> bool:
        """Determines if the issue is a bug report based on extracted concepts."""
        bug_indicators = {
            'error_pattern', 'exception_pattern', 'bug_pattern', 'crash_pattern',
            'zero_speed', 'speed_error'  # Speed-related issues are often bugs
        }
        concepts = {concept.split(':')[0] for concept in analysis.key_concepts}
        return bool(concepts.intersection(bug_indicators))
    
    def _is_feature_request(self, analysis: IssueAnalysis) -> bool:
        """Determines if the issue is a feature request based on extracted concepts."""
        feature_indicators = {'feature', 'enhancement', 'request', 'add', 'implement'}
        return any(concept.split(':')[1] in feature_indicators for concept in analysis.key_concepts)
    
    def _analyze_bug_report(self, issue: Issue, analysis: IssueAnalysis) -> Optional[List[str]]:
        """Analyzes a bug report to identify affected files."""
        try:
            # Get repository contents
            contents = self.repo.get_contents("")
            
            # Get all comments for additional context
            comments = [comment.body for comment in issue.get_comments()]
            combined_text = f"{issue.title}\n{issue.body or ''}\n{''.join(comments)}".lower()
            
            while contents:
                content = contents.pop(0)
                if content.type == "dir":
                    contents.extend(self.repo.get_contents(content.path))
                    continue
                
                file_path = content.path
                score = self._calculate_relevance_score(file_path, content, combined_text, analysis)
                
                if score > 0.5:  # Threshold for considering a file relevant
                    analysis.affected_files.add(file_path)
                    logger.info(f"Found relevant file: {file_path} (score: {score:.2f})")
            
            affected_files = list(analysis.affected_files)
            
            if not affected_files:
                logger.info("No directly affected files found, analyzing repository structure")
                return self._analyze_repository_structure(issue, analysis)
            
            return affected_files
            
        except Exception as e:
            logger.error(f"Error in bug report analysis: {str(e)}")
            return None

    def _calculate_relevance_score(self, file_path: str, content, issue_text: str, analysis: IssueAnalysis) -> float:
        """Calculates how relevant a file is to the issue."""
        score = 0.0
        
        try:
            # Check if file is directly referenced
            if file_path.lower() in issue_text:
                score += 1.0
            
            # Check if file extension matches any mentioned technology
            ext = file_path.split('.')[-1].lower()
            if f".{ext}" in issue_text:
                score += 0.3
            
            # For code files, analyze content
            if ext in ['py', 'js', 'cpp', 'h', 'cs']:
                try:
                    content_text = content.decoded_content.decode('utf-8').lower()
                    
                    # Check for key concepts in file content
                    for concept in analysis.key_concepts:
                        if concept.split(':')[1] in content_text:
                            score += 0.4
                    
                    # Special handling for Python files
                    if ext == 'py':
                        module_name = file_path.replace('/', '.').replace('.py', '')
                        if module_name in issue_text:
                            score += 0.5
                    
                except Exception as e:
                    logger.error(f"Error analyzing file content: {str(e)}")
            
            # Check for structural relevance
            if 'main' in file_path.lower():
                score += 0.2
            if 'core' in file_path.lower():
                score += 0.2
            if 'test' in file_path.lower() and 'test' in issue_text:
                score += 0.3
            
        except Exception as e:
            logger.error(f"Error calculating relevance score: {str(e)}")
        
        return score
    
    def _analyze_repository_structure(self, issue: Issue, analysis: IssueAnalysis) -> Optional[List[str]]:
        """Analyzes repository structure to find relevant files."""
        try:
            contents = self.repo.get_contents("")
            core_files = []
            test_files = []
            
            while contents:
                content = contents.pop(0)
                if content.type == "dir":
                    contents.extend(self.repo.get_contents(content.path))
                else:
                    file_path = content.path.lower()
                    
                    # Categorize files
                    if file_path.endswith(('.py', '.js', '.cpp', '.h', '.cs')):
                        if 'test' in file_path:
                            test_files.append(content.path)
                        elif any(x in file_path for x in ['main', 'core', 'index']):
                            core_files.append(content.path)
            
            # For bugs, include both core and test files
            if self._is_bug_report(analysis):
                return core_files + test_files
            
            # For features, prefer core files
            return core_files if core_files else test_files
            
        except Exception as e:
            logger.error(f"Error in repository structure analysis: {str(e)}")
            return None
            
    def _analyze_feature_request(self, issue: Issue, analysis: IssueAnalysis) -> Optional[List[str]]:
        """Analyzes a feature request to identify relevant files for implementation."""
        try:
            # For feature requests, we want to find the best places to add new code
            return self._analyze_repository_structure(issue, analysis)
        except Exception as e:
            logger.error(f"Error analyzing feature request: {str(e)}")
            return None
