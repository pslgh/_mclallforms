import sys
import os
from PySide6.QtWidgets import QApplication
from views.login import LoginWindow
from views.main_window import MainWindow
import json
from pathlib import Path

# Import from new structure
from services.data_service import DataService
from utils.path_utils import ensure_directory, get_data_path

def initialize_app():
    """Initialize application directories and files"""
    # Ensure data directories exist
    ensure_directory(get_data_path("userinfo"))
    ensure_directory(get_data_path("expenses"))
    ensure_directory(get_data_path("timesheet"))
    
    # Initialize DataService (this will ensure directories and default admin)
    data_service = DataService()
    
    # Create users.json file if it doesn't exist
    users_file = get_data_path("userinfo/users.json")
    if not users_file.exists():
        # Create with default admin user
        default_users = {
            "users": [
                {
                    "username": "a",
                    "password_hash": "hardcoded_special_case",
                    "salt": "not_used_for_default_admin",
                    "first_name": "First",
                    "last_name": "Admin",
                    "position": "admin",
                    "register_date": "2025-04-17 16:58:19"
                }
            ]
        }
        with open(users_file, 'w', encoding='utf-8') as f:
            json.dump(default_users, f, indent=2, ensure_ascii=False)

def load_user_info(username):
    """Load user information using the DataService"""
    try:
        # Use DataService to get user information
        data_service = DataService()
        user = data_service.get_user_by_username(username)
        
        if user:
            # Return only necessary information
            return {
                "username": user.get("username", username),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "position": user.get("position", "")
            }
                
        print(f"User '{username}' not found in users.json")
        return {"username": username, "first_name": "", "last_name": "", "position": ""}
    except Exception as e:
        print(f"Error loading user info: {e}")
        return {"username": username, "first_name": "", "last_name": "", "position": ""}

def main():
    # Initialize app directories and files
    initialize_app()
    
    app = QApplication(sys.argv)
    app.setApplicationName("MCL All Forms")
    
    # For development, uncomment to bypass login:
    # main_window = MainWindow({"username": "dev", "first_name": "Developer", "last_name": "User", "position": "admin"})
    # main_window.show()
    # return app.exec()
    
    # Normal flow with login:
    login_window = LoginWindow()
    if login_window.exec():
        # On successful login, show main window with user info
        username = login_window.logged_in_username
        user_info = load_user_info(username)
        
        main_window = MainWindow(user_info)
        main_window.show()
        return app.exec()
    else:
        return 0

if __name__ == "__main__":
    sys.exit(main())
