"""
Form tab for the expense reimbursement module.
This tab allows creating new expense forms.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QDoubleSpinBox, QMessageBox, QHeaderView, QInputDialog
)
from PySide6.QtGui import QDoubleValidator
from PySide6.QtCore import Qt, Signal, QDate

# import pycountry
# import iso4217

from modules.expense.models.expense_data import ExpenseItem, ExpenseFormData
from modules.expense.utils.currency_helper import COUNTRY_CURRENCY_MAP, CURRENCY_NAMES, COUNTRY_LIST, CURRENCY_VALUES, get_currency_name

class FormTab(QWidget):
    """Tab for creating new expense forms"""
    
    # Signals
    expense_added = Signal(object)  # When an expense is added to the table
    form_saved = Signal(str)  # When a form is saved (emits form ID)
    data_changed = Signal()  # When any data in the form is changed
    
    def __init__(self, parent=None, user_info=None, data_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.user_info = user_info or {}
        self.data_manager = data_manager
        self.expenses = []  # List to hold expense items
        self.initializing = True  # Flag to prevent dialogs during init
        
        self.setup_ui()
        self.initializing = False  # Done initializing
        
    def setup_ui(self):
        """Create the UI components"""
        form_layout = QVBoxLayout(self)
        
        # Top section with project and currency info side by side
        top_layout = QHBoxLayout()
        
        # Project information group
        project_group = QGroupBox("Project Information")
        self.project_layout = QFormLayout(project_group)
        
        self.project_name_input = QLineEdit()
        self.work_location_combo = QComboBox()
        self.work_location_combo.addItems(["Thailand", "Abroad"])
        self.work_location_combo.currentIndexChanged.connect(self.on_work_location_changed)
        
        # Country selection for abroad work
        self.country_combo = QComboBox()
        # Use our predefined list of countries
        self.country_combo.addItems(COUNTRY_LIST)
        # Set Thailand as default (avoids triggering for Afghanistan which has No Currency)
        default_index = self.country_combo.findText("Thailand")
        if default_index >= 0:
            self.country_combo.setCurrentIndex(default_index)
        self.country_combo.setVisible(False)  # Initially hidden
        self.country_combo.currentIndexChanged.connect(self.on_country_changed)
        
        self.project_layout.addRow("Project Name:", self.project_name_input)
        self.project_layout.addRow("Work Location:", self.work_location_combo)
        self.project_layout.addRow("Work Country:", self.country_combo)
        
        # Currency group
        currency_group = QGroupBox("Fund & Currency Information")
        self.currency_layout = QFormLayout(currency_group)
        
        self.fund_thb_input = QDoubleSpinBox()
        self.fund_thb_input.setRange(0, 1000000)
        self.fund_thb_input.setDecimals(2)
        self.fund_thb_input.setSingleStep(100)
        self.fund_thb_input.valueChanged.connect(self.on_data_changed)
        
        self.receive_date_input = QDateEdit()
        self.receive_date_input.setCalendarPopup(True)
        self.receive_date_input.setDate(QDate.currentDate())
        
        self.currency_layout.addRow("Fund Amount (THB):", self.fund_thb_input)
        self.currency_layout.addRow("Receive Date:", self.receive_date_input)
        
        # Exchange rate widgets
        self.thb_usd_input = QDoubleSpinBox()
        self.thb_usd_input.setRange(0, 100)
        self.thb_usd_input.setDecimals(2)
        self.thb_usd_input.setSingleStep(0.1)
        self.thb_usd_input.valueChanged.connect(self.on_data_changed)
        self.currency_layout.addRow("THB to USD Rate:", self.thb_usd_input)
        
        # Third currency (for abroad)
        self.third_currency_combo = QComboBox()
        
        # Add None option
        self.third_currency_combo.addItem("None")
        
        # Add currencies directly from country mapping values - code only, no descriptions
        for code in CURRENCY_VALUES:
            if code != "No Currency":  # Skip No Currency in the dropdown
                self.third_currency_combo.addItem(code)
        self.third_currency_combo.currentIndexChanged.connect(self.on_third_currency_changed)
        
        self.third_currency_usd_input = QDoubleSpinBox()
        self.third_currency_usd_input.setRange(0, 1000000)  # Increased maximum value
        self.third_currency_usd_input.setDecimals(4)
        self.third_currency_usd_input.setSingleStep(0.1)
        self.third_currency_usd_input.valueChanged.connect(self.on_data_changed)
        
        self.currency_widgets = QWidget()
        currency_extra_layout = QFormLayout(self.currency_widgets)
        currency_extra_layout.addRow("Third Currency:", self.third_currency_combo)
        currency_extra_layout.addRow("Third Currency to USD Rate:", self.third_currency_usd_input)
        self.currency_widgets.setVisible(False)
        
        self.currency_layout.addWidget(self.currency_widgets)
        
        # Add project and currency groups side by side
        top_layout.addWidget(project_group, 1)  # 1 = stretch factor
        top_layout.addWidget(currency_group, 1)  # 1 = stretch factor
        
        # Expense table
        expense_group = QGroupBox("Expenses")
        expense_layout = QVBoxLayout(expense_group)
        
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(8)
        self.expense_table.setHorizontalHeaderLabels([
            "Date", "Detail", "Vendor", "Category", "Amount", "Currency", 
            "Receipt Type", "Actions"
        ])
        
        # Enable sorting for the table
        self.expense_table.setSortingEnabled(True)
        
        # Connect headerClicked signal to ensure sorting works with our custom widgets
        self.expense_table.horizontalHeader().sectionClicked.connect(self.handle_header_click)
        
        header = self.expense_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Amount
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Currency
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Receipt Type
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Actions
        
        # Add expense button
        self.add_expense_button = QPushButton("Add Empty Row")
        self.add_expense_button.clicked.connect(self.add_empty_row)
        self.add_expense_button.setStyleSheet("background-color:#4fa7f4; color: white; font-weight: bold;")
        
        expense_layout.addWidget(self.expense_table)
        expense_layout.addWidget(self.add_expense_button)
        
        # Summary group
        summary_group = QGroupBox("Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.total_label = QLabel("0.00 THB")
        self.total_label.setStyleSheet("font-weight: bold;")
        self.remaining_label = QLabel("0.00 THB")
        self.remaining_label.setStyleSheet("font-weight: bold;")
        
        summary_layout.addWidget(QLabel("Total Expenses:"), 0, 0)
        summary_layout.addWidget(self.total_label, 0, 1)
        summary_layout.addWidget(QLabel("Remaining Funds:"), 1, 0)
        summary_layout.addWidget(self.remaining_label, 1, 1)
        
        # Issued by section
        issued_group = QGroupBox("Issued By")
        issued_layout = QFormLayout(issued_group)
        
        self.issued_by_input = QLineEdit()
        if self.user_info:
            self.issued_by_input.setText(f"{self.user_info.get('first_name', '')} {self.user_info.get('last_name', '')}")
        
        self.issue_date_input = QDateEdit()
        self.issue_date_input.setCalendarPopup(True)
        self.issue_date_input.setDate(QDate.currentDate())
        
        issued_layout.addRow("Name:", self.issued_by_input)
        issued_layout.addRow("Date:", self.issue_date_input)
        
        # Save button
        self.save_button = QPushButton("Save Form")
        self.save_button.clicked.connect(self.save_form)
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        
        # Create bottom layout for summary and issued by sections side by side
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(summary_group, 1)  # 1 = stretch factor
        bottom_layout.addWidget(issued_group, 1)  # 1 = stretch factor
        
        # Add all groups to main layout
        form_layout.addLayout(top_layout)  # Add the side-by-side layout first
        form_layout.addWidget(expense_group)
        form_layout.addLayout(bottom_layout)  # Add the side-by-side layout for bottom sections
        form_layout.addWidget(self.save_button)
        
        # Set default values
        self.clear_form()
        self.on_work_location_changed(0)  # 0 is the index for Thailand
        
    def on_work_location_changed(self, index):
        """Handle work location change"""
        is_abroad = self.work_location_combo.currentText() == "Abroad"
        
        # Show/hide country selector and row label
        self.country_combo.setVisible(is_abroad)
        
        # Find and access the "Work Country:" label item in the form layout
        for i in range(self.project_layout.rowCount()):
            label_item = self.project_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget():
                if label_item.widget().text() == "Work Country:":
                    label_item.widget().setVisible(is_abroad)
                    break
        
        # Show currency exchange widgets only for abroad work
        self.currency_widgets.setVisible(is_abroad)
        
        # Hide THB to USD Rate label and field for Thailand work
        for i in range(self.currency_layout.rowCount()):
            label_item = self.currency_layout.itemAt(i, QFormLayout.LabelRole)
            field_item = self.currency_layout.itemAt(i, QFormLayout.FieldRole)
            if label_item and label_item.widget() and field_item and field_item.widget():
                if label_item.widget().text() == "THB to USD Rate:":
                    label_item.widget().setVisible(is_abroad)
                    field_item.widget().setVisible(is_abroad)
                    break
        
        # Set country and update third currency for Thailand
        if not is_abroad:
            self.country_combo.setCurrentText("Thailand")
            self.update_country_currency("Thailand")
        else:
            # Update currency for selected country
            current_country = self.country_combo.currentText()
            self.update_country_currency(current_country)
        
        self.on_data_changed()
            
    def on_country_changed(self, index):
        """Handle country change"""
        country_name = self.country_combo.currentText()
        self.update_country_currency(country_name)
        self.on_data_changed()
        
    def on_third_currency_changed(self, index):
        """Handle third currency change"""
        # Update all existing currency dropdowns in the expense table
        self.update_all_currency_dropdowns()
        self.on_data_changed()
        
    def update_all_currency_dropdowns(self):
        """Update all currency dropdowns in the expense table"""
        # Always include THB and USD
        available_currencies = ["THB", "USD"]
        
        # Add third currency if it's selected and not None
        third_currency = self.third_currency_combo.currentText()
        if third_currency and third_currency != "None" and third_currency not in available_currencies:
            # Extract just the currency code if it contains a space (like "USD - US Dollar")
            if " - " in third_currency:
                third_currency = third_currency.split(" - ")[0]
            available_currencies.append(third_currency)
            
        # Update each row's currency dropdown
        for row in range(self.expense_table.rowCount()):
            currency_combo = self.expense_table.cellWidget(row, 5)
            if currency_combo and isinstance(currency_combo, QComboBox):
                # Save current selection
                current_currency = currency_combo.currentText()
                
                # Block signals temporarily to avoid triggering events
                currency_combo.blockSignals(True)
                
                # Clear and add new items
                currency_combo.clear()
                currency_combo.addItems(available_currencies)
                
                # Restore selection if possible, or default to THB
                if current_currency in available_currencies:
                    currency_combo.setCurrentText(current_currency)
                else:
                    currency_combo.setCurrentText("THB")
                    # Also update the model
                    if 0 <= row < len(self.expenses):
                        self.expenses[row].currency = "THB"
                
                # Unblock signals
                currency_combo.blockSignals(False)
        
    def update_country_currency(self, country_name):
        """Update third currency based on selected country"""
        # Get the currency code from our simplified mapping
        currency_code = COUNTRY_CURRENCY_MAP.get(country_name, None)
        
        # Block signals to prevent triggering update events
        self.third_currency_combo.blockSignals(True)
        
        # Handle special case for "No Currency" - but only if not initializing
        if currency_code == "No Currency" and not self.initializing:
            # Ask user to select a currency via popup
            currency_code = self.prompt_for_currency_selection(country_name)
        elif currency_code == "No Currency" and self.initializing:
            # Default to None during initialization
            currency_code = None
            
        # Update the third currency combo box
        if currency_code and currency_code != "No Currency":
            # Look for the currency in the dropdown
            found = False
            for i in range(self.third_currency_combo.count()):
                text = self.third_currency_combo.itemText(i)
                if text == currency_code:
                    self.third_currency_combo.setCurrentIndex(i)
                    found = True
                    break
                    
            if not found:
                # If not found, add it to the dropdown
                self.third_currency_combo.addItem(currency_code)
                self.third_currency_combo.setCurrentIndex(self.third_currency_combo.count() - 1)
                print(f"Added custom currency {currency_code} to dropdown")
        else:
            # Default to "None" if no currency found or user canceled
            self.third_currency_combo.setCurrentIndex(0)
            
        # Unblock signals
        self.third_currency_combo.blockSignals(False)
        
        # Update the expense table currency options
        self.update_all_currency_dropdowns()
        
    def prompt_for_currency_selection(self, country_name):
        """Prompt the user to select a currency for a country that doesn't have a standard currency"""
        # Create dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("Currency Selection")
        dialog.setText(f"{country_name} does not have a standard currency in our database.")
        dialog.setInformativeText("Please select a currency to use:")
        
        # Add currency options as buttons
        common_currencies = ["USD", "EUR", "GBP", "JPY", "CNY"]
        
        dialog.addButton("None", QMessageBox.RejectRole)
        currency_buttons = {}
        
        for currency in common_currencies:
            button = dialog.addButton(currency, QMessageBox.ActionRole)
            currency_buttons[button] = currency
            
        # Add a custom option
        custom_button = dialog.addButton("Other...", QMessageBox.ActionRole)
        
        # Show dialog
        dialog.exec_()
        
        clicked_button = dialog.clickedButton()
        
        # Handle custom entry
        if clicked_button == custom_button:
            # Show an input dialog for custom currency
            custom_currency, ok = QInputDialog.getText(
                self, 
                "Custom Currency", 
                "Enter the 3-letter currency code (e.g., USD, EUR):"
            )
            
            if ok and custom_currency:
                return custom_currency.strip().upper()[:3]  # Limit to 3 characters, uppercase
            else:
                return None
        
        # Return the selected currency or None
        return currency_buttons.get(clicked_button, None)
    
    def add_empty_row(self):
        """Add an empty row to the expense table"""
        # Create a new expense item with default values
        expense = ExpenseItem()
        expense.expense_date = QDate.currentDate().toString("yyyy-MM-dd")
        expense.currency = "THB"  # Default currency
        
        # Add to the table
        self.add_expense_to_table(expense)
        
        # Add to the expenses list
        self.expenses.append(expense)
        
        # Emit signal
        self.expense_added.emit(expense)
        self.data_changed.emit()
        
    def add_expense_to_table(self, expense_item):
        """Add an expense item to the table with interactive widgets"""
        # Get the current row count
        row = self.expense_table.rowCount()
        
        # Insert a new row
        self.expense_table.insertRow(row)
        
        # Date column (0)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.fromString(expense_item.expense_date, "yyyy-MM-dd"))
        date_edit.setProperty("row", row)
        date_edit.dateChanged.connect(lambda date, r=row: self.update_expense_date(r, date.toString("yyyy-MM-dd")))
        self.expense_table.setCellWidget(row, 0, date_edit)
        
        # Detail column (1)
        detail_edit = QLineEdit()
        detail_edit.setText(expense_item.detail)
        detail_edit.setProperty("row", row)
        detail_edit.textChanged.connect(lambda text, r=row: self.update_expense_detail(r, text))
        self.expense_table.setCellWidget(row, 1, detail_edit)
        
        # Vendor column (2)
        vendor_edit = QLineEdit()
        vendor_edit.setText(expense_item.vendor)
        vendor_edit.setProperty("row", row)
        vendor_edit.textChanged.connect(lambda text, r=row: self.update_expense_vendor(r, text))
        self.expense_table.setCellWidget(row, 2, vendor_edit)
        
        # Category column (3)
        category_combo = QComboBox()
        if self.data_manager:
            category_combo.addItems(self.data_manager.settings.categories)
        category_combo.setProperty("row", row)
        if expense_item.category and category_combo.findText(expense_item.category) >= 0:
            category_combo.setCurrentText(expense_item.category)
        category_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_category(r, text))
        self.expense_table.setCellWidget(row, 3, category_combo)
        
        # Amount column (4) - using QLineEdit with numeric validation instead of QDoubleSpinBox
        amount_edit = QLineEdit()
        amount_edit.setText(f"{expense_item.amount:.2f}")
        amount_edit.setProperty("row", row)
        
        # Set up validator to only allow valid numbers
        validator = QDoubleValidator(0, 1000000, 2)
        validator.setNotation(QDoubleValidator.StandardNotation)
        amount_edit.setValidator(validator)
        
        # Connect to text changed event
        amount_edit.textChanged.connect(lambda text, r=row: self.update_expense_amount_text(r, text))
        self.expense_table.setCellWidget(row, 4, amount_edit)
        
        # Currency column (5) - Limited to THB, USD and selected third currency
        currency_combo = QComboBox()
        
        # Always include THB and USD
        available_currencies = ["THB", "USD"]
        
        # Add third currency if it's selected and not None
        third_currency = self.third_currency_combo.currentText()
        if third_currency and third_currency != "None" and third_currency not in available_currencies:
            available_currencies.append(third_currency)
            
        # Add the currencies to the combo box
        currency_combo.addItems(available_currencies)
        
        # Set the current currency if it's in the available currencies
        if expense_item.currency in available_currencies:
            currency_combo.setCurrentText(expense_item.currency)
        else:
            # Default to THB if the current currency isn't available
            currency_combo.setCurrentText("THB")
            expense_item.currency = "THB"
            
        currency_combo.setProperty("row", row)
        currency_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_currency(r, text))
        self.expense_table.setCellWidget(row, 5, currency_combo)
        
        # Receipt Type column (6)
        receipt_combo = QComboBox()
        receipt_types = ["No Receipt", "Official Receipt", "Non-Official Receipt"]
        receipt_combo.addItems(receipt_types)
        
        # Set initial receipt type based on the expense_item
        if expense_item.official_receipt:
            receipt_combo.setCurrentText("Official Receipt")
        elif expense_item.non_official_receipt:
            receipt_combo.setCurrentText("Non-Official Receipt")
        else:
            receipt_combo.setCurrentText("No Receipt")
            
        receipt_combo.setProperty("row", row)
        receipt_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_receipt(r, text))
        self.expense_table.setCellWidget(row, 6, receipt_combo)
        
        # Action column (7) with buttons
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        # Duplicate button
        duplicate_button = QPushButton("Duplicate")
        duplicate_button.setProperty("row", row)
        duplicate_button.clicked.connect(self.duplicate_expense)
        
        # Delete button
        delete_button = QPushButton("Delete")
        delete_button.setProperty("row", row)
        delete_button.clicked.connect(self.delete_expense)
        
        action_layout.addWidget(duplicate_button)
        action_layout.addWidget(delete_button)
        
        self.expense_table.setCellWidget(row, 7, action_widget)
        
    def update_expense_date(self, row, date):
        """Update expense date when changed in table"""
        if 0 <= row < len(self.expenses):
            self.expenses[row].expense_date = date
            self.on_data_changed()
            
    def update_expense_detail(self, row, text):
        """Update expense detail when changed in table"""
        if 0 <= row < len(self.expenses):
            self.expenses[row].detail = text
            self.on_data_changed()
    
    def update_expense_vendor(self, row, text):
        """Update expense vendor when changed in table"""
        if 0 <= row < len(self.expenses):
            self.expenses[row].vendor = text
            self.on_data_changed()
    
    def update_expense_category(self, row, text):
        """Update expense category when changed in table"""
        if 0 <= row < len(self.expenses):
            self.expenses[row].category = text
            self.on_data_changed()
    
    def update_expense_amount_text(self, row, text):
        """Update expense amount from text input"""
        if 0 <= row < len(self.expenses):
            try:
                # Convert text to float, handling empty text or invalid input
                value = float(text) if text.strip() else 0.0
                self.expenses[row].amount = value
                self.on_data_changed()
            except ValueError:
                # If conversion fails, don't update the model
                pass
    
    def update_expense_currency(self, row, text):
        """Update expense currency when changed in table"""
        if 0 <= row < len(self.expenses):
            self.expenses[row].currency = text
            self.on_data_changed()
    
    def update_expense_receipt(self, row, text):
        """Update expense receipt type when changed in table"""
        if 0 <= row < len(self.expenses):
            # Clear both receipt flags first
            self.expenses[row].official_receipt = False
            self.expenses[row].non_official_receipt = False
            
            # Set the appropriate flag based on selection
            if text == "Official Receipt":
                self.expenses[row].official_receipt = True
            elif text == "Non-Official Receipt":
                self.expenses[row].non_official_receipt = True
                
            self.on_data_changed()
    
    def duplicate_expense(self):
        """Duplicate an expense item"""
        sender = self.sender()
        row = sender.property("row")
        
        if 0 <= row < len(self.expenses):
            # Create a copy of the expense item
            original = self.expenses[row]
            duplicate = ExpenseItem()
            duplicate.expense_date = original.expense_date
            duplicate.detail = original.detail
            duplicate.vendor = original.vendor
            duplicate.category = original.category
            duplicate.amount = original.amount
            duplicate.currency = original.currency
            duplicate.official_receipt = original.official_receipt
            duplicate.non_official_receipt = original.non_official_receipt
            
            # Add to the table and expenses list
            self.expenses.append(duplicate)
            self.add_expense_to_table(duplicate)
            
            # Emit signals
            self.expense_added.emit(duplicate)
            self.on_data_changed()
    
    def delete_expense(self):
        """Delete an expense item"""
        sender = self.sender()
        row = sender.property("row")
        
        if 0 <= row < len(self.expenses) and self.expense_table.rowCount() > 0:
            # Remove from table
            self.expense_table.removeRow(row)
            
            # Remove from list
            self.expenses.pop(row)
            
            # Update row indices for action buttons
            self.update_row_indices()
            
            # Emit signal
            self.on_data_changed()
    
    def update_row_indices(self):
        """Update the row property for all action buttons in the table"""
        for row in range(self.expense_table.rowCount()):
            # Update action buttons row property
            action_widget = self.expense_table.cellWidget(row, 7)
            if action_widget:
                for button in action_widget.findChildren(QPushButton):
                    button.setProperty("row", row)
            
            # Update other widgets row property
            for col in range(7):  # All columns except action column
                widget = self.expense_table.cellWidget(row, col)
                if widget:
                    widget.setProperty("row", row)
    
    def on_data_changed(self):
        """Handle any data change in the form"""
        self.calculate_totals()
        self.data_changed.emit()
        
    def calculate_totals(self):
        """Calculate total expenses and remaining funds"""
        total = 0.0
        
        # Sum up all expenses converted to THB
        for expense in self.expenses:
            amount = expense.amount
            currency = expense.currency
            
            # Convert to THB if necessary
            if currency == "THB":
                total += amount
            elif currency == "USD" and self.thb_usd_input.value() > 0:
                # USD to THB conversion
                # THB per 1 USD = thb_usd_input value
                total += amount * self.thb_usd_input.value()
            elif currency == self.third_currency_combo.currentText() and self.third_currency_usd_input.value() > 0 and self.thb_usd_input.value() > 0:
                # Third currency to THB conversion (via USD)
                # Step 1: Convert third currency amount to USD
                # Formula: USD = Third currency amount / (Third currency per USD)
                # Note: self.third_currency_usd_input.value() represents Third currency per 1 USD
                usd_amount = amount / self.third_currency_usd_input.value()
                
                # Step 2: Convert USD amount to THB
                # Formula: THB = USD amount * (THB per USD)
                # Note: self.thb_usd_input.value() represents THB per 1 USD
                thb_amount = usd_amount * self.thb_usd_input.value()
                
                # Add to total in THB
                total += thb_amount
        
        # Update display labels
        self.total_label.setText(f"{total:.2f} THB")
        
        # Calculate remaining funds
        fund_amount = self.fund_thb_input.value()
        remaining = fund_amount - total
        self.remaining_label.setText(f"{remaining:.2f} THB")
        
    def clear_form(self):
        """Clear all form inputs and reset to defaults"""
        # Set initializing flag to prevent popups during reset
        self.initializing = True
        
        # Reset project information
        self.project_name_input.clear()
        self.work_location_combo.setCurrentIndex(0)  # Thailand
        self.country_combo.setCurrentIndex(0)  # Thailand
        
        # Reset fund and currency information
        self.fund_thb_input.setValue(0.0)
        self.receive_date_input.setDate(QDate.currentDate())
        self.thb_usd_input.setValue(0.0)
        self.third_currency_combo.setCurrentIndex(0)  # None
        self.third_currency_usd_input.setValue(0.0)
        
        # Clear expense table
        self.expense_table.setRowCount(0)
        self.expenses.clear()
        
        # Reset issued by information
        if self.user_info:
            self.issued_by_input.setText(f"{self.user_info.get('first_name', '')} {self.user_info.get('last_name', '')}")
        else:
            self.issued_by_input.clear()
        self.issue_date_input.setDate(QDate.currentDate())
        
        # Update totals
        self.calculate_totals()
        
        # Reset initializing flag
        self.initializing = False
        
    def get_form_data(self):
        """Get all form data as an ExpenseFormData object"""
        # Create a new form data object
        form_data = ExpenseFormData()
        
        # Project information
        form_data.project_name = self.project_name_input.text().strip()
        form_data.work_location = self.work_location_combo.currentText()
        form_data.work_country = self.country_combo.currentText() if form_data.work_location == "Abroad" else "Thailand"
        
        # Fund and currency information
        form_data.fund_thb = self.fund_thb_input.value()
        form_data.receive_date = self.receive_date_input.date().toString("yyyy-MM-dd")
        form_data.thb_usd = self.thb_usd_input.value()
        
        # Get third currency - now just the code directly
        third_currency = self.third_currency_combo.currentText()
        form_data.third_currency = self.extract_currency_code(third_currency)
            
        form_data.third_currency_usd = self.third_currency_usd_input.value()
        
        # Expense items
        form_data.expenses = self.expenses.copy()
        
        # Calculate and store total expense and remaining funds
        total_expense = float(self.total_label.text().split()[0])
        remaining_funds = float(self.remaining_label.text().split()[0])
        form_data.total_expense_thb = total_expense
        form_data.remaining_funds_thb = remaining_funds
        
        # Issued by information
        form_data.issued_by = self.issued_by_input.text().strip()
        form_data.issue_date = self.issue_date_input.date().toString("yyyy-MM-dd")
        
        return form_data
        
    def extract_currency_code(self, text):
        """Extract currency code from combo box text"""
        # Text is either "None" or just the currency code
        if text == "None":
            return None
        elif " - " in text:
            return text.split(" - ")[0]
        return text
        
    def handle_header_click(self, logical_index):
        """Handle header section click for sorting, especially for date column
        
        Args:
            logical_index (int): The column index that was clicked
        """
        # Temporarily disable sorting to handle it manually
        self.expense_table.setSortingEnabled(False)
        
        # Store current order (ascending/descending)
        header = self.expense_table.horizontalHeader()
        sort_order = header.sortIndicatorOrder()
        
        # Special handling for date column (index 0)
        if logical_index == 0:
            # Get all dates and rows for sorting
            date_row_pairs = []
            for row in range(self.expense_table.rowCount()):
                date_widget = self.expense_table.cellWidget(row, 0)
                if isinstance(date_widget, QDateEdit):
                    # Store QDate object and row index
                    date_row_pairs.append((date_widget.date(), row))
            
            # Sort by date
            if sort_order == Qt.AscendingOrder:
                date_row_pairs.sort(key=lambda x: x[0])  # Sort ascending
            else:
                date_row_pairs.sort(key=lambda x: x[0], reverse=True)  # Sort descending
            
            # Reorder the expenses list according to the sorted order
            sorted_expenses = []
            for _, row in date_row_pairs:
                sorted_expenses.append(self.expenses[row])
            
            # Store current selection
            current_row = self.expense_table.currentRow()
            current_selected_expense = self.expenses[current_row] if 0 <= current_row < len(self.expenses) else None
            
            # Update expenses list with sorted order
            self.expenses = sorted_expenses
            
            # Clear and rebuild table with sorted expenses
            self.expense_table.setRowCount(0)
            for expense in self.expenses:
                self.add_expense_to_table(expense)
                
            # Restore selection if possible
            if current_selected_expense:
                for row, expense in enumerate(self.expenses):
                    if expense == current_selected_expense:
                        self.expense_table.setCurrentCell(row, 0)
                        break
        
        # Re-enable sorting
        self.expense_table.setSortingEnabled(True)
    
    def save_form(self):
        """Save the current form"""
        # Validate form data
        if not self.validate_form():
            return
        
        try:
            # Get form data
            form_data = self.get_form_data()
            
            # Save using data manager
            if self.data_manager:
                # Use username from user_info if available
                username = self.user_info.get("username", "user")
                form_id = self.data_manager.save_form(form_data, username)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Form Saved",
                    f"Expense form saved successfully with ID: {form_id}"
                )
                
                # Clear the form for a new entry
                self.clear_form()
                
                # Emit signal that form was saved
                self.form_saved.emit(form_id)
            else:
                QMessageBox.warning(
                    self,
                    "Error",
                    "Data manager not available. Unable to save form."
                )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save form: {str(e)}"
            )
            
    def validate_form(self):
        """Validate form data before saving"""
        # Check if project name is provided
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter a project name.")
            return False
            
        # Check if there are any expenses
        if not self.expenses:
            QMessageBox.warning(self, "Validation Error", "Please add at least one expense item.")
            return False
            
        # Check if issuer name is provided
        if not self.issued_by_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please enter the name of the person issuing this form.")
            return False
            
        # For abroad work, check if exchange rates are provided
        if self.work_location_combo.currentText() == "Abroad":
            if self.thb_usd_input.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid THB to USD exchange rate.")
                return False
                
            # If third currency is selected, check its exchange rate
            if self.third_currency_combo.currentText() != "None" and self.third_currency_usd_input.value() <= 0:
                QMessageBox.warning(self, "Validation Error", "Please enter a valid exchange rate for the third currency.")
                return False
                
        return True
