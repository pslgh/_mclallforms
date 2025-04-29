"""
Reports Tab - For generating timesheet reports and summaries
"""
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QPushButton, QLabel, QComboBox, QDateEdit, 
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal

class ReportsTab(QWidget):
    """Tab for generating timesheet reports and summaries"""
    
    def __init__(self, parent, data_manager):
        super().__init__(parent)
        self.parent = parent
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
        
        # Header
        header_label = QLabel("Timesheet Reports")
        header_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        scroll_layout.addWidget(header_label)
        
        # Report Parameters Section
        params_group = QGroupBox("Report Parameters")
        params_layout = QVBoxLayout(params_group)
        
        # First row for report type and client
        top_params_layout = QHBoxLayout()
        
        type_label = QLabel("Report Type:")
        self.report_type_input = QComboBox()
        self.report_type_input.addItems([
            "Monthly Summary", 
            "Client Summary",
            "Engineer Summary",
            "Overtime Summary"
        ])
        
        client_label = QLabel("Client:")
        self.client_filter = QComboBox()
        self.client_filter.addItem("All Clients")
        self.client_filter.setEditable(True)
        
        top_params_layout.addWidget(type_label)
        top_params_layout.addWidget(self.report_type_input, 2)
        top_params_layout.addWidget(client_label)
        top_params_layout.addWidget(self.client_filter, 2)
        
        # Second row for dates and generate button
        bottom_params_layout = QHBoxLayout()
        
        start_label = QLabel("Start:")
        self.start_date_filter = QDateEdit()
        self.start_date_filter.setCalendarPopup(True)
        self.start_date_filter.setDisplayFormat("yyyy/MM/dd")
        self.start_date_filter.setDate(datetime.datetime.now().date().replace(day=1))  # First day of current month
        
        end_label = QLabel("End:")
        self.end_date_filter = QDateEdit()
        self.end_date_filter.setCalendarPopup(True)
        self.end_date_filter.setDisplayFormat("yyyy/MM/dd")
        self.end_date_filter.setDate(datetime.datetime.now().date())  # Today
        
        # Generate button
        generate_button = QPushButton("Generate Report")
        generate_button.clicked.connect(self.generate_report)
        
        bottom_params_layout.addWidget(start_label)
        bottom_params_layout.addWidget(self.start_date_filter)
        bottom_params_layout.addWidget(end_label)
        bottom_params_layout.addWidget(self.end_date_filter)
        bottom_params_layout.addWidget(generate_button)
        
        # Add rows to main layout
        params_layout.addLayout(top_params_layout)
        params_layout.addLayout(bottom_params_layout)
        
        scroll_layout.addWidget(params_group)
        
        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        scroll_layout.addWidget(separator)
        
        # Report Results Section
        report_group = QGroupBox("Report Results")
        report_layout = QVBoxLayout(report_group)
        
        self.report_title = QLabel("No report generated yet")
        self.report_title.setStyleSheet("font-size: 14px; font-weight: bold;")
        report_layout.addWidget(self.report_title)
        
        # Table for report data
        self.report_table = QTableWidget(0, 4)  # Default columns, will be adjusted based on report
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        report_layout.addWidget(self.report_table)
        
        # Summary labels
        self.summary_label = QLabel("")
        self.summary_label.setStyleSheet("font-weight: bold;")
        report_layout.addWidget(self.summary_label)
        
        scroll_layout.addWidget(report_group)
        
        # Export button
        export_button = QPushButton("Export Report to PDF")
        export_button.clicked.connect(self.export_report)
        scroll_layout.addWidget(export_button)
        
        scroll_layout.addStretch()
        
        # Set the scroll widget
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Update client filter options
        self.update_client_filter_options()
        
    def update_client_filter_options(self):
        """Update the client filter combobox options"""
        entries = self.data_manager.load_entries()
        
        # Clear and repopulate
        current_text = self.client_filter.currentText()
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
    
    def generate_report(self):
        """Generate the selected report type"""
        report_type = self.report_type_input.currentText()
        client = self.client_filter.currentText()
        start_date = self.start_date_filter.date().toString("yyyy/MM/dd")
        end_date = self.end_date_filter.date().toString("yyyy/MM/dd")
        
        # Check dates
        if start_date > end_date:
            QMessageBox.warning(self, "Invalid Date Range", "Start date must be before or equal to end date.")
            return
        
        # Update report title
        client_text = f"for {client}" if client != "All Clients" else ""
        date_range_text = f"from {start_date} to {end_date}"
        self.report_title.setText(f"{report_type} {client_text} {date_range_text}")
        
        # Generate the appropriate report
        if report_type == "Monthly Summary":
            self.generate_monthly_summary(client, start_date, end_date)
        elif report_type == "Client Summary":
            self.generate_client_summary(client, start_date, end_date)
        elif report_type == "Engineer Summary":
            self.generate_engineer_summary(client, start_date, end_date)
        elif report_type == "Overtime Summary":
            self.generate_overtime_summary(client, start_date, end_date)
    
    def generate_monthly_summary(self, client, start_date, end_date):
        """Generate a monthly summary report"""
        # Load entries within date range
        entries = self.data_manager.get_entries_by_date_range(start_date, end_date)
        
        # Filter by client if needed
        if client != "All Clients":
            entries = [e for e in entries if e.client == client]
        
        # Prepare table
        self.report_table.clear()
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Month", "Client", "Regular Hours", "OT1 Hours", "OT1.5 Hours", "Total Hours"
        ])
        
        # Group by month and client
        monthly_data = {}
        for entry in entries:
            # Process each time entry
            for time_entry in entry.time_entries:
                entry_date = time_entry.get('date', '')
                if not entry_date or not (start_date <= entry_date <= end_date):
                    continue
                    
                # Extract month and year
                try:
                    date_obj = datetime.datetime.strptime(entry_date, "%Y-%m-%d")
                    month_key = date_obj.strftime("%Y-%m")
                    month_name = date_obj.strftime("%b %Y")
                    
                    # Create client key
                    client_key = entry.client
                    
                    # Create composite key
                    key = (month_key, client_key)
                    
                    if key not in monthly_data:
                        monthly_data[key] = {
                            'month': month_name,
                            'client': client_key,
                            'regular': 0,
                            'ot1': 0,
                            'ot15': 0
                        }
                    
                    # Parse start and end times
                    start_time = time_entry.get('start_time', '')
                    end_time = time_entry.get('end_time', '')
                    overtime_rate = time_entry.get('overtime_rate', 'Regular')
                    
                    try:
                        # Convert to hours and minutes
                        start_hours = int(start_time[:2])
                        start_minutes = int(start_time[2:]) if len(start_time) > 2 else 0
                        end_hours = int(end_time[:2])
                        end_minutes = int(end_time[2:]) if len(end_time) > 2 else 0
                        
                        # Calculate duration in hours
                        start_decimal = start_hours + (start_minutes / 60)
                        end_decimal = end_hours + (end_minutes / 60)
                        
                        # Handle overnight entries
                        if end_decimal < start_decimal:
                            duration = (24 - start_decimal) + end_decimal
                        else:
                            duration = end_decimal - start_decimal
                        
                        # Add to appropriate category
                        if overtime_rate == "OT1":
                            monthly_data[key]['ot1'] += duration
                        elif overtime_rate == "OT1.5":
                            monthly_data[key]['ot15'] += duration
                        else:
                            monthly_data[key]['regular'] += duration
                            
                    except (ValueError, IndexError):
                        # Skip invalid time format
                        continue
                        
                except ValueError:
                    # Skip invalid date format
                    continue
        
        # Sort by month and client
        sorted_data = sorted(monthly_data.items())
        
        # Populate table
        grand_total_regular = 0
        grand_total_ot1 = 0
        grand_total_ot15 = 0
        
        for key, data in sorted_data:
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            
            total = data['regular'] + data['ot1'] + data['ot15']
            
            self.report_table.setItem(row, 0, QTableWidgetItem(data['month']))
            self.report_table.setItem(row, 1, QTableWidgetItem(data['client']))
            self.report_table.setItem(row, 2, QTableWidgetItem(f"{data['regular']:.1f}"))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"{data['ot1']:.1f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{data['ot15']:.1f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"{total:.1f}"))
            
            # Add to grand totals
            grand_total_regular += data['regular']
            grand_total_ot1 += data['ot1']
            grand_total_ot15 += data['ot15']
        
        # Update summary
        grand_total = grand_total_regular + grand_total_ot1 + grand_total_ot15
        summary = (f"Grand Total: Regular: {grand_total_regular:.1f}, "
                   f"OT1: {grand_total_ot1:.1f}, OT1.5: {grand_total_ot15:.1f}, "
                   f"Total: {grand_total:.1f} hours")
        self.summary_label.setText(summary)
    
    def generate_client_summary(self, client_filter, start_date, end_date):
        """Generate a client summary report"""
        # Load entries within date range
        entries = self.data_manager.get_entries_by_date_range(start_date, end_date)
        
        # Filter by client if needed
        if client_filter != "All Clients":
            entries = [e for e in entries if e.client == client_filter]
        
        # Prepare table
        self.report_table.clear()
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels([
            "Client", "Regular Hours", "OT1 Hours", "OT1.5 Hours", "Total Hours"
        ])
        
        # Group by client
        client_data = {}
        for entry in entries:
            # Create or get client summary
            client_key = entry.client
            if client_key not in client_data:
                client_data[client_key] = {
                    'regular': 0,
                    'ot1': 0,
                    'ot15': 0
                }
            
            # Calculate hours for this entry
            hours = entry.calculate_total_hours()
            
            # Add to client totals
            client_data[client_key]['regular'] += hours['regular']
            client_data[client_key]['ot1'] += hours['ot1']
            client_data[client_key]['ot15'] += hours['ot15']
        
        # Sort by client name
        sorted_clients = sorted(client_data.items())
        
        # Populate table
        grand_total_regular = 0
        grand_total_ot1 = 0
        grand_total_ot15 = 0
        
        for client_name, data in sorted_clients:
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            
            total = data['regular'] + data['ot1'] + data['ot15']
            
            self.report_table.setItem(row, 0, QTableWidgetItem(client_name))
            self.report_table.setItem(row, 1, QTableWidgetItem(f"{data['regular']:.1f}"))
            self.report_table.setItem(row, 2, QTableWidgetItem(f"{data['ot1']:.1f}"))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"{data['ot15']:.1f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{total:.1f}"))
            
            # Add to grand totals
            grand_total_regular += data['regular']
            grand_total_ot1 += data['ot1']
            grand_total_ot15 += data['ot15']
        
        # Update summary
        grand_total = grand_total_regular + grand_total_ot1 + grand_total_ot15
        summary = (f"Grand Total: Regular: {grand_total_regular:.1f}, "
                   f"OT1: {grand_total_ot1:.1f}, OT1.5: {grand_total_ot15:.1f}, "
                   f"Total: {grand_total:.1f} hours")
        self.summary_label.setText(summary)
    
    def generate_engineer_summary(self, client_filter, start_date, end_date):
        """Generate an engineer summary report"""
        # Load entries within date range
        entries = self.data_manager.get_entries_by_date_range(start_date, end_date)
        
        # Filter by client if needed
        if client_filter != "All Clients":
            entries = [e for e in entries if e.client == client_filter]
        
        # Prepare table
        self.report_table.clear()
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(6)
        self.report_table.setHorizontalHeaderLabels([
            "Engineer", "Client", "Regular Hours", "OT1 Hours", "OT1.5 Hours", "Total Hours"
        ])
        
        # Group by engineer and client
        engineer_data = {}
        for entry in entries:
            # Create engineer key
            engineer_name = f"{entry.engineer_name} {entry.engineer_surname}"
            
            # Create client key
            client_key = entry.client
            
            # Create composite key
            key = (engineer_name, client_key)
            
            if key not in engineer_data:
                engineer_data[key] = {
                    'engineer': engineer_name,
                    'client': client_key,
                    'regular': 0,
                    'ot1': 0,
                    'ot15': 0
                }
            
            # Calculate hours for this entry
            hours = entry.calculate_total_hours()
            
            # Add to engineer totals
            engineer_data[key]['regular'] += hours['regular']
            engineer_data[key]['ot1'] += hours['ot1']
            engineer_data[key]['ot15'] += hours['ot15']
        
        # Sort by engineer name then client
        sorted_engineers = sorted(engineer_data.items())
        
        # Populate table
        grand_total_regular = 0
        grand_total_ot1 = 0
        grand_total_ot15 = 0
        
        for key, data in sorted_engineers:
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            
            total = data['regular'] + data['ot1'] + data['ot15']
            
            self.report_table.setItem(row, 0, QTableWidgetItem(data['engineer']))
            self.report_table.setItem(row, 1, QTableWidgetItem(data['client']))
            self.report_table.setItem(row, 2, QTableWidgetItem(f"{data['regular']:.1f}"))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"{data['ot1']:.1f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{data['ot15']:.1f}"))
            self.report_table.setItem(row, 5, QTableWidgetItem(f"{total:.1f}"))
            
            # Add to grand totals
            grand_total_regular += data['regular']
            grand_total_ot1 += data['ot1']
            grand_total_ot15 += data['ot15']
        
        # Update summary
        grand_total = grand_total_regular + grand_total_ot1 + grand_total_ot15
        summary = (f"Grand Total: Regular: {grand_total_regular:.1f}, "
                   f"OT1: {grand_total_ot1:.1f}, OT1.5: {grand_total_ot15:.1f}, "
                   f"Total: {grand_total:.1f} hours")
        self.summary_label.setText(summary)
    
    def generate_overtime_summary(self, client_filter, start_date, end_date):
        """Generate an overtime summary report"""
        # Load entries within date range
        entries = self.data_manager.get_entries_by_date_range(start_date, end_date)
        
        # Filter by client if needed
        if client_filter != "All Clients":
            entries = [e for e in entries if e.client == client_filter]
        
        # Prepare table
        self.report_table.clear()
        self.report_table.setRowCount(0)
        self.report_table.setColumnCount(5)
        self.report_table.setHorizontalHeaderLabels([
            "Engineer", "Client", "OT1 Hours", "OT1.5 Hours", "Total OT Hours"
        ])
        
        # Group by engineer and client
        engineer_data = {}
        for entry in entries:
            # Create engineer key
            engineer_name = f"{entry.engineer_name} {entry.engineer_surname}"
            
            # Create client key
            client_key = entry.client
            
            # Create composite key
            key = (engineer_name, client_key)
            
            if key not in engineer_data:
                engineer_data[key] = {
                    'engineer': engineer_name,
                    'client': client_key,
                    'ot1': 0,
                    'ot15': 0
                }
            
            # Calculate hours for this entry
            hours = entry.calculate_total_hours()
            
            # Add to engineer totals (only overtime)
            engineer_data[key]['ot1'] += hours['ot1']
            engineer_data[key]['ot15'] += hours['ot15']
        
        # Sort by engineer name then client
        sorted_engineers = sorted(engineer_data.items())
        
        # Populate table
        grand_total_ot1 = 0
        grand_total_ot15 = 0
        
        for key, data in sorted_engineers:
            # Skip if no overtime
            if data['ot1'] == 0 and data['ot15'] == 0:
                continue
                
            row = self.report_table.rowCount()
            self.report_table.insertRow(row)
            
            total_ot = data['ot1'] + data['ot15']
            
            self.report_table.setItem(row, 0, QTableWidgetItem(data['engineer']))
            self.report_table.setItem(row, 1, QTableWidgetItem(data['client']))
            self.report_table.setItem(row, 2, QTableWidgetItem(f"{data['ot1']:.1f}"))
            self.report_table.setItem(row, 3, QTableWidgetItem(f"{data['ot15']:.1f}"))
            self.report_table.setItem(row, 4, QTableWidgetItem(f"{total_ot:.1f}"))
            
            # Add to grand totals
            grand_total_ot1 += data['ot1']
            grand_total_ot15 += data['ot15']
        
        # Update summary
        grand_total = grand_total_ot1 + grand_total_ot15
        summary = f"Grand Total: OT1: {grand_total_ot1:.1f}, OT1.5: {grand_total_ot15:.1f}, Total OT: {grand_total:.1f} hours"
        self.summary_label.setText(summary)
    
    def export_report(self):
        """Export the current report to PDF"""
        # This is a placeholder for PDF export functionality
        # In a real implementation, you would create a PDF with reportlab
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            "Export PDF", 
            "PDF export functionality will be implemented soon."
        )
