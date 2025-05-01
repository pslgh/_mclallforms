"""
History Tab - For viewing and managing timesheet entries
"""
import datetime
import os
import json
import traceback
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QLabel, QComboBox, QDateEdit, 
    QGroupBox, QFormLayout, QMessageBox, QSplitter, QTextEdit,
    QLineEdit, QFrame, QCheckBox, QScrollArea, QSizePolicy, QGridLayout,
    QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QDate
from PySide6.QtGui import QColor, QFont, QIcon, QBrush

from ..models.timesheet_data import TimesheetEntry

class HistoryTab(QWidget):
    """Tab for viewing and managing timesheet entries"""
    
    # Signals
    view_entry_requested = Signal(str)  # Emits entry ID
    edit_entry_requested = Signal(str)  # Emits entry ID
    entry_deleted = Signal(str)  # Emits entry ID
    close_requested = Signal()  # Emits when close button is clicked
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        self.filtered_entries = []
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Action buttons at the top
        toolbar_layout = QHBoxLayout()
        
        # Title label
        title_label = QLabel("Timesheet History")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        toolbar_layout.addWidget(title_label)
        
        toolbar_layout.addStretch()
        
        # New Entry button
        new_entry_button = QPushButton("New Entry")
        new_entry_button.setFixedWidth(100)
        new_entry_button.clicked.connect(self.create_new_entry)
        toolbar_layout.addWidget(new_entry_button)
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setFixedWidth(80)
        close_button.clicked.connect(self.close_requested.emit)
        toolbar_layout.addWidget(close_button)
        
        main_layout.addLayout(toolbar_layout)
        
        # Filter controls
        filter_group = QGroupBox("Filter Entries")
        filter_layout = QGridLayout()
        
        # Date range
        date_label = QLabel("Date Range:")
        filter_layout.addWidget(date_label, 0, 0)
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        filter_layout.addWidget(self.date_from, 0, 1)
        
        date_to_label = QLabel("to")
        filter_layout.addWidget(date_to_label, 0, 2)
        
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        filter_layout.addWidget(self.date_to, 0, 3)
        
        # Customer filter
        customer_label = QLabel("Customer:")
        filter_layout.addWidget(customer_label, 1, 0)
        
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.addItem("All")
        filter_layout.addWidget(self.customer_combo, 1, 1)
        
        # Project filter
        project_label = QLabel("Project:")
        filter_layout.addWidget(project_label, 1, 2)
        
        self.project_combo = QComboBox()
        self.project_combo.setEditable(True)
        self.project_combo.addItem("All")
        filter_layout.addWidget(self.project_combo, 1, 3)
        
        # Search box
        search_label = QLabel("Search:")
        filter_layout.addWidget(search_label, 2, 0)
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search by keyword or ID")
        filter_layout.addWidget(self.search_edit, 2, 1, 1, 2)
        
        # Show all reports checkbox
        self.show_all_checkbox = QCheckBox("Show All Reports")
        self.show_all_checkbox.stateChanged.connect(self.on_show_all_changed)
        filter_layout.addWidget(self.show_all_checkbox, 3, 0, 1, 2)
        
        # Apply filter button
        self.apply_filter_button = QPushButton("Apply Filters")
        self.apply_filter_button.clicked.connect(self.apply_filters)
        filter_layout.addWidget(self.apply_filter_button, 2, 3)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Entries table
        self.create_table()
        main_layout.addWidget(self.table)
        
        # Connect signals
        self.connect_signals()
        
    def connect_signals(self):
        """Connect signals to slots"""
        self.table.itemDoubleClicked.connect(self.on_table_item_double_clicked)
        self.search_edit.textChanged.connect(self.on_search_text_changed)
        self.show_all_checkbox.stateChanged.connect(self.on_show_all_changed)
        
    def create_table(self):
        """Create the table widget for displaying timesheet entries"""
        self.table = QTableWidget()
        self.table.setRowCount(0)
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "ID", "Date", "Customer", "Work Type", "Project Name", 
            "Total Hours", "Total Amount", "Actions"
        ])
        
        # Set column widths
        self.table.setColumnWidth(0, 80)   # ID
        self.table.setColumnWidth(1, 100)  # Date
        self.table.setColumnWidth(2, 150)  # Customer
        self.table.setColumnWidth(3, 150)  # Project
        self.table.setColumnWidth(4, 200)  # Description
        self.table.setColumnWidth(5, 100)  # Total Hours
        self.table.setColumnWidth(6, 120)  # Total Amount
        
        # Set light blue selection highlight
        self.table.setStyleSheet("""
            QTableWidget::item:selected {
                background-color: #ADD8E6; /* Light blue */
                color: black; /* Keep text black for better readability */
            }
        """)
        self.table.setColumnWidth(7, 120)  # Actions
        
        # Set table properties
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        
        # Load initial entries
        self.update_entries_table()
        
    def on_table_item_double_clicked(self, item):
        """Handle table item double click to view the entry"""
        row = item.row()
        entry_id = self.table.item(row, 0).text()
        self.view_entry_requested.emit(entry_id)
    
    def create_new_entry(self):
        """Create a new timesheet entry"""
        # Signal to the parent to show the entry tab with a new entry
        self.parent.create_new_entry()
    
    def on_view_button_clicked(self, row):
        """Handle view button click"""
        entry_id = self.table.item(row, 0).text()
        self.view_entry_requested.emit(entry_id)
    
    def on_edit_button_clicked(self, row):
        """Handle edit button click"""
        entry_id = self.table.item(row, 0).text()
        self.edit_entry_requested.emit(entry_id)
    
    def on_delete_button_clicked(self, row):
        """Handle delete button click"""
        entry_id = self.table.item(row, 0).text()
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Confirm Deletion",
            f"Are you sure you want to delete this timesheet entry (ID: {entry_id})?\n\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Signal to delete the entry
            self.entry_deleted.emit(entry_id)
            
            # Update the table
            self.update_entries_table()
    
    def apply_filters(self):
        """Apply filters to the entries table"""
        self.update_entries_table()
    
    def on_search_text_changed(self, text):
        """Handle search text changes"""
        if len(text) >= 3 or len(text) == 0:
            # Only search if at least 3 characters or if cleared
            self.update_entries_table()
    
    def on_show_all_changed(self, state):
        """Handle show all reports checkbox state changes"""
        # Update filters when checkbox state changes
        self.update_entries_table()
        
    def load_historical_entries(self):
        """Load historical entries - called from timesheet_widget"""
        # This method is called from timesheet_widget.py after saving an entry
        self.update_entries_table()
    
    def update_entries_table(self):
        """Update the entries table with filtered entries"""
        # Clear the table
        self.table.setRowCount(0)
        
        # Get all entries
        entries = self.data_manager.load_entries()
        
        # Apply filters
        self.filtered_entries = self.filter_entries(entries)
        
        # Populate table with filtered entries
        self.populate_table(self.filtered_entries)
        
        # Update status
        self.update_filter_status()
    
    def filter_entries(self, entries):
        """Filter entries based on the current filter settings"""
        filtered = []
        
        # If show all checkbox is checked, return all entries
        if self.show_all_checkbox.isChecked():
            return entries
        
        # Get filter values
        date_from = self.date_from.date().toPython()
        date_to = self.date_to.date().toPython()
        customer = self.customer_combo.currentText()
        work_type = self.project_combo.currentText()
        search_text = self.search_edit.text().lower()
        
        for entry in entries:
            # Get entry date
            try:
                # Try to get date from time_entries
                time_entries = self.safe_get_attribute(entry, 'time_entries', [])
                if time_entries and isinstance(time_entries, list) and len(time_entries) > 0:
                    entry_date_str = self.safe_get_attribute(time_entries[0], 'date', '')
                else:
                    # Try creation_date as fallback
                    entry_date_str = self.safe_get_attribute(entry, 'creation_date', '')
                
                if entry_date_str:
                    # Handle different date formats
                    if '/' in entry_date_str:
                        entry_date = datetime.datetime.strptime(entry_date_str, '%Y/%m/%d').date()
                    else:
                        entry_date = datetime.datetime.strptime(entry_date_str, '%Y-%m-%d').date()
                else:
                    # Skip entries without a date
                    continue
            except (ValueError, TypeError):
                # Skip entries with invalid dates
                continue
            
            # Filter by date range
            if entry_date < date_from or entry_date > date_to:
                continue
            
            # Filter by customer
            if customer != "All":
                entry_customer = self.safe_get_attribute(entry, 'client_company_name', '')
                if not entry_customer or customer.lower() not in entry_customer.lower():
                    continue
            
            # Filter by work_type/project
            if work_type != "All":
                entry_work_type = self.safe_get_attribute(entry, 'work_type', '')
                if not entry_work_type or work_type.lower() not in entry_work_type.lower():
                    continue
            
            # Filter by search text
            if search_text:
                # Search in multiple fields
                search_fields = [
                    str(self.safe_get_attribute(entry, 'entry_id', '')),
                    self.safe_get_attribute(entry, 'client_company_name', ''),
                    self.safe_get_attribute(entry, 'work_type', ''),
                    self.safe_get_attribute(entry, 'project_name', ''),
                    self.safe_get_attribute(entry, 'project_description', ''),
                    self.safe_get_attribute(entry, 'report_description', ''),
                    self.safe_get_attribute(entry, 'client_address', ''),
                    self.safe_get_attribute(entry, 'purchasing_order_number', ''),
                    self.safe_get_attribute(entry, 'quotation_number', '')
                ]
                
                # Also search in time_entries descriptions
                time_entries = self.safe_get_attribute(entry, 'time_entries', [])
                for time_entry in time_entries:
                    if isinstance(time_entry, dict):
                        desc = self.safe_get_attribute(time_entry, 'description', '')
                        if desc:
                            search_fields.append(desc)
                
                # Check if search text is in any of the fields
                found = False
                for field in search_fields:
                    if field and search_text in str(field).lower():
                        found = True
                        break
                
                if not found:
                    continue
            
            # Entry passed all filters, add to filtered list
            filtered.append(entry)
        
        return filtered
    
    def populate_table(self, entries):
        """Populate the table with the given entries"""
        # Set the row count
        self.table.setRowCount(len(entries))
        
        # Populate the rows
        for row, entry in enumerate(entries):
            # ID
            entry_id = self.safe_get_attribute(entry, 'entry_id', '')
            id_item = QTableWidgetItem(str(entry_id))
            self.table.setItem(row, 0, id_item)
            
            # Date
            # Try to get date from time_entries first
            date_str = ''
            time_entries = self.safe_get_attribute(entry, 'time_entries', [])
            if time_entries and isinstance(time_entries, list) and len(time_entries) > 0:
                date_str = self.safe_get_attribute(time_entries[0], 'date', '')
            
            # If not found, use creation_date as fallback
            if not date_str:
                date_str = self.safe_get_attribute(entry, 'creation_date', '')
            
            try:
                # Convert to more readable format if possible
                if '/' in date_str:  # Handle different date formats
                    date_obj = datetime.datetime.strptime(date_str, '%Y/%m/%d').date()
                else:
                    date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
                date_str = date_obj.strftime('%d-%b-%Y')
            except (ValueError, TypeError):
                pass
            
            date_item = QTableWidgetItem(date_str)
            self.table.setItem(row, 1, date_item)
            
            # Customer
            customer = self.safe_get_attribute(entry, 'client_company_name', '')
            customer_item = QTableWidgetItem(customer)
            self.table.setItem(row, 2, customer_item)
            
            # Project/Work Type
            work_type = self.safe_get_attribute(entry, 'work_type', '')
            work_type_item = QTableWidgetItem(work_type)
            self.table.setItem(row, 3, work_type_item)
            
            # Project Name
            project_name = self.safe_get_attribute(entry, 'project_name', '')
            project_name_item = QTableWidgetItem(project_name)
            self.table.setItem(row, 4, project_name_item)
            
            # Total Hours
            total_hours = self.calculate_total_hours(entry)
            hours_item = QTableWidgetItem(f"{total_hours:.2f}")
            hours_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 5, hours_item)
            
            # Total Amount
            total_amount = self.safe_get_attribute(entry, 'total_service_charge', 0)
            if isinstance(total_amount, str):
                try:
                    total_amount = float(total_amount.replace(',', ''))
                except (ValueError, TypeError):
                    total_amount = 0
            
            currency = self.safe_get_attribute(entry, 'currency', 'THB')
            currency_symbol = '£' if currency == 'GBP' else ('$' if currency == 'USD' else '฿')
            
            amount_item = QTableWidgetItem(f"{currency_symbol}{total_amount:.2f}")
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(row, 6, amount_item)
            
            # Actions
            actions_widget = self.create_action_buttons(row)
            self.table.setCellWidget(row, 7, actions_widget)
    
    def create_action_buttons(self, row):
        """Create a widget with action buttons for a row"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(5)
        
        # View button
        view_button = QPushButton("View")
        view_button.setFixedSize(QSize(50, 25))
        view_button.clicked.connect(lambda: self.on_view_button_clicked(row))
        layout.addWidget(view_button)
        
        # Edit button
        edit_button = QPushButton("Edit")
        edit_button.setFixedSize(QSize(50, 25))
        edit_button.clicked.connect(lambda: self.on_edit_button_clicked(row))
        layout.addWidget(edit_button)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setFixedSize(QSize(50, 25))
        delete_button.clicked.connect(lambda: self.on_delete_button_clicked(row))
        layout.addWidget(delete_button)
        
        return widget
    
    def calculate_total_hours(self, entry):
        """Calculate the total hours from a timesheet entry"""
        try:
            # Try to get total equivalent hours directly from time_summary
            time_summary = self.safe_get_attribute(entry, 'time_summary', {})
            if isinstance(time_summary, dict) and 'total_equivalent_hours' in time_summary:
                return float(time_summary['total_equivalent_hours'])
            
            # If not available, try to calculate from time entries
            time_entries = self.safe_get_attribute(entry, 'time_entries', [])
            if not time_entries or not isinstance(time_entries, list):
                return 0
                
            total_hours = 0
            for time_entry in time_entries:
                if not isinstance(time_entry, dict):
                    continue
                    
                start_time = self.safe_get_attribute(time_entry, 'start_time', '')
                end_time = self.safe_get_attribute(time_entry, 'end_time', '')
                rest_hours = self.safe_get_attribute(time_entry, 'rest_hours', 0)
                
                if not start_time or not end_time:
                    continue
                
                # Parse times (handle different formats)
                try:
                    if ':' in start_time:  # Format like '08:00'
                        start = datetime.datetime.strptime(start_time, '%H:%M')
                    else:  # Format like '0800'
                        start = datetime.datetime.strptime(start_time, '%H%M')
                        
                    if ':' in end_time:  # Format like '17:00'
                        end = datetime.datetime.strptime(end_time, '%H:%M')
                    else:  # Format like '1700'
                        end = datetime.datetime.strptime(end_time, '%H%M')
                    
                    # Calculate duration in hours
                    diff = end - start
                    hours = diff.seconds / 3600
                    
                    # Subtract rest hours
                    if isinstance(rest_hours, str):
                        try:
                            rest_hours = float(rest_hours)
                        except (ValueError, TypeError):
                            rest_hours = 0
                    
                    # Add to total hours
                    total_hours += (hours - float(rest_hours))
                except (ValueError, TypeError):
                    continue
            
            return total_hours
        except Exception:
            return 0
    
    def update_filter_status(self):
        """Update the filter status (customer and project dropdowns)"""
        # Store current selections
        current_customer = self.customer_combo.currentText()
        current_work_type = self.project_combo.currentText()
        
        # Clear dropdowns but keep "All" option
        self.customer_combo.clear()
        self.project_combo.clear()
        
        self.customer_combo.addItem("All")
        self.project_combo.addItem("All")
        
        # Collect unique customers and work types
        customers = set()
        work_types = set()
        
        # Get all entries to populate filter dropdowns
        all_entries = self.data_manager.load_entries()
        
        for entry in all_entries:
            customer = self.safe_get_attribute(entry, 'client_company_name', '')
            work_type = self.safe_get_attribute(entry, 'work_type', '')
            
            if customer:
                customers.add(customer)
            if work_type:
                work_types.add(work_type)
        
        # Add to dropdowns
        for customer in sorted(customers):
            self.customer_combo.addItem(customer)
        
        for work_type in sorted(work_types):
            self.project_combo.addItem(work_type)
        
        # Restore selections if possible
        customer_index = self.customer_combo.findText(current_customer)
        if customer_index >= 0:
            self.customer_combo.setCurrentIndex(customer_index)
        
        work_type_index = self.project_combo.findText(current_work_type)
        if work_type_index >= 0:
            self.project_combo.setCurrentIndex(work_type_index)
    
    def safe_get_attribute(self, entry, attr_name, default=None):
        """Safely get an attribute from an entry with a default fallback"""
        # First, check if entry has _raw_data dictionary (TimesheetEntry class)
        if hasattr(entry, '_raw_data') and isinstance(entry._raw_data, dict):
            if attr_name in entry._raw_data:
                return entry._raw_data[attr_name]
        
        # If not found in _raw_data or entry doesn't have _raw_data,
        # try direct attribute access
        if hasattr(entry, attr_name):
            return getattr(entry, attr_name)
        
        # Try dictionary access if entry is a dict
        if isinstance(entry, dict) and attr_name in entry:
            return entry[attr_name]
        
        # Fall back to the default value
        return default