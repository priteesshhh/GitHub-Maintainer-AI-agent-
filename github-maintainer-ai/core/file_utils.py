import os
import json
from typing import Dict, Any

class FileUtils:
    @staticmethod
    def read_json(file_path: str) -> Dict:
        """Read a JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {e}")
            return {}
    
    @staticmethod
    def write_json(file_path: str, data: Dict) -> bool:
        """Write data to a JSON file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            print(f"Error writing JSON file {file_path}: {e}")
            return False
    
    @staticmethod
    def append_json(file_path: str, data: Dict) -> bool:
        """Append data to a JSON file."""
        try:
            existing_data = FileUtils.read_json(file_path)
            if isinstance(existing_data, list):
                existing_data.append(data)
            else:
                existing_data.update(data)
            return FileUtils.write_json(file_path, existing_data)
        except Exception as e:
            print(f"Error appending to JSON file {file_path}: {e}")
            return False
