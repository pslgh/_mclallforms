import json
import os
from pathlib import Path
import shutil
import threading

class DataService:
    """
    Service class that abstracts all data operations.
    This provides a unified interface for working with JSON files now,
    with the ability to switch to MongoDB in the future.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(DataService, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the data service"""
        if self._initialized:
            return
            
        self._initialized = True
        self.base_path = Path("data")
        
        # Ensure data directories exist
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        dirs = ["userinfo", "expenses", "timesheet"]
        for dir_name in dirs:
            dir_path = self.base_path / dir_name
            os.makedirs(dir_path, exist_ok=True)
    
    def get_users(self):
        """Get all users from the users.json file"""
        users_file = self.base_path / "userinfo" / "users.json"
        if not users_file.exists():
            return {"users": []}
            
        try:
            with open(users_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {"users": []}
    
    def save_users(self, users_data):
        """Save users data to the users.json file"""
        users_file = self.base_path / "userinfo" / "users.json"
        os.makedirs(users_file.parent, exist_ok=True)
        
        try:
            with open(users_file, 'w', encoding='utf-8') as f:
                json.dump(users_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving users: {e}")
            return False
    
    def get_user_by_username(self, username):
        """Get a specific user by username"""
        users_data = self.get_users()
        
        for user in users_data.get("users", []):
            if user.get("username") == username:
                return user
                
        return None
    
    def update_user(self, user_data):
        """Update a user's information"""
        username = user_data.get("username")
        if not username:
            return False
            
        users_data = self.get_users()
        
        # Find and update the user
        for i, user in enumerate(users_data.get("users", [])):
            if user.get("username") == username:
                # Update user data while preserving fields not in user_data
                updated_user = user.copy()
                updated_user.update(user_data)
                users_data["users"][i] = updated_user
                return self.save_users(users_data)
        
        # User not found
        return False
    
    def add_user(self, user_data):
        """Add a new user"""
        username = user_data.get("username")
        if not username:
            return False
            
        users_data = self.get_users()
        
        # Check if user already exists
        for user in users_data.get("users", []):
            if user.get("username") == username:
                return False
        
        # Add new user
        users_data.setdefault("users", []).append(user_data)
        return self.save_users(users_data)
    
    def delete_user(self, username):
        """Delete a user by username"""
        if not username:
            return False
            
        users_data = self.get_users()
        
        # Filter out the user to delete
        original_count = len(users_data.get("users", []))
        users_data["users"] = [user for user in users_data.get("users", []) 
                              if user.get("username") != username]
        
        # Check if a user was actually removed
        if len(users_data.get("users", [])) < original_count:
            return self.save_users(users_data)
        
        return False
    
    # Future methods for other data types (expenses, timesheet, etc.)
    # These would follow the same pattern as the user methods
