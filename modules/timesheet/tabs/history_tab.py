"""
History Tab - For viewing and managing timesheet entries
"""
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QComboBox, QDateEdit, 
    QGroupBox, QFormLayout, QMessageBox
)
from PySide6.QtCore import Qt, Signal

class HistoryTab(QWidget):
    """Tab for viewing and managing timesheet entries"""
    
    # Signals
    view_entry_requested = Signal(str)  # Emits entry ID
    edit_entry_requested = Signal(str)  # Emits entry ID
    entry_deleted = Signal(str)  # Emits entry ID
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Filter section
        filter_group = QGroupBox("Filter Entries")
        filter_layout = QVBoxLayout(filter_group)
        
        # First row for client and status filters
        top_filter_layout = QHBoxLayout()
        
        client_label = QLabel("Client:")
        self.client_filter = QComboBox()
        self.client_filter.addItem("All Clients")
        self.client_filter.setEditable(True)
        self.client_filter.currentTextChanged.connect(self.apply_filters)
        
        status_label = QLabel("Status:")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "draft", "submitted", "approved", "rejected"])
        self.status_filter.currentTextChanged.connect(self.apply_filters)
        
        top_filter_layout.addWidget(client_label)
        top_filter_layout.addWidget(self.client_filter, 1)
        top_filter_layout.addWidget(status_label)
        top_filter_layout.addWidget(self.status_filter, 1)
        
        # Second row for date filters and reset button
        bottom_filter_layout = QHBoxLayout()
        
        start_date_label = QLabel("Start:")
        self.start_date_filter = QDateEdit()
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setDisplayFormat("yyyy/MM/dd")
        self.start_date_filter.setDate(datetime.datetime.now().date().replace(day=1))  # First day of current month
        self.start_date_filter.dateChanged.connect(self.apply_filters)
        
        end_date_label = QLabel("End:")
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setDisplayFormat("yyyy/MM/dd")
        self.end_date_filter.setDate(datetime.datetime.now().date())  # Today
        self.end_date_filter.dateChanged.connect(self.apply_filters)
        
        reset_button = QPushButton("Reset Filters")
        reset_button.clicked.connect(self.reset_filters)
        
        bottom_filter_layout.addWidget(start_date_label)
        bottom_filter_layout.addWidget(self.start_date_filter)
        bottom_filter_layout.addWidget(end_date_label)
        bottom_filter_layout.addWidget(self.end_date_filter)
        bottom_filter_layout.addWidget(reset_button)
        
        # Add rows to main filter layout
        filter_layout.addLayout(top_filter_layout)
        filter_layout.addLayout(bottom_filter_layout)
        
        main_layout.addWidget(filter_group)
        
        # Table for displaying timesheet entries
        table_label = QLabel("Timesheet Entries")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(table_label)
        
        self.entries_table = QTableWidget(0, 7)
        self.entries_table.setHorizontalHeaderLabels([
            "Entry ID", "Client", "Work Type", "Engineer", "Creation Date", "Status", "Total Hours"
        ])
        self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.entries_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.entries_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.on_table_double_clicked)
        
        main_layout.addWidget(self.entries_table)
        
        # Action buttons
        button_layout = QHBoxLayout()
        
        self.view_button = QPushButton("View")
        self.view_button.clicked.connect(self.view_selected_entry)
        
        self.edit_button = QPushButton("Edit")
        self.edit_button.clicked.connect(self.edit_selected_entry)
        
        self.delete_button = QPushButton("Delete Selected Row")
        self.delete_button.clicked.connect(self.delete_selected_entry)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.load_historical_entries)
        
        button_layout.addWidget(self.view_button)
        button_layout.addWidget(self.edit_button)
        button_layout.addWidget(self.delete_button)
        button_layout.addStretch()
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
    
    def load_historical_entries(self):
        """Load all timesheet entries from the data file"""
        entries = self.data_manager.load_entries()
        
        # Update client filter options
        self.update_client_filter_options(entries)
        
        # Apply filters
        self.apply_filters()
    
    def update_client_filter_options(self, entries):
        """Update the client filter combobox options"""
        # Save current selection
        current_text = self.client_filter.currentText()
        
        # Clear and repopulate
        self.client_filter.clear()
        self.client_filter.addItem("All Clients")
        
        # Add unique clients
        clients = set()
        for entry in entries:
            if entry.client and entry.client not in clients:
                clients.add(entry.client)
        
        for client in sorted(clients):
            self.client_filter.addItem(client)
        
        # Restore selection if possible
        index = self.client_filter.findText(current_text)
        if index >= 0:
            self.client_filter.setCurrentIndex(index)
    
    def apply_filters(self):
        """Apply filters to the entries table"""
        entries = self.data_manager.load_entries()
        filtered_entries = []
        
        # Get filter values
        client_filter = self.client_filter.currentText()
        status_filter = self.status_filter.currentText()
        start_date = self.start_date_filter.date().toString("yyyy/MM/dd")
        end_date = self.end_date_filter.date().toString("yyyy/MM/dd")
        
        # Apply filters
        for entry in entries:
            # Client filter
            if client_filter != "All Clients" and entry.client != client_filter:
                continue
                
            # Status filter
            if status_filter != "All Statuses" and entry.status != status_filter:
                continue
                
            # Date filter - any time entry with date in range passes
            date_match = False
            for time_entry in entry.time_entries:
                entry_date = time_entry.get('date', '')
                if start_date <= entry_date <= end_date:
                    date_match = True
                    break
                    
            if not date_match and entry.time_entries:
                continue
                
            # If passed all filters, add to filtered list
            filtered_entries.append(entry)
        
        # Update table
        self.update_entries_table(filtered_entries)
    
    def reset_filters(self):
        """Reset all filters to default values"""
        self.client_filter.setCurrentText("All Clients")
        self.status_filter.setCurrentText("All Statuses")
        self.start_date_filter.setDate(datetime.datetime.now().date().replace(day=1))
        self.end_date_filter.setDate(datetime.datetime.now().date())
        
        # Apply the reset filters
        self.apply_filters()
    
    def update_entries_table(self, entries):
        """Update the table with the given entries"""
        self.entries_table.setRowCount(0)
        
        for entry in entries:
            row = self.entries_table.rowCount()
            self.entries_table.insertRow(row)
            
            # Calculate total hours
            hours = entry.calculate_total_hours()
            total_hours = f"{hours['total']:.1f}"
            
            # Add entry data to table
            self.entries_table.setItem(row, 0, QTableWidgetItem(entry.entry_id))
            self.entries_table.setItem(row, 1, QTableWidgetItem(entry.client))
            self.entries_table.setItem(row, 2, QTableWidgetItem(entry.work_type))
            self.entries_table.setItem(row, 3, QTableWidgetItem(f"{entry.engineer_name} {entry.engineer_surname}"))
            self.entries_table.setItem(row, 4, QTableWidgetItem(entry.creation_date))
            self.entries_table.setItem(row, 5, QTableWidgetItem(entry.status))
            self.entries_table.setItem(row, 6, QTableWidgetItem(total_hours))
    
    def on_table_double_clicked(self, index):
        """Handle double click on table item"""
        # Get the entry ID from the first column
        row = index.row()
        entry_id = self.entries_table.item(row, 0).text()
        
        # Request to view the entry
        self.view_entry_requested.emit(entry_id)
    
    def get_selected_entry_id(self):
        """Get the ID of the selected entry"""
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            return None
            
        row = selected_rows[0].row()
        return self.entries_table.item(row, 0).text()
    
    def view_selected_entry(self):
        """View the selected entry"""
        entry_id = self.get_selected_entry_id()
        if entry_id:
            self.view_entry_requested.emit(entry_id)
        else:
            QMessageBox.warning(self, "Selection Error", "Please select an entry.")
    
    def edit_selected_entry(self):
        """Edit the selected entry"""
        entry_id = self.get_selected_entry_id()
        if entry_id:
            self.edit_entry_requested.emit(entry_id)
        else:
            QMessageBox.warning(self, "Selection Error", "Please select an entry.")
    
    def delete_selected_entry(self):
        """Delete the selected entry"""
        entry_id = self.get_selected_entry_id()
        if not entry_id:
            QMessageBox.warning(self, "Selection Error", "Please select an entry.")
            return
            
        # Confirm deletion
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this timesheet entry?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.data_manager.delete_entry(entry_id):
                QMessageBox.information(self, "Success", "Timesheet entry deleted successfully.")
                self.entry_deleted.emit(entry_id)
                self.load_historical_entries()
            else:
                QMessageBox.critical(self, "Error", "Failed to delete timesheet entry.")
