"""
Configuration tab for the expense reimbursement module.
This tab allows configuring categories, currencies, and other settings.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGroupBox,
    QLabel, QLineEdit, QPushButton, QListWidget, QListWidgetItem,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import Signal, Qt

class ConfigTab(QWidget):
    """Tab for configuring expense module settings"""
    
    # Signal when settings are changed
    settings_changed = Signal()
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.data_manager = data_manager
        
        # Create UI components
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the configuration tab UI"""
        config_layout = QVBoxLayout(self)
        
        # Categories section
        category_group = QGroupBox("Expense Categories")
        category_layout = QVBoxLayout(category_group)
        
        self.category_list = QListWidget()
        
        category_button_layout = QHBoxLayout()
        self.add_category_button = QPushButton("Add Category")
        self.add_category_button.clicked.connect(self.add_category)
        self.remove_category_button = QPushButton("Remove Category")
        self.remove_category_button.clicked.connect(self.remove_category)
        
        category_button_layout.addWidget(self.add_category_button)
        category_button_layout.addWidget(self.remove_category_button)
        
        category_layout.addWidget(QLabel("Manage expense categories:"))
        category_layout.addWidget(self.category_list)
        category_layout.addLayout(category_button_layout)
        
        # Save button
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self.save_settings)
        
        # Add all to main layout
        config_layout.addWidget(category_group)
        config_layout.addWidget(self.save_settings_button)
        
        # Load current settings
        self.load_settings()
        
    def load_settings(self):
        """Load current settings from data manager"""
        if not self.data_manager:
            return
            
        # Clear list
        self.category_list.clear()
        
        # Load categories
        for category in self.data_manager.settings.categories:
            self.category_list.addItem(category)
    
    def add_category(self):
        """Add a new expense category"""
        category, ok = QInputDialog.getText(
            self, "Add Category", "Enter new expense category name:"
        )
        
        if ok and category:
            # Check if category already exists
            items = self.category_list.findItems(category, Qt.MatchExactly)
            if items:
                QMessageBox.warning(self, "Warning", f"Category '{category}' already exists.")
                return
                
            # Add to list
            self.category_list.addItem(category)
    
    def remove_category(self):
        """Remove selected expense category"""
        selected_items = self.category_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Warning", "Please select a category to remove.")
            return
            
        # Remove selected item
        for item in selected_items:
            self.category_list.takeItem(self.category_list.row(item))
    

    
    def save_settings(self):
        """Save settings to data manager"""
        if not self.data_manager:
            return
            
        # Get categories from list
        categories = []
        for i in range(self.category_list.count()):
            categories.append(self.category_list.item(i).text())
            
        # Update settings in data manager
        self.data_manager.settings.categories = categories
        
        # Save settings
        try:
            self.data_manager.save_settings(self.data_manager.settings)
            QMessageBox.information(self, "Success", "Settings saved successfully.")
            
            # Emit signal that settings have changed
            self.settings_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save settings: {str(e)}")
