from PySide6.QtWidgets import (QDialog, QLabel, QLineEdit, QPushButton, 
                               QVBoxLayout, QHBoxLayout, QFormLayout, 
                               QMessageBox, QFrame, QComboBox)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
import os
import json
import datetime
import hashlib
import secrets
from pathlib import Path
import sys

# Add parent directory to path so we can import our services and utils
sys.path.append(str(Path(__file__).resolve().parents[1]))
from services.data_service import DataService
from utils.path_utils import get_data_path, get_resource_path

class SignupDialog(QDialog):
    """Dialog for new user registration"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sign Up - MCL All Forms")
        self.setMinimumWidth(450)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Form layout for signup fields
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Choose a username")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Choose a password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter your first name")
        
        self.surname_input = QLineEdit()
        self.surname_input.setPlaceholderText("Enter your last name")
        
        self.position_input = QComboBox()
        self.position_input.addItems(["user", "manager", "admin"])
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        form_layout.addRow("First Name:", self.name_input)
        form_layout.addRow("Last Name:", self.surname_input)
        form_layout.addRow("Position:", self.position_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.signup_button = QPushButton("Sign Up")
        self.signup_button.clicked.connect(self.try_signup)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.signup_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add all widgets to main layout
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
    
    def try_signup(self):
        # Get form data
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()
        first_name = self.name_input.text().strip()
        last_name = self.surname_input.text().strip()
        position = self.position_input.currentText()
        
        # Validate form data
        if not username or not password or not confirm_password or not first_name or not last_name:
            QMessageBox.warning(
                self, 
                "Registration Failed", 
                "All fields are required."
            )
            return
        
        if password != confirm_password:
            QMessageBox.warning(
                self, 
                "Registration Failed", 
                "Passwords do not match."
            )
            return
        
        # Check if username already exists
        if self.username_exists(username):
            QMessageBox.warning(
                self, 
                "Registration Failed", 
                f"Username '{username}' is already taken. Please choose another."
            )
            return
        
        # Create user data
        salt = secrets.token_hex(16)
        password_hash = self.hash_password(password, salt)
        
        user_data = {
            "username": username,
            "password_hash": password_hash,
            "salt": salt,
            "first_name": first_name,
            "last_name": last_name,
            "position": position,
            "register_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Save user data
        if self.save_user(user_data):
            QMessageBox.information(
                self, 
                "Registration Successful", 
                f"User '{username}' has been registered successfully!"
            )
            self.accept()
        else:
            QMessageBox.critical(
                self, 
                "Registration Failed", 
                "An error occurred while saving user data."
            )
    
    def username_exists(self, username):
        """Check if a username already exists in users.json"""
        # Special case for the default admin user
        if username == 'a':
            print(f"Username check: 'a' is reserved")
            return True
            
        # Debug print to identify which usernames are being checked
        print(f"Checking if username '{username}' exists...")
        
        try:
            # Check if users.json exists
            users_file = Path("data/userinfo/users.json")
            if not users_file.exists():
                print(f"Users file does not exist")
                return False
                
            # Load users data
            with open(users_file, 'r', encoding='utf-8') as f:
                users_data = json.load(f)
                
            # Check if username exists in users list
            for user in users_data.get("users", []):
                if user.get("username") == username:
                    print(f"Found username match in users.json: {username}")
                    return True
            
            print(f"Username '{username}' is available")
            return False
        except Exception as e:
            print(f"Error in username_exists: {e}")
            # If there's an error, default to false to allow registration
            return False
    
    def hash_password(self, password, salt):
        """Create a secure hash of the password with the given salt"""
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # Use PBKDF2 with SHA-256 and 100,000 iterations
        key = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 100000)
        return key.hex()
    
    def save_user(self, user_data):
        """Save user data using DataService"""
        try:
            # Use DataService to add a new user
            data_service = DataService()
            return data_service.add_user(user_data)
        except Exception as e:
            print(f"Error saving user: {e}")
            return False


class LoginWindow(QDialog):
    """Login dialog for application authentication"""
    login_successful = Signal(str)  # Signal to emit username on success
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Login - MCL All Forms")
        self.setMinimumWidth(400)
        self.logged_in_username = ""  # Store the logged-in username
        self.setup_ui()
        self.ensure_default_admin()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Logo and title container
        logo_container = QVBoxLayout()
        logo_container.setSpacing(10)
        
        # Add logo
        logo_label = QLabel()
        logo_path = get_resource_path("logo/mcllogo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Scale the logo to a reasonable size (max 200px width)
            if pixmap.width() > 200:
                pixmap = pixmap.scaledToWidth(200, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            # Fallback if logo not found
            logo_label.setText("[Logo not found]")
            logo_label.setStyleSheet("color: gray;")
            logo_label.setAlignment(Qt.AlignCenter)
        
        # App title
        title_label = QLabel("MCL All Forms")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 20px;")
        
        # Add logo and title to container
        logo_container.addWidget(logo_label)
        logo_container.addWidget(title_label)
        main_layout.addLayout(logo_container)
        
        # Form layout for login fields
        form_layout = QFormLayout()
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setEchoMode(QLineEdit.Password)
        
        form_layout.addRow("Username:", self.username_input)
        form_layout.addRow("Password:", self.password_input)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        self.login_button = QPushButton("Login")
        self.login_button.setDefault(True)
        self.login_button.clicked.connect(self.try_login)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.cancel_button)
        
        # Sign up link
        signup_layout = QHBoxLayout()
        
        signup_label = QLabel("Don't have an account?")
        self.signup_button = QPushButton("Sign Up")
        self.signup_button.setFlat(True)
        self.signup_button.setCursor(Qt.PointingHandCursor)
        self.signup_button.clicked.connect(self.open_signup)
        
        signup_layout.addWidget(signup_label)
        signup_layout.addWidget(self.signup_button)
        signup_layout.addStretch()
        
        # Add all widgets to main layout
        main_layout.addWidget(title_label)
        main_layout.addLayout(form_layout)
        main_layout.addLayout(button_layout)
        main_layout.addLayout(signup_layout)
        
    def open_signup(self):
        """Open the signup dialog"""
        dialog = SignupDialog(self)
        if dialog.exec():
            # If signup was successful, pre-fill the username
            if hasattr(dialog, 'username_input'):
                self.username_input.setText(dialog.username_input.text())
                self.password_input.setFocus()
        
    def try_login(self):
        username = self.username_input.text().strip()
        password = self.password_input.text().strip()
        
        if not username or not password:
            QMessageBox.warning(
                self, 
                "Login Failed", 
                "Please enter both username and password."
            )
            return
        
        # Check default admin
        if username == 'a' and password == 'a':
            self.logged_in_username = username  # Store the username
            self.login_successful.emit(username)
            self.accept()
            return
        
        # Check user credentials
        if self.verify_credentials(username, password):
            self.logged_in_username = username  # Store the username
            self.login_successful.emit(username)
            self.accept()
        else:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Invalid username or password."
            )
    
    def verify_credentials(self, username, password):
        """Verify user credentials against stored user data"""
        try:
            # Use DataService to get user by username
            data_service = DataService()
            user = data_service.get_user_by_username(username)
            
            if not user:
                return False
            
            # Get stored salt and hash
            salt = user.get("salt")
            stored_hash = user.get("password_hash")
            
            if not salt or not stored_hash:
                return False
                
            # Hash provided password with the same salt
            input_hash = self.hash_password(password, salt)
            
            # Compare hashes
            return input_hash == stored_hash
        except Exception as e:
            print(f"Error verifying credentials: {e}")
            return False
    
    def hash_password(self, password, salt):
        """Create a secure hash of the password with the given salt"""
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        # Use PBKDF2 with SHA-256 and 100,000 iterations
        key = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 100000)
        return key.hex()
    
    def ensure_default_admin(self):
        """Ensure that the default admin user 'a' with password 'a' is always available"""
        try:
            # Use DataService to ensure admin exists
            data_service = DataService()
            admin = data_service.get_user_by_username("a")
            
            # If admin doesn't exist, create it
            if not admin:
                # Default admin data
                admin_data = {
                    "username": "a",
                    "password_hash": "hardcoded_special_case",  # Actually checked directly in try_login
                    "salt": "not_used_for_default_admin",
                    "first_name": "First",
                    "last_name": "Admin",
                    "position": "admin",
                    "register_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Add admin user
                data_service.add_user(admin_data)
        except Exception as e:
            print(f"Error ensuring default admin: {e}")
