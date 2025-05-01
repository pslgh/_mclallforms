"""
Entry Tab - For creating new timesheet entries using direct edit table
"""
import os
import uuid
import datetime
import json
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QTableWidget, QTableWidgetItem, 
    QAbstractItemView, QHeaderView, QLabel, QComboBox, QDateEdit, QTimeEdit, QTextEdit, 
    QLineEdit, QSpinBox, QDoubleSpinBox, QPushButton, QMessageBox, QCheckBox, QGroupBox,
    QScrollArea, QSizePolicy, QFrame, QLayout, QFormLayout, QStyledItemDelegate
)
from PySide6.QtCore import Qt, Signal, QDate
from PySide6.QtGui import QPalette, QBrush, QFont

# Custom delegate for top alignment of all cells
class TopAlignDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Ensure alignment is top-left for all cells
        option.displayAlignment = Qt.AlignTop | Qt.AlignLeft
        super().paint(painter, option, index)
        
    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        option.displayAlignment = Qt.AlignTop | Qt.AlignLeft

# Custom delegate for text fields with word wrap
class TextEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QTextEdit(parent)
        editor.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole) or ""
        editor.setText(value)
        
    def setModelData(self, editor, model, index):
        model.setData(index, editor.toPlainText(), Qt.EditRole)
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)
        
    def sizeHint(self, option, index):
        # Ensure cells with text editors have enough height
        size = super().sizeHint(option, index)
        size.setHeight(60)  # Minimum height for text cells
        return size

# Custom delegate for date editing
class DateEditDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QDateEdit(parent)
        editor.setCalendarPopup(True)
        editor.setDisplayFormat("ddd, yyyy/MM/dd")
        
        # Set white background for better visibility
        editor.setStyleSheet("QDateEdit { background-color: white; color: black; }")
        
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        try:
            if value:
                # Try to parse the date with different potential formats
                if "," in value:  # New format with day name
                    # Extract just the date part after the comma
                    date_part = value.split(", ", 1)[1] if ", " in value else value
                    date_obj = datetime.datetime.strptime(date_part, "%Y/%m/%d").date()
                elif "/" in value:  # Old format with slash
                    date_obj = datetime.datetime.strptime(value, "%Y/%m/%d").date()
                else:  # Fall back to dash format
                    date_obj = datetime.datetime.strptime(value, "%Y-%m-%d").date()
                editor.setDate(date_obj)
            else:
                editor.setDate(datetime.datetime.now().date())
        except (ValueError, TypeError):
            editor.setDate(datetime.datetime.now().date())
        
    def setModelData(self, editor, model, index):
        date_str = editor.date().toString("ddd, yyyy/MM/dd")
        model.setData(index, date_str, Qt.EditRole)
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

# Custom delegate for combo boxes
class ComboBoxDelegate(QStyledItemDelegate):
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
        
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(self.items)
        editor.setStyleSheet("QComboBox { background-color: white; color: black; }")
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value:
            idx = editor.findText(value)
            if idx >= 0:
                editor.setCurrentIndex(idx)
        
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

# Custom delegate for hour selection
class HourComboDelegate(QStyledItemDelegate):
    def __init__(self, min_hour=0, max_hour=24, parent=None):
        super().__init__(parent)
        self.min_hour = min_hour
        self.max_hour = max_hour
        
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        for hour in range(self.min_hour, self.max_hour + 1):
            editor.addItem(f"{hour:02d}:00", hour)
        editor.setStyleSheet("QComboBox { background-color: white; color: black; }")
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        if value:
            idx = editor.findText(value)
            if idx >= 0:
                editor.setCurrentIndex(idx)
        
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
        model.setData(index, editor.currentData(), Qt.UserRole)
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

