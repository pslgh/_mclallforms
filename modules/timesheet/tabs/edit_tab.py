"""
Edit Tab - For modifying existing timesheet entries
"""
import os
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QLineEdit, QComboBox, QTextEdit, QPushButton, QDateEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QTimeEdit,
    QMessageBox, QGroupBox, QScrollArea, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal, QTime, QDate
from PySide6.QtGui import QPalette, QBrush

class EditTab(QWidget):
    """Tab for editing existing timesheet entries"""
    
    # Signal to emit when an entry is updated
    entry_updated = Signal(str)  # Emits entry ID
    
    def __init__(self, parent, entry_id, user_info, data_manager):
        super().__init__(parent)
        self.parent = parent
        self.entry_id = entry_id
        self.user_info = user_info
        self.data_manager = data_manager
        
        # Get the entry
        self.entry = self.data_manager.get_entry_by_id(entry_id)
        if not self.entry:
            QMessageBox.warning(self, "Error", f"Entry {entry_id} not found.")
            return
            
        # Copy time entries
        self.time_entries = self.entry.time_entries.copy()
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create a scroll area for the form
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Header
        header_label = QLabel(f"Edit Timesheet Entry: {self.entry_id}")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        scroll_layout.addWidget(header_label)
        
        # Client Information Section
        client_group = QGroupBox("Client Information")
        client_layout = QHBoxLayout(client_group)
        
        # Create widgets
        client_label = QLabel("Client:")
        self.client_input = QLineEdit()
        self.client_input.setText(self.entry.client)
        
        work_type_label = QLabel("Work Type:")
        self.work_type_input = QComboBox()
        self.work_type_input.addItems(["", "Special Field Services", "Regular Field Services", "Consultation", "Emergency Support", "Other"])
        self.work_type_input.setEditable(True)
        # Set current text if it exists
        if self.entry.work_type:
            index = self.work_type_input.findText(self.entry.work_type)
            if index >= 0:
                self.work_type_input.setCurrentIndex(index)
            else:
                self.work_type_input.setCurrentText(self.entry.work_type)
        
        tier_label = QLabel("Tier:")
        self.tier_input = QComboBox()
        self.tier_input.addItems(["", "1", "2", "3", "4"])
        # Set current text if it exists
        if self.entry.tier:
            index = self.tier_input.findText(self.entry.tier)
            if index >= 0:
                self.tier_input.setCurrentIndex(index)
        
        # Add widgets to layout
        client_layout.addWidget(client_label)
        client_layout.addWidget(self.client_input, 2) # Give more space to client input
        client_layout.addWidget(work_type_label)
        client_layout.addWidget(self.work_type_input, 2)
        client_layout.addWidget(tier_label)
        client_layout.addWidget(self.tier_input)
        
        scroll_layout.addWidget(client_group)
        
        # Engineer Information Section
        engineer_group = QGroupBox("Engineer Information")
        engineer_layout = QHBoxLayout(engineer_group)
        
        # Create widgets
        name_label = QLabel("Name:")
        self.engineer_name_input = QLineEdit()
        self.engineer_name_input.setText(self.entry.engineer_name)
        
        surname_label = QLabel("Surname:")
        self.engineer_surname_input = QLineEdit()
        self.engineer_surname_input.setText(self.entry.engineer_surname)
        
        status_label = QLabel("Status:")
        # Status ComboBox
        self.status_input = QComboBox()
        self.status_input.addItems(["draft", "submitted", "approved", "rejected"])
        # Set current status
        index = self.status_input.findText(self.entry.status)
        if index >= 0:
            self.status_input.setCurrentIndex(index)
            
        # Add widgets to layout
        engineer_layout.addWidget(name_label)
        engineer_layout.addWidget(self.engineer_name_input)
        engineer_layout.addWidget(surname_label)
        engineer_layout.addWidget(self.engineer_surname_input)
        engineer_layout.addWidget(status_label)
        engineer_layout.addWidget(self.status_input)
        
        # Add a second row for read-only information
        read_only_group = QGroupBox("Entry Information")
        read_only_layout = QHBoxLayout(read_only_group)
        
        # Read-only fields
        created_date_label = QLabel("Created:")
        creation_date_label = QLabel(self.entry.creation_date)
        created_by_text_label = QLabel("By:")
        created_by_label = QLabel(self.entry.created_by)
        
        read_only_layout.addWidget(created_date_label)
        read_only_layout.addWidget(creation_date_label)
        read_only_layout.addWidget(created_by_text_label)
        read_only_layout.addWidget(created_by_label)
        read_only_layout.addStretch()
        
        # Add read-only group to main layout
        scroll_layout.addWidget(read_only_group)
        
        scroll_layout.addWidget(engineer_group)
        
        # Time Entry Section
        time_entry_group = QGroupBox("Add Time Entry")
        time_entry_layout = QVBoxLayout(time_entry_group)
        
        # Time selection row with left alignment
        time_selection_layout = QHBoxLayout()
        time_selection_layout.setAlignment(Qt.AlignLeft)
        
        date_label = QLabel("Date:")
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDisplayFormat("yyyy/MM/dd")
        self.date_input.setDate(datetime.datetime.now().date())
        
        start_label = QLabel("Start:")
        self.start_time_input = QComboBox()
        for hour in range(25):  # 0 to 24
            self.start_time_input.addItem(f"{hour:02d}:00", hour)
        self.start_time_input.setCurrentIndex(8)  # Default 08:00
        self.start_time_input.currentIndexChanged.connect(self.update_end_time)
        
        end_label = QLabel("End:")
        self.end_time_input = QComboBox()
        # End time options will be populated in update_end_time method
        
        rest_label = QLabel("Rest Hours:")
        self.rest_hours_input = QComboBox()
        for hour in range(9):  # 0 to 8 hours rest
            self.rest_hours_input.addItem(f"{hour}", hour)
        self.rest_hours_input.setCurrentIndex(0)  # Default 0 hours rest
        
        ot_label = QLabel("OT Rate:")
        self.overtime_rate_input = QComboBox()
        self.overtime_rate_input.addItems(["Regular", "OT1.5", "OT2.0"])
        
        # Add widgets to time selection layout
        time_selection_layout.addWidget(date_label)
        time_selection_layout.addWidget(self.date_input)
        time_selection_layout.addWidget(start_label)
        time_selection_layout.addWidget(self.start_time_input)
        time_selection_layout.addWidget(end_label)
        time_selection_layout.addWidget(self.end_time_input)
        time_selection_layout.addWidget(rest_label)
        time_selection_layout.addWidget(self.rest_hours_input)
        time_selection_layout.addWidget(ot_label)
        time_selection_layout.addWidget(self.overtime_rate_input)
        time_selection_layout.addStretch(1)  # Push everything to the left
        
        # Description row (kept as is)
        description_layout = QFormLayout()
        self.description_input = QTextEdit()
        self.description_input.setPlaceholderText("Describe the work performed")
        self.description_input.setMaximumHeight(100)
        description_layout.addRow("Description:", self.description_input)
        
        # Add layouts to time entry layout
        time_entry_layout.addLayout(time_selection_layout)
        time_entry_layout.addLayout(description_layout)
        
        # Initialize end time dropdown based on start time
        self.update_end_time()
        
        add_button = QPushButton("Add Time Entry")
        add_button.clicked.connect(self.add_time_entry)
        
        time_entry_layout.addWidget(add_button)
        
        scroll_layout.addWidget(time_entry_group)
        
        # Table for displaying added time entries
        entry_list_group = QGroupBox("Time Entries")
        entry_list_layout = QVBoxLayout(entry_list_group)
        
        self.entries_table = QTableWidget(0, 6)
        self.entries_table.setHorizontalHeaderLabels(["Date", "Start Time", "End Time", "Rest Hours", "Description", "OT Rate"])
        self.entries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Description column stretches
        self.entries_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        # Ensure good visibility for the table
        self.entries_table.setStyleSheet("""
            QTableWidget { 
                gridline-color: #d0d0d0; 
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #e0e0e0;
            }
            QTableWidget::item { color: black; }
            QHeaderView::section { 
                background-color: #f0f0f0; 
                color: black; 
                padding: 4px;
                border: 1px solid #d0d0d0;
            }
        """)
        self.entries_table.setAlternatingRowColors(True)
        self.populate_entries_table()
        
        entry_list_layout.addWidget(self.entries_table)
        
        # Add button to remove selected entry
        remove_button = QPushButton("Remove Selected Entry")
        remove_button.clicked.connect(self.remove_time_entry)
        entry_list_layout.addWidget(remove_button)
        
        scroll_layout.addWidget(entry_list_group)
        
        # Buttons for form actions
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_changes)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_changes)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)
        
        scroll_layout.addLayout(button_layout)
        scroll_layout.addStretch()
        
        # Set the scroll widget
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
    
    def populate_entries_table(self):
        """Populate the table with existing time entries"""
        self.entries_table.setRowCount(0)
        
        for entry in self.time_entries:
            row = self.entries_table.rowCount()
            self.entries_table.insertRow(row)
            
            # Add entry data to table
            start_time = entry.get('start_time', '')
            end_time = entry.get('end_time', '')
            date_str = entry.get('date', '')
            start_display = f"{start_time[:2]}:00" if len(start_time) >= 2 else start_time
            end_display = f"{end_time[:2]}:00" if len(end_time) >= 2 else end_time
            
            # Create date editor for date column
            date_edit = QDateEdit()
            date_edit.setCalendarPopup(True)
            date_edit.setDisplayFormat("yyyy/MM/dd")
            
            # Set a comprehensive style to ensure white background throughout all states
            date_edit.setStyleSheet("""
                QDateEdit { 
                    background-color: white; 
                    color: black;
                    selection-background-color: #d0d0d0;
                    selection-color: black; 
                }
                QDateEdit::drop-down { background-color: white; }
                QDateEdit QAbstractItemView { 
                    background-color: white; 
                    color: black;
                    selection-background-color: #d0d0d0;
                    selection-color: black; 
                }
            """)
            
            # Set white background for the widget
            palette = date_edit.palette()
            palette.setColor(QPalette.Base, Qt.white)
            palette.setColor(QPalette.Text, Qt.black)
            date_edit.setPalette(palette)
            try:
                if "/" in date_str:
                    date = datetime.datetime.strptime(date_str, "%Y/%m/%d").date()
                else:
                    date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
                date_edit.setDate(date)
            except ValueError:
                date_edit.setDate(datetime.datetime.now().date())
            self.entries_table.setCellWidget(row, 0, date_edit)
            
            # Create non-editable items for other columns with explicit black text
            start_item = QTableWidgetItem(start_display)
            start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
            start_item.setForeground(QBrush(Qt.black))
            
            end_item = QTableWidgetItem(end_display)
            end_item.setFlags(end_item.flags() & ~Qt.ItemIsEditable)
            end_item.setForeground(QBrush(Qt.black))
            
            # Get rest hours with default of 0
            rest_hours = entry.get('rest_hours', 0)
            rest_item = QTableWidgetItem(str(rest_hours))
            rest_item.setFlags(rest_item.flags() & ~Qt.ItemIsEditable)
            rest_item.setForeground(QBrush(Qt.black))
            
            desc_item = QTableWidgetItem(entry.get('description', ''))
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            desc_item.setForeground(QBrush(Qt.black))
            
            ot_item = QTableWidgetItem(entry.get('overtime_rate', ''))
            ot_item.setFlags(ot_item.flags() & ~Qt.ItemIsEditable)
            ot_item.setForeground(QBrush(Qt.black))
            
            self.entries_table.setItem(row, 1, start_item)
            self.entries_table.setItem(row, 2, end_item)
            self.entries_table.setItem(row, 3, rest_item)
            self.entries_table.setItem(row, 4, desc_item)
            self.entries_table.setItem(row, 5, ot_item)
    
    def update_end_time(self):
        """Update end time options to only show times after the selected start time"""
        start_hour = self.start_time_input.currentData()
        
        # Remember currently selected end time if possible
        current_end_hour = None
        if self.end_time_input.count() > 0 and self.end_time_input.currentData() is not None:
            current_end_hour = self.end_time_input.currentData()
        
        # Clear current items
        self.end_time_input.clear()
        
        # Add only hours after the start time
        selected_hour = None
        for hour in range(25):  # 0 to 24
            if hour > start_hour:
                self.end_time_input.addItem(f"{hour:02d}:00", hour)
                
                # If this was previously selected, remember the index
                if hour == current_end_hour:
                    selected_hour = hour
        
        # Set default end time (start_hour + 1) or the previously selected time if valid
        default_end_hour = start_hour + 1
        if default_end_hour > 24:
            default_end_hour = 0  # Wrap around to midnight
            
        # Find the index to select
        select_index = 0  # Default to first item
        
        if selected_hour is not None:
            # Try to keep previously selected time if it's still valid
            for i in range(self.end_time_input.count()):
                if self.end_time_input.itemData(i) == selected_hour:
                    select_index = i
                    break
        else:            
            # Otherwise use the default (start_hour + 1)
            for i in range(self.end_time_input.count()):
                if self.end_time_input.itemData(i) == default_end_hour:
                    select_index = i
                    break
        
        # Set the selected index if we have items
        if self.end_time_input.count() > 0:
            self.end_time_input.setCurrentIndex(select_index)
    
    def add_time_entry(self):
        """Add a time entry to the list"""
        # Get values from form
        date = self.date_input.date().toString("yyyy/MM/dd")
        start_hour = self.start_time_input.currentData()
        end_hour = self.end_time_input.currentData()
        rest_hours = self.rest_hours_input.currentData()
        start_time = f"{start_hour:02d}00"
        end_time = f"{end_hour:02d}00"
        
        # Ensure end time is after start time
        if end_hour <= start_hour:
            QMessageBox.warning(self, "Invalid Time Range", "End time must be after start time.")
            return
        description = self.description_input.toPlainText().strip()
        overtime_rate = self.overtime_rate_input.currentText()
        
        # Validate
        if not description:
            QMessageBox.warning(self, "Validation Error", "Please enter a description.")
            return
        
        # Add to internal list
        entry = {
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'rest_hours': rest_hours,
            'description': description,
            'overtime_rate': overtime_rate
        }
        self.time_entries.append(entry)
        
        # Add to table
        row = self.entries_table.rowCount()
        self.entries_table.insertRow(row)
        
        # Create date editor for date column
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDisplayFormat("yyyy/MM/dd")
        try:
            if "/" in date:
                date_obj = datetime.datetime.strptime(date, "%Y/%m/%d").date()
            else:
                date_obj = datetime.datetime.strptime(date, "%Y-%m-%d").date()
            date_edit.setDate(date_obj)
        except ValueError:
            date_edit.setDate(datetime.datetime.now().date())
        self.entries_table.setCellWidget(row, 0, date_edit)
        
        # Create non-editable items for other columns with explicit black text
        start_item = QTableWidgetItem(f"{start_time[:2]}:00")
        start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
        start_item.setForeground(QBrush(Qt.black))
        
        end_item = QTableWidgetItem(f"{end_time[:2]}:00")
        end_item.setFlags(end_item.flags() & ~Qt.ItemIsEditable)
        end_item.setForeground(QBrush(Qt.black))
        
        rest_item = QTableWidgetItem(str(rest_hours))
        rest_item.setFlags(rest_item.flags() & ~Qt.ItemIsEditable)
        rest_item.setForeground(QBrush(Qt.black))
        
        desc_item = QTableWidgetItem(description)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
        desc_item.setForeground(QBrush(Qt.black))
        
        ot_item = QTableWidgetItem(overtime_rate)
        ot_item.setFlags(ot_item.flags() & ~Qt.ItemIsEditable)
        ot_item.setForeground(QBrush(Qt.black))
        
        self.entries_table.setItem(row, 1, start_item)
        self.entries_table.setItem(row, 2, end_item)
        self.entries_table.setItem(row, 3, rest_item)
        self.entries_table.setItem(row, 4, desc_item)
        self.entries_table.setItem(row, 5, ot_item)
        
        # Clear inputs for next entry
        self.description_input.clear()
    
    def remove_time_entry(self):
        """Remove the selected time entry"""
        selected_row = self.entries_table.currentRow()
        if selected_row >= 0:
            self.entries_table.removeRow(selected_row)
            if selected_row < len(self.time_entries):
                self.time_entries.pop(selected_row)
    
    def save_changes(self):
        """Save changes to the timesheet entry"""
        # Get values from form
        client = self.client_input.text().strip()
        work_type = self.work_type_input.currentText().strip()
        tier = self.tier_input.currentText().strip()
        engineer_name = self.engineer_name_input.text().strip()
        engineer_surname = self.engineer_surname_input.text().strip()
        status = self.status_input.currentText()
        
        # Update time entries with current date widget values
        for i in range(len(self.time_entries)):
            if i < self.entries_table.rowCount():
                date_widget = self.entries_table.cellWidget(i, 0)
                if date_widget and isinstance(date_widget, QDateEdit):
                    self.time_entries[i]['date'] = date_widget.date().toString("yyyy/MM/dd")
        
        # Validate
        if not client:
            QMessageBox.warning(self, "Validation Error", "Please enter a client name.")
            return
            
        if not engineer_name or not engineer_surname:
            QMessageBox.warning(self, "Validation Error", "Please enter engineer name and surname.")
            return
            
        if not self.time_entries:
            QMessageBox.warning(self, "Validation Error", "Please add at least one time entry.")
            return
        
        # Update entry object
        self.entry.client = client
        self.entry.work_type = work_type
        self.entry.tier = tier
        self.entry.engineer_name = engineer_name
        self.entry.engineer_surname = engineer_surname
        self.entry.status = status
        self.entry.time_entries = self.time_entries.copy()
        
        # Save to data file
        if self.data_manager.update_entry(self.entry):
            QMessageBox.information(self, "Success", "Timesheet entry updated successfully.")
            self.entry_updated.emit(self.entry_id)
        else:
            QMessageBox.critical(self, "Error", "Failed to update timesheet entry.")
    
    def cancel_changes(self):
        """Cancel editing and close tab"""
        reply = QMessageBox.question(
            self, "Confirm Cancel",
            "Cancel editing? Any unsaved changes will be lost.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.entry_updated.emit(self.entry_id)
