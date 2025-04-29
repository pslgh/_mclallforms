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
    QLineEdit, QFrame, QCheckBox, QScrollArea, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QColor, QFont, QIcon, QBrush

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
        
        # Create splitter for table and details view
        splitter = QSplitter(Qt.Vertical)
        main_layout.addWidget(splitter, 1)  # Give it stretch factor of 1
        
        # Top part: Table for displaying timesheet entries
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        
        table_header = QWidget()
        table_header_layout = QHBoxLayout(table_header)
        table_header_layout.setContentsMargins(0, 0, 0, 0)
        
        table_label = QLabel("Timesheet Entries")
        table_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        search_label = QLabel("Quick Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search any column")
        self.search_input.textChanged.connect(self.apply_filters)
        
        table_header_layout.addWidget(table_label)
        table_header_layout.addStretch()
        table_header_layout.addWidget(search_label)
        table_header_layout.addWidget(self.search_input)
        
        table_layout.addWidget(table_header)
        
        # Enhanced table with more columns
        self.entries_table = QTableWidget(0, 9)
        self.entries_table.setHorizontalHeaderLabels([
            "Entry ID", "Client", "Work Type", "Engineer", "Creation Date", "Status", 
            "Total Hours", "Total Cost", "Currency"
        ])
        
        # Set column widths
        self.entries_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        self.entries_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)  # Client
        self.entries_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Work Type
        self.entries_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Engineer
        self.entries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Date
        self.entries_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Status
        self.entries_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Hours
        self.entries_table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Total Cost
        self.entries_table.horizontalHeader().setSectionResizeMode(8, QHeaderView.ResizeToContents)  # Currency
        
        # Style the table
        self.entries_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background-color: white;
                gridline-color: #e0e0e0;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                border: 1px solid #d0d0d0;
                padding: 4px;
                font-weight: bold;
            }
            QTableWidget::item {
                padding: 4px;
            }
        """)
        
        self.entries_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.entries_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.entries_table.doubleClicked.connect(self.on_table_double_clicked)
        self.entries_table.setAlternatingRowColors(True)
        self.entries_table.verticalHeader().setVisible(False)
        self.entries_table.verticalHeader().setDefaultSectionSize(40)  # Set row height
        
        # Connect selection change to update details view
        self.entries_table.itemSelectionChanged.connect(self.update_detail_view)
        
        table_layout.addWidget(self.entries_table)
        splitter.addWidget(table_container)
        
        # Bottom part: Details view for selected timesheet
        self.detail_view = QScrollArea()
        self.detail_view.setWidgetResizable(True)
        self.detail_view.setMinimumHeight(250)
        
        self.detail_container = QWidget()
        self.detail_layout = QVBoxLayout(self.detail_container)
        
        # No selection message
        self.no_selection_label = QLabel("Select a timesheet entry above to view details")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 14px; color: #888;")
        self.detail_layout.addWidget(self.no_selection_label)
        
        self.detail_view.setWidget(self.detail_container)
        splitter.addWidget(self.detail_view)
        
        # Set initial splitter sizes (70% table, 30% details)
        splitter.setSizes([700, 300])
        
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
        """Load timesheet entries from the data manager"""
        print("\n[HistoryTab] Loading historical entries")
        
        entries = []
        
        # First try using the data manager
        try:
            entries = self.data_manager.load_entries()
            print(f"[HistoryTab] Loaded {len(entries)} entries from data manager")
        except Exception as e:
            print(f"[HistoryTab] Error loading from data manager: {e}")
            
            # Fallback: Try to load directly from file
            if self.data_manager.data_file_path.exists():
                try:
                    # Try to read the file directly
                    from modules.timesheet.models.timesheet_data import TimesheetEntry
                    with open(self.data_manager.data_file_path, 'r', encoding='utf-8') as f:
                        print("[HistoryTab] Reading directly from file...")
                        raw_data = json.load(f)
                        if 'entries' in raw_data and isinstance(raw_data['entries'], list):
                            for entry_dict in raw_data['entries']:
                                try:
                                    entry = TimesheetEntry.from_dict(entry_dict)
                                    entries.append(entry)
                                except Exception as entry_err:
                                    print(f"[HistoryTab] Error parsing entry: {entry_err}")
                            print(f"[HistoryTab] Loaded {len(entries)} entries directly from file")
                except Exception as file_e:
                    print(f"[HistoryTab] Error reading file directly: {file_e}")
                    traceback.print_exc()
        
        # Show what we loaded
        if entries:
            print(f"[HistoryTab] First few entries:")
            for i, entry in enumerate(entries[:3]):
                print(f"[HistoryTab] Entry {i}: ID={entry.entry_id}, Client={entry.client}")
                if i >= 2:  # Only show the first 3
                    break
        else:
            print("[HistoryTab] No entries loaded")
        
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
    
    def reset_filters(self):
        """Reset all filters to default values"""
        print("\n[HistoryTab] Resetting filters")
        self.client_filter.setCurrentText("All Clients")
        self.status_filter.setCurrentText("All Statuses")
        
        # Reset dates to current month
        today = datetime.datetime.now().date()
        first_day = today.replace(day=1)
        self.start_date_filter.setDate(first_day)
        self.end_date_filter.setDate(today)
        
        # Clear search
        self.search_input.clear()
        
        # Apply the reset filters
        self.apply_filters()
    
    def apply_filters(self):
        """Apply filters to the entries table"""
        print("\n[HistoryTab] Applying filters")
        
        # Get entries from data manager or try direct file loading
        try:
            entries = self.data_manager.load_entries()
            print(f"[HistoryTab] Got {len(entries)} entries for filtering from data manager")
        except Exception as e:
            print(f"[HistoryTab] Error getting entries from data manager: {e}")
            # Fall back to entries loaded in load_historical_entries
            entries = []
            # We could add a fallback here to load directly from file like in load_historical_entries
            # but that would duplicate code. Better to call load_historical_entries again.
            try:
                print("[HistoryTab] Running load_historical_entries again...")
                self.load_historical_entries()
                return  # This will handle updating the table via apply_filters
            except Exception as e2:
                print(f"[HistoryTab] Fallback also failed: {e2}")
                
        # Get filter values
        client_filter = self.client_filter.currentText()
        status_filter = self.status_filter.currentText()
        start_date = self.start_date_filter.date().toString("yyyy/MM/dd")
        end_date = self.end_date_filter.date().toString("yyyy/MM/dd")
        search_text = self.search_input.text().lower()
        
        print(f"[HistoryTab] Filters: Client='{client_filter}', Status='{status_filter}', "
              f"DateRange={start_date} to {end_date}, Search='{search_text}'")
        
        # Apply filters
        filtered_entries = []
        for entry in entries:
            try:
                # Search text filter (searches across all fields)
                if search_text and not self._entry_matches_search(entry, search_text):
                    continue
                    
                # Client filter
                has_client = hasattr(entry, 'client') and entry.client
                if client_filter != "All Clients" and (not has_client or entry.client != client_filter):
                    continue
                    
                # Status filter
                has_status = hasattr(entry, 'status') and entry.status
                if status_filter != "All Statuses" and (not has_status or entry.status != status_filter):
                    continue
                    
                # Date filter - any time entry with date in range passes
                has_time_entries = hasattr(entry, 'time_entries') and entry.time_entries
                if has_time_entries:  # Only apply date filter if there are time entries
                    date_match = False
                    for time_entry in entry.time_entries:
                        entry_date = time_entry.get('date', '')
                        if start_date <= entry_date <= end_date:
                            date_match = True
                            break
                            
                    if not date_match:
                        continue
                
                # If passed all filters, add to filtered list
                filtered_entries.append(entry)
            except Exception as entry_err:
                print(f"[HistoryTab] Error filtering entry: {entry_err}")
                # Skip entries that cause errors during filtering
                continue
        
        # Update table
        print(f"[HistoryTab] Filtered to {len(filtered_entries)} entries")
        self.update_entries_table(filtered_entries)
        
        # Clear detail view if no entries or no selection
        if not filtered_entries or not self.entries_table.selectedItems():
            self.clear_detail_view()

    def _entry_matches_search(self, entry, search_text):
        """Check if entry matches the search text in any field"""
        # Helper function to safely check if attribute contains search text
        def safe_check(attr_name):
            if hasattr(entry, attr_name):
                attr_value = getattr(entry, attr_name)
                if attr_value is not None:
                    if isinstance(attr_value, str) and search_text in attr_value.lower():
                        return True
                    elif not isinstance(attr_value, str) and search_text in str(attr_value).lower():
                        return True
            return False
        
        # Check common fields
        if safe_check('entry_id') or safe_check('client') or safe_check('work_type') or \
           safe_check('engineer_name') or safe_check('engineer_surname') or \
           safe_check('status') or safe_check('creation_date') or \
           safe_check('total_service_charge') or safe_check('currency'):
            return True
            
        # Check time entries if they exist
        if hasattr(entry, 'time_entries') and entry.time_entries:
            for time_entry in entry.time_entries:
                if (search_text in str(time_entry.get('date', '')).lower() or
                    search_text in str(time_entry.get('description', '')).lower()):
                    return True
                    
        # Check tool usage if it exists
        if hasattr(entry, 'tool_usage') and entry.tool_usage:
            for tool in entry.tool_usage:
                if search_text in str(tool.get('tool_name', '')).lower():
                    return True
                    
        return False
        
    def update_entries_table(self, entries):
        """Update the entries table with the filtered entries"""
        print(f"\n[HistoryTab] Updating entries table with {len(entries)} entries")
        
        # Clear the table
        self.entries_table.setRowCount(0)
        
        # Add each entry to the table
        for i, entry in enumerate(entries):
            try:
                row = self.entries_table.rowCount()
                self.entries_table.insertRow(row)
                
                # Calculate total hours with error handling
                total_hours = "0.0"
                try:
                    if hasattr(entry, 'calculate_total_hours'):
                        hours = entry.calculate_total_hours()
                        total_hours = f"{hours['total']:.1f}"
                    elif hasattr(entry, 'time_entries') and entry.time_entries:
                        # Manual calculation if method not available
                        total = 0.0
                        for time_entry in entry.time_entries:
                            total += float(time_entry.get('equivalent_hours', 0))
                        total_hours = f"{total:.1f}"
                except Exception as e:
                    print(f"[HistoryTab] Error calculating hours: {e}")
                
                # Get basic entry info with safe defaults
                entry_id = getattr(entry, 'entry_id', 'Unknown')
                client = getattr(entry, 'client', 'Unknown')
                work_type = getattr(entry, 'work_type', 'Unknown')
                
                # Format engineer name
                engineer_name = ""
                if hasattr(entry, 'engineer_name'):
                    engineer_name = entry.engineer_name
                    if hasattr(entry, 'engineer_surname') and entry.engineer_surname:
                        engineer_name += f" {entry.engineer_surname}"
                
                # Format creation date
                creation_date = "Unknown"
                if hasattr(entry, 'creation_date') and entry.creation_date:
                    creation_date = entry.creation_date
                    if ' ' in creation_date:  # Has time component
                        creation_date = creation_date.split(' ')[0]  # Keep only the date part
                
                # Determine status with safe default
                status = "Open"
                if hasattr(entry, 'status') and entry.status:
                    status = entry.status
                elif hasattr(entry, 'payment_status') and entry.payment_status:
                    status = entry.payment_status
                
                # Get total cost with safe handling
                total_cost = 0.0
                total_cost_str = "0.00"
                if hasattr(entry, 'total_service_charge') and entry.total_service_charge is not None:
                    try:
                        total_cost = float(entry.total_service_charge)
                        total_cost_str = f"{total_cost:,.2f}"
                    except (ValueError, TypeError):
                        total_cost_str = str(entry.total_service_charge)
                
                # Get currency with safe default
                currency = "THB"
                if hasattr(entry, 'currency') and entry.currency:
                    currency = entry.currency
                
                # Create table items
                id_item = QTableWidgetItem(str(entry_id))
                client_item = QTableWidgetItem(client)
                work_type_item = QTableWidgetItem(work_type)
                engineer_item = QTableWidgetItem(engineer_name)
                date_item = QTableWidgetItem(creation_date)
                
                # Color-code status based on value
                status_item = QTableWidgetItem(status)
                if status.lower() == "approved":
                    status_item.setForeground(QBrush(QColor("green")))
                elif status.lower() == "rejected":
                    status_item.setForeground(QBrush(QColor("red")))
                elif status.lower() == "submitted":
                    status_item.setForeground(QBrush(QColor("blue")))
                
                hours_item = QTableWidgetItem(total_hours)
                hours_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                cost_item = QTableWidgetItem(total_cost_str)
                cost_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                
                currency_item = QTableWidgetItem(currency)
                
                # Add items to table
                self.entries_table.setItem(row, 0, id_item)
                self.entries_table.setItem(row, 1, client_item)
                self.entries_table.setItem(row, 2, work_type_item)
                self.entries_table.setItem(row, 3, engineer_item)
                self.entries_table.setItem(row, 4, date_item)
                self.entries_table.setItem(row, 5, status_item)
                self.entries_table.setItem(row, 6, hours_item)
                self.entries_table.setItem(row, 7, cost_item)
                self.entries_table.setItem(row, 8, currency_item)
                
            except Exception as e:
                print(f"[HistoryTab] Error adding entry {i} to table: {e}")
                import traceback
                traceback.print_exc()
    
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

    def update_detail_view(self):
        """Update the detail view based on the selected timesheet"""
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            self.clear_detail_view()
            return
            
        # Get the selected entry
        row = selected_rows[0].row()
        entry_item = self.entries_table.item(row, 0)
        entry = entry_item.data(Qt.UserRole)
        
        if not entry:
            self.clear_detail_view()
            return
            
        # Clear the current detail view
        self._clear_layout(self.detail_layout)
        
        # Create a fancy detail view with all timesheet information
        self._create_detail_view(entry)
    
    def clear_detail_view(self):
        """Clear the detail view"""
        self._clear_layout(self.detail_layout)
        self.no_selection_label = QLabel("Select a timesheet entry above to view details")
        self.no_selection_label.setAlignment(Qt.AlignCenter)
        self.no_selection_label.setStyleSheet("font-size: 14px; color: #888;")
        self.detail_layout.addWidget(self.no_selection_label)
    
    def _clear_layout(self, layout):
        """Clear all widgets from a layout"""
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())
    
    def _create_detail_view(self, entry):
        """Create a detailed view of the timesheet entry with safe attribute access"""
        # Get client name with safe attribute access
        client_name = "Unknown"
        if hasattr(entry, 'client') and entry.client:
            client_name = entry.client
            
        # Title section
        title_label = QLabel(f"Timesheet Details: {client_name}")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        self.detail_layout.addWidget(title_label)
        
        # Create a horizontal layout for the key information
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.StyledPanel)
        info_frame.setStyleSheet("background-color: #f9f9f9; border-radius: 5px; padding: 10px;")
        info_layout = QHBoxLayout(info_frame)
        
        # Left column - General Info
        left_column = QVBoxLayout()
        left_column.addWidget(QLabel(f"<b>ID:</b> {entry.entry_id}"))
        left_column.addWidget(QLabel(f"<b>Created:</b> {entry.creation_date}"))
        left_column.addWidget(QLabel(f"<b>Status:</b> {entry.status}"))
        
        # Middle column - Engineer & Work Info
        middle_column = QVBoxLayout()
        middle_column.addWidget(QLabel(f"<b>Engineer:</b> {entry.engineer_name} {entry.engineer_surname}"))
        middle_column.addWidget(QLabel(f"<b>Work Type:</b> {entry.work_type}"))
        emergency = "Yes" if entry.emergency_request else "No"
        middle_column.addWidget(QLabel(f"<b>Emergency Request:</b> {emergency}"))
        
        # Right column - Financial Info
        right_column = QVBoxLayout()
        right_column.addWidget(QLabel(f"<b>Currency:</b> {entry.currency}"))
        hours = entry.calculate_total_hours()
        right_column.addWidget(QLabel(f"<b>Total Hours:</b> {hours['total']:.1f}"))
        right_column.addWidget(QLabel(f"<b>Total Cost:</b> {entry.currency} {entry.total_service_charge:,.2f}"))
        
        info_layout.addLayout(left_column)
        info_layout.addLayout(middle_column)
        info_layout.addLayout(right_column)
        
        self.detail_layout.addWidget(info_frame)
        
        # Time Entries Section
        if entry.time_entries:
            time_section = QGroupBox("Time Entries")
            time_layout = QVBoxLayout(time_section)
            
            time_table = QTableWidget(len(entry.time_entries), 6)
            time_table.setHorizontalHeaderLabels(["Date", "Start", "End", "Rest Hours", "Description", "OT Rate"])
            time_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Description stretches
            time_table.setEditTriggers(QTableWidget.NoEditTriggers)
            time_table.setAlternatingRowColors(True)
            time_table.verticalHeader().setVisible(False)
            
            for i, time_entry in enumerate(entry.time_entries):
                time_table.setItem(i, 0, QTableWidgetItem(time_entry.get('date', '')))
                time_table.setItem(i, 1, QTableWidgetItem(time_entry.get('start_time', '')))
                time_table.setItem(i, 2, QTableWidgetItem(time_entry.get('end_time', '')))
                time_table.setItem(i, 3, QTableWidgetItem(str(time_entry.get('rest_hours', ''))))
                time_table.setItem(i, 4, QTableWidgetItem(time_entry.get('description', '')))
                time_table.setItem(i, 5, QTableWidgetItem(time_entry.get('overtime_rate', '')))
            
            time_layout.addWidget(time_table)
            self.detail_layout.addWidget(time_section)
        
        # Tool Usage Section
        if entry.tool_usage:
            tool_section = QGroupBox("Tool Usage")
            tool_layout = QVBoxLayout(tool_section)
            
            tool_table = QTableWidget(len(entry.tool_usage), 5)
            tool_table.setHorizontalHeaderLabels(["Tool Name", "Amount", "Start Date", "End Date", "Days"])
            tool_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Tool name stretches
            tool_table.setEditTriggers(QTableWidget.NoEditTriggers)
            tool_table.setAlternatingRowColors(True)
            tool_table.verticalHeader().setVisible(False)
            
            for i, tool in enumerate(entry.tool_usage):
                tool_table.setItem(i, 0, QTableWidgetItem(tool.get('tool_name', '')))
                tool_table.setItem(i, 1, QTableWidgetItem(str(tool.get('amount', ''))))
                tool_table.setItem(i, 2, QTableWidgetItem(tool.get('start_date', '')))
                tool_table.setItem(i, 3, QTableWidgetItem(tool.get('end_date', '')))
                tool_table.setItem(i, 4, QTableWidgetItem(str(tool.get('total_days', ''))))
            
            tool_layout.addWidget(tool_table)
            self.detail_layout.addWidget(tool_section)
        
        # Rate Information
        rates_section = QGroupBox("Rate Information")
        rates_layout = QGridLayout(rates_section)
        
        rates_layout.addWidget(QLabel("<b>Service Hour Rate:</b>"), 0, 0)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.service_hour_rate:,.2f}"), 0, 1)
        
        rates_layout.addWidget(QLabel("<b>Tool Usage Rate:</b>"), 1, 0)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.tool_usage_rate:,.2f}"), 1, 1)
        
        rates_layout.addWidget(QLabel("<b>T&L Rate (<80km):</b>"), 2, 0)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.tl_rate_short:,.2f}"), 2, 1)
        
        rates_layout.addWidget(QLabel("<b>T&L Rate (>80km):</b>"), 3, 0)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.tl_rate_long:,.2f}"), 3, 1)
        
        rates_layout.addWidget(QLabel("<b>Offshore Day Rate:</b>"), 0, 2)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.offshore_day_rate:,.2f}"), 0, 3)
        
        rates_layout.addWidget(QLabel("<b>Emergency Rate:</b>"), 1, 2)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.emergency_rate:,.2f}"), 1, 3)
        
        rates_layout.addWidget(QLabel("<b>Other Transport:</b>"), 2, 2)
        rates_layout.addWidget(QLabel(f"{entry.currency} {entry.other_transport_charge:,.2f}"), 2, 3)
        
        self.detail_layout.addWidget(rates_section)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        edit_button = QPushButton("Edit This Timesheet")
        edit_button.clicked.connect(lambda: self.edit_entry_requested.emit(entry.entry_id))
        edit_button.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)
        
        export_button = QPushButton("Export to PDF")
        export_button.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        
        button_layout.addWidget(edit_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        
        self.detail_layout.addLayout(button_layout)
        
        # Add stretch at the end to push everything up
        self.detail_layout.addStretch()
