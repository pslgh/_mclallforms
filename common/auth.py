import os
import json
import hashlib
import secrets
import datetime
from pathlib import Path

class AuthManager:
    """Handles user authentication and session management"""
    
    def __init__(self, data_dir="data"):
        # Get the project root directory
        self.project_root = Path(__file__).resolve().parents[1]
        self.users_file = self.project_root / data_dir / "users.json"
        self.sessions_file = self.project_root / data_dir / "sessions.json"
        
        # Ensure data directory exists
        os.makedirs(self.users_file.parent, exist_ok=True)
        
        # Initialize users file if it doesn't exist
        if not self.users_file.exists():
            self._create_default_users()
        
        # Initialize sessions file if it doesn't exist
        if not self.sessions_file.exists():
            with open(self.sessions_file, 'w', encoding='utf-8') as f:
                json.dump({"sessions": []}, f, indent=2)
    
    def _create_default_users(self):
        """Create a default users file with admin user"""
        # Hash the password 'admin'
        salt = secrets.token_hex(16)
        password_hash = self._hash_password("admin", salt)
        
        users = {
            "users": [
                {
                    "username": "admin",
                    "display_name": "Administrator",
                    "password_hash": password_hash,
                    "salt": salt,
                    "role": "admin"
                }
            ]
        }
        
        with open(self.users_file, 'w', encoding='utf-8') as f:
            json.dump(users, f, indent=2)
    
    def _hash_password(self, password, salt):
        """Create a secure hash of the password with the given salt"""
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # Use PBKDF2 with SHA-256 and 100,000 iterations
        key = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 100000)
        return key.hex()
    
    def authenticate(self, username, password):
        """Verify username and password"""
        with open(self.users_file, 'r', encoding='utf-8') as f:
            users_data = json.load(f)
        
        # Find user by username
        for user in users_data.get("users", []):
            if user["username"] == username:
                # Get stored salt and hash
                salt = user["salt"]
                stored_hash = user["password_hash"]
                
                # Hash provided password with the same salt
                input_hash = self._hash_password(password, salt)
                
                # Compare hashes
                return input_hash == stored_hash
        
        return False
    
    def create_session(self, username):
        """Create a new session for the authenticated user"""
        session_token = secrets.token_hex(32)
        
        with open(self.sessions_file, 'r', encoding='utf-8') as f:
            sessions_data = json.load(f)
        
        # Add new session
        sessions_data["sessions"].append({
            "username": username,
            "token": session_token,
            "created_at": str(datetime.datetime.now())
        })
        
        with open(self.sessions_file, 'w', encoding='utf-8') as f:
            json.dump(sessions_data, f, indent=2)
        
        return session_token
    
    def validate_session(self, session_token):
        """Validate a session token and return the username if valid"""
        with open(self.sessions_file, 'r', encoding='utf-8') as f:
            sessions_data = json.load(f)
        
        for session in sessions_data.get("sessions", []):
            if session["token"] == session_token:
                # In a real app, you'd check expiration time here
                return session["username"]
        
        return None
