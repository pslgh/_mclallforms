from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, 
    QPushButton, QMessageBox, QDialog, QLineEdit, QLabel,
    QFormLayout, QComboBox, QHBoxLayout, QTabWidget,
    QHeaderView
)
from PySide6.QtCore import Qt, Signal
from pathlib import Path
import datetime
import sys

# Add parent directory to path so we can import our services and utils
sys.path.append(str(Path(__file__).resolve().parents[2]))
from services.data_service import DataService
from utils.path_utils import get_data_path

class EditUserDialog(QDialog):
    """Dialog for editing user information"""
    
    def __init__(self, user_data, is_self=True, parent=None):
        super().__init__(parent)
        self.user_data = user_data.copy()
        self.is_self = is_self  # Whether user is editing their own info
        self.original_username = user_data.get("username", "")
        
        title = "Edit Your Information" if is_self else f"Edit User: {self.original_username}"
        self.setWindowTitle(title)
        self.setMinimumWidth(400)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Username (read-only)
        self.username_label = QLabel(self.original_username)
        self.username_label.setStyleSheet("font-weight: bold;")
        form_layout.addRow("Username:", self.username_label)
        
        # First Name
        self.first_name_input = QLineEdit(self.user_data.get("first_name", ""))
        form_layout.addRow("First Name:", self.first_name_input)
        
        # Last Name
        self.last_name_input = QLineEdit(self.user_data.get("last_name", ""))
        form_layout.addRow("Last Name:", self.last_name_input)
        
        # Position (only editable by admins for other users)
        self.position_input = QComboBox()
        self.position_input.addItems(["user", "manager", "admin"])
        current_position = self.user_data.get("position", "user")
        index = self.position_input.findText(current_position)
        if index >= 0:
            self.position_input.setCurrentIndex(index)
            
        # Non-admins can't change their own position
        if self.is_self and current_position != "admin":
            self.position_input.setEnabled(False)
            
        form_layout.addRow("Position:", self.position_input)
        
        # Password change section
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Enter new password (leave blank to keep current)")
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("New Password:", self.password_input)
        
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Confirm new password")
        self.confirm_password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Confirm Password:", self.confirm_password_input)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        # Add to main layout
        layout.addLayout(form_layout)
        layout.addLayout(button_layout)
        
    def save_changes(self):
        # Validate form
        first_name = self.first_name_input.text().strip()
        last_name = self.last_name_input.text().strip()
        position = self.position_input.currentText()
        new_password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        if not first_name or not last_name:
            QMessageBox.warning(self, "Validation Error", "First name and last name are required.")
            return
            
        # Check password match if changing password
        if new_password:
            if new_password != confirm_password:
                QMessageBox.warning(self, "Validation Error", "Passwords do not match.")
                return
                
        # Update user data
        self.user_data["first_name"] = first_name
        self.user_data["last_name"] = last_name
        self.user_data["position"] = position
        
        # If password is provided, it will be hashed by the caller
        if new_password:
            self.user_data["new_password"] = new_password
            
        self.accept()
        
    def get_updated_data(self):
        return self.user_data


