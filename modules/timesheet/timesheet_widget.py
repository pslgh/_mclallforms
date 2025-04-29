"""
Timesheet Widget - Main Module
This module coordinates all timesheet tabs and functionality.
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
from modules.timesheet.models.timesheet_data import TimesheetEntry, TimesheetDataManager

# Import tab widgets
from modules.timesheet.tabs.entry_tab import EntryTab
from modules.timesheet.tabs.history_tab import HistoryTab
from modules.timesheet.tabs.view_tab import ViewTab
from modules.timesheet.tabs.edit_tab import EditTab
from modules.timesheet.tabs.reports_tab import ReportsTab
from modules.timesheet.tabs.rates_tab import RatesTab

class TimesheetWidget(QWidget):
    """Main widget for timesheet functionality"""
    
    # Signal to emit when a timesheet is saved
    entry_saved = Signal(str)  # Emits entry ID
    
    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self.user_info = user_info or {}
        self.data_manager = TimesheetDataManager(get_data_path("timesheet/timesheet_entries.json"))
        
        # Track dynamic tabs
        self.edit_tabs = {}  # Maps entry_id to tab widget and index
        self.view_tabs = {}  # Maps entry_id to tab widget and index
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs for entry, history and reports
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.on_tab_close_requested)
        
        # Entry tab
        self.entry_tab = EntryTab(self, self.user_info, self.data_manager)
        self.entry_tab_index = self.tab_widget.addTab(self.entry_tab, "New Timesheet Entry")
        
        # History tab
        self.history_tab = HistoryTab(self, self.data_manager)
        self.history_tab_index = self.tab_widget.addTab(self.history_tab, "History")
        
        # Reports tab
        self.reports_tab = ReportsTab(self, self.data_manager)
        self.reports_tab_index = self.tab_widget.addTab(self.reports_tab, "Reports")
        
        # Standard Service Rate tab
        self.rates_tab = RatesTab(self, self.data_manager)
        self.rates_tab_index = self.tab_widget.addTab(self.rates_tab, "Standard Service Rate")
        
        # Don't allow closing the main tabs
        self.tab_widget.tabBar().setTabButton(self.entry_tab_index, QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(self.history_tab_index, QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(self.reports_tab_index, QTabBar.RightSide, None)
        self.tab_widget.tabBar().setTabButton(self.rates_tab_index, QTabBar.RightSide, None)
        
        main_layout.addWidget(self.tab_widget)
        
        # Connect signals
        self.entry_tab.entry_saved.connect(self.on_entry_saved)
        self.history_tab.view_entry_requested.connect(self.view_entry)
        self.history_tab.edit_entry_requested.connect(self.edit_entry)
        self.history_tab.entry_deleted.connect(self.on_entry_deleted)
    
    def on_tab_close_requested(self, index):
        """Handle a tab close request"""
        # Get the widget at this index
        widget = self.tab_widget.widget(index)
        
        # Check if this is a view tab
        for entry_id, tab_info in list(self.view_tabs.items()):
            if tab_info['index'] == index:
                self.close_view_tab(entry_id)
                return
                
        # Check if this is an edit tab
        for entry_id, tab_info in list(self.edit_tabs.items()):
            if tab_info['index'] == index:
                self.close_edit_tab(entry_id)
                return
    
    def close_view_tab(self, entry_id):
        """Close a view tab"""
        if entry_id in self.view_tabs:
            tab_index = self.view_tabs[entry_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.view_tabs[entry_id]
            
            # Update tab indices
            self.update_tab_indices()
    
    def close_edit_tab(self, entry_id):
        """Close an edit tab"""
        if entry_id in self.edit_tabs:
            tab_index = self.edit_tabs[entry_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.edit_tabs[entry_id]
            
            # Update tab indices
            self.update_tab_indices()
    
    def update_tab_indices(self):
        """Update tab indices after tab removal"""
        # Update view tab indices
        for entry_id, tab_info in self.view_tabs.items():
            tab_info['index'] = self.tab_widget.indexOf(tab_info['tab'])
            
        # Update edit tab indices
        for entry_id, tab_info in self.edit_tabs.items():
            tab_info['index'] = self.tab_widget.indexOf(tab_info['tab'])
    
    def on_entry_saved(self, entry_id):
        """Handle an entry being saved"""
        # Reload historical entries
        self.history_tab.load_historical_entries()
        
        # Switch to history tab
        self.tab_widget.setCurrentIndex(self.history_tab_index)
        
        # Forward the signal
        self.entry_saved.emit(entry_id)
    
    def view_entry(self, entry_id):
        """View an entry in a new tab"""
        # Check if this entry is already being viewed
        if entry_id in self.view_tabs:
            # Switch to the existing tab
            tab_index = self.view_tabs[entry_id]['index']
            self.tab_widget.setCurrentIndex(tab_index)
            return
            
        # Get the entry
        entry = self.data_manager.get_entry_by_id(entry_id)
        if not entry:
            QMessageBox.warning(self, "Error", f"Entry {entry_id} not found.")
            return
        
        # Create a new view tab
        view_tab = ViewTab(self, entry, self.data_manager)
        
        # Add the tab
        tab_title = f"View: {entry_id}"
        tab_index = self.tab_widget.addTab(view_tab, tab_title)
        
        # Track this tab
        self.view_tabs[entry_id] = {
            'tab': view_tab,
            'index': tab_index
        }
        
        # Connect close signal
        view_tab.close_requested.connect(lambda: self.close_view_tab(entry_id))
        
        # Switch to the new tab
        self.tab_widget.setCurrentIndex(tab_index)
    
    def edit_entry(self, entry_id):
        """Edit an entry in a new tab"""
        # Check if this entry is already being edited
        if entry_id in self.edit_tabs:
            # Switch to the existing tab
            tab_index = self.edit_tabs[entry_id]['index']
            self.tab_widget.setCurrentIndex(tab_index)
            return
        
        # Create a new edit tab
        edit_tab = EditTab(self, entry_id, self.user_info, self.data_manager)
        
        # Add the tab
        tab_title = f"Editing: {entry_id}"
        tab_index = self.tab_widget.addTab(edit_tab, tab_title)
        
        # Track this tab
        self.edit_tabs[entry_id] = {
            'tab': edit_tab,
            'index': tab_index
        }
        
        # Connect signals
        edit_tab.entry_updated.connect(self.on_entry_updated)
        
        # Switch to the new tab
        self.tab_widget.setCurrentIndex(tab_index)
    
    def on_entry_updated(self, entry_id):
        """Handle an entry being updated"""
        # Reload historical entries
        self.history_tab.load_historical_entries()
        
        # Close the edit tab
        if entry_id in self.edit_tabs:
            tab_index = self.edit_tabs[entry_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.edit_tabs[entry_id]
            
            # Update tab indices for all remaining tabs
            self.update_tab_indices()
        
        # Also close any view tab for this entry (since it's now outdated)
        if entry_id in self.view_tabs:
            tab_index = self.view_tabs[entry_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.view_tabs[entry_id]
            
            # Update tab indices again
            self.update_tab_indices()
        
        # Switch to history tab
        self.tab_widget.setCurrentIndex(self.history_tab_index)
    
    def on_entry_deleted(self, entry_id):
        """Handle an entry being deleted"""
        # Close the edit tab if it's open
        if entry_id in self.edit_tabs:
            tab_index = self.edit_tabs[entry_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.edit_tabs[entry_id]
            
            # Update tab indices for all remaining tabs
            self.update_tab_indices()
            
        # Close the view tab if it's open
        if entry_id in self.view_tabs:
            tab_index = self.view_tabs[entry_id]['index']
            self.tab_widget.removeTab(tab_index)
            del self.view_tabs[entry_id]
            
            # Update tab indices again
            self.update_tab_indices()
