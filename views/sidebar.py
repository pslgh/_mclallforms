from PySide6.QtWidgets import (QWidget, QVBoxLayout, QPushButton, QLabel,
                              QScrollArea, QFrame, QSpacerItem, QSizePolicy,
                              QHBoxLayout, QToolButton)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
import sys
from pathlib import Path

# Add parent directory to path so we can import our utils
sys.path.append(str(Path(__file__).resolve().parents[1]))
from utils.path_utils import get_resource_path

class SidebarButton(QPushButton):
    """Custom button for sidebar navigation"""
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setFlat(True)
        self.setCheckable(True)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QPushButton {
                text-align: left;
                padding: 10px;
                border: none;
                font-size: 14px;
            }
            QPushButton:checked {
                background-color: #2980b9;
                color: white;
            }
            QPushButton:hover:!checked {
                background-color: #e0e0e0;
            }
        """)

class Sidebar(QWidget):
    """Sidebar navigation widget"""
    moduleSelected = Signal(str)
    logoutRequested = Signal()
    
    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self.setFixedWidth(250)
        self.setStyleSheet("background-color: #d4f1f9;")
        self.user_info = user_info or {"username": "", "first_name": "", "last_name": "", "position": ""}
        self.setup_ui()
        
    def setup_ui(self):
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Logo container
        logo_container = QVBoxLayout()
        logo_container.setContentsMargins(10, 10, 10, 5)
        logo_container.setSpacing(5)
        
        # MCL Logo
        logo_label = QLabel()
        logo_path = get_resource_path("logo/mcllogo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Scale the logo to fit the sidebar width
            pixmap = pixmap.scaledToWidth(220, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            # Fallback if logo not found
            logo_label.setText("MCL")
            logo_label.setStyleSheet("""
                color: white;
                font-size: 24px;
                font-weight: bold;
                background-color: #2980b9;
                padding: 15px;
            """)
            logo_label.setAlignment(Qt.AlignCenter)
        
        # App title
        title_label = QLabel("All Forms")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            font-weight: bold;
            background-color: #2980b9;
            padding-bottom: 10px;
        """)
        
        # Add logo and title to container
        logo_widget = QWidget()
        logo_widget.setStyleSheet("background-color: #2980b9;")
        logo_widget.setLayout(logo_container)
        logo_container.addWidget(logo_label)
        logo_container.addWidget(title_label)
        
        # User info section
        user_widget = QWidget()
        user_widget.setStyleSheet("background-color: #bbd9e5; padding: 10px;")
        user_layout = QVBoxLayout(user_widget)
        
        # User's full name
        full_name = f"{self.user_info.get('first_name', '')} {self.user_info.get('last_name', '')}".strip()
        if not full_name:
            full_name = self.user_info.get('username', 'User')
            
        name_label = QLabel(full_name)
        name_label.setStyleSheet("font-weight: bold; font-size: 16px; color: #333;")
        
        # User's position
        position = self.user_info.get('position', '').capitalize()
        position_label = QLabel(position)
        position_label.setStyleSheet("font-size: 14px; color: #555;")
        
        user_layout.addWidget(name_label)
        user_layout.addWidget(position_label)
        user_layout.setSpacing(5)
        
        # Buttons container (scrollable)
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        
        # Container for menu buttons
        menu_widget = QWidget()
        self.menu_layout = QVBoxLayout(menu_widget)
        self.menu_layout.setContentsMargins(0, 0, 0, 0)
        self.menu_layout.setSpacing(0)
        
        # Add menu buttons - keep original keys for internal references
        menu_items = [
            "dashboard",
            "expense",
            "timesheet",
            "quotation",
            "po_tracking",
            "manage_users",
            "settings",
            "help" 
        ]
        
        # Display names for buttons (what users actually see)
        display_names = {
            "dashboard": "Dashboard (pending)",
            "expense": "Expense",
            "timesheet": "Timesheet",
            "quotation": "Quotation (pending)",
            "po_tracking": "PO Tracking (pending)",
            "manage_users": "Manage Users",
            "settings": "Settings (pending)",
            "help": "Help (pending)"
        }
        
        self.buttons = {}
        for item in menu_items:
            # Use display name if available, otherwise use the default formatting
            display_name = display_names.get(item, item.replace("_", " ").capitalize())
            button = SidebarButton(display_name)
            button.clicked.connect(lambda checked, i=item: self.on_button_clicked(i))
            self.menu_layout.addWidget(button)
            self.buttons[item] = button
        
        # Set dashboard as default selected
        self.buttons["dashboard"].setChecked(True)
        
        # Add logout button at the end of menu items
        logout_button = QPushButton("Logout")
        logout_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        logout_button.clicked.connect(self.logoutRequested.emit)
        logout_button.setCursor(Qt.PointingHandCursor)
        self.menu_layout.addWidget(logout_button)
        
        # Add spacing at the bottom
        self.menu_layout.addSpacerItem(
            QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        )
        
        # Set up scroll area
        scroll_area.setWidget(menu_widget)
        
        # Add widgets to main layout
        main_layout.addWidget(logo_widget)
        main_layout.addWidget(user_widget)
        main_layout.addWidget(scroll_area)
        
    def on_button_clicked(self, module_name):
        # Uncheck all other buttons
        for name, button in self.buttons.items():
            if name != module_name:
                button.setChecked(False)
        
        # Emit signal with selected module
        self.moduleSelected.emit(module_name)
