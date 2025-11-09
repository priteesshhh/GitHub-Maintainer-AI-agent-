from typing import Dict, List, Optional
import json
import os
from datetime import datetime
from loguru import logger

class LearningSystem:
    def __init__(self, memory_dir: str = "./memory"):
        self.memory_dir = memory_dir
        self.fixes_memory_path = os.path.join(memory_dir, "learned_fixes.json")
        self.patterns_memory_path = os.path.join(memory_dir, "learned_patterns.json")
        self._load_memory()

    def _load_memory(self):
        """Load learned patterns and fixes from disk."""
        try:
            if os.path.exists(self.fixes_memory_path):
                with open(self.fixes_memory_path, 'r') as f:
                    self.fixes_memory = json.load(f)
            else:
                self.fixes_memory = []

            if os.path.exists(self.patterns_memory_path):
                with open(self.patterns_memory_path, 'r') as f:
                    self.patterns_memory = json.load(f)
            else:
                self.patterns_memory = {
                    "file_patterns": {},
                    "code_patterns": {},
                    "fix_strategies": {}
                }
        except Exception as e:
            logger.error(f"Error loading memory: {e}")
            self.fixes_memory = []
            self.patterns_memory = {
                "file_patterns": {},
                "code_patterns": {},
                "fix_strategies": {}
            }

    def _save_memory(self):
        """Save learned patterns and fixes to disk."""
        try:
            os.makedirs(self.memory_dir, exist_ok=True)
            with open(self.fixes_memory_path, 'w') as f:
                json.dump(self.fixes_memory, f, indent=2)
            with open(self.patterns_memory_path, 'w') as f:
                json.dump(self.patterns_memory, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving memory: {e}")

    def learn_from_fix(self, issue_data: Dict, files: List[str], fix_data: Dict, success: bool):
        """Learn from a fix attempt."""
        try:
            # Record the fix attempt
            fix_record = {
                "timestamp": datetime.now().isoformat(),
                "issue": {
                    "title": issue_data.get("title", ""),
                    "body": issue_data.get("body", ""),
                    "labels": issue_data.get("labels", [])
                },
                "affected_files": files,
                "fix_data": fix_data,
                "success": success,
                "patterns_identified": fix_data.get("patterns_found", []),
                "fix_strategy": fix_data.get("strategy", "")
            }
            self.fixes_memory.append(fix_record)

            # Update pattern recognition
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext not in self.patterns_memory["file_patterns"]:
                    self.patterns_memory["file_patterns"][ext] = {"count": 0, "issues": {}}
                self.patterns_memory["file_patterns"][ext]["count"] += 1
                
                # Track issue types per file extension
                for label in issue_data.get("labels", []):
                    if label not in self.patterns_memory["file_patterns"][ext]["issues"]:
                        self.patterns_memory["file_patterns"][ext]["issues"][label] = 0
                    self.patterns_memory["file_patterns"][ext]["issues"][label] += 1

            # Learn from code patterns
            for pattern in fix_data.get("patterns_found", []):
                if pattern not in self.patterns_memory["code_patterns"]:
                    self.patterns_memory["code_patterns"][pattern] = {
                        "count": 0,
                        "success_count": 0,
                        "related_patterns": {}
                    }
                self.patterns_memory["code_patterns"][pattern]["count"] += 1
                if success:
                    self.patterns_memory["code_patterns"][pattern]["success_count"] += 1

            # Learn fix strategies
            strategy = fix_data.get("strategy", "")
            if strategy:
                if strategy not in self.patterns_memory["fix_strategies"]:
                    self.patterns_memory["fix_strategies"][strategy] = {
                        "count": 0,
                        "success_count": 0,
                        "related_issues": {}
                    }
                self.patterns_memory["fix_strategies"][strategy]["count"] += 1
                if success:
                    self.patterns_memory["fix_strategies"][strategy]["success_count"] += 1

            self._save_memory()
            logger.info(f"Learned from fix attempt: {success}")
        except Exception as e:
            logger.error(f"Error learning from fix: {e}")

    def get_fix_suggestion(self, issue_data: Dict, files: List[str]) -> Optional[Dict]:
        """Get fix suggestions based on learned patterns."""
        try:
            suggestions = {
                "file_suggestions": [],
                "pattern_suggestions": [],
                "strategy_suggestions": []
            }

            # Check file patterns
            for file in files:
                ext = os.path.splitext(file)[1]
                if ext in self.patterns_memory["file_patterns"]:
                    pattern = self.patterns_memory["file_patterns"][ext]
                    if pattern["count"] > 0:
                        common_issues = sorted(
                            pattern["issues"].items(),
                            key=lambda x: x[1],
                            reverse=True
                        )[:3]
                        suggestions["file_suggestions"].append({
                            "file_type": ext,
                            "frequency": pattern["count"],
                            "common_issues": common_issues
                        })

            # Find similar successful fixes
            similar_fixes = []
            for fix in self.fixes_memory:
                if fix["success"]:
                    # Calculate similarity score
                    score = self._calculate_similarity(issue_data, fix["issue"])
                    if score > 0.5:  # Threshold for similarity
                        similar_fixes.append((score, fix))

            # Get top patterns and strategies from similar fixes
            if similar_fixes:
                similar_fixes.sort(reverse=True)  # Sort by similarity score
                for _, fix in similar_fixes[:3]:
                    for pattern in fix["patterns_identified"]:
                        if pattern in self.patterns_memory["code_patterns"]:
                            p_data = self.patterns_memory["code_patterns"][pattern]
                            success_rate = p_data["success_count"] / p_data["count"]
                            if success_rate > 0.7:  # Only suggest patterns with good success rate
                                suggestions["pattern_suggestions"].append({
                                    "pattern": pattern,
                                    "success_rate": success_rate,
                                    "frequency": p_data["count"]
                                })
                    
                    strategy = fix["fix_strategy"]
                    if strategy and strategy in self.patterns_memory["fix_strategies"]:
                        s_data = self.patterns_memory["fix_strategies"][strategy]
                        success_rate = s_data["success_count"] / s_data["count"]
                        if success_rate > 0.7:
                            suggestions["strategy_suggestions"].append({
                                "strategy": strategy,
                                "success_rate": success_rate,
                                "frequency": s_data["count"]
                            })

            return suggestions if any(suggestions.values()) else None

        except Exception as e:
            logger.error(f"Error getting fix suggestions: {e}")
            return None

    def _calculate_similarity(self, issue1: Dict, issue2: Dict) -> float:
        """Calculate similarity between two issues."""
        try:
            # Simple text similarity for now
            text1 = (issue1.get("title", "") + " " + issue1.get("body", "")).lower()
            text2 = (issue2.get("title", "") + " " + issue2.get("body", "")).lower()
            
            # Get words
            words1 = set(text1.split())
            words2 = set(text2.split())
            
            # Calculate Jaccard similarity
            intersection = len(words1.intersection(words2))
            union = len(words1.union(words2))
            
            return intersection / union if union > 0 else 0
            
        except Exception as e:
            logger.error(f"Error calculating similarity: {e}")
            return 0.0
