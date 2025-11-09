from typing import Dict, List, Optional, Set, Tuple
import re
from dataclasses import dataclass
from github import Repository
from loguru import logger

@dataclass
class DependencyInfo:
    file_path: str
    references: List[str]  # Files that this file references
    referenced_by: List[str]  # Files that reference this file
    symbols_defined: Set[str]  # Symbols defined in this file
    symbols_used: Set[str]  # Symbols used from other files

class MultiFileDependencyAnalyzer:
    def __init__(self, repo: Repository):
        self.repo = repo
        self.dependency_cache: Dict[str, DependencyInfo] = {}
        
    def analyze_dependencies(self, files: List[str]) -> Dict[str, DependencyInfo]:
        """Analyzes dependencies between files."""
        try:
            # Clear cache for new analysis
            self.dependency_cache.clear()
            
            # First pass: collect all symbol definitions
            for file_path in files:
                self._analyze_file_symbols(file_path)
            
            # Second pass: analyze dependencies
            for file_path in files:
                self._analyze_file_dependencies(file_path)
            
            # Return relevant subset of dependency cache
            return {f: self.dependency_cache[f] for f in files if f in self.dependency_cache}
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies: {e}")
            return {}
    
    def _analyze_file_symbols(self, file_path: str):
        """Analyzes symbols defined in a file."""
        try:
            content = self._get_file_content(file_path)
            if not content:
                return
            
            # Initialize dependency info
            info = DependencyInfo(
                file_path=file_path,
                references=[],
                referenced_by=[],
                symbols_defined=set(),
                symbols_used=set()
            )
            
            # Look for symbol definitions based on file type
            ext = file_path.split('.')[-1].lower()
            
            if ext in ['cs']:  # C# files
                # Find class definitions
                class_matches = re.finditer(r'(?:public|private|protected)\s+(?:class|interface|struct)\s+(\w+)', content)
                for match in class_matches:
                    info.symbols_defined.add(match.group(1))
                
                # Find method definitions
                method_matches = re.finditer(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>[\]]+\s+(\w+)\s*\(', content)
                for match in method_matches:
                    info.symbols_defined.add(match.group(1))
                
                # Find property definitions
                prop_matches = re.finditer(r'(?:public|private|protected)\s+(?:static\s+)?[\w<>[\]]+\s+(\w+)\s*\{', content)
                for match in prop_matches:
                    info.symbols_defined.add(match.group(1))
                
            elif ext in ['py']:  # Python files
                # Find class definitions
                class_matches = re.finditer(r'class\s+(\w+)', content)
                for match in class_matches:
                    info.symbols_defined.add(match.group(1))
                
                # Find function definitions
                func_matches = re.finditer(r'def\s+(\w+)', content)
                for match in func_matches:
                    info.symbols_defined.add(match.group(1))
                
                # Find variable definitions at module level
                var_matches = re.finditer(r'^(\w+)\s*=', content, re.MULTILINE)
                for match in var_matches:
                    info.symbols_defined.add(match.group(1))
            
            # Store in cache
            self.dependency_cache[file_path] = info
            
        except Exception as e:
            logger.error(f"Error analyzing symbols in {file_path}: {e}")
    
    def _analyze_file_dependencies(self, file_path: str):
        """Analyzes dependencies between files."""
        try:
            if file_path not in self.dependency_cache:
                return
            
            content = self._get_file_content(file_path)
            if not content:
                return
            
            info = self.dependency_cache[file_path]
            ext = file_path.split('.')[-1].lower()
            
            # Look for symbol usage
            for other_file, other_info in self.dependency_cache.items():
                if other_file == file_path:
                    continue
                
                # Check for usage of symbols from other file
                for symbol in other_info.symbols_defined:
                    # Skip very short symbols to avoid false positives
                    if len(symbol) < 3:
                        continue
                        
                    # Look for usage patterns based on file type
                    if ext in ['cs']:  # C# files
                        patterns = [
                            rf'\b{symbol}\b',  # Direct usage
                            rf'new\s+{symbol}\b',  # Object creation
                            rf':\s*{symbol}\b',  # Inheritance
                            rf'<\s*{symbol}\s*>',  # Generic type
                        ]
                    elif ext in ['py']:  # Python files
                        patterns = [
                            rf'\b{symbol}\b',  # Direct usage
                            rf'from\s+\w+\s+import\s+{symbol}',  # Import
                            rf'import\s+{symbol}',  # Direct import
                        ]
                    else:
                        patterns = [rf'\b{symbol}\b']  # Default pattern
                    
                    # Check each pattern
                    for pattern in patterns:
                        if re.search(pattern, content):
                            info.symbols_used.add(symbol)
                            info.references.append(other_file)
                            other_info.referenced_by.append(file_path)
                            break
            
        except Exception as e:
            logger.error(f"Error analyzing dependencies in {file_path}: {e}")
    
    def _get_file_content(self, file_path: str) -> Optional[str]:
        """Gets file content from repository."""
        try:
            file_content = self.repo.get_contents(file_path)
            return file_content.decoded_content.decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
            return None
    
    def get_affected_files(self, primary_files: List[str]) -> List[str]:
        """Gets the full list of files that might need to be modified."""
        affected = set(primary_files)
        to_process = list(primary_files)
        
        while to_process:
            current = to_process.pop(0)
            if current not in self.dependency_cache:
                continue
            
            info = self.dependency_cache[current]
            
            # Add referenced files
            for ref in info.references:
                if ref not in affected:
                    affected.add(ref)
                    to_process.append(ref)
            
            # Add files that reference this one
            for ref in info.referenced_by:
                if ref not in affected:
                    affected.add(ref)
                    to_process.append(ref)
        
        return list(affected)
    
    def analyze_change_impact(self, files: List[str]) -> Dict[str, Dict]:
        """Analyzes the potential impact of changes to the given files."""
        impacts = {}
        for file_path in files:
            if file_path not in self.dependency_cache:
                continue
                
            info = self.dependency_cache[file_path]
            impacts[file_path] = {
                "direct_dependencies": info.references,
                "dependent_files": info.referenced_by,
                "symbols_affected": list(info.symbols_defined),
                "risk_level": self._calculate_risk_level(info)
            }
        
        return impacts
    
    def _calculate_risk_level(self, info: DependencyInfo) -> str:
        """Calculates risk level based on dependencies."""
        ref_count = len(info.referenced_by)
        if ref_count > 10:
            return "high"
        elif ref_count > 5:
            return "medium"
        return "low"
