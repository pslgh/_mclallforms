"""
View Tab - For viewing timesheet entry details
"""
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QScrollArea, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QFont, QBrush

class ViewTab(QWidget):
    """Tab for viewing timesheet entry details"""
    
    # Signal for closing the tab
    close_requested = Signal()
    
    def __init__(self, parent, entry, data_manager):
        super().__init__(parent)
        self.parent = parent
        self.entry = entry
        self.data_manager = data_manager
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create a scroll area for the content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Header with entry ID
        header_layout = QHBoxLayout()
        
        header_label = QLabel(f"Timesheet Entry: {self.entry.entry_id}")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        
        # Status label
        status_label = QLabel(f"Status: {self.entry.status.upper()}")
        status_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(status_label)
        
        scroll_layout.addLayout(header_layout)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        scroll_layout.addWidget(separator)
        
        # Client Information Section
        client_group = QGroupBox("Client Information")
        client_layout = QFormLayout(client_group)
        
        client_layout.addRow("Client:", QLabel(self.entry.client))
        client_layout.addRow("Work Type:", QLabel(self.entry.work_type))
        client_layout.addRow("Tier:", QLabel(self.entry.tier))
        
        scroll_layout.addWidget(client_group)
        
        # Engineer Information Section
        engineer_group = QGroupBox("Engineer Information")
        engineer_layout = QFormLayout(engineer_group)
        
        engineer_name = f"{self.entry.engineer_name} {self.entry.engineer_surname}"
        engineer_layout.addRow("Engineer:", QLabel(engineer_name))
        engineer_layout.addRow("Created By:", QLabel(self.entry.created_by))
        engineer_layout.addRow("Creation Date:", QLabel(self.entry.creation_date))
        
        scroll_layout.addWidget(engineer_group)
        
        # Time Entries Section
        time_entries_group = QGroupBox("Time Entries")
        time_entries_layout = QVBoxLayout(time_entries_group)
        
        # Set up the entries table
        self.entries_table = QTableWidget(0, 6)
        self.entries_table.setHorizontalHeaderLabels(["Date", "Start Time", "End Time", "Rest Hours", "Description", "OT Rate"])
        self.entries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.entries_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        # Add entries to table
        for entry in self.entry.time_entries:
            row = self.entries_table.rowCount()
            self.entries_table.insertRow(row)
            
            # Add entry data to table
            start_time = entry.get('start_time', '')
            end_time = entry.get('end_time', '')
            date_str = entry.get('date', '')
            start_time_display = f"{start_time[:2]}:00" if len(start_time) >= 2 else start_time
            end_time_display = f"{end_time[:2]}:00" if len(end_time) >= 2 else end_time
            
            # All items are non-editable in view mode
            date_item = QTableWidgetItem(date_str)
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            date_item.setForeground(QBrush(Qt.black))
            
            start_item = QTableWidgetItem(start_time_display)
            start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
            start_item.setForeground(QBrush(Qt.black))
            
            end_item = QTableWidgetItem(end_time_display)
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
            
            self.entries_table.setItem(row, 0, date_item)
            self.entries_table.setItem(row, 1, start_item)
            self.entries_table.setItem(row, 2, end_item)
            self.entries_table.setItem(row, 3, rest_item)
            self.entries_table.setItem(row, 4, desc_item)
            self.entries_table.setItem(row, 5, ot_item)
        
        time_entries_layout.addWidget(self.entries_table)
        
        scroll_layout.addWidget(time_entries_group)
        
        # Summary Section
        summary_group = QGroupBox("Summary")
        summary_layout = QFormLayout(summary_group)
        
        # Calculate hours
        hours = self.entry.calculate_total_hours()
        
        summary_layout.addRow("Regular Hours:", QLabel(f"{hours['regular']:.1f}"))
        summary_layout.addRow("OT1 Hours:", QLabel(f"{hours['ot1']:.1f}"))
        summary_layout.addRow("OT1.5 Hours:", QLabel(f"{hours['ot15']:.1f}"))
        
        # Total with bold font
        total_label = QLabel(f"{hours['total']:.1f}")
        total_font = QFont()
        total_font.setBold(True)
        total_label.setFont(total_font)
        summary_layout.addRow("Total Hours:", total_label)
        
        scroll_layout.addWidget(summary_group)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        
        edit_button = QPushButton("Edit")
        edit_button.clicked.connect(self.edit_entry)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.close_requested.emit)
        
        export_button = QPushButton("Export PDF")
        export_button.clicked.connect(self.export_to_pdf)
        
        button_layout.addWidget(edit_button)
        button_layout.addWidget(export_button)
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        scroll_layout.addLayout(button_layout)
        scroll_layout.addStretch()
        
        # Set the scroll widget
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
    
    def edit_entry(self):
        """Request to edit this entry"""
        self.parent.edit_entry(self.entry.entry_id)
        self.close_requested.emit()
    
    def export_to_pdf(self):
        """Export the timesheet entry to PDF"""
        # This is a placeholder for PDF export functionality
        # In a real implementation, you would create a PDF with reportlab
        # similar to how it's done in the expense module
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "Export PDF", 
            "PDF export functionality will be implemented soon."
        )
