from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                              QPushButton, QLabel, QStackedWidget)
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QIcon

from views.sidebar import Sidebar
from modules.manage_users.user_management_widget import UserManagementWidget
from modules.expense.expense_reimbursement_widget import ExpenseReimbursementWidget
from modules.timesheet.timesheet_widget import TimesheetWidget

class MainWindow(QMainWindow):
    """Main application window with sidebar navigation."""
    def __init__(self, user_info=None):
        super().__init__()
        self.setWindowTitle("MCL All Forms")
        self.setMinimumSize(1200, 800)
        self.user_info = user_info or {"username": "", "first_name": "", "last_name": "", "position": ""}
        self.setupUi()
        
    def setupUi(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        
        # Main layout (horizontal)
        self.main_layout = QHBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create sidebar with user info
        self.sidebar = Sidebar(self.user_info, self)
        self.main_layout.addWidget(self.sidebar)
        
        # Main content area
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header with toggle button and title
        self.header_widget = QWidget()
        self.header_layout = QHBoxLayout(self.header_widget)
        self.header_layout.setContentsMargins(0, 0, 0, 10)
        
        self.toggle_button = QPushButton()
        self.toggle_button.setText("≡")  # Unicode menu icon as fallback
        self.toggle_button.setFlat(True)
        self.toggle_button.clicked.connect(self.toggleSidebar)
        
        self.title_label = QLabel("Dashboard")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: bold;")
        
        self.header_layout.addWidget(self.toggle_button)
        self.header_layout.addWidget(self.title_label)
        self.header_layout.addStretch()
        
        # Stacked widget to hold different modules
        self.module_stack = QStackedWidget()
        
        # Add placeholder for dashboard
        self.dashboard_placeholder = QLabel("Dashboard Module (Coming Soon)")
        self.dashboard_placeholder.setAlignment(Qt.AlignCenter)
        self.dashboard_placeholder.setStyleSheet("font-size: 16px; color: gray;")
        self.dashboard_placeholder.setProperty("module_name", "dashboard")
        self.module_stack.addWidget(self.dashboard_placeholder)
        
        # Add everything to content layout
        self.content_layout.addWidget(self.header_widget)
        self.content_layout.addWidget(self.module_stack)
        
        # Add content widget to main layout
        self.main_layout.addWidget(self.content_widget, 1)  # Stretch factor 1
        
        # Connect sidebar signals
        self.sidebar.moduleSelected.connect(self.loadModule)
        self.sidebar.logoutRequested.connect(self.handleLogout)
        
    def toggleSidebar(self):
        """Show/hide sidebar"""
        if self.sidebar.isVisible():
            self.sidebar.hide()
        else:
            self.sidebar.show()
    
    @Slot(str)
    def loadModule(self, module_name):
        """Load the selected module"""
        # Update title
        self.title_label.setText(module_name.capitalize().replace("_", " "))
        
        # Clear any existing widgets in the content layout first
        for i in range(self.module_stack.count()):
            widget = self.module_stack.widget(i)
            if widget and widget.property("module_name") == module_name:
                self.module_stack.setCurrentWidget(widget)
                return
        
        # Load the requested module
        if module_name == "dashboard":
            # For now, use the dashboard placeholder
            self.module_stack.setCurrentIndex(0)
        elif module_name == "manage_users":
            # Load the User Management module
            user_management = UserManagementWidget(self.user_info)
            # Connect user update signal to update sidebar
            user_management.user_updated.connect(self.update_user_info)
            user_management.setProperty("module_name", module_name)
            self.module_stack.addWidget(user_management)
            self.module_stack.setCurrentWidget(user_management)
        elif module_name == "expense":
            # Load the Expense Reimbursement module
            expense_widget = ExpenseReimbursementWidget(self.user_info)
            expense_widget.setProperty("module_name", module_name)
            self.module_stack.addWidget(expense_widget)
            self.module_stack.setCurrentWidget(expense_widget)
        elif module_name == "timesheet":
            # Load the Timesheet module
            timesheet_widget = TimesheetWidget(self.user_info)
            timesheet_widget.setProperty("module_name", module_name)
            self.module_stack.addWidget(timesheet_widget)
            self.module_stack.setCurrentWidget(timesheet_widget)
        else:
            # Create placeholder for other modules
            placeholder = QLabel(f"{module_name.capitalize().replace('_', ' ')} Module (Coming Soon)")
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setStyleSheet("font-size: 16px; color: gray;")
            placeholder.setProperty("module_name", module_name)
            
            self.module_stack.addWidget(placeholder)
            self.module_stack.setCurrentWidget(placeholder)
    
    def update_user_info(self, updated_user_info):
        """Update the current user information and refresh the sidebar"""
        self.user_info.update(updated_user_info)
        
        # Re-create sidebar with updated user info (simplest way to refresh)
        old_sidebar = self.sidebar
        self.sidebar = Sidebar(self.user_info, self)
        self.main_layout.replaceWidget(old_sidebar, self.sidebar)
        old_sidebar.deleteLater()
        
        # Connect sidebar signals
        self.sidebar.moduleSelected.connect(self.loadModule)
        self.sidebar.logoutRequested.connect(self.handleLogout)
        
    def handleLogout(self):
        """Handle logout request from sidebar"""
        # Close the main window, which will return to main.py
        # and could restart the login process if needed
        self.close()
