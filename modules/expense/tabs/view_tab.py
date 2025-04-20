"""
View tab for the expense reimbursement module.
This tab displays an existing expense form in read-only mode.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QTableWidget, QTableWidgetItem, QMessageBox,
    QPushButton, QGroupBox, QHeaderView, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

from modules.expense.pdf_export import generate_expense_form_pdf

class ViewTab(QWidget):
    """Tab for viewing existing expense forms in read-only mode"""
    
    # Signals
    close_requested = Signal()  # When the tab should be closed
    
    def __init__(self, parent=None, form=None, data_manager=None):
        super().__init__(parent)
        self.form = form
        self.data_manager = data_manager
        self.parent_widget = parent
        
        # Create UI components
        self.setup_ui()
        
        # Load the form data
        if form:
            self.load_form_data()
        
    def setup_ui(self):
        """Create the UI components"""
        view_layout = QVBoxLayout(self)
        
        # Top section with project and currency info side by side
        top_layout = QHBoxLayout()
        
        # Project information group
        project_group = QGroupBox("Project Information")
        self.project_layout = QFormLayout(project_group)
        
        self.project_name_label = QLabel()
        self.work_location_label = QLabel()
        self.country_label = QLabel()
        
        self.project_layout.addRow("Project Name:", self.project_name_label)
        self.project_layout.addRow("Work Location:", self.work_location_label)
        self.project_layout.addRow("Work Country:", self.country_label)
        
        # Currency group
        currency_group = QGroupBox("Fund & Currency Information")
        self.currency_layout = QFormLayout(currency_group)
        
        self.fund_thb_label = QLabel()
        self.receive_date_label = QLabel()
        self.thb_usd_label = QLabel()
        self.third_currency_label = QLabel()
        self.third_currency_usd_label = QLabel()
        
        self.currency_layout.addRow("Fund Amount (THB):", self.fund_thb_label)
        self.currency_layout.addRow("Receive Date:", self.receive_date_label)
        self.currency_layout.addRow("THB to USD Rate:", self.thb_usd_label)
        self.currency_layout.addRow("Third Currency:", self.third_currency_label)
        self.currency_layout.addRow("Third Currency to USD Rate:", self.third_currency_usd_label)
        
        # Add project and currency groups side by side
        top_layout.addWidget(project_group, 1)  # 1 = stretch factor
        top_layout.addWidget(currency_group, 1)  # 1 = stretch factor
        
        # Expense table
        expense_group = QGroupBox("Expenses")
        expense_layout = QVBoxLayout(expense_group)
        
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(7)  # No Actions column needed
        self.expense_table.setHorizontalHeaderLabels([
            "Date", "Detail", "Vendor", "Category", "Amount", "Currency", 
            "Receipt Type"
        ])
        
        # Make the table read-only
        self.expense_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        header = self.expense_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Currency
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Receipt Type
        
        expense_layout.addWidget(self.expense_table)
        
        # Summary group
        summary_group = QGroupBox("Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.total_label = QLabel()
        self.total_label.setStyleSheet("font-weight: bold;")
        self.remaining_label = QLabel()
        self.remaining_label.setStyleSheet("font-weight: bold;")
        
        summary_layout.addWidget(QLabel("Total Expenses:"), 0, 0)
        summary_layout.addWidget(self.total_label, 0, 1)
        summary_layout.addWidget(QLabel("Remaining Funds:"), 1, 0)
        summary_layout.addWidget(self.remaining_label, 1, 1)
        
        # Issued by section
        issued_group = QGroupBox("Issued By")
        issued_layout = QFormLayout(issued_group)
        
        self.issued_by_label = QLabel()
        self.issue_date_label = QLabel()
        
        issued_layout.addRow("Name:", self.issued_by_label)
        issued_layout.addRow("Date:", self.issue_date_label)
        
        # Create bottom layout for summary and issued by sections side by side
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(summary_group, 1)  # 1 = stretch factor
        bottom_layout.addWidget(issued_group, 1)  # 1 = stretch factor
        
        # Buttons layout
        buttons_layout = QHBoxLayout()
        
        # Add spacer to push buttons to the right
        spacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        buttons_layout.addItem(spacer)
        
        # Export to PDF button
        self.export_button = QPushButton("Export to PDF")
        self.export_button.clicked.connect(self.export_to_pdf)
        buttons_layout.addWidget(self.export_button)
        self.export_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")

        
        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_tab)
        buttons_layout.addWidget(self.close_button)
        self.close_button.setStyleSheet("background-color: #f44336; color: white;")

        
        # Add all groups to main layout
        view_layout.addLayout(top_layout)  # Add the side-by-side layout first
        view_layout.addWidget(expense_group)
        view_layout.addLayout(bottom_layout)  # Add the side-by-side layout for bottom sections
        view_layout.addLayout(buttons_layout)
        
    def load_form_data(self):
        """Load form data into UI elements"""
        if not self.form:
            return
            
        # Project information
        self.project_name_label.setText(self.form.project_name)
        
        # Work location information
        is_abroad = self.form.work_location == "Abroad"
        
        if is_abroad:
            self.work_location_label.setText("Abroad")
            self.country_label.setText(self.form.work_country)
            self.country_label.setVisible(True)
            # Show the country label's row in the form layout
            for i in range(self.project_layout.rowCount()):
                label_item = self.project_layout.itemAt(i, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    if label_item.widget().text() == "Work Country:":
                        label_item.widget().setVisible(True)
                        break
        else:
            self.work_location_label.setText("Thailand")
            self.country_label.setText("Thailand")
            self.country_label.setVisible(False)
            # Hide the country label's row in the form layout
            for i in range(self.project_layout.rowCount()):
                label_item = self.project_layout.itemAt(i, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    if label_item.widget().text() == "Work Country:":
                        label_item.widget().setVisible(False)
                        break
        
        # Currency information
        self.fund_thb_label.setText(f"{self.form.fund_thb:.2f} THB")
        self.receive_date_label.setText(self.form.receive_date)
        
        # Exchange rate information
        self.thb_usd_label.setText(f"{self.form.thb_usd:.4f}")
        
        # Third currency information
        is_abroad = self.form.work_location == "Abroad"
        if is_abroad and self.form.third_currency != "None":
            self.third_currency_label.setText(self.form.third_currency)
            self.third_currency_usd_label.setText(f"{self.form.third_currency_usd:.4f}")
            # Show the third currency fields
            for i in range(self.currency_layout.rowCount()):
                label_item = self.currency_layout.itemAt(i, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    if label_item.widget().text() == "Third Currency:" or label_item.widget().text() == "Third Currency to USD Rate:":
                        label_item.widget().setVisible(True)
                        field_item = self.currency_layout.itemAt(i, QFormLayout.FieldRole)
                        if field_item and field_item.widget():
                            field_item.widget().setVisible(True)
        else:
            self.third_currency_label.setText("None")
            self.third_currency_usd_label.setText("0.0000")
            # Hide the third currency fields
            for i in range(self.currency_layout.rowCount()):
                label_item = self.currency_layout.itemAt(i, QFormLayout.LabelRole)
                if label_item and label_item.widget():
                    if label_item.widget().text() == "Third Currency:" or label_item.widget().text() == "Third Currency to USD Rate:":
                        label_item.widget().setVisible(False)
                        field_item = self.currency_layout.itemAt(i, QFormLayout.FieldRole)
                        if field_item and field_item.widget():
                            field_item.widget().setVisible(False)
        
        # Only show THB to USD rate for abroad work
        is_abroad = self.form.work_location == "Abroad"
        for i in range(self.currency_layout.rowCount()):
            label_item = self.currency_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget():
                if label_item.widget().text() == "THB to USD Rate:":
                    label_item.widget().setVisible(is_abroad)
                    field_item = self.currency_layout.itemAt(i, QFormLayout.FieldRole)
                    if field_item and field_item.widget():
                        field_item.widget().setVisible(is_abroad)
                    break
        
        # Load expense items
        self.load_expenses()
        
        # Update summary
        total = self.form.calculate_total_thb()
        remaining = self.form.fund_thb - total
        self.total_label.setText(f"{total:.2f} THB")
        self.remaining_label.setText(f"{remaining:.2f} THB")
        
        # Issued by information
        self.issued_by_label.setText(self.form.issued_by)
        self.issue_date_label.setText(self.form.issue_date)
        
    def load_expenses(self):
        """Load expense items into the table"""
        if not self.form:
            return
            
        # Clear table
        self.expense_table.setRowCount(0)
        
        # Add rows for each expense
        for expense in self.form.expenses:
            row = self.expense_table.rowCount()
            self.expense_table.insertRow(row)
            
            # Date
            date_item = QTableWidgetItem(expense.expense_date)
            date_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 0, date_item)
            
            # Detail
            detail_item = QTableWidgetItem(expense.detail)
            detail_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 1, detail_item)
            
            # Vendor
            vendor_item = QTableWidgetItem(expense.vendor)
            vendor_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 2, vendor_item)
            
            # Category
            category_item = QTableWidgetItem(expense.category)
            category_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 3, category_item)
            
            # Amount
            amount_item = QTableWidgetItem(f"{expense.amount:.2f}")
            amount_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 4, amount_item)
            
            # Currency
            currency_item = QTableWidgetItem(expense.currency)
            currency_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 5, currency_item)
            
            # Receipt Type
            receipt_type = "No Receipt"
            if expense.official_receipt:
                receipt_type = "Official Receipt"
            elif expense.non_official_receipt:
                receipt_type = "Non-Official Receipt"
            
            receipt_item = QTableWidgetItem(receipt_type)
            receipt_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.expense_table.setItem(row, 6, receipt_item)
    
    def export_to_pdf(self):
        """Export the form to PDF"""
        if self.form and self.data_manager:
            try:
                # Pass the form data and self as the parent widget for the file dialog
                pdf_path = generate_expense_form_pdf(
                    self.form,
                    self  # Pass self as parent_widget for the file dialog
                )
                
                # If user cancelled, just return without showing a message
                if not pdf_path:
                    return
                
                # Show success message with file path
                QMessageBox.information(
                    self,
                    "PDF Exported",
                    f"The expense form has been exported to:\n{pdf_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Export Failed",
                    f"Failed to export PDF: {str(e)}"
                )
    
    def close_tab(self):
        """Request to close this tab"""
        self.close_requested.emit()
