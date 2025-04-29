"""
Entry Tab - For creating new timesheet entries using direct edit table
"""
import os
import uuid
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QComboBox, QTextEdit, QPushButton, QDateEdit, QSpinBox, QDoubleSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QStyledItemDelegate, QGroupBox, QMessageBox, QFrame, QGridLayout,
    QScrollArea, QSizePolicy
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
        editor.setDisplayFormat("yyyy/MM/dd")
        
        # Set white background for better visibility
        editor.setStyleSheet("QDateEdit { background-color: white; color: black; }")
        
        return editor
        
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.EditRole)
        try:
            if value:
                if "/" in value:
                    date_obj = datetime.datetime.strptime(value, "%Y/%m/%d").date()
                else:
                    date_obj = datetime.datetime.strptime(value, "%Y-%m-%d").date()
                editor.setDate(date_obj)
            else:
                editor.setDate(datetime.datetime.now().date())
        except (ValueError, TypeError):
            editor.setDate(datetime.datetime.now().date())
        
    def setModelData(self, editor, model, index):
        date_str = editor.date().toString("yyyy/MM/dd")
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
        self.contract_agreement_input.setStyleSheet(f"QComboBox {{ {input_style} }}")
        
        # Create emergency request dropdown
        emergency_label = QLabel("Emergency Request?")
        self.emergency_request_input = QComboBox()
        self.emergency_request_input.addItems(["No", "Yes"])
        self.emergency_request_input.setStyleSheet(f"QComboBox {{ {input_style} }}")
        
        # Add fields to the first row
        client_po_row.addWidget(po_label)
        client_po_row.addWidget(self.po_number_input)
        client_po_row.addWidget(quotation_label)
        client_po_row.addWidget(self.quotation_number_input)
        client_po_row.addWidget(contract_label)
        client_po_row.addWidget(self.contract_agreement_input)
        client_po_row.addWidget(emergency_label)
        client_po_row.addWidget(self.emergency_request_input)
        
        # Create second row for client name
        client_row = QHBoxLayout()
        client_row.setSpacing(10)
        
        # Create widgets for client info
        client_label = QLabel("Client:")
        self.client_input = QLineEdit()
        self.client_input.setStyleSheet(input_style)
        
        # Add client name to second row
        client_row.addWidget(client_label)
        client_row.addWidget(self.client_input)
        client_row.addStretch(1)  # Add stretch to push everything to the left
        
        # Create service engineer row (moved to bottom)
        engineer_row = QHBoxLayout()
        engineer_row.setSpacing(10)
        
        # Create widgets for engineer info
        name_label = QLabel("Service Engineer Name:")
        self.engineer_name_input = QLineEdit()
        self.engineer_name_input.setStyleSheet(input_style)
        if self.user_info and 'first_name' in self.user_info:
            self.engineer_name_input.setText(self.user_info['first_name'])
        
        surname_label = QLabel("Surname:")
        self.engineer_surname_input = QLineEdit()
        self.engineer_surname_input.setStyleSheet(input_style)
        if self.user_info and 'last_name' in self.user_info:
            self.engineer_surname_input.setText(self.user_info['last_name'])
        
        work_type_label = QLabel("Work Type:")
        self.work_type_input = QComboBox()
        self.work_type_input.addItems(["", "Special Field Services", "Regular Field Services", "Consultation", "Emergency Support", "Other"])
        self.work_type_input.setEditable(True)
        self.work_type_input.setStyleSheet(f"QComboBox {{ {input_style} }}")
        
        tier_label = QLabel("Tier:")
        self.tier_input = QComboBox()
        self.tier_input.addItems(["", "Tier 1", "Tier 2", "Tier 3", "Tier 4"])
        self.tier_input.setEditable(True)
        self.tier_input.setStyleSheet(f"QComboBox {{ {input_style} }}")
        
        # Create engineer widgets layout - these will now be at the bottom
        engineer_row.addWidget(name_label)
        engineer_row.addWidget(self.engineer_name_input)
        engineer_row.addWidget(surname_label)
        engineer_row.addWidget(self.engineer_surname_input)
        engineer_row.addWidget(work_type_label)
        engineer_row.addWidget(self.work_type_input)
        engineer_row.addWidget(tier_label)
        engineer_row.addWidget(self.tier_input)
        engineer_row.addStretch(1)  # Push everything to the left
        
        # Create a row for client address
        client_address_row = QHBoxLayout()
        client_address_row.setSpacing(10)
        
        client_address_label = QLabel("Client Address:")
        self.client_address_input = QTextEdit()
        self.client_address_input.setFixedHeight(60)  # Limit height for paragraph input
        self.client_address_input.setStyleSheet(input_style)
        
        client_row.addWidget(client_label)
        client_row.addWidget(self.client_input)
        client_address_row.addWidget(client_address_label)
        client_address_row.addWidget(self.client_address_input)
        
        # Create a row for client representative information
        client_rep_row = QHBoxLayout()
        client_rep_row.setSpacing(10)
        
        client_rep_label = QLabel("Client Representative Name:")
        self.client_rep_input = QLineEdit()
        self.client_rep_input.setStyleSheet(input_style)
        
        client_phone_label = QLabel("Phone Number:")
        self.client_phone_input = QLineEdit()
        self.client_phone_input.setStyleSheet(input_style)
        
        client_email_label = QLabel("Email:")
        self.client_email_input = QLineEdit()
        self.client_email_input.setStyleSheet(input_style)
        
        client_rep_row.addWidget(client_rep_label)
        client_rep_row.addWidget(self.client_rep_input)
        client_rep_row.addWidget(client_phone_label)
        client_rep_row.addWidget(self.client_phone_input)
        client_rep_row.addWidget(client_email_label)
        client_rep_row.addWidget(self.client_email_input)
        
        # Add all rows to client layout in the correct order
        client_layout.addLayout(client_po_row)
        client_layout.addLayout(client_row)      # Client name now second
        client_layout.addLayout(client_address_row)
        client_layout.addLayout(client_rep_row)
        client_layout.addLayout(engineer_row)  # Service Engineer info at the bottom
        
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
        
        # Set reasonable initial row height with top alignment
        self.entries_table.verticalHeader().setDefaultSectionSize(80)  # Reduced from 180 to 80
        self.entries_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)  # Allow auto-expansion
        
        # Set minimum height for the table to ensure multiple rows are visible
        self.entries_table.setMinimumHeight(350)
        
        # Set the text alignment to top for all cells
        for col in range(self.entries_table.columnCount()):
            self.entries_table.horizontalHeaderItem(col).setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            
        # Make the table items' text align to the top
        self.entries_table.setStyleSheet(self.entries_table.styleSheet() + """
            QTableWidget::item {
                padding: 4px;
                alignment: top;
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
            QTableWidget::item { padding: 2px }
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
        
        # Save button
        save_button = QPushButton("Save Timesheet")
        save_button.clicked.connect(self.save_timesheet)
        
        # Clear Form button
        clear_button = QPushButton("Clear Form")
        clear_button.clicked.connect(self.clear_form)
        
        # Add buttons to layout
        button_layout.addWidget(add_row_button)
        button_layout.addWidget(remove_row_button)
        button_layout.addStretch(1)  # Push save and clear buttons to the right
        button_layout.addWidget(save_button)
        button_layout.addWidget(clear_button)
        
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
                background-color: white; 
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
        
        # Create Calculation Group
        calc_group = QGroupBox("Total Cost Calculation")
        calc_layout = QVBoxLayout(calc_group)
        
        # Create formula display label
        formula_label = QLabel("""Formula:\n((Service Hours + Report Preparation Hours) * Normal Hour Rate) + \n((Number of T&L day) * the selected T&L Rate) + \nEmergency Request Charge (If any) + \n(Offshore Daily Rate * counted Offshore day) + \nOther Transportation Charge""")
        calc_layout.addWidget(formula_label)
        
        # Create total cost display
        self.total_cost_label = QLabel("Total Cost: 0.00")
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        self.total_cost_label.setFont(font)
        calc_layout.addWidget(self.total_cost_label)
        
        # Add update button for calculation
        self.calculate_button = QPushButton("Calculate Total Cost")
        self.calculate_button.clicked.connect(self.calculate_total_cost)
        calc_layout.addWidget(self.calculate_button)
        
        # Add calculation group to service charge layout
        service_charge_layout.addWidget(calc_group)
        
        # Add the service charge group to main layout
        main_layout.addWidget(service_charge_group)
        
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
        today = datetime.datetime.now().date().strftime("%Y/%m/%d")
        
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
        except (ValueError, TypeError, IndexError) as e:
            equiv_item.setText("Error")
            # For debugging
            print(f"Error calculating equivalent hours: {str(e)}")
            
    def save_timesheet(self):
        """Save the timesheet to the data manager"""
        # Get client and engineer info
        client = self.client_input.text().strip()
        work_type = self.work_type_input.currentText().strip()
        tier = self.tier_input.currentText().strip()
        engineer_name = self.engineer_name_input.text().strip()
        engineer_surname = self.engineer_surname_input.text().strip()
        emergency_request = self.emergency_request_input.currentText() == "Yes"
        
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
        
        # Create timesheet entry
        timesheet = {
            'entry_id': entry_id,
            'client': client,
            'work_type': work_type,
            'tier': tier,
            'engineer_name': engineer_name,
            'engineer_surname': engineer_surname,
            'creation_date': datetime.datetime.now().strftime("%Y/%m/%d"),
            'time_entries': time_entries,
            'tool_usage': tool_entries,
            'report_description': report_description,
            'report_hours': report_hours,
            'emergency_request': emergency_request,
            'currency': self.currency_input.currentText(),
            'service_hour_rate': self.service_rate_input.value(),
            'tool_usage_rate': self.tool_rate_input.value(),
            'tl_rate_short': self.tl_short_input.value(),
            'tl_rate_long': self.tl_long_input.value(),
            'offshore_day_rate': self.offshore_rate_input.value(),
            'emergency_rate': self.emergency_rate_input.value(),
            'other_transport_charge': self.transport_charge_input.value(),
            'other_transport_note': self.transport_note_input.toPlainText().strip(),
            'total_service_charge': self.extract_numeric_value(self.total_cost_label.text())
        }
        
        # Save to data manager
        try:
            self.data_manager.save_timesheet(timesheet)
            QMessageBox.information(self, "Success", "Timesheet saved successfully.")
            
            # Emit signal
            self.entry_saved.emit(timesheet['entry_id'])
            
            # Clear form
            self.clear_form()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving timesheet: {str(e)}")
    
    def clear_form(self):
        """Clear the form after saving"""
        # Clear all rows in the table
        self.entries_table.setRowCount(0)
        
        # Add a fresh empty row
        self.add_new_row()
        
        # Clear input fields
        self.client_input.clear()
        self.work_type_input.setCurrentIndex(0)
        self.tier_input.setCurrentIndex(0)
        
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
        today = datetime.datetime.now().date().strftime("%Y/%m/%d")
        tomorrow = (datetime.datetime.now().date() + datetime.timedelta(days=1)).strftime("%Y/%m/%d")
        
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
            
            print(f"Tool cell changed at row {row}, column {column} - summary updated")
        except Exception as e:
            print(f"Error handling tool cell change: {str(e)}")
    
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
            
            if '/' in start_text:
                start_date = datetime.datetime.strptime(start_text, "%Y/%m/%d").date()
            else:
                start_date = datetime.datetime.strptime(start_text, "%Y-%m-%d").date()
                
            if '/' in end_text:
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
            
            # Print debug info about date ranges
            print("\nDIRECT: Date ranges collected:")
            for date_range, days in date_ranges.items():
                print(f"DIRECT: Date range: {date_range}, Days: {days}")
            
            # Calculate total days by summing all unique date ranges
            # This ensures tools used in the same period are counted only once
            total_days = sum(date_ranges.values())
            print(f"DIRECT: Total tool days calculated: {total_days}")
            
            # Format the tools used text
            tool_descriptions = []
            for tool_name, count in tools_used.items():
                tool_descriptions.append(f"{count} {tool_name}")
            
            # Join with 'and' for better readability
            if len(tool_descriptions) > 1:
                text = "Tools Used: " + " and ".join(tool_descriptions)
            else:
                text = "Tools Used: " + ", ".join(tool_descriptions)
                
            print(f"DIRECT UPDATE: Setting label to '{text}'")
            
            # Now we know the labels exist, update them directly
            self.tools_used_label.setText(text)
            self.total_tool_days_label.setText(f"Total Special Tools Usage Day: {total_days}")
            print("Tool summary labels updated successfully")
                
        except Exception as e:
            print(f"CRITICAL ERROR in direct update: {str(e)}")
    
    def update_tool_summary(self):
        """Calculate and update the tool usage summary labels"""
        print("*** update_tool_summary called ***")
        
        # We no longer call the direct update method from here to avoid circular updates
        # This prevents overwriting of the correct total_days value
        # self.update_tool_summary_direct() <- Removed this line
        
        try:
            # Get the row count
            row_count = self.tool_table.rowCount()
            print(f"Tool table has {row_count} rows")
            
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
                print(f"MAIN: Row {row}: Tool={tool_name}, Amount={amount}, Days={days}, DateRange={date_range_key}")
                
                # Track the maximum number of days for this date range
                if date_range_key in date_ranges:
                    old_days = date_ranges[date_range_key]
                    date_ranges[date_range_key] = max(old_days, days)
                    print(f"MAIN: Found existing date range {date_range_key}: old days={old_days}, new days={days}, using max={date_ranges[date_range_key]}")
                else:
                    date_ranges[date_range_key] = days
                    print(f"MAIN: New date range {date_range_key}: days={days}")
            
            # Print debug info about date ranges
            print("\nMAIN: Date ranges collected:")
            for date_range, days in date_ranges.items():
                print(f"MAIN: Date range: {date_range}, Days: {days}")
                
            # Calculate total days by summing all unique date ranges
            # This ensures tools used in the same period are counted only once
            total_tool_days = sum(date_ranges.values())
            print(f"MAIN: Total tool days calculated: {total_tool_days}")
            
            # Create output text
            parts = []
            for tool_name, count in tools_used.items():
                parts.append(f"{count} {tool_name}")
                
            if parts:
                text = f"Tools Used: {', '.join(parts)}"
                print(f"Setting label to: {text}")
                
                # Update labels
                if hasattr(self, 'tools_used_label'):
                    self.tools_used_label.setText(text)
                    self.tools_used_label.repaint()
                    
                if hasattr(self, 'total_tool_days_label'):
                    self.total_tool_days_label.setText(f"Total Special Tools Usage Day: {total_tool_days}")
                    self.total_tool_days_label.repaint()
        
        except Exception as e:
            print(f"Error in update_tool_summary: {str(e)}")
            
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
        
        # Calculate service hours
        total_service_hours = 0
        regular_hours = 0
        ot15_hours = 0
        ot2_hours = 0
        
        # Count travel days (T&L)
        short_travel_days = 0  # < 80 km
        long_travel_days = 0   # > 80 km
        
        # Count offshore days
        offshore_days = 0
        
        # Process all time entries
        for row in range(self.entries_table.rowCount()):
            # Check if we have all required items
            date_item = self.entries_table.item(row, 0)
            start_item = self.entries_table.item(row, 1)
            end_item = self.entries_table.item(row, 2)
            rest_item = self.entries_table.item(row, 3)
            ot_item = self.entries_table.item(row, 5)
            offshore_item = self.entries_table.item(row, 6)
            tl_item = self.entries_table.item(row, 7)
            travel_far_item = self.entries_table.item(row, 8)
            
            if not all([date_item, start_item, end_item, rest_item, ot_item, offshore_item, tl_item, travel_far_item]):
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
            hours_worked = (end_hour - start_hour) - rest_hours
            if hours_worked <= 0:
                continue
                
            # Add to total service hours based on overtime rate
            total_service_hours += hours_worked
            ot_rate = ot_item.text()
            if ot_rate == "Regular":
                regular_hours += hours_worked
            elif ot_rate == "OT1.5":
                ot15_hours += hours_worked
            elif ot_rate == "OT2.0":
                ot2_hours += hours_worked
                
            # Check for offshore work
            if offshore_item.text() == "Yes":
                offshore_days += 1
                
            # Check for travel (T&L)
            if tl_item.text() == "Yes":
                if travel_far_item.text() == "Yes":  # > 80 km
                    long_travel_days += 1
                else:  # < 80 km
                    short_travel_days += 1
        
        # Calculate total tool usage cost
        total_tool_days = 0
        for row in range(self.tool_table.rowCount()):
            days_item = self.tool_table.item(row, 4)
            if days_item and days_item.text():
                try:
                    days = int(days_item.text())
                    total_tool_days += days
                except ValueError:
                    pass
        
        # Calculate costs
        service_hours_cost = (total_service_hours + report_hours) * service_rate
        tool_usage_cost = total_tool_days * tool_rate
        travel_cost = (short_travel_days * tl_short_rate) + (long_travel_days * tl_long_rate)
        offshore_cost = offshore_days * offshore_rate
        emergency_cost = emergency_rate if is_emergency else 0
        
        # Calculate total cost
        total_cost = service_hours_cost + tool_usage_cost + travel_cost + offshore_cost + emergency_cost + other_transport
        
        # Update the label with the formatted total cost
        self.total_cost_label.setText(f"Total Cost: {total_cost:.2f} {currency}")
