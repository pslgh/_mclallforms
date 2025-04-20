"""
Expense Reimbursement Widget - Main Module
This module coordinates all expense reimbursement tabs and functionality.
"""
import sys
from pathlib import Path
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QTabBar, QMessageBox
)
from PySide6.QtCore import Qt, Signal

# Add parent directory to path so we can import our services and utils
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.path_utils import get_data_path

# Import models
from modules.expense.models.expense_data import ExpenseFormData, ExpenseDataManager

# Import tab widgets
from modules.expense.tabs.form_tab import FormTab
from modules.expense.tabs.history_tab import HistoryTab
from modules.expense.tabs.config_tab import ConfigTab
from modules.expense.tabs.edit_tab import EditTab
from modules.expense.tabs.view_tab import ViewTab

class ExpenseReimbursementWidget(QWidget):
    """Main widget for expense reimbursement functionality"""
    
    # Signal to emit when a form is saved
    form_saved = Signal(str)  # Emits form ID
    
    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self.user_info = user_info or {}
        self.data_manager = ExpenseDataManager(get_data_path("expenses/expense_forms.json"))
        
        # Track dynamic tabs
        self.edit_tabs = {}  # Maps form_id to tab widget and index
        self.view_tabs = {}  # Maps form_id to tab widget and index
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs for form, history and config
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.on_tab_close_requested)
        
        # Form tab
        self.form_tab = FormTab(self, self.user_info, self.data_manager)
        self.form_tab_index = self.tab_widget.addTab(self.form_tab, "New Expense Form")
        
        # History tab
        self.history_tab = HistoryTab(self, self.data_manager)
        self.history_tab_index = self.tab_widget.addTab(self.history_tab, "History")
        
        # Config tab
        self.config_tab = ConfigTab(self, self.data_manager)
        self.config_tab_index = self.tab_widget.addTab(self.config_tab, "Config")
        
        # Don't allow closing the main tabs
        self.tab_widget.tabBar().setTabButton(self.form_tab_index, QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(self.history_tab_index, QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(self.config_tab_index, QTabBar.RightSide, None)
        
        main_layout.addWidget(self.tab_widget)
        
        # Connect signals
        self.form_tab.form_saved.connect(self.on_form_saved)
        self.history_tab.view_form_requested.connect(self.view_form)
        self.history_tab.edit_form_requested.connect(self.edit_form)
        self.history_tab.form_deleted.connect(self.on_form_deleted)
        self.config_tab.settings_changed.connect(self.on_settings_changed)
        
        # Load historical forms
        self.history_tab.load_historical_forms()
    
    def on_form_saved(self, form_id):
        """Handle a form being saved"""
        # Reload historical forms
        self.history_tab.load_historical_forms()
        
        # Switch to history tab
        self.tab_widget.setCurrentIndex(self.history_tab_index)
        
        # Forward the signal
        self.form_saved.emit(form_id)
    
    def view_form(self, form_id):
        """View a form in a new tab"""
        # Check if this form is already being viewed
        if form_id in self.view_tabs:
            # Switch to the existing tab
            tab_index = self.view_tabs[form_id]['index']
            self.tab_widget.setCurrentIndex(tab_index)
            return
            
        # Get the form
        form = self.data_manager.get_form_by_id(form_id)
        if not form:
            QMessageBox.warning(self, "Error", f"Form {form_id} not found.")
            return
        
        # Create a new view tab
        view_tab = ViewTab(self, form, self.data_manager)
        
        # Add the tab
        tab_title = f"{form_id}"
        tab_index = self.tab_widget.addTab(view_tab, tab_title)
        
        # Track this tab
        self.view_tabs[form_id] = {
            'tab': view_tab,
            'index': tab_index
        }
        
        # Connect close signal
        view_tab.close_requested.connect(lambda: self.close_view_tab(form_id))
        
        # Switch to the new tab
        self.tab_widget.setCurrentIndex(tab_index)
    
    def edit_form(self, form_id):
        """Edit a form in a new tab"""
        # Check if this form is already being edited
        if form_id in self.edit_tabs:
            # Switch to the existing tab
            tab_index = self.edit_tabs[form_id]['index']
            self.tab_widget.setCurrentIndex(tab_index)
            return
        
        # Create a new edit tab
        edit_tab = EditTab(self, form_id, self.user_info, self.data_manager)
        
        # Add the tab
        tab_title = f"Editing: {form_id}"
        tab_index = self.tab_widget.addTab(edit_tab, tab_title)
        
        # Track this tab
        self.edit_tabs[form_id] = {
            'tab': edit_tab,
            'index': tab_index
        }
        
        # Connect signals
        edit_tab.form_updated.connect(self.on_form_updated)
        
        # Switch to the new tab
        self.tab_widget.setCurrentIndex(tab_index)
    
    def on_form_updated(self, form_id):
        """Handle a form being updated"""
        # Reload historical forms
        self.history_tab.load_historical_forms()
        
        # Close the edit tab
        if form_id in self.edit_tabs:
            tab_index = self.edit_tabs[form_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.edit_tabs[form_id]
            
            # Update tab indices for all remaining tabs
            self.update_tab_indices()
        
        # Also close any view tab for this form (since it's now outdated)
        if form_id in self.view_tabs:
            tab_index = self.view_tabs[form_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.view_tabs[form_id]
            
            # Update tab indices again
            self.update_tab_indices()
        
        # Switch to history tab
        self.tab_widget.setCurrentIndex(self.history_tab_index)
    
    def on_form_deleted(self, form_id):
        """Handle a form being deleted"""
        # Close the edit tab if it's open
        if form_id in self.edit_tabs:
            tab_index = self.edit_tabs[form_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.edit_tabs[form_id]
            
            # Update tab indices for all remaining tabs
            self.update_tab_indices()
            
        # Close the view tab if it's open
        if form_id in self.view_tabs:
            tab_index = self.view_tabs[form_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.view_tabs[form_id]
            
            # Update tab indices again
            self.update_tab_indices()
    
    def on_settings_changed(self):
        """Handle settings being changed"""
        # Update references to settings in all tabs
        self.form_tab.data_manager = self.data_manager
        for form_id, tab_info in self.edit_tabs.items():
            tab_info['tab'].data_manager = self.data_manager
    
    def on_tab_close_requested(self, index):
        """Handle tab close requests"""
        # Don't allow closing the main tabs
        if index == self.form_tab_index or index == self.history_tab_index or index == self.config_tab_index:
            return
        
        # Find which edit tab this is
        form_id_to_remove = None
        for form_id, tab_info in self.edit_tabs.items():
            if tab_info['index'] == index:
                form_id_to_remove = form_id
                break
        
        if form_id_to_remove:
            # Ask for confirmation if there are unsaved changes
            # For simplicity, always ask for confirmation
            confirm = QMessageBox.question(
                self,
                "Confirm Close",
                "Are you sure you want to close this editing tab?\nAny unsaved changes will be lost.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if confirm == QMessageBox.Yes:
                # Remove the tab
                self.tab_widget.removeTab(index)
                del self.edit_tabs[form_id_to_remove]
                
                # Update tab indices for all remaining tabs
                self.update_tab_indices()
            return
        
        # Find which view tab this is
        form_id_to_remove = None
        for form_id, tab_info in self.view_tabs.items():
            if tab_info['index'] == index:
                form_id_to_remove = form_id
                break
        
        if form_id_to_remove:
            # Just close the tab without confirmation for view tabs
            self.tab_widget.removeTab(index)
            del self.view_tabs[form_id_to_remove]
            
            # Update tab indices for all remaining tabs
            self.update_tab_indices()
            return
            
        # This is some other custom tab, just close it
        self.tab_widget.removeTab(index)
    
    def update_tab_indices(self):
        """Update the index values for all dynamic tabs"""
        for form_id, tab_info in self.edit_tabs.items():
            tab_info['index'] = self.tab_widget.indexOf(tab_info['tab'])
            
        for form_id, tab_info in self.view_tabs.items():
            tab_info['index'] = self.tab_widget.indexOf(tab_info['tab'])
            
    def close_view_tab(self, form_id):
        """Close a view tab by form ID"""
        if form_id in self.view_tabs:
            tab_index = self.view_tabs[form_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.view_tabs[form_id]
            
            # Update tab indices for all remaining tabs
            self.update_tab_indices()