# Custom delegate for spin boxes (Rest Hours)
class SpinBoxDelegate(QStyledItemDelegate):
    def __init__(self, min_value=0, max_value=8, parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        
    def createEditor(self, parent, option, index):
        editor = QSpinBox(parent)
        editor.setMinimum(self.min_value)
        editor.setMaximum(self.max_value)
        editor.setStyleSheet("QSpinBox { background-color: white; color: black; }")
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        try:
            editor.setValue(int(value) if value else 0)
        except (ValueError, TypeError):
            editor.setValue(0)
        
    def setModelData(self, editor, model, index):
        model.setData(index, str(editor.value()), Qt.EditRole)
        model.setData(index, editor.value(), Qt.UserRole)
        
    def updateEditorGeometry(self, editor, option, index):
        editor.setGeometry(option.rect)

class EntryTab(QWidget):
    """Tab for creating new timesheet entries with direct table editing"""
    # Signal to notify when a timesheet is saved
    entry_saved = Signal(str)  # Emits the timesheet ID
    
    def __init__(self, parent, user_info, data_manager):
        super(EntryTab, self).__init__(parent)
        self.parent = parent
        self.user_info = user_info
        self.data_manager = data_manager
        self.time_entries = []
        self.updating_cell = False  # Flag to prevent recursive update calls
        
        # Import QTimer here to avoid circular imports
        from PySide6.QtCore import QTimer
        self.update_timer = QTimer()
        
        self.setup_ui()
        self.connect_signals()
        
    def connect_signals(self):
        """Connect signals to slots after UI setup"""
        # Connect signals for calculation
        self.service_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.tool_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.tl_short_input.valueChanged.connect(self.calculate_total_cost)
        self.tl_long_input.valueChanged.connect(self.calculate_total_cost)
        self.offshore_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.emergency_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.transport_charge_input.valueChanged.connect(self.calculate_total_cost)
        self.emergency_request_input.currentIndexChanged.connect(self.calculate_total_cost)
        self.report_hours_input.valueChanged.connect(self.calculate_total_cost)
        self.currency_input.currentIndexChanged.connect(self.calculate_total_cost)
        
        # Initialize the tool summary AFTER all UI elements have been created
        # This ensures tools_used_label exists when we try to update it
        from PySide6.QtCore import QTimer
        QTimer.singleShot(100, self.update_tool_summary_direct)
        
    def setup_table_delegates(self):
        """Set up the delegates for the table columns"""
        # Set top alignment for all cells as the default delegate
        self.entries_table.setItemDelegate(TopAlignDelegate(self))
        
        # Date column uses date delegate
        self.entries_table.setItemDelegateForColumn(0, DateEditDelegate(self))
        
        # Start time uses hour delegate
        start_delegate = HourComboDelegate(0, 24, self)
        self.entries_table.setItemDelegateForColumn(1, start_delegate)
        
        # End time uses hour delegate
        self.entries_table.setItemDelegateForColumn(2, HourComboDelegate(1, 24, self))
        
        # Rest hours uses spin box delegate
        self.entries_table.setItemDelegateForColumn(3, SpinBoxDelegate(0, 8, self))
        
        # Description uses text edit delegate
        self.entries_table.setItemDelegateForColumn(4, TextEditDelegate(self))
        
        # OT Rate uses numeric value delegate
        self.entries_table.setItemDelegateForColumn(5, ComboBoxDelegate(["1", "1.5", "2"], self))
        
        # Offshore column uses combo box delegate with Yes/No options
        self.entries_table.setItemDelegateForColumn(6, ComboBoxDelegate(["No", "Yes"], self))
        
        # T&L column uses combo box delegate with Yes/No options (Yes first)
        self.entries_table.setItemDelegateForColumn(7, ComboBoxDelegate(["Yes", "No"], self))
        
        # <80km column uses combo box delegate with Yes/No options (Yes first)
        self.entries_table.setItemDelegateForColumn(8, ComboBoxDelegate(["Yes", "No"], self))
        
        # >80km column uses combo box delegate with Yes/No options (No first)
        self.entries_table.setItemDelegateForColumn(9, ComboBoxDelegate(["No", "Yes"], self))
        
        # Equivalent Hours is read-only and calculated
        
    def setup_tool_delegates(self):
        """Set up the delegates for the tool table columns"""
        # Tool column uses combo box delegate
        tool_options = ["AS-1250FE", "AS-320", "T-Wave T8"]
        self.tool_table.setItemDelegateForColumn(0, ComboBoxDelegate(tool_options, self))
        
        # Amount column uses spin box delegate
        self.tool_table.setItemDelegateForColumn(1, SpinBoxDelegate(1, 999, self))
        
        # Start date column uses date delegate
        self.tool_table.setItemDelegateForColumn(2, DateEditDelegate(self))
        
        # End date column uses date delegate
        self.tool_table.setItemDelegateForColumn(3, DateEditDelegate(self))
        
        # Total Days column is read-only and calculated
    
    def setup_ui(self):
        """Create the UI components with optimized direct-edit table"""
        self_layout = QVBoxLayout(self)
        self_layout.setContentsMargins(0, 0, 0, 0)
        self_layout.setSpacing(0)
        
        # Create a scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create a widget to hold all the content
        content_widget = QWidget()
        content_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create the main layout for all the content
        main_layout = QVBoxLayout(content_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # Create all summary labels so they can be referenced later
        self.total_hours_label = QLabel("Total Hours: 0.0")
        self.regular_hours_label = QLabel("Regular Hours: 0.0")
        self.ot15_hours_label = QLabel("OT 1.5x Hours: 0.0")
        self.ot20_hours_label = QLabel("OT 2.0x Hours: 0.0")
        self.equivalent_hours_label = QLabel("Equivalent Hours: 0.0")
        self.total_tool_days_label = QLabel("Total Tool Days: 0")
        
        # Create project info group
        client_group = QGroupBox("Project Information")
        client_layout = QVBoxLayout(client_group)
        
        # Define light yellow background style for all input fields
        input_style = "background-color: #FFFFD0; color: black; padding: 4px;"
        input_client_style = "background-color: #FFFFD0; color: black; padding: 4px; min-width: 600px;"
        input_boolean_style = "background-color: #FFFFD0; color: black; padding: 4px; min-width: 50px;"
        input_worktype_style = "background-color: #FFFFD0; color: black; padding: 4px; min-width: 180px;"
        input_project_style = "background-color: #FFFFD0; color: black; padding: 4px; min-width: 600px;"

        # Create top row layout for PO/quotation information
        client_po_row = QHBoxLayout()
        client_po_row.setSpacing(10)
        
        # Add PO, quotation, and contract fields to the first row
        po_label = QLabel("Purchasing Order Number:")
        self.po_number_input = QLineEdit()
        self.po_number_input.setStyleSheet(input_style)
        
        quotation_label = QLabel("Quotation Number:")
        self.quotation_number_input = QLineEdit()
        self.quotation_number_input.setStyleSheet(input_style)
        
        contract_label = QLabel("Under Contract Agreement?")
        self.contract_agreement_input = QComboBox()
        self.contract_agreement_input.addItems(["No", "Yes"])
        self.contract_agreement_input.setStyleSheet(f"QComboBox {{ {input_boolean_style} }}")
        
        # Create emergency request dropdown
        emergency_label = QLabel("Emergency Request?")
        self.emergency_request_input = QComboBox()
        self.emergency_request_input.addItems(["No", "Yes"])
        self.emergency_request_input.setStyleSheet(f"QComboBox {{ {input_boolean_style} }}")
        
        # Add fields to the first row
        client_po_row.addWidget(po_label)
        client_po_row.addWidget(self.po_number_input)
        client_po_row.addWidget(quotation_label)
        client_po_row.addWidget(self.quotation_number_input)
        client_po_row.addWidget(contract_label)
        client_po_row.addWidget(self.contract_agreement_input)
        client_po_row.addWidget(emergency_label)
        client_po_row.addWidget(self.emergency_request_input)
        
        # Create project name row - full width row after client info
        project_name_row = QHBoxLayout()
        project_name_row.setSpacing(10)
        
        # Create widgets for project name
        project_name_label = QLabel("Project Name:")
        self.project_name_input = QLineEdit()
        self.project_name_input.setStyleSheet(input_project_style)
        self.project_name_input.setMinimumWidth(600)  # Increased by 200% from 300px
        
        # Add project name to row
        project_name_row.addWidget(project_name_label)
        project_name_row.addWidget(self.project_name_input)
        project_name_row.addStretch(1)  # Add stretch to push everything to the left
        
        # Create second row for client name
        client_row = QHBoxLayout()
        client_row.setSpacing(10)
        
        # Create widgets for client info
        client_label = QLabel("Client:")
        self.client_input = QLineEdit()
        self.client_input.setStyleSheet(input_client_style)
        self.client_input.setMinimumWidth(600)  # Increased by 200% from default 300px width
        
        # Add client name to second row
        client_row.addWidget(client_label)
        client_row.addWidget(self.client_input)
        client_row.addStretch(1)  # Add stretch to push everything to the left
        
        # Create a row for client address (left) and representative (right)
        client_address_row = QHBoxLayout()
        client_address_row.setSpacing(10)
        
        # Left side - Client Address
        address_layout = QVBoxLayout()
        client_address_label = QLabel("Address:")
        address_layout.addWidget(client_address_label)
        
        self.client_address_input = QTextEdit()
        self.client_address_input.setFixedHeight(110)  # Taller to match height with representative fields
        self.client_address_input.setStyleSheet(input_style)
        address_layout.addWidget(self.client_address_input)
        
        # Right side - Client Representative, Phone, Email
        rep_layout = QFormLayout()
        rep_layout.setContentsMargins(20, 0, 0, 0)  # Add margin on left
        
        # Client Representative
        self.client_rep_input = QLineEdit()
        self.client_rep_input.setStyleSheet(input_style)
        rep_layout.addRow("Client Representative:", self.client_rep_input)
        
        # Phone Number
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setStyleSheet(input_style)
        rep_layout.addRow("Phone Number:", self.client_phone_input)
        
        # Email
        self.client_email_input = QLineEdit()
        self.client_email_input.setStyleSheet(input_style)
        rep_layout.addRow("Email:", self.client_email_input)
        
        # Add both layouts to the row
        client_address_row.addLayout(address_layout, 1)  # Give more space to address
        client_address_row.addLayout(rep_layout, 1)
        
        # Create Project Description/Service Engineer row - matching the layout image
        project_desc_engineer_row = QHBoxLayout()
        project_desc_engineer_row.setSpacing(10)
        
        # Left side - Project Description
        project_desc_layout = QVBoxLayout()
        project_desc_layout.setSpacing(10)
        
        project_description_label = QLabel("Project Description:")
        project_desc_layout.addWidget(project_description_label)
        
        self.project_description_input = QTextEdit()
        self.project_description_input.setFixedHeight(120)  # Taller to match height with engineer fields
        self.project_description_input.setStyleSheet(input_style)
        project_desc_layout.addWidget(self.project_description_input)
        
        # Right side - Service Engineer info
        engineer_layout = QFormLayout()
        engineer_layout.setSpacing(10)
        engineer_layout.setContentsMargins(20, 0, 0, 0)  # Add margin on left
        
        # Create widgets for engineer info
        self.engineer_name_input = QLineEdit()
        self.engineer_name_input.setStyleSheet(input_style)
        if self.user_info and 'first_name' in self.user_info:
            self.engineer_name_input.setText(self.user_info['first_name'])
        
        self.engineer_surname_input = QLineEdit()
        self.engineer_surname_input.setStyleSheet(input_style)
        if self.user_info and 'last_name' in self.user_info:
            self.engineer_surname_input.setText(self.user_info['last_name'])
        
        self.work_type_input = QComboBox()
        self.work_type_input.addItems(["Special Field Services", "Regular Field Services", "Consultation", "Emergency Support", "Other"])
        self.work_type_input.setCurrentIndex(0)  # Set default to "Special Field Services"
        self.work_type_input.setEditable(True)
        self.work_type_input.setStyleSheet(f"QComboBox {{ {input_worktype_style} }}")
        
        # Add fields to form layout
        engineer_layout.addRow("Service Engineer Name:", self.engineer_name_input)
        engineer_layout.addRow("Surname:", self.engineer_surname_input)
        engineer_layout.addRow("Work Type:", self.work_type_input)
        
        # Add both sides to the row
        project_desc_engineer_row.addLayout(project_desc_layout, 1)  # Give more space to project description
        project_desc_engineer_row.addLayout(engineer_layout, 1)
        
        # Add all rows to client layout in the correct order
        client_layout.addLayout(client_po_row)  # First row: PO, Quotation, Agreement, Emergency
        client_layout.addLayout(client_row)  # Second row: Client
        client_layout.addLayout(client_address_row)  # Third row: Address and Client Representative info
        client_layout.addLayout(project_name_row)  # Fourth row: Project Name (full width)
        client_layout.addLayout(project_desc_engineer_row)  # Fifth row: Project Description with Service Engineer
        
        # Add client group to main layout
        main_layout.addWidget(client_group)
        
        # Create Time Entries Group with editable table
        entries_group = QGroupBox("Time Entries")
        entries_container_layout = QHBoxLayout(entries_group)  # Container for table and summary, set as the group's layout
        entries_layout = QVBoxLayout()
        
        # Create table for direct editing of time entries
        self.entries_table = QTableWidget(0, 11)  # 11 columns with two travel distance columns
        self.entries_table.setHorizontalHeaderLabels([
            "Date", "Start Time", "End Time", "Rest Hours", 
            "Description", "OT Rate", "Offshore?", "T&L?", "<80km", ">80km", "Equivalent Hours"
        ])
        
        # Set up column widths and stretching
        self.entries_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)  # Description stretches
        for col in [0, 1, 2, 3, 5, 6, 7, 8, 9]:  # Set fixed width for other columns
            self.entries_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        
        # Set smaller row height with fixed size
        self.entries_table.verticalHeader().setDefaultSectionSize(40)  # Reduced from 80 to 40
        self.entries_table.verticalHeader().setSectionResizeMode(QHeaderView.Fixed)  # Use fixed height instead of auto-expansion
        
        # Set minimum height for the table to ensure multiple rows are visible
        self.entries_table.setMinimumHeight(350)
        
        # Set the text alignment to top for all cells
        for col in range(self.entries_table.columnCount()):
            self.entries_table.horizontalHeaderItem(col).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
        # Make the table items' text align to the top
        self.entries_table.setStyleSheet(self.entries_table.styleSheet() + """
            QTableWidget::item {
                padding: 1px;
                alignment: top;
                margin: 0px;
            }
            QTableWidget QAbstractItemView {
                alignment: top;
            }
        """)
        
        # Set the item delegate to handle alignment
        for col in range(self.entries_table.columnCount()):
            self.entries_table.setItemDelegateForColumn(col, TopAlignDelegate(self))
        
        # Ensure consistent minimum width for better presentation
        self.entries_table.setMinimumWidth(800)
        
        # Setup delegates for each column type
        self.setup_table_delegates()
        
        # Set table properties
        # Add background color to table
        self.entries_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #C0C0C0;
                alternate-background-color: #F2F2F2;
                background-color: white;
                color: black;
            }
            QTableWidget::item { padding: 1px; margin: 0px; }
            QHeaderView::section { 
                background-color: #E0E0E0;
                color: black;
                padding: 4px;
                border: 1px solid #C0C0C0;
            }
        """)
        self.entries_table.setAlternatingRowColors(True)
        
        # Connect cell changed signal
        self.entries_table.cellChanged.connect(self.on_cell_changed)
        
        # Add to group layout
        entries_layout.addWidget(self.entries_table)
        
        # Add button row to entries layout
        button_layout = QHBoxLayout()
        
        # Add Row button
        add_row_button = QPushButton("Add Row")
        add_row_button.clicked.connect(self.add_new_row)
        
        # Remove Selected Row button
        remove_row_button = QPushButton("Remove Selected Row")
        remove_row_button.clicked.connect(self.remove_selected_row)
        
        # Buttons removed as requested
        
        # Add buttons to layout
        button_layout.addWidget(add_row_button)
        button_layout.addWidget(remove_row_button)
        button_layout.addStretch(1)  # Maintain layout spacing
        
        # Add button layout to entries layout
        entries_layout.addLayout(button_layout)
        
        # Add table layout to container layout
        entries_container_layout.addLayout(entries_layout, 1)
        
        # Add entries group to main layout
        main_layout.addWidget(entries_group)
        
        # Create Special Tool Usage Group with table
        tool_usage_group = QGroupBox("Special Tool Usage")
        tool_container_layout = QHBoxLayout(tool_usage_group)
        tool_layout = QVBoxLayout()
        
        # Increase height of the Special Tool Usage groupbox by 200%
        tool_usage_group.setMinimumHeight(200)  # Set a larger minimum height
        # Make sure the content expands to fill the space
        tool_usage_group.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Create table for tool usage
        self.tool_table = QTableWidget(0, 5)  # 5 columns
        self.tool_table.setHorizontalHeaderLabels([
            "Tool", "Amount", "Start Date", "End Date", "Total Days"
        ])
        
        # Set up column widths for a more professional appearance
        self.tool_table.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)  # Set all columns to fixed first
        
        # Set specific column widths in pixels
        self.tool_table.setColumnWidth(0, 150)  # Tool column - wider for dropdown
        self.tool_table.setColumnWidth(1, 80)   # Amount column - narrower for numbers
        self.tool_table.setColumnWidth(2, 120)  # Start Date column
        self.tool_table.setColumnWidth(3, 120)  # End Date column
        self.tool_table.setColumnWidth(4, 100)  # Total Days column
        
        # Set minimum width for the table itself
        self.tool_table.setMinimumWidth(600)
        
        # Apply enhanced styling to the tool table for professional look
        self.tool_table.setStyleSheet("""
            QTableWidget { 
                gridline-color: #d0d0d0; 
                background-color: white;
                alternate-background-color: #f9f9f9;
                selection-background-color: #e0e0e0;
            }
            QTableWidget::item { 
                color: black;
                padding: 4px;
            }
            QHeaderView::section { 
                background-color: #f0f0f0; 
                color: black; 
                padding: 6px;
                border: 1px solid #d0d0d0;
                font-weight: bold;
            }
        """)
        self.tool_table.setAlternatingRowColors(True)
        self.tool_table.verticalHeader().setDefaultSectionSize(40)  # Set appropriate row height
        
        # Set up delegates for tool table
        self.setup_tool_delegates()
        
        # Connect signals for tool table with explicit column handling
        self.tool_table.cellChanged.connect(self.on_tool_cell_changed)
        
        # Make sure the tool summary is updated when the table gets focus
        # This helps catch any external changes
        self.tool_table.itemSelectionChanged.connect(self.update_tool_summary_direct)
        
        # Add table to tool layout
        tool_layout.addWidget(self.tool_table)
        
        # Button layout for tool table
        tool_button_layout = QHBoxLayout()
        
        # Add tool button
        add_tool_button = QPushButton("Add Tool")
        add_tool_button.clicked.connect(self.add_new_tool_row)
        
        # Remove tool button
        remove_tool_button = QPushButton("Remove Selected Tool")
        remove_tool_button.clicked.connect(self.remove_selected_tool)
        
        # Add buttons to layout
        tool_button_layout.addWidget(add_tool_button)
        tool_button_layout.addWidget(remove_tool_button)
        tool_button_layout.addStretch(1)
        
        # Add button layout to tool layout
        tool_layout.addLayout(tool_button_layout)
        
        # Define label variables for tool usage tracking (not displayed in UI now)
        self.total_tools_label = QLabel("Total Tools: 0")
        self.as1250fe_count_label = QLabel("AS-1250FE: 0")
        self.as320_count_label = QLabel("AS-320: 0")
        self.twave_count_label = QLabel("T-Wave T8: 0")
        self.total_days_label = QLabel("Total Usage Days: 0")
        
        # Add tool table layout to container layout
        tool_container_layout.addLayout(tool_layout, 1)
        
        # Add tool usage group to main layout
        main_layout.addWidget(tool_usage_group)
        
        # Create Report Preparation Hour Group
        report_group = QGroupBox("Report Preparation Hour")
        report_layout = QVBoxLayout(report_group)
        
        # Create description input
        description_label = QLabel("Report Description:")
        self.report_description_input = QTextEdit()
        self.report_description_input.setPlaceholderText("Enter description of the report preparation work")
        self.report_description_input.setMaximumHeight(100)
        
        # Create hours input with spin box
        hours_layout = QHBoxLayout()
        hours_label = QLabel("Report Preparation Hours:")
        self.report_hours_input = QSpinBox()
        self.report_hours_input.setRange(0, 100)  # Allow up to 100 hours
        self.report_hours_input.setValue(0)  # Default to 0
        self.report_hours_input.setSingleStep(1)  # Increment by 1
        
        # Style the spin box
        self.report_hours_input.setStyleSheet("""
            QSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 80px;
            }
        """)
        
        # Add to hours layout
        hours_layout.addWidget(hours_label)
        hours_layout.addWidget(self.report_hours_input)
        hours_layout.addStretch(1)  # Push to the left
        
        # Add widgets to the layout
        report_layout.addWidget(description_label)
        report_layout.addWidget(self.report_description_input)
        report_layout.addLayout(hours_layout)
        
        # Add report group to main layout
        main_layout.addWidget(report_group)
        
        # Create Service Charge Calculation Group
        service_charge_group = QGroupBox("Service Charge Calculation")
        service_charge_layout = QVBoxLayout(service_charge_group)
        
        # Create Service Rate groupbox
        rate_group = QGroupBox("Service Rate")
        rate_layout = QGridLayout(rate_group)
        
        # Currency selection
        currency_label = QLabel("Currency:")
        self.currency_input = QComboBox()
        self.currency_input.addItems(["THB", "USD"])
        self.currency_input.setStyleSheet("""
            QComboBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
            }
        """)
        # Connect the currency change signal to update the rates
        self.currency_input.currentTextChanged.connect(self.update_default_rates)
        rate_layout.addWidget(currency_label, 0, 0)
        rate_layout.addWidget(self.currency_input, 0, 1)
        
        # Normal Service Hour Rate
        service_rate_label = QLabel("Normal Service Hour Rate:")
        self.service_rate_input = QDoubleSpinBox()
        self.service_rate_input.setRange(0, 1000000)
        self.service_rate_input.setValue(0)
        self.service_rate_input.setSingleStep(100)
        self.service_rate_input.setDecimals(2)
        self.service_rate_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #ffffcc; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(service_rate_label, 1, 0)
        rate_layout.addWidget(self.service_rate_input, 1, 1)
        
        # Special Tools Usage Rate
        tool_rate_label = QLabel("Data Acquisition, Diagnostics Instrument Usage Rate:")
        self.tool_rate_input = QDoubleSpinBox()
        self.tool_rate_input.setRange(0, 1000000)
        self.tool_rate_input.setValue(0)
        self.tool_rate_input.setSingleStep(100)
        self.tool_rate_input.setDecimals(2)
        self.tool_rate_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(tool_rate_label, 2, 0)
        rate_layout.addWidget(self.tool_rate_input, 2, 1)
        
        # < 80 km T&L Rate
        tl_short_label = QLabel("< 80 km T&L Rate:")
        self.tl_short_input = QDoubleSpinBox()
        self.tl_short_input.setRange(0, 1000000)
        self.tl_short_input.setValue(0)
        self.tl_short_input.setSingleStep(100)
        self.tl_short_input.setDecimals(2)
        self.tl_short_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(tl_short_label, 3, 0)
        rate_layout.addWidget(self.tl_short_input, 3, 1)
        
        # > 80 km T&L Rate
        tl_long_label = QLabel("> 80 km T&L Rate:")
        self.tl_long_input = QDoubleSpinBox()
        self.tl_long_input.setRange(0, 1000000)
        self.tl_long_input.setValue(0)
        self.tl_long_input.setSingleStep(100)
        self.tl_long_input.setDecimals(2)
        self.tl_long_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(tl_long_label, 4, 0)
        rate_layout.addWidget(self.tl_long_input, 4, 1)
        
        # Addition Day Rate for Offshore Work
        offshore_label = QLabel("Addition Day Rate for Offshore Work:")
        self.offshore_rate_input = QDoubleSpinBox()
        self.offshore_rate_input.setRange(0, 1000000)
        self.offshore_rate_input.setValue(0)
        self.offshore_rate_input.setSingleStep(100)
        self.offshore_rate_input.setDecimals(2)
        self.offshore_rate_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(offshore_label, 5, 0)
        rate_layout.addWidget(self.offshore_rate_input, 5, 1)
        
        # Emergency Request Rate
        emergency_label = QLabel("Emergency Request (<24H notification) Rate:")
        self.emergency_rate_input = QDoubleSpinBox()
        self.emergency_rate_input.setRange(0, 1000000)
        self.emergency_rate_input.setValue(0)
        self.emergency_rate_input.setSingleStep(100)
        self.emergency_rate_input.setDecimals(2)
        self.emergency_rate_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(emergency_label, 6, 0)
        rate_layout.addWidget(self.emergency_rate_input, 6, 1)
        
        # Other Transportation Charge
        transport_charge_label = QLabel("Other Transportation Charge:")
        self.transport_charge_input = QDoubleSpinBox()
        self.transport_charge_input.setRange(0, 1000000)
        self.transport_charge_input.setValue(0)
        self.transport_charge_input.setSingleStep(100)
        self.transport_charge_input.setDecimals(2)
        self.transport_charge_input.setStyleSheet("""
            QDoubleSpinBox { 
                background-color: #FFFFD0; 
                color: black;
                padding: 4px;
                min-width: 120px;
            }
            QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
                width: 0px;
                height: 0px;
            }
        """)
        rate_layout.addWidget(transport_charge_label, 7, 0)
        rate_layout.addWidget(self.transport_charge_input, 7, 1)
        
        # Other Transportation Charge Note
        transport_note_label = QLabel("Other Transportation Charge Note:")
        self.transport_note_input = QTextEdit()
        self.transport_note_input.setPlaceholderText("Enter notes about transportation charges")
        self.transport_note_input.setMaximumHeight(60)
        self.transport_note_input.setStyleSheet("""
            QTextEdit { 
                background-color: #FFFFD0; 
                color: black;
            }
        """)
        rate_layout.addWidget(transport_note_label, 8, 0)
        rate_layout.addWidget(self.transport_note_input, 8, 1)
        
        # Initialize the default rates based on the current currency
        self.update_default_rates(self.currency_input.currentText())
        
        # Create horizontal layout to hold rate group and summary groups side by side
        service_rate_summary_layout = QHBoxLayout()
        
        # Add rate group to the horizontal layout
        service_rate_summary_layout.addWidget(rate_group, 3)  # Give rate group 3 parts of width
        
        # Create vertical layout for summary groupboxes
        summary_groups_layout = QVBoxLayout()
        
        # Create Time Summary groupbox
        time_summary_group = QGroupBox("Time Summary")
        time_summary_layout = QHBoxLayout(time_summary_group)  # Use horizontal layout for sub-groupboxes
        
        # Style the time summary with bold and larger font
        summary_font = QFont()
        summary_font.setPointSize(10)
        summary_font.setBold(True)
        
        # Create left sub-groupbox for hours
        hours_group = QGroupBox("Hours")
        hours_layout = QVBoxLayout(hours_group)
        
        # Create hours summary labels
        self.regular_hours_label = QLabel("Total Regular Hours: 0.0")
        self.ot15_hours_label = QLabel("Total OT 1.5X Hours: 0.0")
        self.ot20_hours_label = QLabel("Total OT 2.0X Hours: 0.0")
        self.equivalent_hours_label = QLabel("Total Equivalent Hours: 0.0")
        
        # Apply font styling
        self.regular_hours_label.setFont(summary_font)
        self.ot15_hours_label.setFont(summary_font)
        self.ot20_hours_label.setFont(summary_font)
        self.equivalent_hours_label.setFont(summary_font)
        
        # Add hours labels to the left sub-groupbox
        hours_layout.addWidget(self.regular_hours_label)
        hours_layout.addWidget(self.ot15_hours_label)
        hours_layout.addWidget(self.ot20_hours_label)
        hours_layout.addWidget(self.equivalent_hours_label)
        
        # Create right sub-groupbox for days
        days_group = QGroupBox("Days")
        days_layout = QVBoxLayout(days_group)
        
        # Create days summary labels
        self.offshore_days_label = QLabel("Total Offshore Days: 0")
        self.tl_short_days_label = QLabel("Total T&L<80km Days: 0")
        self.tl_long_days_label = QLabel("Total T&L>80km Days: 0")
        
        # Apply font styling
        self.offshore_days_label.setFont(summary_font)
        self.tl_short_days_label.setFont(summary_font)
        self.tl_long_days_label.setFont(summary_font)
        
        # Add days labels to the right sub-groupbox
        days_layout.addWidget(self.offshore_days_label)
        days_layout.addWidget(self.tl_short_days_label)
        days_layout.addWidget(self.tl_long_days_label)
        days_layout.addStretch(1)  # Add stretch to align with the hours groupbox
        
        # Add both sub-groupboxes to the time summary layout
        time_summary_layout.addWidget(hours_group)
        time_summary_layout.addWidget(days_group)
        
        # Create Tool Usage Summary groupbox
        tool_summary_group = QGroupBox("Tool Usage Summary")
        tool_summary_layout = QVBoxLayout(tool_summary_group)
        
        # Create tool usage summary labels with None as default values
        self.tools_used_label = QLabel("Tools Used: None")
        self.total_tool_days_label = QLabel("Total Special Tools Usage Day: 0")
        
        # Apply font styling to the labels
        self.tools_used_label.setFont(summary_font)
        self.total_tool_days_label.setFont(summary_font)
        
        # Allow the tools_used_label to wrap text for long tool lists
        self.tools_used_label.setWordWrap(True)
        
        # Add tool usage summary labels to layout
        tool_summary_layout.addWidget(self.tools_used_label)
        tool_summary_layout.addWidget(self.total_tool_days_label)
        tool_summary_layout.addStretch(1)
        
        # Set special style for time_summary_group to align title in the middle
        time_summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: white;
            }
            QLabel { font-size: 10pt; color: black; }
        """)
        
        # Style tool summary groupbox
        tool_summary_group.setStyleSheet("""
            QGroupBox { 
                font-weight: bold;
                border: 1px solid #d0d0d0; 
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top center;
                padding: 0 5px;
                background-color: white;
            }
            QLabel { font-size: 10pt; color: black; }
        """)
        
        # Add summary groupboxes to vertical layout
        summary_groups_layout.addWidget(time_summary_group)
        summary_groups_layout.addWidget(tool_summary_group)
        
        # Add summary groups layout to the horizontal layout
        service_rate_summary_layout.addLayout(summary_groups_layout, 2)  # Give summary groupboxes 2 parts of width
        
        # Add the horizontal layout to the service charge layout
        service_charge_layout.addLayout(service_rate_summary_layout)
        
        # Create Calculation Group with a grid layout for better space utilization
        calc_group = QGroupBox("Total Cost Calculation")
        calc_layout = QVBoxLayout(calc_group)
        
        # Use a main horizontal layout to create two columns
        main_cost_layout = QHBoxLayout()
        
        # Left column: Subtotals
        left_column = QVBoxLayout()
        
        # Create subtotal grid for itemized costs
        subtotal_grid = QGridLayout()
        subtotal_grid.setHorizontalSpacing(15)  # Add spacing between label and value
        
        # Row 0: Service Hours Subtotal
        subtotal_grid.addWidget(QLabel("Service Hours:"), 0, 0)
        self.service_hours_subtotal = QLabel("0.00")
        self.service_hours_subtotal.setStyleSheet("font-weight: bold;")
        subtotal_grid.addWidget(self.service_hours_subtotal, 0, 1)
        
        # Row 1: Report Preparation Hours Subtotal
        subtotal_grid.addWidget(QLabel("Report Preparation Hours:"), 1, 0)
        self.report_hours_subtotal = QLabel("0.00")
        self.report_hours_subtotal.setStyleSheet("font-weight: bold;")
        subtotal_grid.addWidget(self.report_hours_subtotal, 1, 1)
        
        # Row 2: Special Tools Usage Subtotal
        subtotal_grid.addWidget(QLabel("Special Tools Usage:"), 2, 0)
        self.tool_usage_subtotal = QLabel("0.00")
        self.tool_usage_subtotal.setStyleSheet("font-weight: bold;")
        subtotal_grid.addWidget(self.tool_usage_subtotal, 2, 1)
        
        # Row 3: Travel & Living Subtotal
        subtotal_grid.addWidget(QLabel("Travel & Living:"), 3, 0)
        self.travel_subtotal = QLabel("0.00")
        self.travel_subtotal.setStyleSheet("font-weight: bold;")
        subtotal_grid.addWidget(self.travel_subtotal, 3, 1)
        
        # Add the grid to the left column
        left_column.addLayout(subtotal_grid)
        
        # Right column: Additional costs
        right_column = QVBoxLayout()
        right_grid = QGridLayout()
        right_grid.setHorizontalSpacing(15)  # Add spacing between label and value
        
        # Row 0: Offshore Work Subtotal
        right_grid.addWidget(QLabel("Offshore Work:"), 0, 0)
        self.offshore_subtotal = QLabel("0.00")
        self.offshore_subtotal.setStyleSheet("font-weight: bold;")
        right_grid.addWidget(self.offshore_subtotal, 0, 1)
        
        # Row 1: Emergency Request Subtotal
        right_grid.addWidget(QLabel("Emergency Request:"), 1, 0)
        self.emergency_subtotal = QLabel("0.00")
        self.emergency_subtotal.setStyleSheet("font-weight: bold;")
        right_grid.addWidget(self.emergency_subtotal, 1, 1)
        
        # Row 2: Other Transportation Charge Subtotal
        right_grid.addWidget(QLabel("Other Transportation:"), 2, 0)
        self.transport_subtotal = QLabel("0.00")
        self.transport_subtotal.setStyleSheet("font-weight: bold;")
        right_grid.addWidget(self.transport_subtotal, 2, 1)
        
        # Row 3: Subtotal (Before VAT and Discount)
        right_grid.addWidget(QLabel("Subtotal:"), 3, 0)
        self.subtotal_label = QLabel("0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        right_grid.addWidget(self.subtotal_label, 3, 1)
        
        # Add the grid to the right column
        right_column.addLayout(right_grid)
        
        # Add both columns to the main layout
        main_cost_layout.addLayout(left_column)
        main_cost_layout.addLayout(right_column)
        
        # Add the main layout to the calc layout
        calc_layout.addLayout(main_cost_layout)
        
        # Add a detailed calculation formula display
        self.formula_frame = QFrame()
        self.formula_frame.setFrameShape(QFrame.StyledPanel)
        self.formula_frame.setStyleSheet("background-color: #F8F8F8; padding: 5px; border: 1px solid #E0E0E0;")
        formula_layout = QVBoxLayout(self.formula_frame)
        
        # Title for the formula section
        formula_title = QLabel("Calculation Breakdown:")
        formula_title.setStyleSheet("font-weight: bold; text-decoration: underline;")
        formula_layout.addWidget(formula_title)
        
        # Create a text edit for the formula breakdown
        self.formula_details = QTextEdit()
        self.formula_details.setReadOnly(True)
        self.formula_details.setStyleSheet("background-color: #FFFFFF; color: black; font-family: monospace;")
        self.formula_details.setMaximumHeight(150)  # Slightly increased height for better visibility
        formula_layout.addWidget(self.formula_details)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        
        # Create VAT and Discount fields
        vat_discount_grid = QGridLayout()
        
        # Row 0: VAT %
        vat_discount_grid.addWidget(QLabel("VAT %:"), 0, 0)
        self.vat_percent_input = QDoubleSpinBox()
        self.vat_percent_input.setRange(0, 100)
        self.vat_percent_input.setValue(7)  # Default 7% VAT
        self.vat_percent_input.setSingleStep(0.1)
        self.vat_percent_input.setDecimals(2)
        self.vat_percent_input.valueChanged.connect(self.calculate_total_cost)
        self.vat_percent_input.setStyleSheet(f"background-color: #FFFFD0; color: black; padding: 4px;")
        vat_discount_grid.addWidget(self.vat_percent_input, 0, 1)
        
        # VAT Amount (calculated)
        vat_discount_grid.addWidget(QLabel("VAT Amount:"), 0, 2)
        self.vat_amount_label = QLabel("0.00")
        self.vat_amount_label.setStyleSheet("font-weight: bold;")
        vat_discount_grid.addWidget(self.vat_amount_label, 0, 3)
        
        # Row 1: Discount Amount
        vat_discount_grid.addWidget(QLabel("Discount Amount:"), 1, 0)
        self.discount_amount_input = QDoubleSpinBox()
        self.discount_amount_input.setRange(0, 1000000)
        self.discount_amount_input.setValue(0)
        self.discount_amount_input.setSingleStep(100)
        self.discount_amount_input.setDecimals(2)
        self.discount_amount_input.valueChanged.connect(self.calculate_total_cost)
        self.discount_amount_input.setStyleSheet(f"background-color: #FFFFD0; color: black; padding: 4px;")
        vat_discount_grid.addWidget(self.discount_amount_input, 1, 1)
        
        # Add another separator line
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        
        # Create grand total display
        self.total_cost_label = QLabel("Grand Total: 0.00")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.total_cost_label.setFont(font)
        
        # Create a compact layout for VAT and discount
        vat_discount_grid.setHorizontalSpacing(15)  # Add spacing between elements
        
        # Add separator before VAT/Discount section
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        calc_layout.addWidget(separator)
        
        # Add VAT/Discount section
        calc_layout.addLayout(vat_discount_grid)
        
        # Add separator after VAT/Discount section
        separator2 = QFrame()
        separator2.setFrameShape(QFrame.HLine)
        separator2.setFrameShadow(QFrame.Sunken)
        calc_layout.addWidget(separator2)
        
        # Add formula frame and total cost label
        calc_layout.addWidget(self.formula_frame)
        
        # Make the total cost label more prominent
        self.total_cost_label.setAlignment(Qt.AlignCenter)
        self.total_cost_label.setStyleSheet("font-weight: bold; font-size: 14pt; padding: 5px; margin-top: 5px;")
        calc_layout.addWidget(self.total_cost_label)
        
        # Make calculation automatic and responsive
        self.calculate_button = QPushButton("Refresh Calculation")
        self.calculate_button.clicked.connect(self.calculate_total_cost)
        calc_layout.addWidget(self.calculate_button)
        
        # Connect all inputs to auto-update the calculation
        self.service_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.tool_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.tl_short_input.valueChanged.connect(self.calculate_total_cost)
        self.tl_long_input.valueChanged.connect(self.calculate_total_cost)
        self.offshore_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.emergency_rate_input.valueChanged.connect(self.calculate_total_cost)
        self.transport_charge_input.valueChanged.connect(self.calculate_total_cost)
        self.currency_input.currentTextChanged.connect(self.calculate_total_cost)
        self.report_hours_input.valueChanged.connect(self.calculate_total_cost)
        self.emergency_request_input.currentTextChanged.connect(self.calculate_total_cost)
        
        # Add calculation group to service charge layout
        service_charge_layout.addWidget(calc_group)
        
        # Add the service charge group to main layout
        main_layout.addWidget(service_charge_group)
        
        # Create a new groupbox for Save and Clear buttons
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_group)
        
        # Create Save Timesheet button
        self.save_button = QPushButton("Save Timesheet")
        self.save_button.clicked.connect(self.save_timesheet)
        self.save_button.setMinimumHeight(40)
        self.save_button.setStyleSheet(
            "QPushButton {background-color: #4CAF50; color: white; font-weight: bold; border-radius: 4px; padding: 8px 16px;}"
            "QPushButton:hover {background-color: #45a049;}"
            "QPushButton:pressed {background-color: #388E3C;}"
        )
        
        # Create Clear Form button
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clear_form)
        self.clear_button.setMinimumHeight(40)
        self.clear_button.setStyleSheet(
            "QPushButton {background-color: #f44336; color: white; font-weight: bold; border-radius: 4px; padding: 8px 16px;}"
            "QPushButton:hover {background-color: #d32f2f;}"
            "QPushButton:pressed {background-color: #b71c1c;}"
        )
        
        # Add buttons to the action layout with spacing
        action_layout.addStretch(1)
        action_layout.addWidget(self.save_button)
        action_layout.addSpacing(20)  # Add space between buttons
        action_layout.addWidget(self.clear_button)
        action_layout.addStretch(1)
        
        # Add the action group to the main layout
        main_layout.addWidget(action_group)
        
        # Add some stretch to push everything to the top
        main_layout.addStretch(1)
        
        # Set the content widget as the scroll area's widget
        scroll_area.setWidget(content_widget)
        
        # Add the scroll area to the self layout
        self_layout.addWidget(scroll_area)
        
    def add_new_row(self):
        """Add a new empty row to the table"""
        row = self.entries_table.rowCount()
        self.entries_table.insertRow(row)
        
        # Set default values
        today_date = datetime.datetime.now().date()
        today = today_date.strftime("ddd, %Y/%m/%d").replace("ddd", today_date.strftime("%a"))
        
        # Create items with default values
        date_item = QTableWidgetItem(today)
        date_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        start_item = QTableWidgetItem("08:00")
        start_item.setData(Qt.UserRole, 8)  # Store the hour value
        start_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        end_item = QTableWidgetItem("09:00")
        end_item.setData(Qt.UserRole, 9)  # Store the hour value
        end_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        rest_item = QTableWidgetItem("0")
        rest_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        desc_item = QTableWidgetItem("")
        desc_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        ot_item = QTableWidgetItem("1")
        ot_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        offshore_item = QTableWidgetItem("No")
        offshore_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        travel_count_item = QTableWidgetItem("Yes")
        travel_count_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        travel_short_item = QTableWidgetItem("Yes")
        travel_short_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        travel_long_item = QTableWidgetItem("No")
        travel_long_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        equiv_item = QTableWidgetItem("1.0")
        equiv_item.setTextAlignment(Qt.AlignTop | Qt.AlignLeft)
        
        # Make equivalent hours column read-only
        equiv_item.setFlags(equiv_item.flags() & ~Qt.ItemIsEditable)
        equiv_item.setForeground(QBrush(Qt.black))
        
        # Set all items to the table
        self.entries_table.setItem(row, 0, date_item)
        self.entries_table.setItem(row, 1, start_item)
        self.entries_table.setItem(row, 2, end_item)
        self.entries_table.setItem(row, 3, rest_item)
        self.entries_table.setItem(row, 4, desc_item)
        self.entries_table.setItem(row, 5, ot_item)
        self.entries_table.setItem(row, 6, offshore_item)
        self.entries_table.setItem(row, 7, travel_count_item)
        self.entries_table.setItem(row, 8, travel_short_item)
        self.entries_table.setItem(row, 9, travel_long_item)
        self.entries_table.setItem(row, 10, equiv_item)
        
        # Calculate equivalent hours
        self.calculate_equivalent_hours(row)
        
        # Update summary display
        self.update_time_summary()
        
        # Update total cost calculation to reflect the added row
        self.calculate_total_cost()
    
    def remove_selected_row(self):
        """Remove the selected row from the table"""
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a row to remove.")
            return
            
        for index in sorted(selected_rows, reverse=True):
            self.entries_table.removeRow(index.row())
            
        # Update summary display
        self.update_time_summary()
        
        # Update total cost calculation to reflect removed row
        self.calculate_total_cost()
    
    def on_cell_changed(self, row, column):
        """Handle cell changes and recalculate values as needed"""
        if self.updating_cell:
            return
            
        self.updating_cell = True
        
        try:
            # If start time changed, ensure end time is valid
            if column == 1:  # Start time column
                self.validate_end_time(row)
            
            # If <80km column changed (column 8), update >80km column (column 9)
            if column == 8:  # <80km column
                tl_short_item = self.entries_table.item(row, 8)
                tl_long_item = self.entries_table.item(row, 9)
                
                if tl_short_item and tl_long_item:
                    # Make them mutually exclusive: if <80km is "Yes", >80km must be "No" and vice versa
                    if tl_short_item.text() == "Yes":
                        tl_long_item.setText("No")
                    else:  # "No"
                        tl_long_item.setText("Yes")
            
            # If >80km column changed (column 9), update <80km column (column 8)
            elif column == 9:  # >80km column
                tl_short_item = self.entries_table.item(row, 8)
                tl_long_item = self.entries_table.item(row, 9)
                
                if tl_short_item and tl_long_item:
                    # Make them mutually exclusive: if >80km is "Yes", <80km must be "No" and vice versa
                    if tl_long_item.text() == "Yes":
                        tl_short_item.setText("No")
                    else:  # "No"
                        tl_short_item.setText("Yes")
                
            # Recalculate equivalent hours whenever any relevant field changes
            if column in [1, 2, 3, 5]:  # start time, end time, rest hours, OT rate
                self.calculate_equivalent_hours(row)
                
            # Always update the summary for any cell change
            # This ensures the display updates when cells like offshore or T&L are edited
            self.update_time_summary()
            
            # Update total cost calculation to reflect changes in service hours
            self.calculate_total_cost()
        finally:
            self.updating_cell = False
    
    def validate_end_time(self, row):
        """Ensure end time is after start time"""
        start_item = self.entries_table.item(row, 1)
        end_item = self.entries_table.item(row, 2)
        
        if not start_item or not end_item:
            return
            
        start_hour = start_item.data(Qt.UserRole)
        end_hour = end_item.data(Qt.UserRole)
        
        # If end time is not after start time, set it to start_hour + 1
        if start_hour is not None and (end_hour is None or end_hour <= start_hour):
            new_end_hour = (start_hour + 1) % 25  # Wrap around if needed
            end_item.setText(f"{new_end_hour:02d}:00")
            end_item.setData(Qt.UserRole, new_end_hour)
    
    def calculate_equivalent_hours(self, row):
        """Calculate and update the equivalent hours for a row"""
        # Get values from the row
        start_item = self.entries_table.item(row, 1)
        end_item = self.entries_table.item(row, 2)
        rest_item = self.entries_table.item(row, 3)
        ot_item = self.entries_table.item(row, 5)
        equiv_item = self.entries_table.item(row, 10)  # Updated column index
        
        if not all([start_item, end_item, rest_item, ot_item, equiv_item]):
            return
            
        # Get hours and rate
        try:
            start_hour = start_item.data(Qt.UserRole)
            if start_hour is None and start_item.text():
                # Try to parse from text
                start_hour = int(start_item.text().split(":")[0])
                start_item.setData(Qt.UserRole, start_hour)
                
            end_hour = end_item.data(Qt.UserRole)
            if end_hour is None and end_item.text():
                # Try to parse from text
                end_hour = int(end_item.text().split(":")[0])
                end_item.setData(Qt.UserRole, end_hour)
                
            rest_hours = int(rest_item.text() or 0)
            
            # Get OT rate as a numeric value
            ot_rate_text = ot_item.text()
            try:
                ot_multiplier = float(ot_rate_text)
            except ValueError:
                # Fallback to 1.0 if the rate isn't a valid number
                ot_multiplier = 1.0
                
            # Calculate hours: ((End time - Start Time) - Reset Hour) * OT Rate
            if end_hour < start_hour:  # Overnight shift
                work_hours = (24 - start_hour) + end_hour
            else:
                work_hours = end_hour - start_hour
                
            # Subtract rest hours
            net_hours = max(0, work_hours - rest_hours)
            
            # Apply OT multiplier
            equivalent_hours = round(net_hours * ot_multiplier, 1)
            
            # Update the equivalent hours cell
            equiv_item.setText(f"{equivalent_hours:.1f}")
            
            # Always update the time summary after calculating equivalent hours
            # This ensures the summary values update correctly
            self.update_time_summary()
            
            # Update total cost calculation to reflect changes in service hours
            self.calculate_total_cost()
        except (ValueError, TypeError, IndexError) as e:
            equiv_item.setText("Error")
            # For debugging
            print(f"Error calculating equivalent hours: {str(e)}")
            
    def save_timesheet(self):
        """Save the timesheet to the JSON file"""
        # Get all Project Information fields
        client = self.client_input.text().strip()
        project_name = self.project_name_input.text().strip()  # Added project name field
        project_description = self.project_description_input.toPlainText().strip()  # Added project description field
        work_type = self.work_type_input.currentText().strip()
        engineer_name = self.engineer_name_input.text().strip()
        engineer_surname = self.engineer_surname_input.text().strip()
        emergency_request = self.emergency_request_input.currentText() == "Yes"
        
        # Get additional fields from Project Information groupbox
        po_number = self.po_number_input.text().strip()
        quotation_number = self.quotation_number_input.text().strip()
        contract_agreement = self.contract_agreement_input.currentText() == "Yes"
        client_address = self.client_address_input.toPlainText().strip()
        client_representative = self.client_rep_input.text().strip()
        client_representative_phone = self.client_phone_input.text().strip()
        client_representative_email = self.client_email_input.text().strip()
        
        # Calculate total cost before saving
        self.calculate_total_cost()
        
        # Validate
        if not client:
            QMessageBox.warning(self, "Validation Error", "Please enter a client name.")
            return
            
        if not engineer_name or not engineer_surname:
            QMessageBox.warning(self, "Validation Error", "Please enter the engineer's name and surname.")
            return
            
        # Check if there are any time entries
        if self.entries_table.rowCount() == 0:
            QMessageBox.warning(self, "Validation Error", "Please add at least one time entry.")
            return
            
        print("\n===== STANDALONE SAVE OPERATION =====\n")
            
        # Collect all time entries from the table
        time_entries = []
        for row in range(self.entries_table.rowCount()):
            # Get date
            date_item = self.entries_table.item(row, 0)
            start_item = self.entries_table.item(row, 1)
            end_item = self.entries_table.item(row, 2)
            rest_item = self.entries_table.item(row, 3)
            desc_item = self.entries_table.item(row, 4)
            ot_item = self.entries_table.item(row, 5)
            offshore_item = self.entries_table.item(row, 6)
            travel_count_item = self.entries_table.item(row, 7)
            travel_short_item = self.entries_table.item(row, 8)  # <80km column
            travel_long_item = self.entries_table.item(row, 9)   # >80km column
            
            if not all([date_item, start_item, end_item, rest_item, desc_item, ot_item]):
                continue
                
            description = desc_item.text().strip()
            if not description:
                QMessageBox.warning(
                    self, 
                    "Validation Error", 
                    f"Please enter a description for the entry on {date_item.text()}."
                )
                return
                
            # Ensure start and end time data is valid
            start_hour = start_item.data(Qt.UserRole)
            if start_hour is None:
                # Try to parse from text
                try:
                    start_hour = int(start_item.text().split(":")[0])
                    start_item.setData(Qt.UserRole, start_hour)
                except (ValueError, IndexError):
                    QMessageBox.warning(
                        self, 
                        "Validation Error", 
                        f"Invalid start time for the entry on {date_item.text()}."
                    )
                    return
                    
            end_hour = end_item.data(Qt.UserRole)
            if end_hour is None:
                # Try to parse from text
                try:
                    end_hour = int(end_item.text().split(":")[0])
                    end_item.setData(Qt.UserRole, end_hour)
                except (ValueError, IndexError):
                    QMessageBox.warning(
                        self, 
                        "Validation Error", 
                        f"Invalid end time for the entry on {date_item.text()}."
                    )
                    return
            
            # Create time entry
            entry = {
                'date': date_item.text(),
                'start_time': f"{start_hour:02d}00",
                'end_time': f"{end_hour:02d}00",
                'rest_hours': int(rest_item.text() or 0),
                'description': description,
                'overtime_rate': ot_item.text(),
                'offshore': offshore_item.text() == "Yes",
                'travel_count': travel_count_item.text() == "Yes",
                'travel_far_distance': travel_long_item.text() == "Yes"
            }
            
            # Add travel_short_distance only if it's used elsewhere in the data model
            if travel_short_item.text() == "Yes":
                entry['travel_short_distance'] = True
            time_entries.append(entry)
        
        # Sort time entries by date to find the first date of service
        if time_entries:
            # Sort by date
            sorted_entries = sorted(time_entries, key=lambda x: x['date'])
            first_service_date = sorted_entries[0]['date']
            
            # Extract date components for the ID
            try:
                if '/' in first_service_date:
                    date_obj = datetime.datetime.strptime(first_service_date, "%Y/%m/%d")
                else:
                    date_obj = datetime.datetime.strptime(first_service_date, "%Y-%m-%d")
                date_str = date_obj.strftime("%Y%m%d")
            except ValueError:
                # Fallback to current date if parsing fails
                date_str = datetime.datetime.now().strftime("%Y%m%d")
        else:
            # No time entries, use current date
            date_str = datetime.datetime.now().strftime("%Y%m%d")
        
        # Get username from user info, default to engineer name if not available
        username = ''
        if hasattr(self, 'user_info') and self.user_info and 'username' in self.user_info:
            username = self.user_info['username']
        else:
            # Fallback to engineer's name
            username = engineer_name.lower().replace(' ', '')
        
        # Find the next running number for this user and date
        running_number = self.get_next_running_number(username, date_str)
        
        # Create the entry ID in the format "TS-Username-YYYYMMDD-00"
        entry_id = f"TS-{username}-{date_str}-{running_number:02d}"
        
        # Collect all tool usage entries from the table
        tool_entries = []
        for row in range(self.tool_table.rowCount()):
            # Get tool data
            tool_item = self.tool_table.item(row, 0)
            amount_item = self.tool_table.item(row, 1)
            start_date_item = self.tool_table.item(row, 2)
            end_date_item = self.tool_table.item(row, 3)
            days_item = self.tool_table.item(row, 4)
            
            if not all([tool_item, amount_item, start_date_item, end_date_item, days_item]):
                continue
                
            # Create tool entry
            tool_entry = {
                'tool_name': tool_item.text(),
                'amount': int(amount_item.text() or 1),
                'start_date': start_date_item.text(),
                'end_date': end_date_item.text(),
                'total_days': int(days_item.text() or 1)
            }
            tool_entries.append(tool_entry)
        
        # Get report preparation information
        report_description = self.report_description_input.toPlainText().strip()
        report_hours = self.report_hours_input.value()
        
        # Create time summary data from the time summary section
        time_summary = {
            'total_regular_hours': self.extract_numeric_value(self.regular_hours_label.text()),
            'total_ot_1_5x_hours': self.extract_numeric_value(self.ot15_hours_label.text()),
            'total_ot_2_0x_hours': self.extract_numeric_value(self.ot20_hours_label.text()),
            'total_equivalent_hours': self.extract_numeric_value(self.equivalent_hours_label.text()),
            'total_offshore_days': int(self.offshore_days_label.text().split(':')[1].strip()),
            'total_tl_short_days': int(self.tl_short_days_label.text().split(':')[1].strip()),
            'total_tl_long_days': int(self.tl_long_days_label.text().split(':')[1].strip())
        }
        
        # Create tool usage summary data from the tool usage summary section
        tool_usage_summary = {
            'total_tool_usage_days': int(self.total_tool_days_label.text().split(':')[1].strip()),
            'tools_used': self.tools_used_label.text().replace('Tools Used: ', '')
        }
        
        # Calculate the total based on the time and tool entries and rates
        # Service hours cost
        service_hour_rate = self.service_rate_input.value()
        equivalent_hours = self.extract_numeric_value(self.equivalent_hours_label.text())
        service_hours_cost = service_hour_rate * equivalent_hours
        
        # Tool usage cost
        tool_usage_rate = self.tool_rate_input.value()
        total_tool_days = int(self.total_tool_days_label.text().split(':')[1].strip())
        tool_usage_cost = tool_usage_rate * total_tool_days
        
        # Transportation costs
        tl_rate_short = self.tl_short_input.value()
        tl_short_days = int(self.tl_short_days_label.text().split(':')[1].strip())
        tl_short_cost = tl_rate_short * tl_short_days
        
        tl_rate_long = self.tl_long_input.value()
        tl_long_days = int(self.tl_long_days_label.text().split(':')[1].strip())
        tl_long_cost = tl_rate_long * tl_long_days
        
        # Offshore cost
        offshore_rate = self.offshore_rate_input.value()
        offshore_days = int(self.offshore_days_label.text().split(':')[1].strip())
        offshore_cost = offshore_rate * offshore_days
        
        # Emergency cost - apply if emergency request is enabled
        emergency_rate = self.emergency_rate_input.value() 
        emergency_cost = emergency_rate if self.emergency_request_input.currentText() == "Yes" else 0.0
        
        # Other transport cost
        other_transport_cost = self.transport_charge_input.value()
        
        # Calculate subtotal
        subtotal = service_hours_cost + tool_usage_cost + tl_short_cost + tl_long_cost + offshore_cost + emergency_cost + other_transport_cost
        
        # Default to 7% VAT in Thailand if no VAT input field exists
        vat_percent = self.vat_percent_input.value() if hasattr(self, 'vat_percent_input') else 7.0
        
        # Default discount to 0 if no discount field exists
        discount_amount = self.discount_amount_input.value() if hasattr(self, 'discount_amount_input') else 0.0
        
        # Calculate VAT
        vat_amount = (subtotal - discount_amount) * (vat_percent / 100.0)
        
        # Calculate total with VAT
        total_with_vat = subtotal - discount_amount + vat_amount
        
        # Create total cost calculation data
        total_cost_calculation = {
            'service_hours_cost': service_hours_cost,
            'report_preparation_cost': report_hours * service_hour_rate,
            'tool_usage_cost': tool_usage_cost,
            'transportation_short_cost': tl_short_cost,
            'transportation_long_cost': tl_long_cost,
            'offshore_cost': offshore_cost,
            'emergency_cost': emergency_cost,
            'other_transport_cost': other_transport_cost,
            'subtotal': subtotal,
            'discount_amount': discount_amount,
            'vat_percent': vat_percent,
            'vat_amount': vat_amount,
            'total_with_vat': total_with_vat
        }
        
        # Create detailed calculation breakdown text
        is_emergency = self.emergency_request_input.currentText() == "Yes"
        
        # Get the currency
        currency = self.currency_input.currentText()
        
        # Extract regular, OT 1.5X, and OT 2.0X hours
        regular_hours = self.extract_numeric_value(self.regular_hours_label.text())
        ot15_hours = self.extract_numeric_value(self.ot15_hours_label.text())
        ot2_hours = self.extract_numeric_value(self.ot20_hours_label.text())
        
        # Extract offshore and travel days
        offshore_days = int(self.offshore_days_label.text().split(':')[1].strip())
        short_travel_days = int(self.tl_short_days_label.text().split(':')[1].strip())
        long_travel_days = int(self.tl_long_days_label.text().split(':')[1].strip())
        
        # Get various rates
        service_rate = self.service_rate_input.value()
        tool_rate = self.tool_rate_input.value()
        tl_short_rate = self.tl_short_input.value()
        tl_long_rate = self.tl_long_input.value()
        offshore_rate = self.offshore_rate_input.value()
        emergency_rate = self.emergency_rate_input.value()
        
        # Calculate individual costs
        report_hours = self.report_hours_input.value()
        report_preparation_cost = report_hours * service_rate
        total_service_cost = service_hours_cost
        total_tool_days = int(self.total_tool_days_label.text().split(':')[1].strip())
        travel_cost = short_travel_days * tl_short_rate + long_travel_days * tl_long_rate
        emergency_cost = emergency_rate if is_emergency else 0.0
        other_transport = self.transport_charge_input.value()
        
        # Create detailed calculation breakdown with actual values
        detailed_breakdown = [
            "Detailed Calculation Breakdown:",
            "-------------------------------",
            "1. Service Hours:",
            f"   Regular Hours: {regular_hours:.1f} hrs × {service_rate:.2f} = {regular_hours * service_rate:.2f} {currency}",
            f"   OT 1.5X Hours: {ot15_hours:.1f} hrs × {service_rate:.2f} × 1.5 = {ot15_hours * service_rate * 1.5:.2f} {currency}",
            f"   OT 2.0X Hours: {ot2_hours:.1f} hrs × {service_rate:.2f} × 2.0 = {ot2_hours * service_rate * 2.0:.2f} {currency}",
            f"   Total Service Hours Cost: {total_service_cost:.2f} {currency}",
            "",
            "2. Report Preparation:",
            f"   {report_hours:.1f} hrs × {service_rate:.2f} = {report_preparation_cost:.2f} {currency}",
            "",
            "3. Special Tools Usage:",
            f"   {total_tool_days} days × {tool_rate:.2f} = {tool_usage_cost:.2f} {currency}",
            "",
            "4. Travel & Living:",
            f"   T&L<80km: {short_travel_days} days × {tl_short_rate:.2f} = {short_travel_days * tl_short_rate:.2f} {currency}",
            f"   T&L>80km: {long_travel_days} days × {tl_long_rate:.2f} = {long_travel_days * tl_long_rate:.2f} {currency}",
            f"   Total T&L Cost: {travel_cost:.2f} {currency}",
            "",
            "5. Offshore Work:",
            f"   {offshore_days} days × {offshore_rate:.2f} = {offshore_cost:.2f} {currency}",
            "",
            "6. Emergency Request:",
            f"   {'Yes' if is_emergency else 'No'} × {emergency_rate:.2f} = {emergency_cost:.2f} {currency}",
            "",
            "7. Other Transportation Charge:",
            f"   {other_transport:.2f} {currency}",
            "",
            "8. Subtotal (1+2+3+4+5+6+7):",
            f"   {subtotal:.2f} {currency}",
            "",
            "9. VAT ({vat_percent:.2f}%):",
            f"   {subtotal:.2f} × {vat_percent/100:.4f} = {vat_amount:.2f} {currency}",
            "",
            "10. Discount:",
            f"   {discount_amount:.2f} {currency}",
            "",
            "11. GRAND TOTAL (8+9-10):",
            f"   {subtotal:.2f} + {vat_amount:.2f} - {discount_amount:.2f} = {total_with_vat:.2f} {currency}"
        ]
        
        # Create timesheet entry with all required fields
        timesheet = {
            # Entry ID and creation date
            'entry_id': entry_id,
            'creation_date': datetime.datetime.now().strftime("%Y/%m/%d"),
            
            # Project Information section (following UI order)
            # First row: PO, Quotation, Contract, Emergency
            'purchasing_order_number': po_number,
            'quotation_number': quotation_number, 
            'under_contract_agreement': contract_agreement,
            'emergency_request': emergency_request,
            
            # Second row: Client
            'client_company_name': client,
            
            # Third row: Client Address
            'client_address': client_address,
            
            # Fourth row: Client Representative, Phone, Email
            'client_representative_name': client_representative,
            'client_representative_phone': client_representative_phone,
            'client_representative_email': client_representative_email,
            
            # Project Name and Description fields
            'project_name': project_name,
            'project_description': project_description,
            
            # Fifth row: Engineer Info and Work Type
            'service_engineer_name': engineer_name,
            'service_engineer_surname': engineer_surname,
            'work_type': work_type,
            
            # Time Entries section
            'time_entries': time_entries,
            
            # Time Summary section
            'time_summary': time_summary,
            
            # Tool Usage section
            'tool_usage': tool_entries,
            
            # Tool Usage Summary section
            'tool_usage_summary': tool_usage_summary,
            
            # Report Preparation section
            'report_description': report_description,
            'report_hours': report_hours,
            
            # Service Charge Calculation section
            'currency': self.currency_input.currentText(),
            'service_hour_rate': self.service_rate_input.value(),
            'tool_usage_rate': self.tool_rate_input.value(),
            'tl_rate_short': self.tl_short_input.value(),
            'tl_rate_long': self.tl_long_input.value(),
            'offshore_day_rate': self.offshore_rate_input.value(),
            'emergency_rate': self.emergency_rate_input.value(),
            'other_transport_charge': self.transport_charge_input.value(),
            'other_transport_note': self.transport_note_input.toPlainText().strip(),
            'vat_percent': vat_percent,
            'discount_amount': discount_amount,
            'total_cost_calculation': total_cost_calculation,
            'detailed_calculation_breakdown': '\n'.join(detailed_breakdown),
            'total_service_charge': total_with_vat
        }
        
        # Print debugging information
        print("\n=== SAVE TIMESHEET DEBUGGING ===")
        print(f"Timesheet data before save: {timesheet}")
        print(f"Data manager: {self.data_manager}")
        print(f"Data file path: {self.data_manager.data_file_path}")
        
        # ULTRA SIMPLE DIRECT SAVE - no dependencies on data manager or other methods
        try:
            # 1. Define the output file path
            json_file_path = "data/timesheet/timesheet_entries.json"
            from pathlib import Path
            json_file = Path(json_file_path)
            print(f"[SAVE] Saving to file: {json_file.absolute()}")
            
            # 2. Ensure directory exists
            import os
            os.makedirs(json_file.parent, exist_ok=True)
            
            # 3. Check if file exists, create it if it doesn't
            if not json_file.exists() or json_file.stat().st_size == 0:
                print(f"[SAVE] File doesn't exist or is empty, creating it with initial structure")
                try:
                    # Create a valid initial JSON structure
                    initial_data = {"entries": []}
                    with open(json_file, 'w', encoding='utf-8') as f:
                        json.dump(initial_data, f, indent=2, ensure_ascii=False)
                    print(f"[SAVE] Created initial JSON file: {json_file.absolute()}")
                except Exception as create_err:
                    print(f"[SAVE] Error creating initial file: {create_err}")
                    import traceback
                    traceback.print_exc()
            
            # 4. Load existing data
            existing_entries = []
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    if file_content.strip():
                        data = json.loads(file_content)
                        if 'entries' in data:
                            existing_entries = data['entries']
                            print(f"[SAVE] Loaded {len(existing_entries)} existing entries")
                        else:
                            print(f"[SAVE] File exists but has no 'entries' key, will be created")
                    else:
                        print(f"[SAVE] File exists but is empty, will be initialized")
            except Exception as load_err:
                print(f"[SAVE] Error loading existing file: {load_err}, starting with empty entries")
                import traceback
                traceback.print_exc()
            
            # 5. Add the new entry
            entry_ids = [entry.get('entry_id', '') for entry in existing_entries]
            if timesheet['entry_id'] in entry_ids:
                print(f"[SAVE] Entry ID {timesheet['entry_id']} already exists, replacing")
                for i, entry in enumerate(existing_entries):
                    if entry.get('entry_id') == timesheet['entry_id']:
                        existing_entries[i] = timesheet
                        break
            else:
                print(f"[SAVE] Adding new entry with ID: {timesheet['entry_id']}")
                existing_entries.append(timesheet)
                
            print(f"[SAVE] Total entries after update: {len(existing_entries)}")
            
            # 6. Save data back to file
            json_data = {'entries': existing_entries}
            print(f"[SAVE] Writing data to file: {json_file.absolute()}")
            
            # Write to a temporary file first
            temp_file = json_file.with_suffix('.tmp')
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
                
            print(f"[SAVE] Temp file created with size: {temp_file.stat().st_size} bytes")
            
            # Then replace the original file
            if json_file.exists():
                os.replace(temp_file, json_file)
            else:
                os.rename(temp_file, json_file)
                
            # 7. Verify the save worked
            if json_file.exists() and json_file.stat().st_size > 0:
                with open(json_file, 'r', encoding='utf-8') as f:
                    verify_content = f.read()
                    verify_data = json.loads(verify_content)
                    verify_count = len(verify_data.get('entries', []))
                    print(f"[SAVE] Verification successful - file has {verify_count} entries")
                    print(f"[SAVE] First 100 chars of file: {verify_content[:100]}...")
            else:
                print(f"[SAVE] WARNING: File verification failed!")
            
            # Show success message
            QMessageBox.information(self, "Success", "Timesheet saved successfully.")
            
            # Signal that data has changed (normally done by data_manager)
            if hasattr(self.data_manager, 'data_changed'):
                print("Emitting data_changed signal")
                self.data_manager.data_changed.emit()
            
            # Emit entry saved signal
            print(f"Emitting entry_saved signal with ID: {timesheet['entry_id']}")
            self.entry_saved.emit(timesheet['entry_id'])
            
            # Clear form
            self.clear_form()
        except Exception as e:
            print(f"SAVE ERROR: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(self, "Error", f"Error saving timesheet: {str(e)}")
            
    def extract_numeric_value(self, text_value):
        """Extract numeric value from text string (e.g., "THB 1,234.56" -> 1234.56)"""
        if not text_value:
            return 0.0
            
        # Remove currency symbol, commas, and any other non-numeric characters
        # Keep only digits, decimal point, and negative sign
        numeric_chars = ''
        for char in text_value:
            if char.isdigit() or char == '.' or char == '-':
                numeric_chars += char
                
        try:
            return float(numeric_chars)
        except ValueError:
            return 0.0
    
    def clear_form(self):
        """Clear the form after saving"""
        # Clear all rows in the table
        self.entries_table.setRowCount(0)
        
        # Add a fresh empty row
        self.add_new_row()
        
        # Clear input fields
        self.client_input.clear()
        self.project_name_input.clear()  # Clear project name
        self.project_description_input.clear()  # Clear project description
        self.work_type_input.setCurrentIndex(0)
        # self.tier_input.setCurrentIndex(0)
        
        # Clear time entries list
        self.time_entries.clear()
        
        # Clear tool table
        self.tool_table.setRowCount(0)
        self.add_new_tool_row()
        
        # Clear report preparation fields
        self.report_description_input.clear()
        self.report_hours_input.setValue(0)
        
        # Clear service charge fields
        self.service_rate_input.setValue(0)
        self.tool_rate_input.setValue(0)
        self.tl_short_input.setValue(0)
        self.tl_long_input.setValue(0)
        self.offshore_rate_input.setValue(0)
        self.emergency_rate_input.setValue(0)
        self.transport_charge_input.setValue(0)
        self.transport_note_input.clear()
        self.total_cost_label.setText("Total Cost: 0.00")
        
        # Update summary displays
        self.update_time_summary()
        self.update_tool_summary()
    
    def add_new_tool_row(self):
        """Add a new empty row to the tool table"""
        row = self.tool_table.rowCount()
        self.tool_table.insertRow(row)
        
        # Set default values
        today_date = datetime.datetime.now().date()
        tomorrow_date = today_date + datetime.timedelta(days=1)
        
        # Format with weekday name
        today = today_date.strftime("ddd, %Y/%m/%d").replace("ddd", today_date.strftime("%a"))
        tomorrow = tomorrow_date.strftime("ddd, %Y/%m/%d").replace("ddd", tomorrow_date.strftime("%a"))
        
        # Create items with default values
        tool_item = QTableWidgetItem("AS-1250FE")
        amount_item = QTableWidgetItem("1")
        start_date_item = QTableWidgetItem(today)
        end_date_item = QTableWidgetItem(tomorrow)
        days_item = QTableWidgetItem("1")
        
        # Make total days column read-only
        days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
        days_item.setForeground(QBrush(Qt.black))
        
        # Set all items to the table
        self.tool_table.setItem(row, 0, tool_item)
        self.tool_table.setItem(row, 1, amount_item)
        self.tool_table.setItem(row, 2, start_date_item)
        self.tool_table.setItem(row, 3, end_date_item)
        self.tool_table.setItem(row, 4, days_item)
        
        # Calculate total days
        self.calculate_tool_days(row)
        
        # Direct force update of the summary labels
        self.update_tool_summary_direct()
        
        # Try the regular update too
        self.update_tool_summary()
        
        # Update total cost calculation to reflect added tool
        self.calculate_total_cost()
    
    def remove_selected_tool(self):
        """Remove the selected row from the tool table"""
        selected_rows = self.tool_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a tool row to remove.")
            return
            
        for index in sorted(selected_rows, reverse=True):
            self.tool_table.removeRow(index.row())
            
        # Update tool summary - first call direct method for immediate update
        self.update_tool_summary_direct()
        # Then regular method
        self.update_tool_summary()
        
        # Update total cost calculation to reflect removed tool
        self.calculate_total_cost()
        
        print("Tool row removed - summary updated")
    
    def on_tool_cell_changed(self, row, column):
        """Handle cell changes in the tool table and recalculate values as needed"""
        try:
            # If start or end date changed, recalculate days
            if column in [2, 3]:  # Start or end date changed
                self.calculate_tool_days(row)
            
            # Update for any column change (tool name, amount, dates, etc.)
            # First call the direct method for immediate feedback
            self.update_tool_summary_direct()
            
            # Then call the regular method
            self.update_tool_summary()
            
            # Update total cost calculation to reflect changes in tool usage
            self.calculate_total_cost()
    
        except Exception as e:
            # Silently handle errors in tool cell changes
            pass
    
    def calculate_tool_days(self, row):
        """Calculate the total days between start and end date for a tool"""
        start_item = self.tool_table.item(row, 2)  # Start date
        end_item = self.tool_table.item(row, 3)    # End date
        days_item = self.tool_table.item(row, 4)   # Total days
        
        if not all([start_item, end_item, days_item]):
            return
            
        try:
            # Parse dates
            start_text = start_item.text()
            end_text = end_item.text()
            
            # Parse start date with potential day name prefix
            if ',' in start_text:  # New format with day name (e.g., "Mon, 2025/04/24")
                # Extract the date part after the comma
                date_part = start_text.split(", ", 1)[1] if ", " in start_text else start_text
                start_date = datetime.datetime.strptime(date_part, "%Y/%m/%d").date()
            elif '/' in start_text:
                start_date = datetime.datetime.strptime(start_text, "%Y/%m/%d").date()
            else:
                start_date = datetime.datetime.strptime(start_text, "%Y-%m-%d").date()
                
            # Parse end date with potential day name prefix
            if ',' in end_text:  # New format with day name (e.g., "Mon, 2025/04/24")
                # Extract the date part after the comma
                date_part = end_text.split(", ", 1)[1] if ", " in end_text else end_text
                end_date = datetime.datetime.strptime(date_part, "%Y/%m/%d").date()
            elif '/' in end_text:
                end_date = datetime.datetime.strptime(end_text, "%Y/%m/%d").date()
            else:
                end_date = datetime.datetime.strptime(end_text, "%Y-%m-%d").date()
            
            # Calculate days difference (inclusive of start and end date)
            delta = end_date - start_date
            total_days = delta.days + 1  # +1 to include both start and end date
            
            # Ensure at least 1 day
            if total_days < 1:
                total_days = 1
                
            # Update the days item
            days_item.setText(str(total_days))
            
        except (ValueError, TypeError) as e:
            # Set to 1 day if there's an error
            days_item.setText("1")
    
    def update_tool_summary_direct(self):
        """Directly update the tool summary labels without complex logic"""
        try:
            # Safety check to ensure UI is ready
            if not hasattr(self, 'tools_used_label') or not hasattr(self, 'total_tool_days_label'):
                print("UI not ready yet, deferring tool summary update...")
                # Defer the update using QTimer
                from PySide6.QtCore import QTimer
                QTimer.singleShot(200, self.update_tool_summary_direct)
                return
                
            # Get the row count in the tool table
            row_count = self.tool_table.rowCount()
            
            # Check if there are any rows, show None if empty
            if row_count == 0:
                self.tools_used_label.setText("Tools Used: None")
                self.total_tool_days_label.setText("Total Special Tools Usage Day: 0")
                return
            
            # Count each unique tool type
            tools_used = {}
            
            # Track unique date ranges to avoid double-counting same periods
            date_ranges = {}
            
            # Analyze each row to get the actual tool names and date ranges
            for row in range(row_count):
                # Get all relevant items from the row
                tool_item = self.tool_table.item(row, 0)       # Tool name
                amount_item = self.tool_table.item(row, 1)     # Amount
                start_date_item = self.tool_table.item(row, 2) # Start date
                end_date_item = self.tool_table.item(row, 3)   # End date
                days_item = self.tool_table.item(row, 4)       # Total days
                
                # Use default if missing
                tool_name = "AS-1250FE"
                if tool_item and tool_item.text():
                    tool_name = tool_item.text()
                
                # Get amount with default = 1
                amount = 1
                if amount_item and amount_item.text():
                    try:
                        amount = int(amount_item.text())
                    except ValueError:
                        pass
                
                # Get days with default = 1
                days = 1
                if days_item and days_item.text():
                    try:
                        days = int(days_item.text())
                    except ValueError:
                        pass
                
                # Add to tools_used dictionary for the summary display
                if tool_name in tools_used:
                    tools_used[tool_name] += amount
                else:
                    tools_used[tool_name] = amount
                
                # Get date range to handle same-period tools
                start_date = "Unknown" if not start_date_item or not start_date_item.text() else start_date_item.text()
                end_date = "Unknown" if not end_date_item or not end_date_item.text() else end_date_item.text()
                
                # Create a unique key for this date range
                date_range_key = f"{start_date}_{end_date}"
                
                # Track the maximum number of days for this date range
                if date_range_key in date_ranges:
                    date_ranges[date_range_key] = max(date_ranges[date_range_key], days)
                else:
                    date_ranges[date_range_key] = days
            
            # Calculate total days by summing all unique date ranges
            # This ensures tools used in the same period are counted only once
            total_days = sum(date_ranges.values())
            
            # Format the tools used text
            tool_descriptions = []
            for tool_name, count in tools_used.items():
                tool_descriptions.append(f"{count} {tool_name}")
            
            # Join with 'and' for better readability
            if len(tool_descriptions) > 1:
                text = "Tools Used: " + " and ".join(tool_descriptions)
            else:
                text = "Tools Used: " + ", ".join(tool_descriptions)
                
            # Now we know the labels exist, update them directly
            self.tools_used_label.setText(text)
            self.total_tool_days_label.setText(f"Total Special Tools Usage Day: {total_days}")
                
        except Exception as e:
            # Silently handle errors in direct update
            pass
    
    def update_tool_summary(self):
        """Calculate and update the tool usage summary labels"""
        # We no longer call the direct update method from here to avoid circular updates
        # This prevents overwriting of the correct total_days value
        # self.update_tool_summary_direct() <- Removed this line
        
        try:
            # Get the row count
            row_count = self.tool_table.rowCount()
            
            # Skip complex processing if no rows
            if row_count == 0:
                return
                
            # Initialize tracking
            tools_used = {}
            date_ranges = {}  # Track unique date ranges to avoid double-counting
            
            # Process each row
            for row in range(row_count):
                # Get all relevant items from the row
                tool_item = self.tool_table.item(row, 0)       # Tool name
                amount_item = self.tool_table.item(row, 1)     # Amount
                start_date_item = self.tool_table.item(row, 2) # Start date
                end_date_item = self.tool_table.item(row, 3)   # End date
                days_item = self.tool_table.item(row, 4)       # Total days
                
                # Get values with defaults
                tool_name = "AS-1250FE"
                amount = 1
                days = 1
                
                # Update if items exist
                if tool_item and tool_item.text():
                    tool_name = tool_item.text()
                    
                if amount_item and amount_item.text():
                    try:
                        amount = int(amount_item.text())
                    except (ValueError, TypeError):
                        pass
                        
                if days_item and days_item.text():
                    try:
                        days = int(days_item.text())
                    except (ValueError, TypeError):
                        pass
                
                # Add to tracking for tool counts
                if tool_name in tools_used:
                    tools_used[tool_name] += amount
                else:
                    tools_used[tool_name] = amount
                    
                # Get date range to handle same-period tools
                start_date = "Unknown" if not start_date_item or not start_date_item.text() else start_date_item.text().strip()
                end_date = "Unknown" if not end_date_item or not end_date_item.text() else end_date_item.text().strip()
                
                # Create a unique key for this date range
                date_range_key = f"{start_date}_{end_date}"

                
                # Track the maximum number of days for this date range
                if date_range_key in date_ranges:
                    old_days = date_ranges[date_range_key]
                    date_ranges[date_range_key] = max(old_days, days)

                else:
                    date_ranges[date_range_key] = days

            
            # Calculate total days by summing all unique date ranges
            # This ensures tools used in the same period are counted only once
            total_tool_days = sum(date_ranges.values())
            
            # Create output text
            parts = []
            for tool_name, count in tools_used.items():
                parts.append(f"{count} {tool_name}")
                
            if parts:
                text = f"Tools Used: {', '.join(parts)}"
                
                # Update labels
                if hasattr(self, 'tools_used_label'):
                    self.tools_used_label.setText(text)
                    self.tools_used_label.repaint()
                    
                if hasattr(self, 'total_tool_days_label'):
                    self.total_tool_days_label.setText(f"Total Special Tools Usage Day: {total_tool_days}")
                    self.total_tool_days_label.repaint()
        
        except Exception as e:
            print(f"Error in update_tool_summary: {str(e)}")
            
    # The duplicate save_timesheet method has been removed.
    # The proper implementation is at line ~1440
    
    def clear_form(self):
        """Clear all form inputs"""
        from PySide6.QtWidgets import QMessageBox
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self, 
            "Clear Form", 
            "Are you sure you want to clear all entries? This action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply != QMessageBox.Yes:
            return
            
        # Clear client information fields
        self.po_number_input.clear()
        self.quotation_number_input.clear()
        self.contract_agreement_input.setCurrentIndex(0)  # Set to "No"
        self.emergency_request_input.setCurrentIndex(0)   # Set to "No"
        self.client_input.clear()
        self.client_address_input.clear()
        self.client_rep_input.clear()
        self.client_phone_input.clear()  # Fixed: use the correct field name
        self.client_email_input.clear()  # Fixed: use the correct field name
        
        # Reset work type to default
        self.work_type_input.setCurrentIndex(0)  # Set to "Special Field Services"
        
        # Clear all table entries
        self.entries_table.setRowCount(0)
        self.tool_table.setRowCount(0)
        
        # Reset all summary labels
        self.regular_hours_label.setText("Total Regular Hours: 0.0")
        self.ot15_hours_label.setText("Total OT 1.5X Hours: 0.0")
        self.ot20_hours_label.setText("Total OT 2.0X Hours: 0.0")
        self.equivalent_hours_label.setText("Total Equivalent Hours: 0.0")
        self.offshore_days_label.setText("Total Offshore Days: 0")
        self.tl_short_days_label.setText("Total T&L<80km Days: 0")
        self.tl_long_days_label.setText("Total T&L>80km Days: 0")
        self.tools_used_label.setText("Tools Used: None")
        self.total_tool_days_label.setText("Total Special Tools Usage Day: 0")
        
        # Reset rates to defaults based on current currency
        self.update_default_rates(self.currency_input.currentText())
        
        # Reset VAT and discount
        self.vat_percent_input.setValue(7)  # Reset to default 7%
        self.discount_amount_input.setValue(0)  # Reset to 0
        
        # Recalculate totals
        self.calculate_total_cost()
        
        # Show feedback
        QMessageBox.information(self, "Form Cleared", "All form entries have been cleared.")

    def extract_numeric_value(self, text):
        """Extract numeric value from text that might contain currency symbols
        For example: 'Total Cost: 92000.00 THB' -> 92000.00
        """
        try:
            # First split by colon if present
            if ':' in text:
                text = text.split(':', 1)[1].strip()
            
            # Remove any non-numeric characters except decimal point
            # This will handle currency symbols and thousand separators
            numeric_chars = [c for c in text if c.isdigit() or c == '.']
            numeric_string = ''.join(numeric_chars)
            
            # Convert to float
            return float(numeric_string)
        except (ValueError, IndexError):
            return 0.0
            
    def get_next_running_number(self, username, date_str):
        """Find the next running number for the given username and date"""
        entries = self.data_manager.load_entries()
        max_num = -1
        
        # The format is TS-username-YYYYMMDD-00 where 00 is the running number
        prefix = f"TS-{username}-{date_str}-"
        
        for entry in entries:
            entry_id = entry.entry_id
            # Check if this entry matches our prefix
            if entry_id.startswith(prefix):
                try:
                    # Extract the running number (last 2 digits)
                    num_str = entry_id[-2:]
                    num = int(num_str)
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    pass
        
        # Next running number is one more than the maximum found (or 0 if none found)
        return max_num + 1
        
    def update_default_rates(self, currency):
        """Update all rate fields based on the selected currency"""
        if currency == "THB":
            # Set THB rates from the image
            self.service_rate_input.setValue(6500.00)
            self.tool_rate_input.setValue(25000.00)
            self.tl_short_input.setValue(2500.00)
            self.tl_long_input.setValue(7500.00)
            self.offshore_rate_input.setValue(17500.00)
            self.emergency_rate_input.setValue(16000.00)
            self.transport_charge_input.setValue(0.00)
        else:  # USD
            # Set USD rates from the image
            self.service_rate_input.setValue(220.00)
            self.tool_rate_input.setValue(750.00)
            self.tl_short_input.setValue(100.00)
            self.tl_long_input.setValue(420.00)
            self.offshore_rate_input.setValue(550.00)
            self.emergency_rate_input.setValue(660.00)
            self.transport_charge_input.setValue(0.00)
    
    def update_time_summary(self):
        """Calculate and update the time summary labels"""
        # Safety check during destruction
        if not hasattr(self, 'regular_hours_label') or not hasattr(self, 'offshore_days_label'):
            return
        
        # Hours calculation
        total_hours = 0.0
        regular_hours = 0.0
        ot15_hours = 0.0
        ot20_hours = 0.0
        equivalent_hours = 0.0
        
        # Days calculation - using sets to track unique dates
        offshore_dates = set()  # Set of unique dates for offshore work
        tl_short_dates = set()  # Set of unique dates for T&L <80km
        tl_long_dates = set()   # Set of unique dates for T&L >80km
        
        # Loop through all rows in the table
        for row in range(self.entries_table.rowCount()):
            try:
                # Get date from the current row
                date_item = self.entries_table.item(row, 0)  # Date column
                if not date_item or not date_item.text():
                    continue
                
                # Extract the date string for this entry
                date_str = date_item.text()
                
                # Get items from the row
                start_item = self.entries_table.item(row, 1)      # Start time
                end_item = self.entries_table.item(row, 2)        # End time
                rest_item = self.entries_table.item(row, 3)       # Rest hours
                ot_item = self.entries_table.item(row, 5)         # OT rate
                offshore_item = self.entries_table.item(row, 6)   # Offshore?
                tl_item = self.entries_table.item(row, 7)         # T&L?
                tl_short_item = self.entries_table.item(row, 8)   # <80km?
                tl_long_item = self.entries_table.item(row, 9)    # >80km?
                equiv_item = self.entries_table.item(row, 10)     # Equivalent hours
                
                if not all([start_item, end_item, rest_item, ot_item, equiv_item, 
                          offshore_item, tl_item, tl_short_item, tl_long_item]):
                    continue
                    
                # Get start and end hours
                start_hour = start_item.data(Qt.UserRole)
                if start_hour is None and start_item.text():
                    start_hour = int(start_item.text().split(":")[0])
                    
                end_hour = end_item.data(Qt.UserRole)
                if end_hour is None and end_item.text():
                    end_hour = int(end_item.text().split(":")[0])
                    
                rest_hours = int(rest_item.text() or 0)
                
                # Calculate work hours
                if end_hour < start_hour:  # Overnight shift
                    work_hours = (24 - start_hour) + end_hour
                else:
                    work_hours = end_hour - start_hour
                    
                # Subtract rest hours
                net_hours = max(0, work_hours - rest_hours)
                total_hours += net_hours
                
                # Add to the appropriate OT category based on the numeric OT rate
                ot_rate_text = ot_item.text()
                try:
                    ot_rate = float(ot_rate_text)
                    if ot_rate == 1.5:
                        ot15_hours += net_hours
                    elif ot_rate == 2.0:
                        ot20_hours += net_hours
                    else:  # Regular (1.0)
                        regular_hours += net_hours
                except ValueError:
                    # Fallback if not a valid number
                    regular_hours += net_hours
                    
                # Add to equivalent hours
                try:
                    equiv_hours = float(equiv_item.text() or 0)
                    equivalent_hours += equiv_hours
                except ValueError:
                    pass
                    
                # Count days data if this is a full day entry (8 or more hours)
                # or if T&L is Yes
                is_full_day = net_hours >= 8
                is_tl_day = tl_item.text() == "Yes"
                
                if is_full_day or is_tl_day:
                    # Track unique dates for offshore work
                    if offshore_item.text() == "Yes":
                        offshore_dates.add(date_str)
                    
                    # Track unique dates for T&L by distance
                    if is_tl_day:
                        if tl_short_item.text() == "Yes":
                            tl_short_dates.add(date_str)
                        if tl_long_item.text() == "Yes":
                            tl_long_dates.add(date_str)
                            
            except (ValueError, TypeError, IndexError) as e:
                # Skip if there's an error processing this row
                print(f"Error processing row: {row}, error: {str(e)}")
                continue
        
        # Update the Hours labels
        try:
            self.regular_hours_label.setText(f"Total Regular Hours: {regular_hours:.1f}")
            self.ot15_hours_label.setText(f"Total OT 1.5X Hours: {ot15_hours:.1f}")
            self.ot20_hours_label.setText(f"Total OT 2.0X Hours: {ot20_hours:.1f}")
            self.equivalent_hours_label.setText(f"Total Equivalent Hours: {equivalent_hours:.1f}")
            
            # Update the Days labels with the count of unique dates
            self.offshore_days_label.setText(f"Total Offshore Days: {len(offshore_dates)}")
            self.tl_short_days_label.setText(f"Total T&L<80km Days: {len(tl_short_dates)}")
            self.tl_long_days_label.setText(f"Total T&L>80km Days: {len(tl_long_dates)}")
        except (RuntimeError, AttributeError, TypeError) as e:
            # Widget has been deleted or is invalid, safely ignore
            print(f"Error updating summary labels: {str(e)}")
        
    def update_tool_summary_old(self):
        """DEPRECATED - Old version of tool summary update - do not use"""
        pass  # This method is deprecated and has been replaced by the newer version above
        
    def calculate_total_cost(self):
        """Calculate the total service charge based on time entries, tool usage, and rates"""
        # Check if all necessary UI elements are present
        if not hasattr(self, 'total_cost_label') or not hasattr(self, 'entries_table'):
            return  # Safety check during initialization or destruction
            
        try:
            # Get rate values
            service_rate = self.service_rate_input.value()
            tool_rate = self.tool_rate_input.value()
            tl_short_rate = self.tl_short_input.value()  # < 80 km
            tl_long_rate = self.tl_long_input.value()    # > 80 km
            offshore_rate = self.offshore_rate_input.value()
            emergency_rate = self.emergency_rate_input.value()
            other_transport = self.transport_charge_input.value()
            currency = self.currency_input.currentText()
            is_emergency = self.emergency_request_input.currentText() == "Yes"
            report_hours = self.report_hours_input.value()
            
            # Get VAT and discount values
            vat_percent = self.vat_percent_input.value()
            discount_amount = self.discount_amount_input.value()
            
            # Calculate service hours
            total_service_hours = 0
            regular_hours = 0
            ot15_hours = 0
            ot2_hours = 0
            
            # Get travel days, offshore days from the Time Summary labels
            # instead of recounting rows
            short_travel_days = 0
            long_travel_days = 0
            offshore_days = 0
            
            try:
                # Extract T&L < 80km days from label
                if hasattr(self, 'tl_short_days_label'):
                    tl_short_text = self.tl_short_days_label.text()
                    # Format is like "Total T&L<80km Days: 3"
                    short_travel_days = self.extract_numeric_value(tl_short_text)
                    
                # Extract T&L > 80km days from label
                if hasattr(self, 'tl_long_days_label'):
                    tl_long_text = self.tl_long_days_label.text()
                    # Format is like "Total T&L>80km Days: 2"
                    long_travel_days = self.extract_numeric_value(tl_long_text)
                    
                # Extract offshore days from label
                if hasattr(self, 'offshore_days_label'):
                    offshore_text = self.offshore_days_label.text()
                    # Format is like "Total Offshore Days: 1"
                    offshore_days = self.extract_numeric_value(offshore_text)
                    
            except Exception as e:
                print(f"Error extracting days from summary labels: {str(e)}")
            
            # Process all time entries to get service hours
            for row in range(self.entries_table.rowCount()):
                # Check if we have all required items
                date_item = self.entries_table.item(row, 0)
                start_item = self.entries_table.item(row, 1)
                end_item = self.entries_table.item(row, 2)
                rest_item = self.entries_table.item(row, 3)
                ot_item = self.entries_table.item(row, 5)
                
                if not all([date_item, start_item, end_item, rest_item, ot_item]):
                    continue
                    
                # Get start and end hour
                start_hour = start_item.data(Qt.UserRole)
                if start_hour is None:
                    try:
                        start_hour = int(start_item.text().split(":")[0])
                    except (ValueError, IndexError):
                        continue
                        
                end_hour = end_item.data(Qt.UserRole)
                if end_hour is None:
                    try:
                        end_hour = int(end_item.text().split(":")[0])
                    except (ValueError, IndexError):
                        continue
                        
                # Calculate hours worked
                rest_hours = int(rest_item.text() or 0)
                if end_hour < start_hour:  # Overnight shift
                    hours_worked = (24 - start_hour) + end_hour - rest_hours
                else:
                    hours_worked = (end_hour - start_hour) - rest_hours
                    
                if hours_worked <= 0:
                    continue
                    
                # Add to total service hours based on overtime rate
                total_service_hours += hours_worked
                ot_rate = ot_item.text()
                if ot_rate == "1.5" or ot_rate == "OT1.5":
                    ot15_hours += hours_worked
                elif ot_rate == "2" or ot_rate == "2.0" or ot_rate == "OT2.0":
                    ot2_hours += hours_worked
                else:  # Regular (1.0)
                    regular_hours += hours_worked
            
            # Get tool days from the Tool Usage Summary label instead of recalculating
            total_tool_days = 0
            if hasattr(self, 'total_tool_days_label'):
                try:
                    # Extract the numeric value from the label
                    total_tool_days_text = self.total_tool_days_label.text()
                    # Format is like "Total Special Tools Usage Day: 5"
                    total_tool_days = self.extract_numeric_value(total_tool_days_text)
                except Exception as e:
                    print(f"Error extracting tool days from label: {str(e)}")
            
            # Calculate individual costs for subtotals
            service_hours_cost = regular_hours * service_rate
            ot15_cost = ot15_hours * service_rate * 1.5
            ot2_cost = ot2_hours * service_rate * 2.0
            total_service_cost = service_hours_cost + ot15_cost + ot2_cost
            
            report_preparation_cost = report_hours * service_rate  # Uses the regular rate
            tool_usage_cost = total_tool_days * tool_rate
            travel_cost = (short_travel_days * tl_short_rate) + (long_travel_days * tl_long_rate)
            offshore_cost = offshore_days * offshore_rate
            emergency_cost = emergency_rate if is_emergency else 0
            
            # Update all the subtotal labels
            self.service_hours_subtotal.setText(f"{total_service_cost:.2f} {currency}")
            self.report_hours_subtotal.setText(f"{report_preparation_cost:.2f} {currency}")
            self.tool_usage_subtotal.setText(f"{tool_usage_cost:.2f} {currency}")
            self.travel_subtotal.setText(f"{travel_cost:.2f} {currency}")
            self.offshore_subtotal.setText(f"{offshore_cost:.2f} {currency}")
            self.emergency_subtotal.setText(f"{emergency_cost:.2f} {currency}")
            self.transport_subtotal.setText(f"{other_transport:.2f} {currency}")
            
            # Calculate subtotal before VAT and discount
            subtotal = total_service_cost + report_preparation_cost + tool_usage_cost + \
                       travel_cost + offshore_cost + emergency_cost + other_transport
            self.subtotal_label.setText(f"{subtotal:.2f} {currency}")
            
            # Calculate VAT amount
            vat_amount = subtotal * (vat_percent / 100.0)
            self.vat_amount_label.setText(f"{vat_amount:.2f} {currency}")
            
            # Calculate final total (with VAT and discount)
            grand_total = subtotal + vat_amount - discount_amount
            if grand_total < 0:  # Ensure total is not negative
                grand_total = 0
            
            # Update the grand total label
            self.total_cost_label.setText(f"Grand Total: {grand_total:.2f} {currency}")
            
            # Create detailed calculation breakdown with actual values
            breakdown = [
                "Detailed Calculation Breakdown:",
                "-------------------------------",
                "1. Service Hours:",
                f"   Regular Hours: {regular_hours:.1f} hrs × {service_rate:.2f} = {regular_hours * service_rate:.2f} {currency}",
                f"   OT 1.5X Hours: {ot15_hours:.1f} hrs × {service_rate:.2f} × 1.5 = {ot15_hours * service_rate * 1.5:.2f} {currency}",
                f"   OT 2.0X Hours: {ot2_hours:.1f} hrs × {service_rate:.2f} × 2.0 = {ot2_hours * service_rate * 2.0:.2f} {currency}",
                f"   Total Service Hours Cost: {total_service_cost:.2f} {currency}",
                "",
                "2. Report Preparation:",
                f"   {report_hours:.1f} hrs × {service_rate:.2f} = {report_preparation_cost:.2f} {currency}",
                "",
                "3. Special Tools Usage:",
                f"   {total_tool_days} days × {tool_rate:.2f} = {tool_usage_cost:.2f} {currency}",
                "",
                "4. Travel & Living:",
                f"   T&L<80km: {short_travel_days} days × {tl_short_rate:.2f} = {short_travel_days * tl_short_rate:.2f} {currency}",
                f"   T&L>80km: {long_travel_days} days × {tl_long_rate:.2f} = {long_travel_days * tl_long_rate:.2f} {currency}",
                f"   Total T&L Cost: {travel_cost:.2f} {currency}",
                "",
                "5. Offshore Work:",
                f"   {offshore_days} days × {offshore_rate:.2f} = {offshore_cost:.2f} {currency}",
                "",
                "6. Emergency Request:",
                f"   {'Yes' if is_emergency else 'No'} × {emergency_rate:.2f} = {emergency_cost:.2f} {currency}",
                "",
                "7. Other Transportation Charge:",
                f"   {other_transport:.2f} {currency}",
                "",
                "8. Subtotal (1+2+3+4+5+6+7):",
                f"   {subtotal:.2f} {currency}",
                "",
                "9. VAT ({vat_percent:.2f}%):",
                f"   {subtotal:.2f} × {vat_percent/100:.4f} = {vat_amount:.2f} {currency}",
                "",
                "10. Discount:",
                f"   {discount_amount:.2f} {currency}",
                "",
                "11. GRAND TOTAL (8+9-10):",
                f"   {subtotal:.2f} + {vat_amount:.2f} - {discount_amount:.2f} = {grand_total:.2f} {currency}"
            ]
            
            # Update the formula details text edit with the breakdown
            self.formula_details.setPlainText("\n".join(breakdown))
            
        except Exception as e:
            print(f"Error in calculate_total_cost: {str(e)}")
