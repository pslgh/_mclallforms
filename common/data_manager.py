import os
import json
from pathlib import Path

class DataManager:
    """Handles JSON data storage and retrieval"""
    
    def __init__(self, data_dir="data"):
        # Get the project root directory
        self.project_root = Path(__file__).resolve().parents[1]
        self.data_dir = self.project_root / data_dir
        
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)
    
    def get_data_path(self, collection, ensure_exists=True):
        """Get the path for a data collection and ensure it exists"""
        collection_dir = self.data_dir / collection
        if ensure_exists:
            os.makedirs(collection_dir, exist_ok=True)
        return collection_dir
    
    def save_data(self, collection, filename, data):
        """Save data to a JSON file"""
        collection_dir = self.get_data_path(collection)
        file_path = collection_dir / f"{filename}.json"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def load_data(self, collection, filename):
        """Load data from a JSON file"""
        collection_dir = self.get_data_path(collection, ensure_exists=False)
        file_path = collection_dir / f"{filename}.json"
        
        if not file_path.exists():
            return None
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def list_files(self, collection):
        """List all JSON files in a collection"""
        collection_dir = self.get_data_path(collection, ensure_exists=False)
        
        if not collection_dir.exists():
            return []
        
        return [f.stem for f in collection_dir.glob("*.json")]
