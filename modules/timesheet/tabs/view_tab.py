"""
View Tab - For viewing timesheet entry details in A4 portrait format
"""
import datetime
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, 
    QPushButton, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QScrollArea, QFrame, QMessageBox, QFileDialog,
    QSizePolicy, QSpacerItem, QGridLayout
)
from PySide6.QtCore import Qt, Signal, QSize, QRect, QMargins
from PySide6.QtGui import QFont, QBrush, QPixmap, QColor, QPainter, QPen, QPdfWriter, QPageSize

class ViewTab(QWidget):
    """Tab for viewing timesheet entry details in A4 portrait layout"""
    
    # Signal for closing the tab
    close_requested = Signal()
    
    # A4 dimensions in pixels at 72 DPI
    A4_WIDTH = 595
    A4_HEIGHT = 842
    
    def __init__(self, parent, entry, data_manager):
        super().__init__(parent)
        self.parent = parent
        self.entry = entry
        self.data_manager = data_manager
        
        # Path to logo
        self.logo_path = str(Path(os.getcwd()) / "assets" / "logo" / "mcllogo.png")
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Action buttons at the top
        toolbar_layout = QHBoxLayout()
        
        # Close button
        close_button = QPushButton("Close")
        close_button.setFixedWidth(80)
        close_button.clicked.connect(self.close_requested.emit)
        toolbar_layout.addWidget(close_button)
        toolbar_layout.addStretch()
        
        main_layout.addLayout(toolbar_layout)
        
        # Scroll area for A4 view
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # A4 Page widget
        self.page_widget = QWidget()
        self.page_widget.setFixedWidth(self.A4_WIDTH)  # A4 width in points
        self.page_widget.setStyleSheet("background-color: white;")
        
        self.page_layout = QVBoxLayout(self.page_widget)
        self.page_layout.setSpacing(0)
        
        # Create header with logo, title and ID
        self.create_header()
        
        # Create the project information section
        self.create_project_info()
        
        # Set the scroll area content and add to main layout
        scroll_area.setWidget(self.page_widget)
        main_layout.addWidget(scroll_area)
        
    def create_header(self):
        """Create the document header with logo, title and report ID"""
        # Header container
        header_layout = QGridLayout()
        
        # Logo on the left
        logo_label = QLabel()
        logo_pixmap = QPixmap(self.logo_path)
        if not logo_pixmap.isNull():
            logo_pixmap = logo_pixmap.scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            logo_label.setPixmap(logo_pixmap)
        else:
            logo_label.setText("MCL LOGO")
            logo_label.setStyleSheet("font-weight: bold; color: #777;")
        logo_label.setFixedSize(120, 60)
        
        # Title in the center - simplified
        title_label = QLabel("Service Timesheet and Charge Summary")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 12px;
            font-weight: bold;
            color: #2c3e50;
            text-align: center;
        """)
        
        # Report ID and page info on the right
        id_label = QLabel(f"Report ID: {self.entry.entry_id}")
        id_label.setAlignment(Qt.AlignRight)
        id_label.setStyleSheet("font-weight: bold;")
        
        page_label = QLabel("Page 1 of 1")
        page_label.setAlignment(Qt.AlignRight)
        
        # Date on the right
        date_label = QLabel(f"Date: {getattr(self.entry, 'creation_date', datetime.datetime.now().strftime('%Y-%m-%d'))}")
        date_label.setAlignment(Qt.AlignRight)
        
        # Add to grid layout
        header_layout.addWidget(logo_label, 0, 0, 2, 1)  # Logo spans 2 rows
        header_layout.addWidget(title_label, 0, 1, 1, 1)  # Title in center
        header_layout.addWidget(id_label, 0, 2, 1, 1)     # ID on right
        header_layout.addWidget(date_label, 1, 2, 1, 1)   # Date below ID
        
        # Add header to page
        self.page_layout.addLayout(header_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("background-color: #2c3e50;")
        self.page_layout.addWidget(separator)
        
        # Add a little space
        self.page_layout.addSpacing(10)
        
    def create_project_info(self):
        """Create the project information section based on JSON data"""
        # Project Information section
        self.page_layout.addSpacing(10)
        info_group = QGroupBox("Project Information")
        self.page_layout.addWidget(info_group)
               
        info_group.setStyleSheet("""
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
            QLabel { padding: 2px; }
        """)
        
        # Create grid layout for the information
        info_layout = QVBoxLayout(info_group)
        grid = QGridLayout()
        grid.setColumnStretch(1, 1)  # Make columns with content stretch
        grid.setColumnStretch(3, 1)  # Make columns with content stretch
        grid.setColumnStretch(5, 1)  # Make columns with content stretch
        grid.setHorizontalSpacing(15)
        grid.setVerticalSpacing(8)
        info_layout.addLayout(grid)
        grid.setContentsMargins(15, 15, 15, 15)
        
        # Get entry dictionary data directly if available
        entry_dict = None
        if hasattr(self.entry, '__dict__'):
            entry_dict = self.entry.__dict__
        elif isinstance(self.entry, dict):
            entry_dict = self.entry
        
        # Business Details - Left Top
        # Get data from the entry dictionary with proper fallbacks
        if entry_dict:
            po_number = entry_dict.get('purchasing_order_number', 'N/A')
            quotation = entry_dict.get('quotation_number', 'N/A')
            client = entry_dict.get('client_company_name', entry_dict.get('client', 'N/A'))
            client_address = entry_dict.get('client_address', 'N/A')
        else:
            # Fallback to using safe_get_attribute
            po_number = self.safe_get_attribute('purchasing_order_number', ['po_number', 'Purchasing Order Number'], 'N/A')
            quotation = self.safe_get_attribute('quotation_number', ['Quotation Number'], 'N/A')
            client = self.safe_get_attribute('client_company_name', ['Client', 'client'], 'N/A')
            client_address = self.safe_get_attribute('client_address', ['Client Address'], 'N/A')
        
        # Display PO Number
        grid.addWidget(QLabel("PO #:"), 0, 0)  # Changed label to PO #
        grid.addWidget(QLabel(f"<b>{po_number}</b>"), 0, 1)
        
        # Display Quotation Number
        grid.addWidget(QLabel("Quotation #:"), 1, 0)
        grid.addWidget(QLabel(f"<b>{quotation}</b>"), 1, 1)
        
        # Display Client Information
        grid.addWidget(QLabel("Client:"), 2, 0)
        grid.addWidget(QLabel(f"<b>{client}</b>"), 2, 1)
        
        # Display Address
        grid.addWidget(QLabel("Address:"), 3, 0)
        grid.addWidget(QLabel(f"<b>{client_address}</b>"), 3, 1)
        
        # Client Representative - Middle
        client_rep = self.safe_get_attribute('client_representative_name', 
                                        ['Client Representative Name', 'client_representative'], 'N/A')
        rep_phone = self.safe_get_attribute('client_representative_phone', ['Phone Number'], 'N/A')
        rep_email = self.safe_get_attribute('client_representative_email', ['Email'], 'N/A')
        
        grid.addWidget(QLabel("Representative:"), 0, 2)
        grid.addWidget(QLabel(f"<b>{client_rep}</b>"), 0, 3)
        
        grid.addWidget(QLabel("Rep. Phone:"), 1, 2)
        grid.addWidget(QLabel(f"<b>{rep_phone}</b>"), 1, 3)
        
        grid.addWidget(QLabel("Rep. Email:"), 2, 2)
        grid.addWidget(QLabel(f"<b>{rep_email}</b>"), 2, 3)
        
        # Engineer Information - Right
        engineer_name = self.safe_get_attribute('service_engineer_name', 
                                            ['Service Engineer Name', 'engineer_name'], '')
        engineer_surname = self.safe_get_attribute('service_engineer_surname', 
                                              ['service_angineer_surname', 'Surname', 'engineer_surname'], '')
        engineer_full = f"{engineer_name} {engineer_surname}".strip()
        
        # Work Type & Emergency
        work_type = self.safe_get_attribute('work_type', ['Work Type'], 'N/A')
        emergency = self.safe_get_attribute('emergency_request', ['Emergency Request?'], False)
        emergency_text = "Yes" if emergency else "No"
        
        grid.addWidget(QLabel("Engineer:"), 0, 4)
        grid.addWidget(QLabel(f"<b>{engineer_full}</b>"), 0, 5)
        
        grid.addWidget(QLabel("Work Type:"), 1, 4)
        grid.addWidget(QLabel(f"<b>{work_type}</b>"), 1, 5)
        
        grid.addWidget(QLabel("Emergency:"), 2, 4)
        grid.addWidget(QLabel(f"<b>{emergency_text}</b>"), 2, 5)
        
        # Contract Agreement - Additional Info
        contract = self.safe_get_attribute('under_contract_agreement', ['Under Contract Agreement?'], False)
        contract_text = "Yes" if contract else "No"
        
        grid.addWidget(QLabel("Contract:"), 3, 2)
        grid.addWidget(QLabel(f"<b>{contract_text}</b>"), 3, 3)
        
        # Set column stretch to make the layout more balanced
        for col in range(6):
            grid.setColumnStretch(col, 1)
        
        # Time Entries Section
        self.create_time_entries()
        
    def create_time_entries(self):
        """Create the time entries table with full width display"""
        # Time Entries container
        self.page_layout.addSpacing(20)
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
        
        # Create table for time entries with improved layout
        time_layout = QVBoxLayout(time_group)
        time_layout.setContentsMargins(5, 20, 5, 5)  # Reduced margins for more space
        
        time_table = QTableWidget()
        time_table.setColumnCount(8)  # Date, Start, End, Break, Description, OT Rate, Offshore, Travel
        time_table.setHorizontalHeaderLabels([
            "Date", "Start", "End", "Break (hrs)", "Description", "OT Rate", "Offshore", "Travel"
        ])
        
        # Set custom column widths for better display
        time_table.setEditTriggers(QTableWidget.NoEditTriggers)
        time_table.setAlternatingRowColors(True)
        time_table.verticalHeader().setVisible(False)
        
        # Populate time entries
        if hasattr(self.entry, 'time_entries') and self.entry.time_entries:
            time_table.setRowCount(len(self.entry.time_entries))
            
            for i, entry in enumerate(self.entry.time_entries):
                # Date
                date_item = QTableWidgetItem(entry.get('date', ''))
                date_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 0, date_item)
                
                # Start Time
                start_time = entry.get('start_time', '')
                start_item = QTableWidgetItem(start_time[:2] + ":" + start_time[2:] if len(start_time) == 4 else start_time)
                start_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 1, start_item)
                
                # End Time
                end_time = entry.get('end_time', '')
                end_item = QTableWidgetItem(end_time[:2] + ":" + end_time[2:] if len(end_time) == 4 else end_time)
                end_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 2, end_item)
                
                # Break Hours
                break_item = QTableWidgetItem(str(entry.get('rest_hours', 0)))
                break_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 3, break_item)
                
                # Description
                desc_item = QTableWidgetItem(entry.get('description', ''))
                time_table.setItem(i, 4, desc_item)
                
                # Overtime Rate
                ot_rate = entry.get('overtime_rate', '1')
                if ot_rate == '1': ot_display = "1.0x"
                elif ot_rate == '1.5': ot_display = "1.5x"
                elif ot_rate == '2': ot_display = "2.0x"
                elif ot_rate == '3': ot_display = "3.0x"
                else: ot_display = ot_rate
                
                ot_item = QTableWidgetItem(ot_display)
                ot_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 5, ot_item)
                
                # Offshore
                offshore = "Yes" if entry.get('offshore', False) else "No"
                offshore_item = QTableWidgetItem(offshore)
                offshore_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 6, offshore_item)
                
                # Travel
                travel_count = entry.get('travel_count', False)
                travel_distance = "Far" if entry.get('travel_far_distance', False) else "Short" if entry.get('travel_short_distance', False) else ""
                travel_display = travel_distance if travel_count else "No"
                travel_item = QTableWidgetItem(travel_display)
                travel_item.setTextAlignment(Qt.AlignCenter)
                time_table.setItem(i, 7, travel_item)
            
            # Set rows to be at least 30 pixels high for better readability
            for row in range(time_table.rowCount()):
                time_table.setRowHeight(row, 30)
        else:
            # No time entries
            time_table.setRowCount(1)
            no_data_item = QTableWidgetItem("No time entries available")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            time_table.setSpan(0, 0, 1, 8)  # Span all columns
            time_table.setItem(0, 0, no_data_item)
        
        # Set fixed column widths to optimize display
        time_table.setColumnWidth(0, 100)  # Date
        time_table.setColumnWidth(1, 80)   # Start Time
        time_table.setColumnWidth(2, 80)   # End Time
        time_table.setColumnWidth(3, 80)   # Break
        time_table.setColumnWidth(4, 250)  # Description - wider for details
        time_table.setColumnWidth(5, 70)   # OT Rate
        time_table.setColumnWidth(6, 70)   # Offshore
        time_table.setColumnWidth(7, 70)   # Travel
        
        time_layout.addWidget(time_table)
        self.page_layout.addWidget(time_group)
        
        # Tool Usage Section
        self.create_tool_usage()
        
    def create_tool_usage(self):
        """Create the tool usage table with improved display"""
        # Tool Usage container
        self.page_layout.addSpacing(20)
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
        
        # Create layout with reduced margins for more space
        tool_layout = QVBoxLayout(tool_group)
        tool_layout.setContentsMargins(5, 20, 5, 5)
        
        # Create table with fixed columns for consistent display
        tool_table = QTableWidget()
        tool_table.setColumnCount(5)
        tool_table.setHorizontalHeaderLabels([
            "Tool Name", "Amount", "Start Date", "End Date", "Total Days"
        ])
        
        tool_table.setEditTriggers(QTableWidget.NoEditTriggers)
        tool_table.setAlternatingRowColors(True)
        tool_table.verticalHeader().setVisible(False)
        
        # Populate table with data
        if hasattr(self.entry, 'tool_usage') and self.entry.tool_usage:
            tool_table.setRowCount(len(self.entry.tool_usage))
            
            for i, tool in enumerate(self.entry.tool_usage):
                # Tool Name
                name_item = QTableWidgetItem(tool.get('tool_name', ''))
                tool_table.setItem(i, 0, name_item)
                
                # Amount
                amount_item = QTableWidgetItem(str(tool.get('amount', 0)))
                amount_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 1, amount_item)
                
                # Start Date
                start_date_item = QTableWidgetItem(tool.get('start_date', ''))
                start_date_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 2, start_date_item)
                
                # End Date
                end_date_item = QTableWidgetItem(tool.get('end_date', ''))
                end_date_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 3, end_date_item)
                
                # Total Days
                days_item = QTableWidgetItem(str(tool.get('total_days', 0)))
                days_item.setTextAlignment(Qt.AlignCenter)
                tool_table.setItem(i, 4, days_item)
            
            # Set rows to be at least 30 pixels high for better readability
            for row in range(tool_table.rowCount()):
                tool_table.setRowHeight(row, 30)
        else:
            # No tool usage data
            tool_table.setRowCount(1)
            no_data_item = QTableWidgetItem("No tool usage data available")
            no_data_item.setTextAlignment(Qt.AlignCenter)
            tool_table.setSpan(0, 0, 1, 5)  # Span all columns
            tool_table.setItem(0, 0, no_data_item)
        
        # Set fixed column widths to optimize display
        tool_table.setColumnWidth(0, 200)  # Tool Name - wider for long names
        tool_table.setColumnWidth(1, 80)   # Amount
        tool_table.setColumnWidth(2, 100)  # Start Date
        tool_table.setColumnWidth(3, 100)  # End Date
        tool_table.setColumnWidth(4, 100)  # Total Days
        
        tool_layout.addWidget(tool_table)
        self.page_layout.addWidget(tool_group)
        
        # Service Rates and Summary sections
        self.create_rates_and_summary()
    
    def create_rates_and_summary(self):
        """Create the service rates and summary sections"""
        # Create a container for the rates and summary
        summary_container = QHBoxLayout()
        
        # Service Rates Group
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
        
        rates_layout = QFormLayout(rates_group)
        rates_layout.setVerticalSpacing(8)
        
        # Get currency for formatting
        currency = getattr(self.entry, 'currency', 'THB')
        
        # Service rates
        rates_layout.addRow("Service Hour Rate:", 
            QLabel(f"{currency} {getattr(self.entry, 'service_hour_rate', 0):,.2f}"))
        rates_layout.addRow("Tool Usage Rate:", 
            QLabel(f"{currency} {getattr(self.entry, 'tool_usage_rate', 0):,.2f}"))
        rates_layout.addRow("T&L Rate (<80km):", 
            QLabel(f"{currency} {getattr(self.entry, 'tl_rate_short', 0):,.2f}"))
        rates_layout.addRow("T&L Rate (>80km):", 
            QLabel(f"{currency} {getattr(self.entry, 'tl_rate_long', 0):,.2f}"))
        rates_layout.addRow("Offshore Day Rate:", 
            QLabel(f"{currency} {getattr(self.entry, 'offshore_day_rate', 0):,.2f}"))
        rates_layout.addRow("Emergency Rate:", 
            QLabel(f"{currency} {getattr(self.entry, 'emergency_rate', 0):,.2f}"))
        
        # Time Summary Group
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
        
        summary_layout = QFormLayout(summary_group)
        summary_layout.setVerticalSpacing(8)
        
        # Calculate hours
        hours = {}
        try:
            if hasattr(self.entry, 'calculate_total_hours'):
                hours = self.entry.calculate_total_hours()
            else:
                # Manual calculation
                hours = {'regular': 0, 'ot1': 0, 'ot15': 0, 'ot2': 0, 'total': 0}
                if hasattr(self.entry, 'time_entries'):
                    for entry in self.entry.time_entries:
                        equiv_hours = float(entry.get('equivalent_hours', 0))
                        ot_rate = entry.get('overtime_rate', '1')
                        
                        if ot_rate == '1' or ot_rate == 1:
                            hours['regular'] += equiv_hours
                        elif ot_rate == '1.5' or ot_rate == 1.5:
                            hours['ot15'] += equiv_hours
                        elif ot_rate == '2' or ot_rate == 2:
                            hours['ot2'] += equiv_hours
                        else:
                            hours['ot1'] += equiv_hours
                            
                    hours['total'] = hours['regular'] + hours['ot1'] + hours['ot15'] + hours['ot2']
        except Exception as e:
            print(f"Error calculating hours: {e}")
        
        # Fill summary
        summary_layout.addRow("Regular Hours:", 
            QLabel(f"{hours.get('regular', 0):.1f}"))
        summary_layout.addRow("OT 1.0X Hours:", 
            QLabel(f"{hours.get('ot1', 0):.1f}"))
        summary_layout.addRow("OT 1.5X Hours:", 
            QLabel(f"{hours.get('ot15', 0):.1f}"))
        summary_layout.addRow("OT 2.0X Hours:", 
            QLabel(f"{hours.get('ot2', 0):.1f}"))
        summary_layout.addRow("Total Hours:", 
            QLabel(f"<b>{hours.get('total', 0):.1f}</b>"))
        
        # Tool Summary
        if hasattr(self.entry, 'tool_usage') and self.entry.tool_usage:
            total_days = sum(tool.get('total_days', 0) for tool in self.entry.tool_usage)
            tool_names = [f"{tool.get('amount', 1)} {tool.get('tool_name', '')}" for tool in self.entry.tool_usage]
            tool_text = ", ".join(tool_names)
            
            summary_layout.addRow("Tools Used:", QLabel(tool_text))
            summary_layout.addRow("Total Tool Days:", QLabel(f"{total_days}"))
        
        # Add both to container
        summary_container.addWidget(rates_group, 1)
        summary_container.addWidget(summary_group, 1)
        
        # Add to page layout
        self.page_layout.addLayout(summary_container)
        
        # Final calculation section
        self.create_calculation_section()
    
    def create_calculation_section(self):
        """Create the final calculation and summary section with detailed breakdown"""
        # Calculation group
        calc_group = QGroupBox("Calculation Result")
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
        
        # Get currency for formatting
        currency = getattr(self.entry, 'currency', 'THB')
        total_charge = getattr(self.entry, 'total_service_charge', 0)
        
        # Create total cost label
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
        
        # Add calculation breakdown section
        breakdown_group = QGroupBox("Calculation Breakdown")
        breakdown_group.setStyleSheet("""
            QGroupBox {
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                margin-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                font-weight: bold;
            }
        """)
        
        breakdown_layout = QVBoxLayout(breakdown_group)
        
        # Calculate costs for each service component
        try:
            hours = {}
            if hasattr(self.entry, 'calculate_total_hours'):
                hours = self.entry.calculate_total_hours()
            else:
                # Manual calculation (same as in PDF export)
                hours = {'regular': 0, 'ot1': 0, 'ot15': 0, 'ot2': 0, 'total': 0}
                time_entries = getattr(self.entry, 'time_entries', [])
                if time_entries:
                    for entry in time_entries:
                        equiv_hours = float(entry.get('equivalent_hours', 0))
                        ot_rate = entry.get('overtime_rate', '1')
                        
                        if ot_rate == '1' or ot_rate == 1:
                            hours['regular'] += equiv_hours
                        elif ot_rate == '1.5' or ot_rate == 1.5:
                            hours['ot15'] += equiv_hours
                        elif ot_rate == '2' or ot_rate == 2:
                            hours['ot2'] += equiv_hours
                        else:
                            hours['ot1'] += equiv_hours
                            
                    hours['total'] = hours['regular'] + hours['ot1'] + hours['ot15'] + hours['ot2']
            
            # Service hour rates and costs
            service_hour_rate = getattr(self.entry, 'service_hour_rate', 0)
            
            # Create breakdown table
            breakdown_table = QTableWidget()
            breakdown_table.setColumnCount(4)
            breakdown_table.setHorizontalHeaderLabels(["Item", "Rate", "Quantity", "Amount"])
            
            # Style the table
            breakdown_table.setStyleSheet("""
                QTableWidget {
                    border: 1px solid #d0d0d0;
                    gridline-color: #e0e0e0;
                }
                QHeaderView::section {
                    background-color: #f5f5f5;
                    border: 1px solid #d0d0d0;
                    padding: 4px;
                    font-weight: bold;
                }
                QTableWidget::item:selected {
                    background-color: #ffffd0; /* Light yellow */
                    color: black;
                }
            """)
            
            # Configure table appearance
            breakdown_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Item column stretches
            breakdown_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Rate column
            breakdown_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)  # Quantity column
            breakdown_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Amount column
            
            # Add rows for service hours
            row_count = 0
            
            # Regular hours
            if hours.get('regular', 0) > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("Regular Hours"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {service_hour_rate:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{hours['regular']:.1f}"))
                amount = hours['regular'] * service_hour_rate
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # OT 1.0X hours
            if hours.get('ot1', 0) > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("OT 1.0X Hours"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {service_hour_rate:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{hours['ot1']:.1f}"))
                amount = hours['ot1'] * service_hour_rate
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # OT 1.5X hours
            if hours.get('ot15', 0) > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("OT 1.5X Hours"))
                ot15_rate = service_hour_rate * 1.5
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {ot15_rate:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{hours['ot15']:.1f}"))
                amount = hours['ot15'] * ot15_rate
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # OT 2.0X hours
            if hours.get('ot2', 0) > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("OT 2.0X Hours"))
                ot2_rate = service_hour_rate * 2.0
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {ot2_rate:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{hours['ot2']:.1f}"))
                amount = hours['ot2'] * ot2_rate
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # Tool usage
            tool_usage = getattr(self.entry, 'tool_usage', [])
            tool_usage_rate = getattr(self.entry, 'tool_usage_rate', 0)
            total_tool_days = sum(tool.get('total_days', 0) for tool in tool_usage)
            
            if total_tool_days > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("Tool Usage"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {tool_usage_rate:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{total_tool_days:.1f}"))
                amount = total_tool_days * tool_usage_rate
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # Transportation charges
            tl_rate_short = getattr(self.entry, 'tl_rate_short', 0)
            tl_rate_long = getattr(self.entry, 'tl_rate_long', 0)
            
            # Count transportation instances
            short_trips = 0
            long_trips = 0
            for entry in getattr(self.entry, 'time_entries', []):
                if entry.get('travel_count', False):
                    if entry.get('travel_short_distance', False):
                        short_trips += 1
                    elif entry.get('travel_far_distance', False):
                        long_trips += 1
            
            # Add short distance transport
            if short_trips > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("Transport (<80km)"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {tl_rate_short:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{short_trips}"))
                amount = short_trips * tl_rate_short
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # Add long distance transport
            if long_trips > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("Transport (>80km)"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {tl_rate_long:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem(f"{long_trips}"))
                amount = long_trips * tl_rate_long
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {amount:,.2f}"))
                row_count += 1
            
            # Add other transport charge if any
            other_transport_charge = getattr(self.entry, 'other_transport_charge', 0)
            if other_transport_charge > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("Additional Transport"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem("-"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem("1"))
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {other_transport_charge:,.2f}"))
                row_count += 1
            
            # Add emergency surcharge if applicable
            emergency_rate = getattr(self.entry, 'emergency_rate', 0)
            if getattr(self.entry, 'emergency_request', False) and emergency_rate > 0:
                breakdown_table.insertRow(row_count)
                breakdown_table.setItem(row_count, 0, QTableWidgetItem("Emergency Surcharge"))
                breakdown_table.setItem(row_count, 1, QTableWidgetItem(f"{currency} {emergency_rate:,.2f}"))
                breakdown_table.setItem(row_count, 2, QTableWidgetItem("1"))
                breakdown_table.setItem(row_count, 3, QTableWidgetItem(f"{currency} {emergency_rate:,.2f}"))
                row_count += 1
            
            # Add the table to the breakdown layout
            breakdown_layout.addWidget(breakdown_table)
            
            # Special notes or explanations
            if hasattr(self.entry, 'calculation_notes') and self.entry.calculation_notes:
                notes_label = QLabel("Notes: " + self.entry.calculation_notes)
                notes_label.setWordWrap(True)
                notes_label.setStyleSheet("padding: 5px; font-style: italic;")
                breakdown_layout.addWidget(notes_label)
                
        except Exception as e:
            error_label = QLabel(f"Error generating calculation breakdown: {str(e)}")
            error_label.setStyleSheet("color: red;")
            breakdown_layout.addWidget(error_label)
        
        # Add the breakdown group to the calculation layout
        calc_layout.addWidget(breakdown_group)
        
        # Add other charges if any
        if hasattr(self.entry, 'other_transport_charge') and self.entry.other_transport_charge > 0:
            if hasattr(self.entry, 'other_transport_note') and self.entry.other_transport_note:
                note_label = QLabel(f"Note: {self.entry.other_transport_note}")
                note_label.setWordWrap(True)
                note_label.setStyleSheet("font-style: italic; padding: 5px;")
                calc_layout.addWidget(note_label)
        
        # Add to page layout
        self.page_layout.addWidget(calc_group)
        
        # Add some stretching space at the bottom
        self.page_layout.addStretch()
    
    def safe_get_attribute(self, primary_attr, fallback_attrs=None, default_value=''):
        """Safely get an attribute with fallbacks
        
        Args:
            primary_attr: The primary attribute name to check
            fallback_attrs: List of fallback attribute names
            default_value: Default value if no attributes found
            
        Returns:
            The attribute value or default value
        """
        # First try to use our new TimesheetEntry.__getitem__ method which checks _raw_data
        if hasattr(self.entry, '__getitem__'):
            try:
                value = self.entry[primary_attr]
                if value is not None:
                    return value
            except (KeyError, TypeError):
                pass
        
        # Try direct raw_data access if available
        if hasattr(self.entry, 'get_raw_data'):
            raw_data = self.entry.get_raw_data()
            if primary_attr in raw_data:
                return raw_data[primary_attr]
        
        # Try dictionary-style access if entry is a dict
        if isinstance(self.entry, dict) and primary_attr in self.entry:
            return self.entry[primary_attr]
        
        # Try attribute-style access
        if hasattr(self.entry, primary_attr):
            return getattr(self.entry, primary_attr)
        
        # Try fallbacks with dictionary-style access through __getitem__
        if fallback_attrs and hasattr(self.entry, '__getitem__'):
            for attr in fallback_attrs:
                try:
                    value = self.entry[attr]
                    if value is not None:
                        return value
                except (KeyError, TypeError):
                    pass
                    
        # Try fallbacks with direct raw_data access
        if fallback_attrs and hasattr(self.entry, 'get_raw_data'):
            raw_data = self.entry.get_raw_data()
            for attr in fallback_attrs:
                if attr in raw_data:
                    return raw_data[attr]
        
        # Try fallbacks with dictionary-style access
        if fallback_attrs and isinstance(self.entry, dict):
            for attr in fallback_attrs:
                if attr in self.entry:
                    return self.entry[attr]
        
        # Try fallbacks with attribute-style access
        if fallback_attrs:
            for attr in fallback_attrs:
                if hasattr(self.entry, attr):
                    return getattr(self.entry, attr)
        
        # Return default if nothing found
        return default_value
        
    def preview_pdf(self):
        """Preview the timesheet as PDF using the PDF export module"""
        try:
            from modules.timesheet.pdf_export import generate_timesheet_pdf
            
            # Generate the PDF using the entry data
            generate_timesheet_pdf(self.entry, self)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Error creating PDF: {str(e)}"
            )
