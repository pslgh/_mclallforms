"""
View Tab - For viewing timesheet entry details in A4 portrait format
"""
import os
import datetime
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea,
    QGroupBox, QFrame, QSizePolicy, QMessageBox, QFileDialog,
    QGridLayout, QFormLayout, QSpacerItem
)
from PySide6.QtCore import Qt, Signal, QSize, QDate
from PySide6.QtGui import (
    QFont, QPixmap, QPainter, QPdfWriter, 
    QPageSize, QColor, QPen, QBrush
)

class ViewTab(QWidget):
    """Tab for viewing timesheet entry details in A4 portrait layout"""
    
    # Signal for closing the tab
    close_requested = Signal()
    
    # Constants for A4 paper size (in points at 72 DPI)
    A4_WIDTH = 595
    A4_HEIGHT = 842
    MARGIN = 20  # Narrow margins as requested
    
    def __init__(self, parent, entry, data_manager):
        """Initialize the ViewTab"""
        super().__init__(parent)
        self.parent = parent
        self.entry = entry
        self.data_manager = data_manager
        
        # Path to logo
        self.logo_path = str(Path(os.getcwd()) / "assets" / "logo" / "mcllogo.png")
        
        # Initialize UI
        self.setup_ui()
    
    def setup_ui(self):
        """Set up the user interface"""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Add control buttons at the top
        controls_layout = QHBoxLayout()
        
        # Back/Close button
        close_button = QPushButton("Close")
        close_button.setFixedWidth(100)
        close_button.clicked.connect(self.close_requested.emit)
        
        # Add Preview in PDF button
        self.export_button = QPushButton("Preview in PDF")
        self.export_button.clicked.connect(self.export_to_pdf)
        self.export_button.setStyleSheet(
            "background-color:#1949d8; color: white; padding: 8px; border-radius: 4px;"
        )
        
        # Add buttons to controls layout
        controls_layout.addWidget(close_button)
        controls_layout.addWidget(self.export_button)
        controls_layout.addStretch(1)
        
        # Add controls to main layout
        main_layout.addLayout(controls_layout)
        
        # Create scroll area for the A4 page
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Create A4 page container
        self.page_widget = QWidget()
        self.page_widget.setFixedWidth(self.A4_WIDTH)
        self.page_widget.setStyleSheet("background-color: white;")
        
        # Page layout with narrow margins
        self.page_layout = QVBoxLayout(self.page_widget)
        self.page_layout.setContentsMargins(self.MARGIN, self.MARGIN, self.MARGIN, self.MARGIN)
        self.page_layout.setSpacing(10)
        
        # Create the report content
        self.create_header()
        self.create_project_info()
        self.create_time_entries()
        self.create_tool_usage()
        self.create_calculation_summary()
        
        # Add spacing at the bottom
        self.page_layout.addStretch(1)
        
        # Set the scroll area's widget and add to main layout
        scroll_area.setWidget(self.page_widget)
        main_layout.addWidget(scroll_area)
        
    def create_header(self):
        """Create the header section with logo and title"""
        # Header container
        header_layout = QGridLayout()
        header_layout.setContentsMargins(0, 0, 0, 10)
        
        # Logo on the left
        logo_label = QLabel()
        logo_pixmap = QPixmap(self.logo_path)
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(100, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("MCL LOGO")
            logo_label.setStyleSheet("font-weight: bold; color: #555;")
        logo_label.setFixedSize(100, 50)
        
        # Title in the center
        title_label = QLabel("Service Timesheet\n and\n Charge Summary")
        title_label.setAlignment(Qt.AlignCenter)
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #2c3e50; font-size: 16px; font-weight: bold;")
        
        # Report ID on the right
        entry_id = self.safe_get_attribute('entry_id', '')
        id_label = QLabel(f"Report ID: {entry_id}")
        id_label.setAlignment(Qt.AlignRight)
        id_label.setStyleSheet("font-weight: bold;")
        
        # Date on the right
        creation_date = self.safe_get_attribute('creation_date', datetime.datetime.now().strftime('%Y-%m-%d'))
        date_label = QLabel(f"Date: {creation_date}")
        date_label.setAlignment(Qt.AlignRight)
        
        # Add elements to the header grid
        header_layout.addWidget(logo_label, 0, 0, 2, 1)  # Logo spans 2 rows
        header_layout.addWidget(title_label, 0, 1, 1, 1) # Title in middle
        header_layout.addWidget(id_label, 0, 2, 1, 1)    # ID on right top
        header_layout.addWidget(date_label, 1, 2, 1, 1)  # Date on right bottom
        
        # Make the middle column stretch
        header_layout.setColumnStretch(1, 1)
        
        # Add header to the page layout
        self.page_layout.addLayout(header_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #2c3e50; min-height: 2px;")
        self.page_layout.addWidget(separator)
        
    def safe_get_attribute(self, attr_name, default_value=None, fallback_attrs=None, entry=None):
        """Safely get an attribute value with fallbacks
        
        Args:
            attr_name: The primary attribute name to check
            default_value: Default value if not found
            fallback_attrs: List of fallback attribute names to check
            
        Returns:
            The attribute value or default value
        """
        # Use provided entry or self.entry
        target_entry = entry if entry is not None else self.entry
        
        # Check if entry has attribute directly
        if hasattr(target_entry, attr_name):
            return getattr(target_entry, attr_name)
            
        # Check if entry has _raw_data
        if hasattr(target_entry, '_raw_data') and isinstance(target_entry._raw_data, dict):
            if attr_name in target_entry._raw_data:
                return target_entry._raw_data[attr_name]
        
        # If entry is a dictionary
        if isinstance(target_entry, dict) and attr_name in target_entry:
            return target_entry[attr_name]
        
        # Try fallback attributes
        if fallback_attrs:
            for fallback in fallback_attrs:
                # Direct attribute check
                if hasattr(target_entry, fallback):
                    return getattr(target_entry, fallback)
                
                # Raw data check
                if hasattr(target_entry, '_raw_data') and isinstance(target_entry._raw_data, dict):
                    if fallback in target_entry._raw_data:
                        return target_entry._raw_data[fallback]
                
                # Dictionary check
                if isinstance(target_entry, dict) and fallback in target_entry:
                    return target_entry[fallback]
        
        # Return default if nothing found
        return default_value
        
    def create_project_info(self):
        """Create the project information section with client and service details"""
        # Project Information Group
        project_group = QGroupBox("Project Information")
        project_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Create a fixed 2-column grid layout with very tight spacing
        project_layout = QGridLayout(project_group)
        project_layout.setVerticalSpacing(6)  # Minimal spacing between rows
        project_layout.setHorizontalSpacing(5)  # Minimal spacing between columns
        project_layout.setContentsMargins(2, 10, 2, 10)  # Tiny left/right margins, normal top/bottom
        
        # Get all data values
        po_number = self.safe_get_attribute('purchasing_order_number', 'N/A', ['po_number'])
        quotation = self.safe_get_attribute('quotation_number', 'N/A')
        contract = self.safe_get_attribute('under_contract_agreement', False, ['Contract Agreement'])
        contract_text = "Yes" if contract else "No"
        emergency = self.safe_get_attribute('emergency_request', False, ['Emergency Request'])
        emergency_text = "Yes" if emergency else "No"
        
        client = self.safe_get_attribute('client_company_name', 'N/A', ['client', 'Client'])
        client_address = self.safe_get_attribute('client_address', 'N/A', ['Client Address'])
        
        client_rep = self.safe_get_attribute('client_representative_name', 'N/A', 
                                        ['client_representative', 'Client Representative Name'])
        rep_phone = self.safe_get_attribute('client_representative_phone', 'N/A', ['Phone Number'])
        rep_email = self.safe_get_attribute('client_representative_email', 'N/A', ['Email'])
        
        project_name = self.safe_get_attribute('project_name', 'N/A')
        project_description = self.safe_get_attribute('project_description', 'N/A')
        
        engineer_name = self.safe_get_attribute('service_engineer_name', '', 
                                            ['engineer_name', 'Service Engineer Name'])
        engineer_surname = self.safe_get_attribute('service_engineer_surname', '', 
                                              ['engineer_surname', 'Surname'])
        work_type = self.safe_get_attribute('work_type', 'N/A', ['Work Type'])
        
        # Define styles for form elements with reduced padding and better wrapping
        label_style = "color: #000000; font-weight: bold; padding-right: 3px; padding-top: 2px;"
        value_style = "color: #000000; background-color: #FFFFD0; border: 1px solid #CCCCCC; border-radius: 3px; padding: 2px 3px; min-height: 18px;"
        value_multi_style = value_style + " min-height: 50px;"
        
        # Create the label-value pairs function with optimized dimensions
        def create_form_field(row, col, label_text, value, multi_line=False):
            # Create label with word wrap and fixed height for multi-line labels
            label = QLabel(label_text)
            label.setStyleSheet(label_style)
            label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Right-align labels
            label.setWordWrap(True)  # Enable word wrapping for long label text
            label.setFixedWidth(95 if col == 0 else 100)  # Narrower fixed width for labels
            # For long labels, set minimum height to allow two lines if needed
            if len(label_text) > 15:
                label.setMinimumHeight(32)
            
            # Create value display that looks like a form field
            value_label = QLabel(value)
            value_label.setTextInteractionFlags(Qt.TextSelectableByMouse)  # Allow text selection
            value_label.setWordWrap(True)  # Enable word wrap for long text
            value_label.setTextFormat(Qt.PlainText)  # Ensure proper text wrapping
            value_label.setStyleSheet(value_multi_style if multi_line else value_style)
            
            # Set different size policies for left vs right columns
            if col == 0:  # Left column - restrict width
                value_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Preferred)
                value_label.setFixedWidth(210)  # Strictly limit width of left column values
                # Ensure text wrapping works properly with fixed width
                value_label.setMinimumWidth(210)  # Make sure the minimum width is set too
            else:  # Right column - expand freely
                value_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            
            # For multi-line fields, ensure they are configured properly for text wrapping
            if multi_line:
                # Configure for optimal text wrapping with top-left alignment
                value_label.setAlignment(Qt.AlignTop | Qt.AlignLeft)  # Align to top-left
                # Force explicit text wrapping settings
                value_label.setWordWrap(True)
                value_label.setTextFormat(Qt.PlainText)
                
                # For special fields that need extra wrapping help
                if col == 0 and (label_text == "Project Name:" or 
                                 label_text == "Project Description:" or 
                                 label_text == "Address:"):
                    # Explicit text wrapping configuration for these fields
                    value_label.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)
                    value_label.setStyleSheet(value_multi_style + "padding: 4px;")
            
            # Add to layout with proper alignment
            project_layout.addWidget(label, row, col*2)
            project_layout.addWidget(value_label, row, col*2 + 1)
            return value_label
        
        # ROW 0: PO Number and Quotation Number
        create_form_field(0, 0, "Purchasing\nOrder #:", po_number)  # Split into two lines
        create_form_field(0, 1, "Quotation #:", quotation)
        
        # ROW 1: Contract and Emergency Request
        create_form_field(1, 0, "Under Contract\nAgreement?:", contract_text)  # Split into two lines
        create_form_field(1, 1, "Emergency\nRequest?:", emergency_text)  # Split into two lines
        
        # ROW 2: Client and Client Representative
        create_form_field(2, 0, "Client:", client)
        create_form_field(2, 1, "Client\nRepresentative:", client_rep)  # Split into two lines
        
        # ROW 3: Address and Phone Number
        create_form_field(3, 0, "Address:", client_address, multi_line=True)
        # Note: No need to set minimum height here as it's now handled in the create_form_field function for multi_line=True
        create_form_field(3, 1, "Phone Number:", rep_phone)
        
        # ROW 4: Project Name and Email
        create_form_field(4, 0, "Project\nName:", project_name, multi_line=True)
        # Add Email field
        create_form_field(4, 1, "Email:", rep_email, multi_line=True)
                
        # ROW 5: Project Description and Service Engineer
        create_form_field(5, 0, "Project\nDescription:", project_description, multi_line=True)
        create_form_field(5, 1, "Service\nEngineer Name:", engineer_name)  # Split into two lines

        # ROW 6: Extra space for left column, Work Type and Suremane
        create_form_field(6, 0, "Work Type:", work_type, multi_line=True)
        create_form_field(6, 1, "Surname:", engineer_surname, multi_line=True)
        
        # Set column stretching to keep left column compact but expand right column
        project_layout.setColumnStretch(0, 0)  # Left labels column - no stretch (fixed width)
        project_layout.setColumnStretch(1, 1)  # Left values column - minimal fixed stretch
        project_layout.setColumnStretch(2, 0)  # Right labels column - no stretch (fixed width)
        project_layout.setColumnStretch(3, 12)  # Right values column - stretch much more
        
        # Add the project group to page layout
        self.page_layout.addWidget(project_group)
        self.page_layout.addSpacing(10)
        
    def create_time_entries(self):
        """Create the time entries table"""
        # Time Entries GroupBox
        time_group = QGroupBox("Time Entries")
        time_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                border: none;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #d0d0d0;
            }
        """)
        
        # Time entries layout
        time_layout = QVBoxLayout(time_group)
        time_layout.setContentsMargins(5, 20, 5, 5)
        
        # Create table for time entries
        time_table = QTableWidget()
        time_table.setAlternatingRowColors(True)
        time_table.setEditTriggers(QTableWidget.NoEditTriggers)
        time_table.verticalHeader().setVisible(False)
        
        # Set up columns
        time_table.setColumnCount(8)
        time_table.setHorizontalHeaderLabels([
            "Date", "Start", "End", "Break (hrs)", "Description", "OT Rate", "Offshore", "Travel"
        ])
        
        # Get time entries from the entry
        time_entries = self.safe_get_attribute('time_entries', [])
        
        if time_entries:
            # Set row count
            time_table.setRowCount(len(time_entries))
            
            # Populate rows
            for i, entry in enumerate(time_entries):
                # Date
                date_item = QTableWidgetItem(self.safe_get_attribute('date', 'N/A', fallback_attrs=None, entry=entry))
                date_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 0, date_item)
                
                # Start Time - Format from 0800 to 08:00
                start_time = self.safe_get_attribute('start_time', '', fallback_attrs=None, entry=entry)
                if len(start_time) == 4:
                    start_time = f"{start_time[:2]}:{start_time[2:]}"
                start_item = QTableWidgetItem(start_time)
                start_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 1, start_item)
                
                # End Time - Format from 1700 to 17:00
                end_time = self.safe_get_attribute('end_time', '', fallback_attrs=None, entry=entry)
                if len(end_time) == 4:
                    end_time = f"{end_time[:2]}:{end_time[2:]}"
                end_item = QTableWidgetItem(end_time)
                end_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 2, end_item)
                
                # Break Hours
                rest_hours = self.safe_get_attribute('rest_hours', 0, fallback_attrs=None, entry=entry)
                rest_item = QTableWidgetItem(str(rest_hours))
                rest_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 3, rest_item)
                
                # Description
                description = self.safe_get_attribute('description', '', fallback_attrs=None, entry=entry)
                desc_item = QTableWidgetItem(description)
                time_table.setItem(i, 4, desc_item)
                
                # Overtime Rate
                ot_rate = self.safe_get_attribute('overtime_rate', '1', fallback_attrs=None, entry=entry)
                if ot_rate == '1': ot_display = "1.0x"
                elif ot_rate == '1.5': ot_display = "1.5x"
                elif ot_rate == '2': ot_display = "2.0x"
                elif ot_rate == '3': ot_display = "3.0x"
                else: ot_display = ot_rate
                ot_item = QTableWidgetItem(ot_display)
                ot_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 5, ot_item)
                
                # Offshore
                offshore = self.safe_get_attribute('offshore', False, fallback_attrs=None, entry=entry)
                offshore_text = "Yes" if offshore else "No"
                offshore_item = QTableWidgetItem(offshore_text)
                offshore_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 6, offshore_item)
                
                # Travel
                travel_count = self.safe_get_attribute('travel_count', False, fallback_attrs=None, entry=entry)
                travel_far = self.safe_get_attribute('travel_far_distance', False, fallback_attrs=None, entry=entry)
                travel_short = self.safe_get_attribute('travel_short_distance', False, fallback_attrs=None, entry=entry)
                
                if travel_count:
                    if travel_far:
                        travel_text = "Far"
                    elif travel_short:
                        travel_text = "Short"
                    else:
                        travel_text = "Yes"
                else:
                    travel_text = "No"
                
                travel_item = QTableWidgetItem(travel_text)
                travel_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 7, travel_item)
                
                # Set row height
                time_table.setRowHeight(i, 30)  # Consistent row height
        else:
            # No time entries available
            time_table.setRowCount(1)
            no_data_item = QTableWidgetItem("No time entries available")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            time_table.setSpan(0, 0, 1, 8)  # Span all columns
            time_table.setItem(0, 0, no_data_item)
        
        # Set column widths
        time_table.setColumnWidth(0, 80)   # Date
        time_table.setColumnWidth(1, 60)   # Start
        time_table.setColumnWidth(2, 60)   # End
        time_table.setColumnWidth(3, 70)   # Break
        time_table.setColumnWidth(4, 200)  # Description - wider for details
        time_table.setColumnWidth(5, 60)   # OT Rate
        time_table.setColumnWidth(6, 60)   # Offshore
        time_table.setColumnWidth(7, 60)   # Travel
        
        # Add table to layout
        time_layout.addWidget(time_table)
        
        # Add to page layout
        self.page_layout.addWidget(time_group)
        self.page_layout.addSpacing(10)
        
    def create_tool_usage(self):
        """Create the special tool usage section"""
        # Tool Usage GroupBox
        tool_group = QGroupBox("Special Tool Usage")
        tool_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
            QTableWidget {
                gridline-color: #d0d0d0;
                border: none;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 5px;
                font-weight: bold;
                border: 1px solid #d0d0d0;
            }
        """)
        
        # Tool usage layout
        tool_layout = QVBoxLayout(tool_group)
        tool_layout.setContentsMargins(5, 20, 5, 5)
        
        # Create table for tool usage
        tool_table = QTableWidget()
        tool_table.setAlternatingRowColors(True)
        tool_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tool_table.verticalHeader().setVisible(False)
        
        # Set up columns
        tool_table.setColumnCount(5)
        tool_table.setHorizontalHeaderLabels([
            "Tool Name", "Amount", "Start Date", "End Date", "Total Days"
        ])
        
        # Get tool usage entries
        tool_entries = self.safe_get_attribute('tool_usage', [])
        
        if tool_entries:
            # Set row count
            tool_table.setRowCount(len(tool_entries))
            
            # Populate rows
            for i, tool in enumerate(tool_entries):
                # Tool Name
                name = self.safe_get_attribute('tool_name', 'N/A', fallback_attrs=None, entry=tool)
                name_item = QTableWidgetItem(name)
                tool_table.setItem(i, 0, name_item)
                
                # Amount
                amount = self.safe_get_attribute('amount', 1, fallback_attrs=None, entry=tool)
                amount_item = QTableWidgetItem(str(amount))
                amount_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 1, amount_item)
                
                # Start Date
                start_date = self.safe_get_attribute('start_date', '', fallback_attrs=None, entry=tool)
                start_item = QTableWidgetItem(start_date)
                start_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 2, start_item)
                
                # End Date
                end_date = self.safe_get_attribute('end_date', '', fallback_attrs=None, entry=tool)
                end_item = QTableWidgetItem(end_date)
                end_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 3, end_item)
                
                # Total Days
                days = self.safe_get_attribute('total_days', 0, fallback_attrs=None, entry=tool)
                days_item = QTableWidgetItem(str(days))
                days_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 4, days_item)
                
                # Set row height
                tool_table.setRowHeight(i, 30)  # Consistent row height
        else:
            # No tool usage data
            tool_table.setRowCount(1)
            no_data_item = QTableWidgetItem("No special tools used")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            tool_table.setSpan(0, 0, 1, 5)  # Span all columns
            tool_table.setItem(0, 0, no_data_item)
        
        # Set column widths
        tool_table.setColumnWidth(0, 180)  # Tool Name
        tool_table.setColumnWidth(1, 70)   # Amount
        tool_table.setColumnWidth(2, 90)   # Start Date
        tool_table.setColumnWidth(3, 90)   # End Date
        tool_table.setColumnWidth(4, 90)   # Total Days
        
        # Add table to layout
        tool_layout.addWidget(tool_table)
        
        # Add tool usage summary if available
        tool_summary = self.safe_get_attribute('tool_usage_summary', None)
        if tool_summary:
            total_days = self.safe_get_attribute('total_tool_usage_days', 0, entry=tool_summary)
            tools_used = self.safe_get_attribute('tools_used', '', entry=tool_summary)
            
            if total_days > 0 or tools_used:
                summary_layout = QHBoxLayout()
                summary_layout.setContentsMargins(5, 10, 5, 5)
                
                if tools_used:
                    tools_label = QLabel(f"<b>Tools Used:</b> {tools_used}")
                    summary_layout.addWidget(tools_label)
                
                if total_days > 0:
                    days_label = QLabel(f"<b>Total Days:</b> {total_days}")
                    days_label.setAlignment(Qt.AlignRight)
                    summary_layout.addWidget(days_label)
                
                tool_layout.addLayout(summary_layout)
        
        # Add to page layout
        self.page_layout.addWidget(tool_group)
        self.page_layout.addSpacing(10)
        
    def create_calculation_summary(self):
        """Create the calculation summary and financial details section"""
        # Get currency for formatting
        currency = self.safe_get_attribute('currency', 'THB')
        
        # Create a container with two columns - rates and summary
        summary_container = QHBoxLayout()
        
        # ------ LEFT COLUMN: Service Rates ------
        rates_group = QGroupBox("Service Rates")
        rates_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Create form layout for rates
        rates_layout = QFormLayout(rates_group)
        rates_layout.setVerticalSpacing(8)
        rates_layout.setContentsMargins(10, 20, 10, 10)
        
        # Add service rates
        rates_layout.addRow("Service Hour Rate:", 
            QLabel(f"{currency} {self.safe_get_attribute('service_hour_rate', 0):,.2f}"))
        rates_layout.addRow("Tool Usage Rate:", 
            QLabel(f"{currency} {self.safe_get_attribute('tool_usage_rate', 0):,.2f}"))
        rates_layout.addRow("T&L Rate (<80km):", 
            QLabel(f"{currency} {self.safe_get_attribute('tl_rate_short', 0):,.2f}"))
        rates_layout.addRow("T&L Rate (>80km):", 
            QLabel(f"{currency} {self.safe_get_attribute('tl_rate_long', 0):,.2f}"))
        rates_layout.addRow("Offshore Day Rate:", 
            QLabel(f"{currency} {self.safe_get_attribute('offshore_day_rate', 0):,.2f}"))
        rates_layout.addRow("Emergency Rate:", 
            QLabel(f"{currency} {self.safe_get_attribute('emergency_rate', 0):,.2f}"))
        
        # ------ RIGHT COLUMN: Time Summary ------
        summary_group = QGroupBox("Time Summary")
        summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Create form layout for summary
        summary_layout = QFormLayout(summary_group)
        summary_layout.setVerticalSpacing(8)
        summary_layout.setContentsMargins(10, 20, 10, 10)
        
        # Get time summary data
        time_summary = self.safe_get_attribute('time_summary', {})
        if time_summary:
            # Regular hours
            reg_hours = self.safe_get_attribute('total_regular_hours', 0, entry=time_summary)
            summary_layout.addRow("Regular Hours:", QLabel(f"{reg_hours:.1f}"))
            
            # OT hours 1.5x
            ot_15x_hours = self.safe_get_attribute('total_ot_1_5x_hours', 0, entry=time_summary)
            summary_layout.addRow("OT 1.5X Hours:", QLabel(f"{ot_15x_hours:.1f}"))
            
            # OT hours 2.0x
            ot_2x_hours = self.safe_get_attribute('total_ot_2_0x_hours', 0, entry=time_summary)
            summary_layout.addRow("OT 2.0X Hours:", QLabel(f"{ot_2x_hours:.1f}"))
            
            # Total equivalent hours
            equiv_hours = self.safe_get_attribute('total_equivalent_hours', 0, entry=time_summary)
            
            # Make the total bold
            total_label = QLabel(f"<b>{equiv_hours:.1f}</b>")
            total_label.setTextFormat(Qt.RichText)
            summary_layout.addRow("<b>Total Hours:</b>", total_label)
            
            # Travel days
            tl_short = self.safe_get_attribute('total_tl_short_days', 0, entry=time_summary)
            tl_long = self.safe_get_attribute('total_tl_long_days', 0, entry=time_summary)
            
            if tl_short > 0:
                summary_layout.addRow("T&L (<80km) Days:", QLabel(f"{tl_short}"))
            
            if tl_long > 0:
                summary_layout.addRow("T&L (>80km) Days:", QLabel(f"{tl_long}"))
            
            # Offshore days
            offshore_days = self.safe_get_attribute('total_offshore_days', 0, entry=time_summary)
            if offshore_days > 0:
                summary_layout.addRow("Offshore Days:", QLabel(f"{offshore_days}"))
        else:
            # No time summary available, add placeholder
            summary_layout.addRow("", QLabel("No time summary available"))
        
        # ------ MIDDLE COLUMN: Tool Usage Summary ------
        tool_summary_group = QGroupBox("Special Tool Usage")
        tool_summary_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 16px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        # Create form layout for tool summary
        tool_summary_layout = QFormLayout(tool_summary_group)
        tool_summary_layout.setVerticalSpacing(8)
        tool_summary_layout.setContentsMargins(10, 20, 10, 10)
        
        # Get tool summary data
        tool_summary = self.safe_get_attribute('tool_usage_summary', {})
        if tool_summary:
            tools_used = self.safe_get_attribute('tools_used', '', entry=tool_summary)
            total_days = self.safe_get_attribute('total_tool_usage_days', 0, entry=tool_summary)
            
            if tools_used:
                tool_summary_layout.addRow("Tools Used:", QLabel(f"{tools_used}"))
            
            if total_days > 0:
                # Make the total bold
                days_label = QLabel(f"<b>{total_days}</b>")
                days_label.setTextFormat(Qt.RichText)
                tool_summary_layout.addRow("<b>Total Tool Days:</b>", days_label)
        else:
            # No tool summary available, add placeholder
            tool_summary_layout.addRow("", QLabel("No tool usage data"))
        
        # Add all groups to the container
        summary_container.addWidget(rates_group)
        summary_container.addWidget(summary_group)
        summary_container.addWidget(tool_summary_group)
        
        # Add the container to page layout
        self.page_layout.addLayout(summary_container)
        
        # ------ FINAL CALCULATIONS ------
        calc_group = QGroupBox("Calculation Results")
        calc_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 16px;
                background-color: #f8f9fa;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        calc_layout = QVBoxLayout(calc_group)
        calc_layout.setContentsMargins(15, 20, 15, 15)
        
        # Get total cost calculation
        total_calc = self.safe_get_attribute('total_cost_calculation', {})
        total_charge = self.safe_get_attribute('total_service_charge', 0)
        
        # Create the total charge display
        total_label = QLabel(f"<b>Total Service Charge: {currency} {total_charge:,.2f}</b>")
        total_label.setStyleSheet("""
            font-size: 16px;
            color: #2c3e50;
            padding: 10px;
            background-color: #ecf0f1;
            border-radius: 4px;
        """)
        total_label.setAlignment(Qt.AlignCenter)
        calc_layout.addWidget(total_label)
        
        # Add detailed breakdown if available
        if total_calc:
            # Create a table for cost components with expanded visible area
            breakdown = QTableWidget()
            breakdown.setAlternatingRowColors(True)
            breakdown.setEditTriggers(QTableWidget.NoEditTriggers)
            breakdown.verticalHeader().setVisible(False)
            breakdown.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
            breakdown.setMinimumHeight(525)  # Increase minimum height to show all rows
            breakdown.setStyleSheet("""
                gridline-color: #d0d0d0;
                alternate-background-color:#dbecab;
                background-color: white;
            """)
            
            # Set columns (removed Details column per request)
            breakdown.setColumnCount(2)
            breakdown.setHorizontalHeaderLabels(["Item", "Amount"])
            
            # Helper function to add rows
            row_index = 0
            def add_cost_row(label, amount, details=""):
                nonlocal row_index
                breakdown.insertRow(row_index)
                
                # Item label with consistent left alignment
                item_label = QTableWidgetItem(label)
                item_label.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)  # Consistent left alignment
                breakdown.setItem(row_index, 0, item_label)
                
                # Amount with currency formatting
                amount_item = QTableWidgetItem(f"{currency} {amount:,.2f}")
                amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                breakdown.setItem(row_index, 1, amount_item)
                
                row_index += 1
            
            # Add cost components
            service_hours_cost = self.safe_get_attribute('service_hours_cost', 0, entry=total_calc)
            if service_hours_cost > 0:
                add_cost_row("On-Site Service", service_hours_cost)
            
            # Add report preparation cost
            report_cost = self.safe_get_attribute('report_preparation_cost', 0, entry=total_calc)
            if report_cost > 0:
                add_cost_row("Report Preparation", report_cost)
            
            tool_usage_cost = self.safe_get_attribute('tool_usage_cost', 0, entry=total_calc)
            if tool_usage_cost > 0:
                add_cost_row("Special Tool Usage", tool_usage_cost)
            
            transport_short = self.safe_get_attribute('transportation_short_cost', 0, entry=total_calc)
            if transport_short > 0:
                add_cost_row("T&L (<80km)", transport_short)
            
            # Always show these rows, even with zero values
            transport_long = self.safe_get_attribute('transportation_long_cost', 0, entry=total_calc)
            add_cost_row("T&L (>80km)", transport_long)
            
            offshore_cost = self.safe_get_attribute('offshore_cost', 0, entry=total_calc)
            add_cost_row("Special Work Environment (Offshore)", offshore_cost)
            
            emergency_cost = self.safe_get_attribute('emergency_cost', 0, entry=total_calc)
            add_cost_row("Emergency Support", emergency_cost)
            
            other_transport = self.safe_get_attribute('other_transport_cost', 0, entry=total_calc)
            add_cost_row("Other Transportation Charge", other_transport)
            
            # Add separator and Subtotal Before Discount row
            if row_index > 0:
                breakdown.insertRow(row_index)
                subtotal_label = QTableWidgetItem("Subtotal Before Discount")
                subtotal_label.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                subtotal_font = QFont(breakdown.font())
                subtotal_font.setBold(True)
                subtotal_label.setFont(subtotal_font)
                breakdown.setItem(row_index, 0, subtotal_label)
                
                subtotal_before_discount = self.safe_get_attribute('subtotal_before_discount', 0, entry=total_calc)
                subtotal_amount = QTableWidgetItem(f"{currency} {subtotal_before_discount:,.2f}")
                subtotal_amount.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                subtotal_amount.setFont(subtotal_font)
                breakdown.setItem(row_index, 1, subtotal_amount)
                
                row_index += 1
                
                # Add Discount row
                discount_amount = self.safe_get_attribute('discount_amount', 0, entry=total_calc)
                add_cost_row("Discount", discount_amount)
                
                # Add Subtotal After Discount row
                breakdown.insertRow(row_index)
                after_discount_label = QTableWidgetItem("Subtotal After Discount")
                after_discount_label.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
                after_discount_label.setFont(subtotal_font)
                breakdown.setItem(row_index, 0, after_discount_label)
                
                subtotal_after_discount = self.safe_get_attribute('subtotal_after_discount', 0, entry=total_calc)
                after_discount_amount = QTableWidgetItem(f"{currency} {subtotal_after_discount:,.2f}")
                after_discount_amount.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                after_discount_amount.setFont(subtotal_font)
                breakdown.setItem(row_index, 1, after_discount_amount)
                
                row_index += 1
            
            # Add VAT
            vat_percent = self.safe_get_attribute('vat_percent', 0, entry=total_calc)
            vat_amount = self.safe_get_attribute('vat_amount', 0, entry=total_calc)
            if vat_amount > 0:
                add_cost_row(f"VAT ({vat_percent:.2f}%)", vat_amount)
            
            # Add Grand Total row
            breakdown.insertRow(row_index)
            
            # Grand Total label with left alignment
            grand_total_item = QTableWidgetItem("GRAND TOTAL")
            grand_total_font = QFont(breakdown.font().family())
            grand_total_font.setBold(True)
            grand_total_font.setPointSize(grand_total_font.pointSize() + 1)  # Slightly larger text
            grand_total_item.setFont(grand_total_font)
            grand_total_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            breakdown.setItem(row_index, 0, grand_total_item)
            
            # Grand Total amount
            total_with_vat = self.safe_get_attribute('total_with_vat', total_charge, entry=total_calc)
            total_amount = QTableWidgetItem(f"{currency} {total_with_vat:,.2f}")
            total_amount.setFont(grand_total_font)
            total_amount.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            breakdown.setItem(row_index, 1, total_amount)
            
            row_index += 1
            
            # Add discount
            discount = self.safe_get_attribute('discount_amount', 0, entry=total_calc)
            if discount > 0:
                add_cost_row("Discount", discount)
            
            # Set row heights and colors
            for i in range(breakdown.rowCount()):
                breakdown.setRowHeight(i, 35)  # Taller row height for better visibility
                
                # Highlight the total row
                if i == breakdown.rowCount() - 1:  # Last row = total
                    for j in range(breakdown.columnCount()):
                        if breakdown.item(i, j):
                            breakdown.item(i, j).setBackground(QColor(220, 230, 241))  # Light blue background
            
            # Set column widths and styling
            breakdown.setColumnWidth(0, 200)  # Item - wider
            breakdown.setColumnWidth(1, 150)  # Amount - wider
            
            # Style the header
            header = breakdown.horizontalHeader()
            header.setStyleSheet("::section { background-color: #eaecee; padding: 6px; font-weight: bold; }")
            header.setMinimumHeight(30)  # Taller header for better visibility
            
            # Set column sizing - properly adjust after setting initial widths
            breakdown.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Item column stretches
            breakdown.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Amount column sized to content
            
            # Add table to layout
            calc_layout.addWidget(breakdown)
        
        # Add the breakdown note if available
        breakdown_text = self.safe_get_attribute('detailed_calculation_breakdown', '')
        if breakdown_text:
            # Create a label with the detailed breakdown text
            breakdown_label = QLabel()
            breakdown_label.setWordWrap(True)
            breakdown_label.setText(breakdown_text)
            breakdown_label.setStyleSheet("""
                font-family: monospace;
                padding: 10px;
                background-color: #f9f9f9;
                border: 1px solid #ddd;
                border-radius: 4px;
            """)
            breakdown_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            
            calc_layout.addSpacing(10)
            calc_layout.addWidget(breakdown_label)
        
        # Add calculation group to page layout
        self.page_layout.addWidget(calc_group)
        
        # Add spacing at the bottom
        self.page_layout.addSpacing(20)
    
    def export_to_pdf(self):
        """Preview the report in PDF before exporting"""
        try:
            # Import the PDF preview functionality directly
            from modules.timesheet.pdf_preview import PDFPreviewDialog, create_and_preview_pdf
            from modules.timesheet.pdf_export import create_timesheet_pdf
            
            # Create a suggested filename
            suggested_filename = f"Timesheet_{self.safe_get_attribute('entry_id', 'report')}.pdf"
            
            # Use the preview module to create and preview the PDF
            result = create_and_preview_pdf(
                create_timesheet_pdf,  # The function that creates the PDF
                self.entry,             # The data to pass to the function
                self,                   # Parent widget for the dialog
                suggested_filename      # Suggested filename
            )
            
            # If result is not None, the PDF was saved successfully
            if result:
                QMessageBox.information(
                    self,
                    "PDF Saved",
                    f"The timesheet PDF has been saved to:\n{result}"
                )
                
        except ImportError as e:
            # If there's an import error, fall back to simpler PDF export
            QMessageBox.warning(
                self,
                "PDF Preview Not Available",
                "PDF preview module could not be loaded. Using direct export instead."
            )
            self.export_to_pdf_direct()
        except Exception as e:
            QMessageBox.critical(
                self,
                "PDF Preview Failed",
                f"Failed to preview PDF: {str(e)}"
            )
    
    def export_to_pdf_direct(self):
        """Direct export to PDF without preview (fallback method)"""
        try:
            # Ask the user for a file location
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Save Timesheet Report as PDF",
                f"Timesheet_{self.safe_get_attribute('entry_id', 'report')}.pdf",
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return  # User cancelled
            
            # Ensure path ends with .pdf
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'
            
            # Create PDF writer
            pdf_writer = QPdfWriter(file_path)
            pdf_writer.setPageSize(QPageSize(QPageSize.A4))
            pdf_writer.setPageMargins(QMargins(20, 20, 20, 20))
            
            # Create painter
            painter = QPainter()
            painter.begin(pdf_writer)
            
            # Calculate the scale factor
            scale_factor = pdf_writer.width() / (self.page_widget.width() - 40)
            painter.scale(scale_factor, scale_factor)
            
            # Render the page widget to PDF
            self.page_widget.render(painter)
            
            # End painting
            painter.end()
            
            # Show success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"Report has been exported to:\n{file_path}"
            )
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Failed",
                f"Failed to export PDF: {str(e)}"
            )