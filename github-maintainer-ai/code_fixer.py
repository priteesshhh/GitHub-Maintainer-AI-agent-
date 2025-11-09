#!/usr/bin/env python3

from typing import List, Optional, Dict
import ast
import re
from github import Repository, Issue
from loguru import logger
from issue_analyzer import CodeFix
from core.learning_system import LearningSystem
from core.dependency_analyzer import MultiFileDependencyAnalyzer
from speed_fixes import (
    _fix_speed_property,
    _fix_speed_method,
    _fix_speed_comparison,
    _fix_speed_general
)

class FixAnalysis:
    def __init__(self):
        self.changes: List[str] = []
        self.testing_steps: List[str] = []
        self.considerations: List[str] = []
        self.potential_impacts: List[str] = []

class CodeFixer:
    def __init__(self, repo: Repository):
        self.repo = repo
        self._current_analysis = None
        self.learning_system = LearningSystem()
        self.dependency_analyzer = MultiFileDependencyAnalyzer(repo)
    
    def get_analysis(self) -> Optional[FixAnalysis]:
        """Returns the analysis from the last fix generation."""
        return self._current_analysis
    
    def generate_fix(self, issue: Issue, affected_files: List[str]) -> Optional[List[CodeFix]]:
        """Generates fixes for the affected files based on the issue description."""
        try:
            fixes = []
            fix_data = {
                "patterns_found": [],
                "strategy": "",
                "changes": []
            }

            # Analyze dependencies
            logger.info("Analyzing file dependencies...")
            self.dependency_analyzer.analyze_dependencies(affected_files)
            
            # Get potential impact
            impact = self.dependency_analyzer.analyze_change_impact(affected_files)
            logger.info("Change impact analysis:")
            for file, details in impact.items():
                logger.info(f"File: {file}")
                logger.info(f"  Risk Level: {details['risk_level']}")
                logger.info(f"  Dependent Files: {len(details['dependent_files'])}")
            
            # Get fix suggestions from learning system
            issue_data = {
                "title": issue.title,
                "body": issue.body,
                "labels": [label.name for label in issue.labels]
            }
            suggestions = self.learning_system.get_fix_suggestion(issue_data, affected_files)
            if suggestions:
                logger.info("Found relevant fix suggestions from previous experience")
                for suggestion in suggestions.get("strategy_suggestions", []):
                    logger.info(f"Strategy: {suggestion['strategy']} (Success rate: {suggestion['success_rate']:.2f})")
            
            # Get all potentially affected files
            all_affected = self.dependency_analyzer.get_affected_files(affected_files)
            if len(all_affected) > len(affected_files):
                logger.info(f"Found additional affected files: {set(all_affected) - set(affected_files)}")
            
            # Process each affected file
            for file_path in all_affected:
                try:
                    # Get the file content
                    file_content = self.repo.get_contents(file_path)
                    
                    # Log file details
                    logger.info(f"Analyzing file: {file_path}")
                    logger.info(f"File size: {file_content.size} bytes")
                    logger.info(f"File encoding: {file_content.encoding}")
                    
                    # Get raw content
                    raw_content = file_content.decoded_content
                    content = None
                    
                    # Try to decode with different encodings
                    for encoding in ['utf-8', 'utf-16', 'latin1', 'ascii']:
                        try:
                            content = raw_content.decode(encoding)
                            logger.info(f"Successfully decoded with {encoding}")
                            break
                        except UnicodeDecodeError:
                            logger.warning(f"Failed to decode with {encoding}")
                            continue
                    
                    if content is None:
                        logger.error(f"Could not decode {file_path} with any known encoding")
                        continue
                    
                    # Log a sample of the content
                    preview = content[:200]
                    if len(content) > 200:
                        preview += '...'
                    logger.info(f"Content preview:\n{preview}")
                    
                    # Initialize analysis for this file
                    analysis = FixAnalysis()
                    self._current_analysis = analysis
                    
                    # Record impact analysis in current analysis
                    if file_path in impact:
                        analysis.potential_impacts.extend([
                            f"Affects {len(impact[file_path]['dependent_files'])} dependent files",
                            f"Risk Level: {impact[file_path]['risk_level']}"
                        ])
                    
                    # Analyze the issue and content to determine the fix
                    fix = self._analyze_and_fix(issue, file_path, content)
                    if fix:
                        fixes.append(fix)
                        fix_data["changes"].append({
                            "file": file_path,
                            "description": fix.description
                        })
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    continue
            
            # Learn from this fix attempt
            if fixes:
                self.learning_system.learn_from_fix(
                    issue_data=issue_data,
                    files=affected_files,
                    fix_data=fix_data,
                    success=True
                )
            
            return fixes if fixes else None
            
        except Exception as e:
            logger.error(f"Error generating fixes: {str(e)}")
            
            # Learn from failed attempt
            self.learning_system.learn_from_fix(
                issue_data=issue_data,
                files=affected_files,
                fix_data=fix_data,
                success=False
            )
            
            return None
    
    def _analyze_and_fix(self, issue: Issue, file_path: str, content: str) -> Optional[CodeFix]:
        """Analyzes the code and generates a fix based on the issue description."""
        try:
            # Extract key information from the issue
            title = issue.title.lower()
            body = (issue.body or "").lower()
            
            # Look for specific patterns that indicate what needs to be fixed
            if "speed" in title or "speed" in body or "mph" in title or "mph" in body:
                return self._analyze_speed_calculation(content)
            elif "error handling" in title or "exception" in body:
                return self._fix_error_handling(content)
            # Add more patterns as needed
            
            return None
            
        except Exception as e:
            logger.error(f"Error in fix analysis: {str(e)}")
            return None
    
    def _analyze_speed_calculation(self, content: str, file_path: str) -> Optional[CodeFix]:
        """Analyzes and fixes speed calculations in code."""
        try:
            logger.info("Starting speed calculation analysis")
            
            # Search for speed-related code sections
            speed_patterns = [
                # Zero speed comparisons (case-insensitive)
                r'(?i)speed\s*[=<>!]=?\s*0(?:\.0+)?[f]?\s*[,;)]',  # Covers =, ==, <=, >=, != with optional float/double suffix
                r'(?i)speed\s*[=<>!]=?\s*0\.[0-9]*[f]?\s*[,;)]',  # Floating point comparisons
                r'(?i)if\s*\(\s*speed\s*[=<>!]=?\s*0',  # Zero speed checks in if statements
                r'(?i)return\s+0[f]?\s*;\s*//.*speed',  # Zero speed returns
                
                # Speed property/variable patterns
                r'(?i)float\s+speed\s*=\s*[^;]+;',  # Speed variable declarations
                r'(?i)double\s+speed\s*=\s*[^;]+;',
                r'(?i)int\s+speed\s*=\s*[^;]+;',
                r'(?i)private\s+(?:float|double|int)\s+_?speed\s*[{;]',  # Private speed fields
                r'(?i)public\s+(?:float|double|int)\s+Speed\s*\{[^}]*\}',  # Speed property
                r'(?i)protected\s+(?:float|double|int)\s+Speed\s*\{[^}]*\}',
                
                # Method patterns
                r'(?i)(?:public|private|protected)\s+(?:float|double|int)\s+GetSpeed\s*\([^)]*\)\s*\{',  # GetSpeed method
                r'(?i)void\s+(?:Set|Update|Calculate)Speed\s*\([^)]*\)\s*\{',  # Speed update methods
                r'(?i)float\s+Calculate(?:Current)?Speed\s*\([^)]*\)\s*\{',  # Speed calculation methods
                
                # Speed calculations and conversions
                r'(?i)speed\s*=\s*(?:Math\.)?(?:Round|Floor|Ceiling)\(',  # Math operations
                r'(?i)speed\s*[+\-*/]=',  # Speed arithmetic
                r'(?i)MPH\s*[=<>!]=?\s*0',  # MPH zero checks
                r'(?i)_?speed\s*=\s*[^;]+mph[^;]*;',  # Speed with MPH unit
                r'(?i)ConvertToMPH\(.*speed.*\)',  # Speed conversions
                r'(?i)ConvertFromMPH\(.*speed.*\)',
                
                # Display/formatting patterns
                r'(?i)string\.Format\s*\(\s*"{0:F[0-9]}\s*MPH"\s*,\s*speed\s*\)',  # String formatting
                r'(?i)\$"{speed:F[0-9]}\s*MPH"',  # String interpolation
                r'(?i)DisplaySpeed\s*=\s*[^;]+speed[^;]*;',  # Speed display assignments
                
                # Comments and regions
                r'(?i)//.*\bspeed\b.*(?:calculation|check|validation)',  # Speed-related comments
                r'(?i)/\*.*\bspeed\b.*\*/',  # Multi-line comments
                r'(?i)#region.*\bspeed\b.*#endregion',  # Code regions
            ]
            
            logger.info("Starting pattern search")
            
            # Split into lines and join with line numbers for better context
            lines = [(i+1, line) for i, line in enumerate(content.split('\n'))]
            
            # Initialize analysis
            self._current_analysis = FixAnalysis()
            
            # Find all matches with context
            matches = []
            current_block = None
            current_block_lines = []
            
            for line_num, line in lines:
                # Check if this line starts a new block
                if any(re.search(pattern, line, re.IGNORECASE) for pattern in speed_patterns):
                    if current_block:
                        # Save previous block if it exists
                        matches.append((current_block, '\n'.join(current_block_lines)))
                    # Start new block with context
                    current_block = line_num
                    current_block_lines = []
                    # Get context around the line
                    start = max(0, line_num - 5)
                    end = min(len(lines), line_num + 6)
                    context = '\n'.join(line for _, line in lines[start:end])
                    current_block_lines.append(context)
                    logger.info(f"Found speed-related code at line {line_num}")
                    logger.info(f"Context:\n{context}")
                
                # Check if we're in a block with braces
                if current_block and ('{' in line or '}' in line):
                    current_block_lines.append(line)
                    # Check if block is complete
                    block_text = '\n'.join(current_block_lines)
                    if block_text.count('{') == block_text.count('}') and block_text.count('{') > 0:
                        matches.append((current_block, block_text))
                        current_block = None
                        current_block_lines = []
            
            # Generate fixes for each match
            for line_num, block in matches:
                logger.info(f"Analyzing block at line {line_num}")
                logger.info(f"Block content:\n{block}")
                
                try:
                    # Record what we're analyzing
                    self._current_analysis.changes.append(f"Analyzing code block at line {line_num}")
                    
                    # Look for train speed monitoring patterns
                    if "TrainSpeedMph" in block:
                        logger.info("Found train speed monitoring code")
                        improved_code = '''double currentSpeed = train.TrainSpeedMph;
                    // Handle very small speeds (effectively stopped)
                    if (Math.Abs(currentSpeed) <= 0.01)
                    {
                        currentSpeed = 0.0;  // Explicitly set to zero
                        train.Status = TrainStatus.Stopped;
                    }
                    double lastKnownSpeed = lastSpeed.ContainsKey(id) ? lastSpeed[id] : currentSpeed;
                    lastSpeed[id] = currentSpeed;

                    // Log speed changes
                    if (Math.Abs(currentSpeed - lastKnownSpeed) > 0.1)  // Only log significant changes
                    {
                        string status = currentSpeed == 0.0 ? "stopped" : 
                                      currentSpeed > lastKnownSpeed ? "accelerating" : "decelerating";
                        string msg = $"[{simNow:T}] {train.EngineerName} on {train.TrainSymbol} {status} " +
                                   $"(Speed: {currentSpeed:F1} MPH, Change: {(currentSpeed - lastKnownSpeed):F1} MPH)";
                        Logger.LogDebug(msg);
                        if (discordEnabled && (currentSpeed == 0.0 || Math.Abs(currentSpeed - lastKnownSpeed) > 5.0))
                        {
                            await discordClient.SendMessage(msg);
                        }
                    }'''
                        fix = CodeFix(
                            file_path=file_path,
                            old_code=block,
                            new_code=improved_code,
                            description="Enhanced train speed monitoring with proper zero-speed handling and improved logging"
                        )
                    # Other speed-related patterns
                    elif "public" in block and "Speed" in block and "{" in block:
                        logger.info("Found Speed property")
                        fix = _fix_speed_property(block)
                        if fix:
                            fix.file_path = file_path
                    elif "GetSpeed" in block or "CalculateSpeed" in block:
                        logger.info("Found speed calculation method")
                        fix = _fix_speed_method(block)
                        if fix:
                            fix.file_path = file_path
                    elif "speed == 0" in block or "speed <= 0" in block:
                        logger.info("Found speed comparison")
                        fix = _fix_speed_comparison(block)
                        if fix:
                            fix.file_path = file_path
                    else:
                        logger.info("Found general speed-related code")
                        fix = _fix_speed_general(block)
                        if fix:
                            fix.file_path = file_path
                    
                    if fix:
                        # Record analysis details
                        self._current_analysis.testing_steps.extend([
                            "Test with speed = 0.0",
                            "Test with speed = 0.01",
                            "Test with negative speeds",
                            "Test with very high speeds",
                            "Verify display formatting"
                        ])
                        self._current_analysis.considerations.extend([
                            "Added proper floating-point comparison",
                            "Improved error handling",
                            "Enhanced speed display formatting",
                            "Added debug logging"
                        ])
                        self._current_analysis.potential_impacts.extend([
                            "Changed speed comparison logic",
                            "Modified display formatting",
                            "Added logging statements"
                        ])
                        return fix
                    
                except Exception as e:
                    logger.error(f"Error analyzing block: {str(e)}")
            
            return None
            
        except Exception as e:
            logger.error(f"Error in speed calculation analysis: {str(e)}")
            return None
    
    def _generate_improved_speed_calc(self, context: str) -> str:
        """Generates improved speed calculation code."""
        try:
            # Determine if this is C# code
            is_csharp = "using System" in context or "public" in context
            
            if is_csharp:
                # C# version
                return '''// Check if vehicle is effectively stopped
if (Math.Abs(speed) <= 0.01f)
{
    speed = 0f;  // Explicitly set to zero
    status = VehicleStatus.Stopped;
    _displayedSpeed = "Stopped";  // Human-readable status
    Logger.LogDebug("Vehicle speed below threshold, marked as stopped");
}
else
{
    _displayedSpeed = $"{speed:F1} MPH";  // One decimal place for non-zero speeds
    Logger.LogDebug($"Vehicle speed updated to {_displayedSpeed}");
}'''
            else:
                # Python version
                return '''# Check if vehicle is effectively stopped
if abs(speed) <= 0.01:
    speed = 0.0  # Explicitly set to zero
    status = VehicleStatus.STOPPED
    displayed_speed = "Stopped"  # Human-readable status
    logger.debug("Vehicle speed below threshold, marked as stopped")
else:
    displayed_speed = f"{speed:.1f} MPH"  # One decimal place for non-zero speeds
    logger.debug(f"Vehicle speed updated to {displayed_speed}")'''
                
        except Exception as e:
            logger.error(f"Error generating improved code: {str(e)}")
            return context  # Return original code if we can't improve it
    
    def _fix_error_handling(self, content: str) -> Optional[CodeFix]:
        """Generates a fix for error handling issues."""
        # To be implemented
        return None