class UserManagementWidget(QWidget):
    """Widget for managing users"""
    
    user_updated = Signal(dict)  # Signal emitted when the current user updates their info
    
    def __init__(self, current_user_info, parent=None):
        super().__init__(parent)
        self.current_user_info = current_user_info
        
        # Ensure the default admin always has admin privileges
        if current_user_info.get("username") == "a":
            self.current_user_info["position"] = "admin"
            
        self.is_admin = current_user_info.get("position") == "admin"
        self.setup_ui()
        
        # Ensure default admin user file exists
        self.ensure_default_admin()
        
        # Load all users
        self.load_users()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("User Management")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)
        
        # Tab widget to separate user profile and admin functions
        self.tab_widget = QTabWidget()
        
        # Tab 1: User Profile (for all users)
        self.profile_tab = QWidget()
        profile_layout = QVBoxLayout(self.profile_tab)
        
        # Current user info
        profile_form = QFormLayout()
        
        self.username_label = QLabel(self.current_user_info.get("username", ""))
        self.username_label.setStyleSheet("font-weight: bold;")
        
        full_name = f"{self.current_user_info.get('first_name', '')} {self.current_user_info.get('last_name', '')}".strip()
        self.name_label = QLabel(full_name)
        
        position = self.current_user_info.get("position", "").capitalize()
        self.position_label = QLabel(position)
        
        profile_form.addRow("Username:", self.username_label)
        profile_form.addRow("Name:", self.name_label)
        profile_form.addRow("Position:", self.position_label)
        
        profile_layout.addLayout(profile_form)
        profile_layout.addSpacing(20)
        
        # Edit button
        self.edit_button = QPushButton("Edit My Information")
        self.edit_button.clicked.connect(self.edit_current_user)
        profile_layout.addWidget(self.edit_button)
        
        profile_layout.addStretch()
        
        # Tab 2: User Management (admin only)
        self.admin_tab = QWidget()
        admin_layout = QVBoxLayout(self.admin_tab)
        
        if self.is_admin:
            # User table
            self.users_table = QTableWidget()
            self.users_table.setColumnCount(5)
            self.users_table.setHorizontalHeaderLabels(["Username", "First Name", "Last Name", "Position", "Actions"])
            self.users_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            self.users_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
            self.users_table.setSelectionBehavior(QTableWidget.SelectRows)
            
            admin_layout.addWidget(self.users_table)
        else:
            # Non-admin message
            non_admin_label = QLabel("Administrator privileges required to access user management.")
            non_admin_label.setAlignment(Qt.AlignCenter)
            non_admin_label.setStyleSheet("color: #777; font-size: 14px;")
            admin_layout.addWidget(non_admin_label)
            
        # Add tabs to tab widget
        self.tab_widget.addTab(self.profile_tab, "My Profile")
        self.tab_widget.addTab(self.admin_tab, "Manage Users")
        
        main_layout.addWidget(self.tab_widget)
        
    def load_users(self):
        """Load all users from users.json for the admin table using DataService"""
        if not self.is_admin:
            return
            
        self.users_table.setRowCount(0)  # Clear table
        
        try:
            # Use DataService to get all users
            data_service = DataService()
            users_data = data_service.get_users()
            
            # Ensure default admin exists
            self.ensure_default_admin()
            
            # Get users list
            users_list = users_data.get("users", [])
            if not users_list:
                QMessageBox.information(
                    self,
                    "No Users Found",
                    "No user accounts have been created yet. You can create new accounts using the sign-up feature."
                )
                return
                
            # Populate table with users
            for user_data in users_list:
                row = self.users_table.rowCount()
                self.users_table.insertRow(row)
                
                # Add user data to row
                username = user_data.get("username", "")
                self.users_table.setItem(row, 0, QTableWidgetItem(username))
                self.users_table.setItem(row, 1, QTableWidgetItem(user_data.get("first_name", "")))
                self.users_table.setItem(row, 2, QTableWidgetItem(user_data.get("last_name", "")))
                self.users_table.setItem(row, 3, QTableWidgetItem(user_data.get("position", "")))
                
                # Create action buttons
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                
                # Can't modify the default admin
                is_default_admin = username == "a"
                
                edit_button = QPushButton("Edit")
                edit_button.setProperty("username", username)
                edit_button.clicked.connect(self.edit_user)
                edit_button.setEnabled(not is_default_admin)
                
                delete_button = QPushButton("Delete")
                delete_button.setProperty("username", username)
                delete_button.clicked.connect(self.delete_user)
                delete_button.setEnabled(not is_default_admin)
                
                actions_layout.addWidget(edit_button)
                actions_layout.addWidget(delete_button)
                
                self.users_table.setCellWidget(row, 4, actions_widget)
                    
        except Exception as e:
            print(f"Error loading users: {e}")
            QMessageBox.critical(
                self,
                "Error",
                f"An error occurred while loading users: {str(e)}"
            )
            
    def edit_current_user(self):
        """Edit the current user's information"""
        try:
            dialog = EditUserDialog(self.current_user_info, is_self=True, parent=self)
            if dialog.exec():
                updated_data = dialog.get_updated_data()
                if self.save_user(updated_data, is_current_user=True):
                    # Update the displayed information
                    full_name = f"{updated_data.get('first_name', '')} {updated_data.get('last_name', '')}".strip()
                    self.name_label.setText(full_name)
                    self.position_label.setText(updated_data.get("position", "").capitalize())
                    
                    # Emit signal that user info has changed
                    self.user_updated.emit(updated_data)
                    
                    QMessageBox.information(self, "Success", "Your information has been updated successfully.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to save user information.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
    def edit_user(self):
        """Edit another user's information (admin only)"""
        if not self.is_admin:
            return
            
        sender = self.sender()
        username = sender.property("username")
        
        try:
            # Load user data
            user_data = self.load_user_data(username)
            if not user_data:
                QMessageBox.warning(self, "Error", f"Could not load user data for {username}")
                return
                
            dialog = EditUserDialog(user_data, is_self=False, parent=self)
            if dialog.exec():
                updated_data = dialog.get_updated_data()
                if self.save_user(updated_data):
                    self.load_users()  # Refresh the user list
                    QMessageBox.information(self, "Success", f"User {username} has been updated successfully.")
                else:
                    QMessageBox.warning(self, "Error", "Failed to save user information.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred: {str(e)}")
            
    def delete_user(self):
        """Delete a user using DataService (admin only)"""
        if not self.is_admin:
            return
            
        sender = self.sender()
        username = sender.property("username")
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete user '{username}'?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            try:
                # Use DataService to delete user
                data_service = DataService()
                if data_service.delete_user(username):
                    self.load_users()  # Refresh the user list
                    QMessageBox.information(self, "Success", f"User {username} has been deleted.")
                else:
                    QMessageBox.warning(self, "Error", f"User {username} could not be deleted.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete user: {str(e)}")
                
    def load_user_data(self, username):
        """Load data for a specific user using DataService"""
        try:
            # Use DataService to get user data
            data_service = DataService()
            return data_service.get_user_by_username(username)
        except Exception as e:
            print(f"Error loading user data: {e}")
            return None
            
    def save_user(self, user_data, is_current_user=False):
        """Save user data using DataService"""
        try:
            # Handle password change if provided
            if "new_password" in user_data and user_data["new_password"]:
                import hashlib
                import secrets
                
                # Generate new salt and hash
                salt = secrets.token_hex(16)
                password = user_data["new_password"]
                password_bytes = password.encode('utf-8')
                salt_bytes = salt.encode('utf-8')
                
                # Use PBKDF2 with SHA-256 and 100,000 iterations
                key = hashlib.pbkdf2_hmac('sha256', password_bytes, salt_bytes, 100000)
                password_hash = key.hex()
                
                user_data["salt"] = salt
                user_data["password_hash"] = password_hash
            
            # Update the current user info if this is the current user
            if is_current_user:
                self.current_user_info["first_name"] = user_data.get("first_name")
                self.current_user_info["last_name"] = user_data.get("last_name")
                self.current_user_info["position"] = user_data.get("position")
            
            # Use DataService to update user
            data_service = DataService()
            return data_service.update_user(user_data)
                
        except Exception as e:
            print(f"Error saving user: {e}")
            return False
            
        except Exception as e:
            print(f"Error saving user data: {e}")
            return False

    # Add a new method to ensure the default admin user exists
    def ensure_default_admin(self):
        """Ensure that the default admin user 'a' with password 'a' is always available"""
        try:
            # Use DataService to check if admin exists
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
