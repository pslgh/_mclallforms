import sys
from pathlib import Path
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QTabWidget, QSplitter, QGroupBox,
    QHeaderView, QMessageBox, QDoubleSpinBox, QDialog, QRadioButton,
    QListWidget, QListWidgetItem, QInputDialog, QMainWindow, QScrollArea,
    QSpacerItem, QSizePolicy, QFrame, QFileDialog
)
from PySide6.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PySide6.QtGui import QPageSize, QPixmap, QColor, QBrush, QPageLayout
from PySide6.QtCore import Qt, Signal, Slot, QDate
from PySide6.QtGui import QPainter, QFont, QTextDocument, QTextCursor, QTextTableFormat, QTextTable, QTextCharFormat, QTextBlockFormat, QTextFrameFormat, QPageSize, QImage, QTextImageFormat, QTextLength, QDoubleValidator
from PySide6.QtCore import QSize, Qt
import pycountry
import iso4217

# Add parent directory to path so we can import our services and utils
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.path_utils import get_data_path, get_resource_path
from modules.expense.models.expense_data import ExpenseItem, ExpenseFormData, ExpenseDataManager

class ExpenseReimbursementWidget(QWidget):
    """Main widget for expense reimbursement functionality"""
    
    # Signal to emit when a form is saved
    form_saved = Signal(str)  # Emits form ID
    
    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self.user_info = user_info or {}
        self.current_form = ExpenseFormData()
        self.data_manager = ExpenseDataManager(get_data_path("expenses/expense_forms.json"))
        
        # Initialize UI
        self.setup_ui()
        self.initialize_form()
        
        # Ensure proper field visibility for default work location (Thailand)
        self.on_work_location_changed(0)  # 0 is the index for Thailand
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create tabs for form, history and config
        self.tab_widget = QTabWidget()
        
        # Form tab
        self.form_tab = QWidget()
        self.setup_form_tab()
        self.tab_widget.addTab(self.form_tab, "New Expense Form")
        
        # History tab
        self.history_tab = QWidget()
        self.setup_history_tab()
        self.tab_widget.addTab(self.history_tab, "History")
        
        # Config tab
        self.config_tab = QWidget()
        self.setup_config_tab()
        self.tab_widget.addTab(self.config_tab, "Config")
        
        main_layout.addWidget(self.tab_widget)
    
    def setup_form_tab(self):
        """Setup the expense form tab"""
        form_layout = QVBoxLayout(self.form_tab)
        
        # Top section with project and currency info side by side
        top_layout = QHBoxLayout()
        
        # Create a global reference to layouts for later access
        global project_layout
        global currency_layout
        
        # Project information group
        project_group = QGroupBox("Project Information")
        project_layout = QFormLayout(project_group)
        
        self.project_name_input = QLineEdit()
        self.work_location_combo = QComboBox()
        self.work_location_combo.addItems(["Thailand", "Abroad"])
        self.work_location_combo.currentIndexChanged.connect(self.on_work_location_changed)
        
        # Country selection for abroad work
        self.country_combo = QComboBox()
        self.country_combo.addItem("Thailand")  # Default country
        # Add all countries from pycountry
        for country in sorted(list(pycountry.countries), key=lambda x: x.name):
            self.country_combo.addItem(country.name)
        self.country_combo.setVisible(False)  # Initially hidden
        self.country_combo.currentIndexChanged.connect(self.on_country_changed)
        
        project_layout.addRow("Project Name:", self.project_name_input)
        project_layout.addRow("Work Location:", self.work_location_combo)
        project_layout.addRow("Work Country:", self.country_combo)
        
        # Currency group
        currency_group = QGroupBox("Fund & Currency Information")
        currency_layout = QFormLayout(currency_group)
        
        self.fund_thb_input = QDoubleSpinBox()
        self.fund_thb_input.setRange(0, 1000000)
        self.fund_thb_input.setDecimals(2)
        self.fund_thb_input.setSingleStep(100)
        self.fund_thb_input.valueChanged.connect(self.calculate_totals)
        
        self.receive_date_input = QDateEdit()
        self.receive_date_input.setCalendarPopup(True)
        self.receive_date_input.setDate(QDate.currentDate())
        
        currency_layout.addRow("Fund Amount (THB):", self.fund_thb_input)
        currency_layout.addRow("Receive Date:", self.receive_date_input)
        
        # Exchange rate widgets
        self.thb_usd_input = QDoubleSpinBox()
        self.thb_usd_input.setRange(0, 100)
        self.thb_usd_input.setDecimals(2)
        self.thb_usd_input.setSingleStep(0.1)
        self.thb_usd_input.valueChanged.connect(self.calculate_totals)
        currency_layout.addRow("THB to USD Rate:", self.thb_usd_input)
        
        # Third currency (for abroad)
        self.third_currency_combo = QComboBox()
        self.third_currency_combo.addItems(["None"] + self.data_manager.settings.currencies)
        
        self.third_currency_usd_input = QDoubleSpinBox()
        self.third_currency_usd_input.setRange(0, 100000)  # Increased maximum value
        self.third_currency_usd_input.setDecimals(4)
        self.third_currency_usd_input.setSingleStep(0.1)
        self.third_currency_usd_input.valueChanged.connect(self.calculate_totals)
        
        self.currency_widgets = QWidget()
        currency_extra_layout = QFormLayout(self.currency_widgets)
        currency_extra_layout.addRow("Third Currency:", self.third_currency_combo)
        currency_extra_layout.addRow("Third Currency to USD Rate:", self.third_currency_usd_input)
        self.currency_widgets.setVisible(False)
        
        currency_layout.addWidget(self.currency_widgets)
        
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
        
        header = self.expense_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Category
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Currency
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Receipt Type
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Actions
        
        # Add expense button
        self.add_expense_button = QPushButton("Add Empty Row")
        self.add_expense_button.clicked.connect(self.add_empty_row)
        
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
        
        # Create bottom layout for summary and issued by sections side by side
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(summary_group, 1)  # 1 = stretch factor
        bottom_layout.addWidget(issued_group, 1)  # 1 = stretch factor
        
        # Add all groups to main layout
        form_layout.addLayout(top_layout)  # Add the side-by-side layout first
        form_layout.addWidget(expense_group)
        form_layout.addLayout(bottom_layout)  # Add the side-by-side layout for bottom sections
        form_layout.addWidget(self.save_button)
    
    def setup_history_tab(self):
        """Setup the history tab"""
        history_layout = QVBoxLayout(self.history_tab)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "ID", "Project Name", "Date", "Total", "Actions"
        ])
        
        header = self.history_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Actions
        
        history_layout.addWidget(self.history_table)
        
        # Load historical forms
        self.load_historical_forms()
    
    def initialize_form(self):
        """Initialize with default values"""
        # Set default values
        self.current_form = ExpenseFormData()
        
        # Clear inputs
        self.project_name_input.clear()
        self.fund_thb_input.setValue(0)
        self.thb_usd_input.setValue(35.0)  # Default THB to USD rate
        self.third_currency_combo.setCurrentIndex(0)
        self.third_currency_usd_input.setValue(0)
        
        # Clear table
        self.expense_table.setRowCount(0)
        
        # Update totals
        self.calculate_totals()
    
    def load_form(self, form_data):
        """Load form data into the UI"""
        self.current_form = form_data
        
        # Set form values
        self.project_name_input.setText(form_data.project_name)
        
        # Set work location
        index = self.work_location_combo.findText(form_data.work_location)
        if index >= 0:
            self.work_location_combo.setCurrentIndex(index)
        
        # Update visibility of third currency widgets and country selection
        is_abroad = form_data.work_location == "Abroad"
        self.currency_widgets.setVisible(is_abroad)
        self.country_combo.setVisible(is_abroad)
        
        # Set country if saved in the form
        if hasattr(form_data, 'work_country') and form_data.work_country:
            country_index = self.country_combo.findText(form_data.work_country)
            if country_index >= 0:
                self.country_combo.setCurrentIndex(country_index)
        
        # Set currency values
        self.fund_thb_input.setValue(form_data.fund_thb)
        
        if form_data.receive_date:
            date = QDate.fromString(form_data.receive_date, "yyyy-MM-dd")
            if date.isValid():
                self.receive_date_input.setDate(date)
        
        self.thb_usd_input.setValue(form_data.thb_usd)
        
        # Set third currency if not None
        if form_data.third_currency and form_data.third_currency != "None":
            index = self.third_currency_combo.findText(form_data.third_currency)
            if index >= 0:
                self.third_currency_combo.setCurrentIndex(index)
            self.third_currency_usd_input.setValue(form_data.third_currency_usd)
        
        # Update expense table display
        self.expense_table.setRowCount(0)
        for expense in form_data.expenses:
            self.add_expense_to_table(expense)
        
        # Set issued by info
        self.issued_by_input.setText(form_data.issued_by)
        
        if form_data.issue_date:
            date = QDate.fromString(form_data.issue_date, "yyyy-MM-dd")
            if date.isValid():
                self.issue_date_input.setDate(date)
        
        # Calculate totals
        self.calculate_totals()
    
    def on_work_location_changed(self, index):
        """Handle work location change"""
        is_abroad = self.work_location_combo.currentText() == "Abroad"
        
        # Show/hide country selector and row label
        self.country_combo.setVisible(is_abroad)
        
        # Find and access the "Work Country:" label item
        work_country_label = None
        for i in range(project_layout.rowCount()):
            label_item = project_layout.itemAt(i, QFormLayout.LabelRole)
            if label_item and label_item.widget():
                if label_item.widget().text() == "Work Country:":
                    label_item.widget().setVisible(is_abroad)
                    work_country_label = label_item.widget()
                    break
                    
        # If we couldn't find the label through the layout, try to find it by querying all labels
        if not work_country_label:
            for child in project_group.findChildren(QLabel):
                if child.text() == "Work Country:":
                    child.setVisible(is_abroad)
                    break
        
        # Show currency exchange widgets only for abroad work
        self.currency_widgets.setVisible(is_abroad)
        
        # Hide THB to USD Rate label and field for Thailand work
        rate_label = None
        rate_field = None
        for i in range(currency_layout.rowCount()):
            label_item = currency_layout.itemAt(i, QFormLayout.LabelRole)
            field_item = currency_layout.itemAt(i, QFormLayout.FieldRole)
            if label_item and label_item.widget() and field_item and field_item.widget():
                if label_item.widget().text() == "THB to USD Rate:":
                    label_item.widget().setVisible(is_abroad)
                    field_item.widget().setVisible(is_abroad)
                    rate_label = label_item.widget()
                    rate_field = field_item.widget()
                    break
                    
        # If we couldn't find the label/field through the layout, try to find it by querying all widgets
        if not rate_label:
            for child in currency_group.findChildren(QLabel):
                if child.text() == "THB to USD Rate:":
                    child.setVisible(is_abroad)
                    break
            # Try to find the input field (QDoubleSpinBox) that corresponds to THB to USD rate
            # This assumes it's the only rate field or we can identify it specifically
            if self.thb_usd_input:
                self.thb_usd_input.setVisible(is_abroad)
        
        # Set country and update third currency for Thailand
        if not is_abroad:
            self.country_combo.setCurrentText("Thailand")
            self.update_country_currency("Thailand")
        else:
            # Update currency for selected country
            current_country = self.country_combo.currentText()
            self.update_country_currency(current_country)
    
    def update_country_currency(self, country_name):
        """Update third currency based on selected country"""
        # Default to None if we can't find a currency
        currency_code = None
        
        try:
            # Try to find the country by name
            if country_name != "Thailand":
                country_obj = None
                for c in pycountry.countries:
                    if c.name == country_name:
                        country_obj = c
                        break
                
                if country_obj:
                    # Get country alpha_2 code
                    country_code = country_obj.alpha_2
                    
                    # Try to get the currency for this country
                    try:
                        currencies = iso4217.Currency.get_by_country(country_code)
                        if currencies and len(currencies) > 0:
                            # Use the first currency code found
                            currency_code = currencies[0].code
                    except (AttributeError, KeyError, IndexError):
                        # If something goes wrong, default to None
                        currency_code = None
        except Exception as e:
            print(f"Error finding currency for {country_name}: {str(e)}")
        
        # Update third currency combo
        if currency_code:
            # Find the currency in the list or add it if not present
            index = self.third_currency_combo.findText(currency_code)
            if index == -1:  # Not found
                # Add the currency to the list and select it
                self.third_currency_combo.addItem(currency_code)
                self.third_currency_combo.setCurrentText(currency_code)
            else:
                # Select the existing currency
                self.third_currency_combo.setCurrentText(currency_code)
        else:
            # Default to None if no currency found
            self.third_currency_combo.setCurrentText("None")
    
    def on_country_changed(self, index):
        """Handle country selection change"""
        country_name = self.country_combo.currentText()
        self.update_country_currency(country_name)
    
    def add_empty_row(self):
        """Add a new empty row to the expense table for direct editing"""
        # Create a new expense item with default values
        expense = ExpenseItem()
        expense.expense_date = QDate.currentDate().toString("yyyy-MM-dd")
        
        # Add to the current form
        self.current_form.expenses.append(expense)
        
        # Add to the table with editable fields
        row = self.expense_table.rowCount()
        self.expense_table.insertRow(row)
        
        # Date field (DateEdit)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.fromString(expense.expense_date, "yyyy-MM-dd"))
        date_edit.dateChanged.connect(lambda date, r=row: self.update_expense_date(r, date))
        self.expense_table.setCellWidget(row, 0, date_edit)
        
        # Detail field (LineEdit)
        detail_edit = QLineEdit()
        detail_edit.textChanged.connect(lambda text, r=row: self.update_expense_detail(r, text))
        self.expense_table.setCellWidget(row, 1, detail_edit)
        
        # Vendor field (LineEdit)
        vendor_edit = QLineEdit()
        vendor_edit.textChanged.connect(lambda text, r=row: self.update_expense_vendor(r, text))
        self.expense_table.setCellWidget(row, 2, vendor_edit)
        
        # Category field (ComboBox)
        category_combo = QComboBox()
        category_combo.addItems(self.data_manager.settings.categories)
        category_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_category(r, text))
        self.expense_table.setCellWidget(row, 3, category_combo)
        
        # Amount field (DoubleSpinBox without arrows)
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0, 1000000)
        amount_spin.setDecimals(2)
        amount_spin.setSingleStep(10)
        amount_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)  # Hide up/down arrows
        amount_spin.setAlignment(Qt.AlignRight)
        amount_spin.valueChanged.connect(lambda value, r=row: self.update_expense_amount(r, value))
        self.expense_table.setCellWidget(row, 4, amount_spin)
        
        # Currency field (ComboBox)
        currencies = ["THB", "USD"]
        third_currency = self.third_currency_combo.currentText()
        if third_currency != "None":
            currencies.append(third_currency)
            
        currency_combo = QComboBox()
        currency_combo.addItems(currencies)
        currency_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_currency(r, text))
        self.expense_table.setCellWidget(row, 5, currency_combo)
        
        # Receipt type field (ComboBox)
        receipt_combo = QComboBox()
        receipt_combo.addItems(["None", "Official Receipt", "Non-Official Receipt"])
        receipt_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_receipt(r, text))
        self.expense_table.setCellWidget(row, 6, receipt_combo)
        
        # Actions
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        duplicate_button = QPushButton("Duplicate")
        duplicate_button.setProperty("row", row)
        duplicate_button.clicked.connect(self.duplicate_expense)
        
        delete_button = QPushButton("Delete")
        delete_button.setProperty("row", row)
        delete_button.clicked.connect(self.delete_expense)
        
        action_layout.addWidget(duplicate_button)
        action_layout.addWidget(delete_button)
        
        self.expense_table.setCellWidget(row, 7, action_widget)
        
        # Update calculations
        self.calculate_totals()
        
    def update_expense_date(self, row, date):
        """Update expense date when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            self.current_form.expenses[row].expense_date = date.toString("yyyy-MM-dd")
            self.calculate_totals()
            
    def update_expense_detail(self, row, text):
        """Update expense detail when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            self.current_form.expenses[row].detail = text
            # Ensure the UI and model are in sync
            detail_edit = self.expense_table.cellWidget(row, 1)
            if isinstance(detail_edit, QLineEdit) and detail_edit.text() != text:
                detail_edit.setText(text)
            
    def update_expense_vendor(self, row, text):
        """Update expense vendor when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            self.current_form.expenses[row].vendor = text
            
    def update_expense_category(self, row, text):
        """Update expense category when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            self.current_form.expenses[row].category = text
            # Ensure the UI and model are in sync
            category_combo = self.expense_table.cellWidget(row, 3)
            if isinstance(category_combo, QComboBox):
                index = category_combo.findText(text)
                if index >= 0 and category_combo.currentIndex() != index:
                    category_combo.setCurrentIndex(index)
            
    def update_expense_amount(self, row, value):
        """Update expense amount when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            self.current_form.expenses[row].amount = value
            self.calculate_totals()
            
    def update_expense_amount_text(self, row, text):
        """Update expense amount from text input"""
        if 0 <= row < len(self.current_form.expenses):
            try:
                # Replace comma with dot for decimal point
                text = text.replace(',', '.')
                # Parse float value
                value = float(text) if text.strip() else 0.0
                self.current_form.expenses[row].amount = value
                self.calculate_totals()
            except ValueError:
                # Invalid number format
                pass
            
    def update_expense_currency(self, row, text):
        """Update expense currency when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            self.current_form.expenses[row].currency = text
            self.calculate_totals()
            
    def update_expense_receipt(self, row, text):
        """Update expense receipt type when changed in table"""
        if 0 <= row < len(self.current_form.expenses):
            # Reset both receipt types
            self.current_form.expenses[row].official_receipt = False
            self.current_form.expenses[row].non_official_receipt = False
            
            # Set the selected receipt type
            if text == "Official Receipt":
                self.current_form.expenses[row].official_receipt = True
            elif text == "Non-Official Receipt":
                self.current_form.expenses[row].non_official_receipt = True
    
    def add_expense_to_table(self, expense_item=None):
        """Add an expense item to the table with editable widgets"""
        if expense_item is None:
            # For backward compatibility
            return
            
        expense = expense_item  # More descriptive name
        row = self.expense_table.rowCount()
        self.expense_table.insertRow(row)
        
        # Print debug info
        print(f"Adding row {row} to table - Category: {expense.category}, Detail: {expense.detail}")
        
        # Date field (DateEdit)
        date_edit = QDateEdit()
        date_edit.setCalendarPopup(True)
        date_edit.setDate(QDate.fromString(expense.expense_date, "yyyy-MM-dd"))
        date_edit.dateChanged.connect(lambda date, r=row: self.update_expense_date(r, date))
        self.expense_table.setCellWidget(row, 0, date_edit)
        
        # Detail field (LineEdit)
        detail_edit = QLineEdit(expense.detail)
        detail_edit.textChanged.connect(lambda text, r=row: self.update_expense_detail(r, text))
        self.expense_table.setCellWidget(row, 1, detail_edit)
        
        # Vendor field (LineEdit)
        vendor_edit = QLineEdit(expense.vendor)
        vendor_edit.textChanged.connect(lambda text, r=row: self.update_expense_vendor(r, text))
        self.expense_table.setCellWidget(row, 2, vendor_edit)
        
        # Category field (ComboBox)
        category_combo = QComboBox()
        category_combo.addItems(self.data_manager.settings.categories)
        index = category_combo.findText(expense.category)
        if index >= 0:
            category_combo.setCurrentIndex(index)
        else:
            # If category not found in list but has a value, add it
            if expense.category:
                category_combo.addItem(expense.category)
                category_combo.setCurrentText(expense.category)
                print(f"Added custom category: {expense.category}")
            else:
                # Ensure default category if none provided
                if category_combo.count() > 0 and expense.category == "":
                    expense.category = category_combo.itemText(0)
                    category_combo.setCurrentIndex(0)
                    print(f"Set default category: {expense.category}")
        
        # Force update model after setting UI widget
        if expense.category == "" and category_combo.currentText() != "":
            expense.category = category_combo.currentText()
            
        print(f"Row {row}: Category = '{expense.category}', Combo = '{category_combo.currentText()}'")
        
        category_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_category(r, text))
        self.expense_table.setCellWidget(row, 3, category_combo)
        
        # Amount field (DoubleSpinBox) for consistent look
        amount_spin = QDoubleSpinBox()
        amount_spin.setRange(0, 1000000)
        amount_spin.setDecimals(2)
        amount_spin.setSingleStep(10)
        amount_spin.setValue(expense.amount)
        amount_spin.setButtonSymbols(QDoubleSpinBox.NoButtons)  # Hide up/down arrows
        amount_spin.setAlignment(Qt.AlignRight)
        amount_spin.valueChanged.connect(lambda value, r=row: self.update_expense_amount(r, value))
        self.expense_table.setCellWidget(row, 4, amount_spin)
        
        # Currency field (ComboBox)
        currencies = ["THB", "USD"]
        third_currency = self.third_currency_combo.currentText()
        if third_currency != "None":
            currencies.append(third_currency)

        currency_combo = QComboBox()
        currency_combo.addItems(currencies)
        index = currency_combo.findText(expense.currency)
        if index >= 0:
            currency_combo.setCurrentIndex(index)
        currency_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_currency(r, text))
        self.expense_table.setCellWidget(row, 5, currency_combo)

        # Receipt type field (ComboBox)
        receipt_combo = QComboBox()
        receipt_combo.addItems(["None", "Official Receipt", "Non-Official Receipt"])
        if expense.official_receipt:
            receipt_combo.setCurrentText("Official Receipt")
        elif expense.non_official_receipt:
            receipt_combo.setCurrentText("Non-Official Receipt")
        receipt_combo.currentTextChanged.connect(lambda text, r=row: self.update_expense_receipt(r, text))
        self.expense_table.setCellWidget(row, 6, receipt_combo)

        # Actions
        action_widget = QWidget()
        action_layout = QHBoxLayout(action_widget)
        action_layout.setContentsMargins(0, 0, 0, 0)

        duplicate_button = QPushButton("Duplicate")
        duplicate_button.setProperty("row", row)
        duplicate_button.clicked.connect(self.duplicate_expense)

        delete_button = QPushButton("Delete")
        delete_button.setProperty("row", row)
        delete_button.clicked.connect(self.delete_expense)

        action_layout.addWidget(duplicate_button)
        action_layout.addWidget(delete_button)

        self.expense_table.setCellWidget(row, 7, action_widget)

        # Update summary
        self.update_expense_summary()

    def duplicate_expense(self):
        """Duplicate an expense item"""
        sender = self.sender()
        row = sender.property("row")

        if 0 <= row < len(self.current_form.expenses):
            # First sync data from UI to ensure we're duplicating the latest values
            self.sync_expense_data_from_ui()

            # Create a deep copy of the expense
            original_expense = self.current_form.expenses[row]
            new_expense = ExpenseItem()
            new_expense.expense_date = original_expense.expense_date
            new_expense.detail = original_expense.detail
            new_expense.vendor = original_expense.vendor
            new_expense.category = original_expense.category
            new_expense.amount = original_expense.amount
            new_expense.currency = original_expense.currency
            new_expense.official_receipt = original_expense.official_receipt
            new_expense.non_official_receipt = original_expense.non_official_receipt

            # Debug info
            print(f"Duplicated expense - Category: {new_expense.category}, Detail: {new_expense.detail}")

            # Add to current form and table
            self.current_form.expenses.append(new_expense)
            self.add_expense_to_table(expense_item=new_expense)

            # Update row indices for all rows to ensure they stay in sync
            self.update_row_indices()

            # Recalculate totals
            self.calculate_totals()
            
    def delete_expense(self):
        """Delete an expense item"""
        sender = self.sender()
        row = sender.property("row")
        
        if 0 <= row < len(self.current_form.expenses):
            # First sync data from UI to ensure we have the latest values
            self.sync_expense_data_from_ui()
            
            # Debug info
            expense = self.current_form.expenses[row]
            print(f"Deleting expense - Category: {expense.category}, Detail: {expense.detail}")
            
            # Remove from current form
            self.current_form.expenses.pop(row)
            
            # Remove from table
            self.expense_table.removeRow(row)
            
            # Update row indices for all rows to ensure they stay in sync
            self.update_row_indices()
            
            # Recalculate totals
            self.calculate_totals()
            
    def update_row_indices(self):
        """Update the row property for all action buttons in the table"""
        for row in range(self.expense_table.rowCount()):
            # Update row property for action buttons (duplicate and delete)
            action_widget = self.expense_table.cellWidget(row, 7)
            if action_widget:
                # Find buttons in the action widget
                for button in action_widget.findChildren(QPushButton):
                    # Update the row property to match the current row index
                    button.setProperty("row", row)
                    
    def sync_expense_data_from_ui(self):
        """Sync expense data from UI widgets to the data model"""
        # Update form-level fields
        self.current_form.project_name = self.project_name_input.text()
        self.current_form.work_location = self.work_location_combo.currentText()
        self.current_form.work_country = self.country_combo.currentText() if self.work_location_combo.currentText() == "Abroad" else "Thailand"
        self.current_form.fund_thb = self.fund_thb_input.value()
        self.current_form.receive_date = self.receive_date_input.date().toString("yyyy-MM-dd")
        self.current_form.thb_usd = self.thb_usd_input.value()
        self.current_form.third_currency = self.third_currency_combo.currentText()
        self.current_form.third_currency_usd = self.third_currency_usd_input.value()
        self.current_form.issued_by = self.issued_by_input.text()
        self.current_form.issue_date = self.issue_date_input.date().toString("yyyy-MM-dd")
        
        # Update expense-level fields
        for row in range(min(self.expense_table.rowCount(), len(self.current_form.expenses))):
            expense = self.current_form.expenses[row]
            
            # Date field
            date_edit = self.expense_table.cellWidget(row, 0)
            if isinstance(date_edit, QDateEdit):
                expense.expense_date = date_edit.date().toString("yyyy-MM-dd")
            
            # Detail field
            detail_edit = self.expense_table.cellWidget(row, 1)
            if isinstance(detail_edit, QLineEdit):
                expense.detail = detail_edit.text()
            
            # Vendor field
            vendor_edit = self.expense_table.cellWidget(row, 2)
            if isinstance(vendor_edit, QLineEdit):
                expense.vendor = vendor_edit.text()
            
            # Category field
            category_combo = self.expense_table.cellWidget(row, 3)
            if isinstance(category_combo, QComboBox):
                expense.category = category_combo.currentText()
            
            # Amount field
            amount_spin = self.expense_table.cellWidget(row, 4)
            if isinstance(amount_spin, QDoubleSpinBox):
                expense.amount = amount_spin.value()
            
            # Currency field
            currency_combo = self.expense_table.cellWidget(row, 5)
            if isinstance(currency_combo, QComboBox):
                expense.currency = currency_combo.currentText()
            
            # Receipt type field
            receipt_combo = self.expense_table.cellWidget(row, 6)
            if isinstance(receipt_combo, QComboBox):
                receipt_type = receipt_combo.currentText()
                expense.official_receipt = (receipt_type == "Official Receipt")
                expense.non_official_receipt = (receipt_type == "Non-Official Receipt")

    def calculate_totals(self):
        """Calculate and update totals"""
        # Update the current form with UI values
        self.current_form.project_name = self.project_name_input.text()
        self.current_form.work_location = self.work_location_combo.currentText()
        self.current_form.fund_thb = self.fund_thb_input.value()
        self.current_form.receive_date = self.receive_date_input.date().toString("yyyy-MM-dd")
        self.current_form.thb_usd = self.thb_usd_input.value()
        self.current_form.third_currency = self.third_currency_combo.currentText()
        self.current_form.third_currency_usd = self.third_currency_usd_input.value()
        self.current_form.issued_by = self.issued_by_input.text()
        self.current_form.issue_date = self.issue_date_input.date().toString("yyyy-MM-dd")

        # Calculate total and remaining
        total = self.current_form.calculate_total_thb()
        remaining = self.current_form.calculate_remaining_funds()

        # Update labels
        self.total_label.setText(f"{total:.2f} THB")
        self.remaining_label.setText(f"{remaining:.2f} THB")

        # Change color of remaining funds based on value
        if remaining < 0:
            self.remaining_label.setStyleSheet("font-weight: bold; color: red;")
        else:
            self.remaining_label.setStyleSheet("font-weight: bold; color: black;")
            
    def update_expense_summary(self):
        """Update the expense summary information"""
        # This method is called after adding, modifying, or removing an expense
        # Simply call calculate_totals to update the summary information
        self.calculate_totals()

    def sync_expense_data_from_ui(self):
        """Force synchronization of expense data from UI to model"""
        print("Synchronizing expense data from UI to model")
        for row in range(self.expense_table.rowCount()):
            if row < len(self.current_form.expenses):
                # Update date
                date_widget = self.expense_table.cellWidget(row, 0)
                if isinstance(date_widget, QDateEdit):
                    self.current_form.expenses[row].expense_date = date_widget.date().toString("yyyy-MM-dd")

                # Update detail
                detail_widget = self.expense_table.cellWidget(row, 1)
                if isinstance(detail_widget, QLineEdit):
                    self.current_form.expenses[row].detail = detail_widget.text()
                    print(f"Row {row}: Synchronized detail: {detail_widget.text()}")

                # Update vendor
                vendor_widget = self.expense_table.cellWidget(row, 2)
                if isinstance(vendor_widget, QLineEdit):
                    self.current_form.expenses[row].vendor = vendor_widget.text()

                # Update category
                category_widget = self.expense_table.cellWidget(row, 3)
                if isinstance(category_widget, QComboBox):
                    category = category_widget.currentText()
                    self.current_form.expenses[row].category = category
                    print(f"Row {row}: Synchronized category: {category}")

                # Update amount
                amount_widget = self.expense_table.cellWidget(row, 4)
                if isinstance(amount_widget, QDoubleSpinBox):
                    self.current_form.expenses[row].amount = amount_widget.value()

                # Update currency
                currency_widget = self.expense_table.cellWidget(row, 5)
                if isinstance(currency_widget, QComboBox):
                    self.current_form.expenses[row].currency = currency_widget.currentText()

                # Update receipt type
                receipt_widget = self.expense_table.cellWidget(row, 6)
                if isinstance(receipt_widget, QComboBox):
                    receipt_type = receipt_widget.currentText()
                    self.current_form.expenses[row].official_receipt = (receipt_type == "Official Receipt")
                    self.current_form.expenses[row].non_official_receipt = (receipt_type == "Non-Official Receipt")

    def save_form(self):
        """Save the current form"""
        # Ensure all row indices are correctly synchronized
        self.update_row_indices()

        # Force sync expense data from UI to model before saving
        self.sync_expense_data_from_ui()

        # Print debug info for all expenses before saving
        for i, expense in enumerate(self.current_form.expenses):
            print(f"Expense {i}: Category = '{expense.category}', Detail = '{expense.detail}'")        

        # Validate form
        if not self.project_name_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Project name is required.")
            return
            
        # Validate expenses
        if not self.current_form.expenses:
            QMessageBox.warning(self, "Validation Error", "At least one expense item is required.")
            return
            
        for expense in self.current_form.expenses:
            if not expense.detail.strip():
                QMessageBox.warning(self, "Validation Error", "All expense items must have a detail/description.")
                return
            if expense.amount <= 0:
                QMessageBox.warning(self, "Validation Error", "All expense items must have an amount greater than zero.")
                return
        
        # Get username from user_info
        username = self.user_info.get('username', 'user')
        
        try:
            # Save the form data
            form_id = self.data_manager.save_form(self.current_form, username)
            
            # Show success message
            QMessageBox.information(self, "Success", f"Expense form saved successfully with ID: {form_id}")
            
            # Emit signal that form was saved
            self.form_saved.emit(form_id)
            
            # Clear the form for new entry
            self.initialize_form()
            
            # Reload the history tab
            self.load_historical_forms()
            
            # Switch to history tab
            self.tab_widget.setCurrentIndex(1)  # Index 1 is the history tab
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save expense form: {str(e)}")
            print(f"Error saving form: {e}")

    def load_historical_forms(self):
        """Load and display historical forms"""
        # Clear table
        self.history_table.setRowCount(0)
        
        # Load forms
        forms = self.data_manager.load_all_forms()
        
        # Populate table
        for form in forms:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            
            # Add data to row with flags set to non-editable
            id_item = QTableWidgetItem(form.id)
            id_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Make read-only
            self.history_table.setItem(row, 0, id_item)
            
            project_item = QTableWidgetItem(form.project_name)
            project_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Make read-only
            self.history_table.setItem(row, 1, project_item)
            
            date_item = QTableWidgetItem(form.issue_date)
            date_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Make read-only
            self.history_table.setItem(row, 2, date_item)
            
            total = form.calculate_total_thb()
            total_item = QTableWidgetItem(f"{total:.2f} THB")
            total_item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)  # Make read-only
            self.history_table.setItem(row, 3, total_item)
            
            # Add action buttons
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            
            view_button = QPushButton("View")
            view_button.setProperty("form_id", form.id)
            view_button.clicked.connect(self.view_form)
            
            edit_button = QPushButton("Edit")
            edit_button.setProperty("form_id", form.id)
            edit_button.clicked.connect(self.edit_form)
            
            delete_button = QPushButton("Delete")
            delete_button.setProperty("form_id", form.id)
            delete_button.clicked.connect(self.delete_form)
            
            action_layout.addWidget(view_button)
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            
            self.history_table.setCellWidget(row, 4, action_widget)
    
    def view_form(self):
        """View a historical form in a new window"""
        sender = self.sender()
        form_id = sender.property("form_id")
        
        # Get the form
        form = self.data_manager.get_form_by_id(form_id)
        if not form:
            QMessageBox.warning(self, "Error", f"Form {form_id} not found.")
            return
        
        # Create a view dialog
        view_dialog = ExpenseFormViewDialog(form, self.data_manager.settings.currencies, parent=self)
        view_dialog.exec()
    
    def edit_form(self):
        """Edit a historical form"""
        sender = self.sender()
        form_id = sender.property("form_id")
        
        # Get the form
        form = self.data_manager.get_form_by_id(form_id)
        if not form:
            QMessageBox.warning(self, "Error", f"Form {form_id} not found.")
            return
            
        # Create the editing tab and populate with form data
        self.setup_editing_tab(form_id)
        
        # Populate form fields with data from the saved form
        self.edit_project_name_input.setText(form.project_name)
        
        # Handle work location selection
        if form.work_location == "Abroad":
            self.edit_work_location_combo.setCurrentIndex(1)  # Abroad is index 1
            self.edit_country_combo.setEnabled(True)
            index = self.edit_country_combo.findText(form.work_country)
            if index >= 0:
                self.edit_country_combo.setCurrentIndex(index)
        else:
            self.edit_work_location_combo.setCurrentIndex(0)  # Thailand is index 0
            self.edit_country_combo.setEnabled(False)
        
        # Set fund amount and date
        self.edit_fund_thb_input.setValue(form.fund_thb)
        
        if form.receive_date:
            date = QDate.fromString(form.receive_date, "yyyy-MM-dd")
            if date.isValid():
                self.edit_receive_date_input.setDate(date)
        
        # Set currency rates
        self.edit_thb_usd_input.setValue(form.thb_usd)
        
        # Set third currency if not None
        if form.third_currency and form.third_currency != "None":
            index = self.edit_third_currency_combo.findText(form.third_currency)
            if index >= 0:
                self.edit_third_currency_combo.setCurrentIndex(index)
            self.edit_third_currency_usd_input.setValue(form.third_currency_usd)
        
        # Set issued by and date
        self.edit_issued_by_input.setText(form.issued_by)
        
        if form.issue_date:
            date = QDate.fromString(form.issue_date, "yyyy-MM-dd")
            if date.isValid():
                self.edit_issue_date_input.setDate(date)
        
        # Clear and populate the expenses table
        self.edit_expense_table.setRowCount(0)
        for expense in form.expenses:
            self.add_expense_to_edit_table(expense)
        
        # Update expense summary
        self.calculate_edit_totals()
    
    def delete_form(self):
        """Delete a historical form"""
        sender = self.sender()
        form_id = sender.property("form_id")
        
        # Confirm deletion
        confirm = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete form {form_id}?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            # Delete the form
            if self.data_manager.delete_form(form_id):
                QMessageBox.information(self, "Success", f"Form {form_id} has been deleted.")
                
                # Refresh history
                self.load_historical_forms()
            else:
                QMessageBox.warning(self, "Error", f"Failed to delete form {form_id}.")
    
    def clear_form_inputs(self):
        """Clear all form inputs"""
        # Reset current form ID
        self.current_form_id = None
        
        # Clear project info
        self.project_name_input.clear()
        self.work_location_combo.setCurrentIndex(0)  # Set to Thailand
        self.country_combo.setEnabled(False)
        self.country_combo.setCurrentIndex(0)  # Set to Thailand
        
        # Clear fund info
        self.fund_thb_input.setValue(0.0)
        self.receive_date_input.setDate(QDate.currentDate())
        
        # Reset currencies
        self.thb_usd_input.setValue(35.0)  # Default THB to USD rate
        self.third_currency_combo.setCurrentIndex(0)  # Reset to first currency
        self.third_currency_usd_input.setValue(0.0)
        
        # Clear issued by and date
        self.issued_by_input.setText(f"{self.user_info.get('first_name', '')} {self.user_info.get('last_name', '')}".strip())
        self.issue_date_input.setDate(QDate.currentDate())
        
        # Clear expenses table
        self.expense_table.setRowCount(0)
        
        # Reset summary
        self.update_expense_summary()
        
    def add_category(self):
        """Add a new expense category"""
        category, ok = QInputDialog.getText(self, "Add Category", "Category name:")
        if ok and category.strip():
            self.categories_list.addItem(category.strip())

    def edit_category(self):
        """Edit a selected category"""
        current_item = self.categories_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Required", "Please select a category to edit.")
            return

        current_text = current_item.text()
        new_text, ok = QInputDialog.getText(self, "Edit Category", "Category name:", text=current_text)
        if ok and new_text.strip():
            current_item.setText(new_text.strip())
    
    def remove_category(self):
        """Remove a selected category"""
        current_item = self.categories_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Required", "Please select a category to remove.")
            return
            
        # Confirm removal
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the category '{current_item.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.categories_list.takeItem(self.categories_list.row(current_item))
            
    def setup_config_tab(self):
        """Setup the configuration tab"""
        config_layout = QVBoxLayout(self.config_tab)
        
        # Create tabs for categories and currencies
        config_tabs = QTabWidget()
        
        # Categories tab
        categories_tab = QWidget()
        categories_layout = QVBoxLayout(categories_tab)
        
        categories_label = QLabel("Expense Categories:")
        categories_label.setStyleSheet("font-weight: bold;")
        
        self.categories_list = QListWidget()
        self.categories_list.addItems(self.data_manager.settings.categories)
        
        categories_buttons = QHBoxLayout()
        add_category_button = QPushButton("Add Category")
        add_category_button.clicked.connect(self.add_category)
        edit_category_button = QPushButton("Edit Category")
        edit_category_button.clicked.connect(self.edit_category)
        remove_category_button = QPushButton("Remove Category")
        remove_category_button.clicked.connect(self.remove_category)
        
        categories_buttons.addWidget(add_category_button)
        categories_buttons.addWidget(edit_category_button)
        categories_buttons.addWidget(remove_category_button)
        
        categories_layout.addWidget(categories_label)
        categories_layout.addWidget(self.categories_list)
        categories_layout.addLayout(categories_buttons)
        
        # Currencies tab
        currencies_tab = QWidget()
        currencies_layout = QVBoxLayout(currencies_tab)
        
        currencies_label = QLabel("Available Currencies:")
        currencies_label.setStyleSheet("font-weight: bold;")
        
        self.currencies_list = QListWidget()
        self.currencies_list.addItems(self.data_manager.settings.currencies)
        
        currencies_buttons = QHBoxLayout()
        add_currency_button = QPushButton("Add Currency")
        add_currency_button.clicked.connect(self.add_currency)
        edit_currency_button = QPushButton("Edit Currency")
        edit_currency_button.clicked.connect(self.edit_currency)
        remove_currency_button = QPushButton("Remove Currency")
        remove_currency_button.clicked.connect(self.remove_currency)
        
        currencies_buttons.addWidget(add_currency_button)
        currencies_buttons.addWidget(edit_currency_button)
        currencies_buttons.addWidget(remove_currency_button)
        
        currencies_layout.addWidget(currencies_label)
        currencies_layout.addWidget(self.currencies_list)
        currencies_layout.addLayout(currencies_buttons)
        
        # Add tabs to config tabs
        config_tabs.addTab(categories_tab, "Categories")
        config_tabs.addTab(currencies_tab, "Currencies")
        
        # Save button
        save_config_button = QPushButton("Save Configuration")
        save_config_button.clicked.connect(self.save_config)
        
        config_layout.addWidget(config_tabs)
        config_layout.addWidget(save_config_button)
    
    def add_currency(self):
        """Add a new currency"""
        currency, ok = QInputDialog.getText(self, "Add Currency", "Currency code (e.g. USD, EUR):")
        if ok and currency.strip():
            self.currencies_list.addItem(currency.strip().upper())
    
    def edit_currency(self):
        """Edit a selected currency"""
        current_item = self.currencies_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Required", "Please select a currency to edit.")
            return
            
        current_text = current_item.text()
        new_text, ok = QInputDialog.getText(self, "Edit Currency", "Currency code:", text=current_text)
        if ok and new_text.strip():
            current_item.setText(new_text.strip().upper())
    
    def remove_currency(self):
        """Remove a selected currency"""
        current_item = self.currencies_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Required", "Please select a currency to remove.")
            return
            
        # Don't allow removal of THB or USD
        if current_item.text() in ["THB", "USD"]:
            QMessageBox.warning(self, "Cannot Remove", "You cannot remove the base currencies (THB and USD).")
            return
            
        # Confirm removal
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the currency '{current_item.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.currencies_list.takeItem(self.currencies_list.row(current_item))
    
    def save_config(self):
        """Save the configuration"""
        # Get categories from list
        categories = []
        for i in range(self.categories_list.count()):
            categories.append(self.categories_list.item(i).text())
        
        # Get currencies from list
        currencies = []
        for i in range(self.currencies_list.count()):
            currencies.append(self.currencies_list.item(i).text())
        
        # Update settings
        settings = ExpenseSettings()
        settings.categories = categories
        settings.currencies = currencies
        
        # Save settings
        self.data_manager.save_settings(settings)
        
        # Update UI
        QMessageBox.information(self, "Success", "Configuration saved successfully.")
    
    def remove_currency(self):
        """Remove a selected currency"""
        current_item = self.currencies_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Selection Required", "Please select a currency to remove.")
            return
            
        # Confirm removal
        confirm = QMessageBox.question(
            self,
            "Confirm Removal",
            f"Are you sure you want to remove the currency '{current_item.text()}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            self.currencies_list.takeItem(self.currencies_list.row(current_item))
    
    def save_config(self):
        """Save the configuration settings"""
        settings = self.data_manager.settings
        
        # Update categories
        settings.categories = [self.categories_list.item(i).text() for i in range(self.categories_list.count())]
        
        # Update currencies
        settings.currencies = [self.currencies_list.item(i).text() for i in range(self.currencies_list.count())]
        
        # Save settings
        self.data_manager.save_settings(settings)
        
        # Show success message
        QMessageBox.information(self, "Success", "Configuration saved successfully.")


class ExpenseFormViewDialog(QDialog):
    """Dialog for viewing an expense form with PDF export option"""
    
    def __init__(self, user_info=None, parent=None):
        super().__init__(parent)
        self.user_info = user_info or {}
        self.current_form = ExpenseFormData()
        self.data_manager = ExpenseDataManager(get_data_path("expenses/expense_forms.json"))
        
        # Add this line:
        self.editing_tab = None
        self.editing_form_id = None
        
        # Initialize UI
        self.setup_ui()
        self.initialize_form()
        
        # Ensure proper field visibility for default work location (Thailand)
        self.on_work_location_changed(0)  # 0 is the index for Thailand
    
    def setup_ui(self):
        """Create the UI components in an A4-friendly layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)  # Margins for A4 paper
        
        # Create scroll area for form content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)  # Important for resizing
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)  # Show scrollbar when needed
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)  # More spacing for better readability
        
        # Company logo instead of text header
        logo_container = QHBoxLayout()
        logo_container.setAlignment(Qt.AlignCenter)
        
        # MCL Logo
        logo_label = QLabel()
        logo_path = get_resource_path("logo/mcllogo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Scale the logo to an appropriate size
            pixmap = pixmap.scaledToWidth(300, Qt.SmoothTransformation)
            logo_label.setPixmap(pixmap)
            logo_label.setAlignment(Qt.AlignCenter)
        else:
            # Fallback if logo not found
            logo_label.setText("MCL ENGINEERING SERVICES")
            logo_label.setStyleSheet("font-size: 18pt; font-weight: bold; text-align: center;")
            logo_label.setAlignment(Qt.AlignCenter)
            
        logo_container.addWidget(logo_label)
        scroll_layout.addLayout(logo_container)
        
        # Form title
        form_title = QLabel("EXPENSE REIMBURSEMENT FORM")
        form_title.setStyleSheet("font-size: 16pt; font-weight: bold; text-align: center;")
        form_title.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(form_title)
        
        # Add some spacing
        scroll_layout.addSpacing(20)
        
        # Form header section with project and currency info side by side (like input form)
        top_layout = QHBoxLayout()
        
        # Left side - Project Information
        project_group = QGroupBox("Project Information")
        project_layout = QFormLayout(project_group)
        project_layout.setSpacing(10)  # More spacing for readability
        
        # Project name
        project_name_value = QLabel(self.form_data.project_name)
        project_name_value.setStyleSheet("font-weight: bold;")
        project_layout.addRow(QLabel("Project Name:"), project_name_value)
        
        # Work location
        work_location_value = QLabel(self.form_data.work_location)
        work_location_value.setStyleSheet("font-weight: bold;")
        project_layout.addRow(QLabel("Work Location:"), work_location_value)
        
        # Work country (if abroad)
        if self.form_data.work_location == "Abroad" and hasattr(self.form_data, 'work_country'):
            work_country_value = QLabel(self.form_data.work_country)
            work_country_value.setStyleSheet("font-weight: bold;")
            project_layout.addRow(QLabel("Work Country:"), work_country_value)
            
        # Form ID
        form_id_value = QLabel(self.form_data.id)
        form_id_value.setStyleSheet("font-weight: bold;")
        project_layout.addRow(QLabel("Form ID:"), form_id_value)
        
        # Right side - Fund & Currency Information
        currency_group = QGroupBox("Fund & Currency Information")
        currency_layout = QFormLayout(currency_group)
        currency_layout.setSpacing(10)  # More spacing for readability
        
        # Fund amount
        fund_value = QLabel(f"{self.form_data.fund_thb:.2f} THB")
        fund_value.setStyleSheet("font-weight: bold;")
        currency_layout.addRow(QLabel("Fund Amount:"), fund_value)
        
        # Receive date
        receive_value = QLabel(self.form_data.receive_date)
        receive_value.setStyleSheet("font-weight: bold;")
        currency_layout.addRow(QLabel("Receive Date:"), receive_value)
        
        # Exchange rates
        if self.form_data.work_location == "Abroad":
            # THB/USD rate
            thb_usd_value = QLabel(f"{self.form_data.thb_usd:.2f}")
            thb_usd_value.setStyleSheet("font-weight: bold;")
            currency_layout.addRow(QLabel("THB to USD Rate:"), thb_usd_value)
            
            # Third currency (if any)
            if self.form_data.third_currency != "None":
                third_currency_value = QLabel(f"{self.form_data.third_currency_usd:.4f}")
                third_currency_value.setStyleSheet("font-weight: bold;")
                currency_layout.addRow(QLabel(f"{self.form_data.third_currency} to USD Rate:"), third_currency_value)
        
        # Add project and currency groups side by side
        top_layout.addWidget(project_group, 1)
        top_layout.addWidget(currency_group, 1)
        scroll_layout.addLayout(top_layout)
        
        # Expense table
        expense_group = QGroupBox("Expenses")
        expense_layout = QVBoxLayout(expense_group)
        
        self.expense_table = QTableWidget()
        self.expense_table.setColumnCount(7)  # Updated for single receipt column
        self.expense_table.setHorizontalHeaderLabels([
            "Date", "Detail", "Vendor", "Category", "Amount", "Currency", 
            "Receipt Type"
        ])
        
        # Enable text wrapping
        self.expense_table.setWordWrap(True)
        self.expense_table.setTextElideMode(Qt.ElideNone)  # Don't truncate text
        
        # Set row height mode to adjust to content
        self.expense_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        
        header = self.expense_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # Date
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Currency
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Receipt Type
        
        # Add expenses to table (all read-only)
        for expense in self.form_data.expenses:
            row = self.expense_table.rowCount()
            self.expense_table.insertRow(row)
            
            # Create read-only items with text wrapping enabled
            date_item = QTableWidgetItem(expense.expense_date)
            date_item.setFlags(Qt.ItemIsEnabled)
            date_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.expense_table.setItem(row, 0, date_item)
            
            detail_item = QTableWidgetItem(expense.detail)
            detail_item.setFlags(Qt.ItemIsEnabled)
            detail_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.expense_table.setItem(row, 1, detail_item)
            
            vendor_item = QTableWidgetItem(expense.vendor)
            vendor_item.setFlags(Qt.ItemIsEnabled)
            vendor_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.expense_table.setItem(row, 2, vendor_item)
            
            category_item = QTableWidgetItem(expense.category)
            category_item.setFlags(Qt.ItemIsEnabled)
            category_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.expense_table.setItem(row, 3, category_item)
            
            amount_item = QTableWidgetItem(f"{expense.amount:.2f}")
            amount_item.setFlags(Qt.ItemIsEnabled)
            amount_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)  # Right-align amounts
            self.expense_table.setItem(row, 4, amount_item)
            
            currency_item = QTableWidgetItem(expense.currency)
            currency_item.setFlags(Qt.ItemIsEnabled)
            currency_item.setTextAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            self.expense_table.setItem(row, 5, currency_item)
            
            # Receipt type in single column
            receipt_type = "None"
            if expense.official_receipt:
                receipt_type = "Official Receipt"
            elif expense.non_official_receipt:
                receipt_type = "Non-Official Receipt"
                
            receipt_item = QTableWidgetItem(receipt_type)
            receipt_item.setFlags(Qt.ItemIsEnabled)
            self.expense_table.setItem(row, 6, receipt_item)
        
        expense_layout.addWidget(self.expense_table)
        scroll_layout.addWidget(expense_group)
        
        # Bottom layout for summary and issued by sections side by side (like input form)
        bottom_layout = QHBoxLayout()
        
        # Left side - Summary
        summary_group = QGroupBox("Summary")
        summary_layout = QFormLayout(summary_group)
        summary_layout.setSpacing(10)  # More spacing for readability
        
        total = self.form_data.calculate_total_thb()
        remaining = self.form_data.calculate_remaining_funds()
        
        # Total expenses
        total_value = QLabel(f"{total:.2f} THB")
        total_value.setStyleSheet("font-weight: bold;")
        summary_layout.addRow(QLabel("Total Expenses:"), total_value)
        
        # Remaining funds
        remaining_value = QLabel(f"{remaining:.2f} THB")
        
        # Set color based on value
        if remaining < 0:
            remaining_value.setStyleSheet("font-weight: bold; color: red;")
        else:
            remaining_value.setStyleSheet("font-weight: bold; color: black;")
            
        summary_layout.addRow(QLabel("Remaining Funds:"), remaining_value)
        
        # Right side - Issued By
        issued_group = QGroupBox("Issued By")
        issued_layout = QFormLayout(issued_group)
        issued_layout.setSpacing(10)  # More spacing for readability
        
        # Issued by
        issued_by_value = QLabel(self.form_data.issued_by)
        issued_by_value.setStyleSheet("font-weight: bold;")
        issued_layout.addRow(QLabel("Name:"), issued_by_value)
        
        # Issue date
        issue_date_value = QLabel(self.form_data.issue_date)
        issue_date_value.setStyleSheet("font-weight: bold;")
        issued_layout.addRow(QLabel("Date:"), issue_date_value)
        
        # Add summary and issued by groups side by side
        bottom_layout.addWidget(summary_group, 1)
        bottom_layout.addWidget(issued_group, 1)
        
        # Add bottom layout to main layout
        scroll_layout.addLayout(bottom_layout)
        
        # Add signature section
        signature_layout = QHBoxLayout()
        signature_layout.setSpacing(50)  # Space between signatures
        
        # Requestor signature
        requestor_layout = QVBoxLayout()
        requestor_layout.addItem(QSpacerItem(0, 60))  # Space for signature
        requestor_line = QFrame()
        requestor_line.setFrameShape(QFrame.HLine)
        requestor_line.setFrameShadow(QFrame.Sunken)
        requestor_layout.addWidget(requestor_line)
        requestor_layout.addWidget(QLabel("Requestor"))
        signature_layout.addLayout(requestor_layout)
        
        # Manager signature
        manager_layout = QVBoxLayout()
        manager_layout.addItem(QSpacerItem(0, 60))  # Space for signature
        manager_line = QFrame()
        manager_line.setFrameShape(QFrame.HLine)
        manager_line.setFrameShadow(QFrame.Sunken)
        manager_layout.addWidget(manager_line)
        manager_layout.addWidget(QLabel("Manager"))
        signature_layout.addLayout(manager_layout)
        
        # Finance signature
        finance_layout = QVBoxLayout()
        finance_layout.addItem(QSpacerItem(0, 60))  # Space for signature
        finance_line = QFrame()
        finance_line.setFrameShape(QFrame.HLine)
        finance_line.setFrameShadow(QFrame.Sunken)
        finance_layout.addWidget(finance_line)
        finance_layout.addWidget(QLabel("Finance"))
        signature_layout.addLayout(finance_layout)
        
        scroll_layout.addLayout(signature_layout)
        
        # Finish setting up the scroll area
        scroll_area.setWidget(scroll_widget)
        main_layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Export to PDF")
        self.export_button.clicked.connect(self.export_to_pdf)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.close_button)
        
        main_layout.addLayout(button_layout)
    
    def export_to_pdf(self):
        """Export the expense form to a PDF file using QTextDocument"""
        try:
            # Ask for the file location
            file_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Export to PDF", 
                f"Expense_Form_{self.form_data.id}.pdf", 
                "PDF Files (*.pdf)"
            )
            
            if not file_path:
                return  # User canceled
            
            # Create PDF with A4 size in landscape orientation
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setPageSize(QPageSize(QPageSize.A4))
            printer.setPageOrientation(QPageLayout.Landscape)  # Set landscape orientation
            printer.setOutputFileName(file_path)
            
            # Create text document for content
            doc = QTextDocument()
            
            # Set A4 landscape page size
            from PySide6.QtCore import QSizeF
            doc.setPageSize(QSizeF(842, 595))  # A4 landscape size in points (842 x 595)
            
            # Set document-wide margins to better use landscape space
            doc.setDocumentMargin(36)  # 0.5 inch margin
            
            # Create cursor for editing the document
            cursor = QTextCursor(doc)
            
            # Create the document content
            self._create_pdf_content(cursor, doc)
            
            # Print the document to PDF
            doc.print_(printer)
            
            # Show success message
            QMessageBox.information(self, "Export Successful", f"The expense form has been exported to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export PDF: {str(e)}")
    
    def _create_pdf_content(self, cursor, doc):
        """Create PDF content using QTextDocument to match exact format shown in the image"""
        # Document setup
        doc.setDocumentMargin(10)  # Reduced margin for the whole document
        
        # Set default font family to Arial with 50% reduced size (6pt)
        default_font = QFont("Arial", 6)  # Reduced from 12pt to 6pt (50%)
        doc.setDefaultFont(default_font)
        
        # 1. Add company logo at the top
        logo_path = "./assets/logo/mcllogo.png"
        try:
            logo_format = QTextBlockFormat()
            logo_format.setAlignment(Qt.AlignCenter)
            cursor.insertBlock(logo_format)
            
            image = QImage(logo_path)
            if not image.isNull():
                # Scale logo appropriately for landscape layout
                scaled_image = image.scaled(QSize(300, 90), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                
                # Create image format
                img_format = QTextImageFormat()
                img_format.setWidth(scaled_image.width()/2)
                img_format.setHeight(scaled_image.height()/2)
                img_format.setName(logo_path)
                
                # Insert the image
                cursor.insertImage(img_format)
            else:
                # Fallback
                print("Logo image could not be loaded")
        except Exception as e:
            print(f"Error loading logo: {e}")
            
        # 2. Title - EXPENSE REIMBURSEMENT FORM
        title_block = QTextBlockFormat()
        title_block.setAlignment(Qt.AlignCenter)
        cursor.insertBlock(title_block)
        
        # Title formatting
        title_char_format = QTextCharFormat()
        title_char_format.setFontFamily("Arial")
        title_char_format.setFontWeight(QFont.Bold)
        title_char_format.setFontPointSize(8)  # Reduced from 16pt to 8pt (50%)
        cursor.insertText("EXPENSE REIMBURSEMENT FORM", title_char_format)
        cursor.insertBlock()
#        cursor.insertBlock()
        
        # 3. Project Information and Fund Currency Information sections in one box
        
        # Create the outer frame for both sections - reduced padding and margin
        info_frame_format = QTextFrameFormat()
        info_frame_format.setBorder(1)
        info_frame_format.setPadding(2)  # Reduced from 10
        info_frame_format.setMargin(2)  # Reduced from 5
        info_frame_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        info_frame = cursor.insertFrame(info_frame_format)
        
        # Setup for headers and content
        info_cursor = QTextCursor(info_frame)
        header_char_format = QTextCharFormat()
        header_char_format.setFontFamily("Arial")
        header_char_format.setFontWeight(QFont.Bold)
        header_char_format.setFontPointSize(7)  # Reduced from 14pt to 7pt (50%)
        detail_format = QTextCharFormat()
        detail_format.setFontFamily("Arial")
        detail_format.setFontPointSize(6)  # Reduced from 12pt to 6pt (50%)
        
        # Create a table inside the frame for side-by-side sections
        info_table_format = QTextTableFormat()
        info_table_format.setBorderStyle(QTextTableFormat.BorderStyle_None)
        info_table_format.setCellPadding(2)  # Reduced from 5
        info_table_format.setCellSpacing(2)  # Reduced from 10
        info_table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        
        info_table = info_cursor.insertTable(1, 2, info_table_format)
        
        # Project Information (left side)
        project_cell = info_table.cellAt(0, 0)
        project_cursor = project_cell.firstCursorPosition()
        
        # Project Information Header
        project_cursor.insertText("Project Information", header_char_format)
        project_cursor.insertBlock()
        # project_cursor.insertBlock()
        
        # Project Name
        project_cursor.insertText("Project Name:", detail_format)
        project_cursor.insertText("\t", detail_format)
        project_cursor.insertText(f"{self.form_data.project_name}", detail_format)
        project_cursor.insertBlock()
        
        # Work Location
        project_cursor.insertText("Work Location:", detail_format)
        project_cursor.insertText("\t", detail_format)
        project_cursor.insertText(f"{self.form_data.work_location}", detail_format)
        project_cursor.insertBlock()
        
        # Work Country (if applicable)
        if self.form_data.work_location == 'Abroad':
            project_cursor.insertText("Work Country:", detail_format)
            project_cursor.insertText("\t", detail_format)
            project_cursor.insertText(f"{self.form_data.work_country}", detail_format)
            project_cursor.insertBlock()
        
        # Form ID
        project_cursor.insertText("Form ID:", detail_format)
        project_cursor.insertText("\t", detail_format)
        project_cursor.insertText(f"{self.form_data.id}", detail_format)
        
        # Fund Currency Information (right side)
        fund_cell = info_table.cellAt(0, 1)
        fund_cursor = fund_cell.firstCursorPosition()
        
        # Fund Information Header
        fund_cursor.insertText("Fund Currency Information", header_char_format)
        fund_cursor.insertBlock()
        #fund_cursor.insertBlock()
        
        # Fund Amount
        fund_cursor.insertText("Fund Amount:", detail_format)
        fund_cursor.insertText("\t", detail_format)
        fund_cursor.insertText(f"{self.form_data.fund_thb:.2f} THB", detail_format)
        fund_cursor.insertBlock()
        
        # Receive Date
        fund_cursor.insertText("Receive Date:", detail_format)
        fund_cursor.insertText("\t", detail_format)
        fund_cursor.insertText(f"{self.form_data.receive_date}", detail_format)
        fund_cursor.insertBlock()
        
        # THB to USD Rate
        fund_cursor.insertText("THB to USD Rate:", detail_format)
        fund_cursor.insertText("\t", detail_format)
        fund_cursor.insertText(f"{self.form_data.thb_usd:.2f}", detail_format)
        
        # Minimal spacing
        cursor.insertBlock()
        
        # 4. Expenses Table
        # Minimal spacing after info sections
        cursor.insertBlock()
        
        # Expenses section header and box - reduced padding and margin
        expense_frame_format = QTextFrameFormat()
        expense_frame_format.setBorder(1)
        expense_frame_format.setPadding(2)  # Reduced from 10
        expense_frame_format.setMargin(2)  # Reduced from 5
        expense_frame = cursor.insertFrame(expense_frame_format)
        
        exp_cursor = QTextCursor(expense_frame)
        exp_cursor.insertText("Expenses", header_char_format)
        exp_cursor.insertBlock()
        # exp_cursor.insertBlock()
        
        # Create expense table - minimized vertical spacing with light gray borders
        exp_table_format = QTextTableFormat()
        exp_table_format.setBorderStyle(QTextTableFormat.BorderStyle_Solid)
        exp_table_format.setCellPadding(1)  # Reduced from 2
        exp_table_format.setCellSpacing(0)
        exp_table_format.setHeaderRowCount(1)
        exp_table_format.setBorder(1)
        exp_table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        
        # Set light gray border color
        border_color = QColor(200, 200, 200)  # Light gray
        exp_table_format.setBorderBrush(QBrush(border_color))
        
        # Set column widths to ensure proper alignment - reduced # and Date column widths
        # Column order: #, Date, Detail, Vendor, Category, Amount, Currency, Receipt Type
        column_widths = [3, 8, 29, 15, 15, 10, 10, 20]  # Percentages for each column
        constraints = []
        for width in column_widths:
            constraints.append(QTextLength(QTextLength.PercentageLength, width))
        exp_table_format.setColumnWidthConstraints(constraints)
        
        # Create table with rows and columns, including an index column
        exp_table = exp_cursor.insertTable(len(self.form_data.expenses) + 1, 8, exp_table_format)
        
        # Set headers
        header_format = QTextCharFormat()
        header_format.setFontFamily("Arial")
        header_format.setFontWeight(QFont.Bold)
        header_format.setFontPointSize(6)  # Reduced from 12pt to 6pt (50%)
        
        header_block_format = QTextBlockFormat()
        header_block_format.setAlignment(Qt.AlignCenter)
        
        headers = ["#", "Date", "Detail", "Vendor", "Category", "Amount", "Currency", "Receipt Type"]
        for col, header in enumerate(headers):
            cell = exp_table.cellAt(0, col)
            cell_cursor = cell.firstCursorPosition()
            cell_cursor.insertBlock(header_block_format)  # Center align header
            cell_cursor.insertText(header, header_format)
        
        # Fill expense data
        for row, expense in enumerate(self.form_data.expenses, 1):
            # Index number - with proper alignment
            cell = exp_table.cellAt(row, 0)
            cell_cursor = cell.firstCursorPosition()
            index_block_format = QTextBlockFormat()
            index_block_format.setAlignment(Qt.AlignCenter)  # Center align index numbers
            cell_cursor.insertBlock(index_block_format)
            cell_cursor.insertText(str(row))
            
            # Date
            cell = exp_table.cellAt(row, 1)
            cell_cursor = cell.firstCursorPosition()
            # Create block format for top alignment
            top_align_format = QTextBlockFormat()
            top_align_format.setAlignment(Qt.AlignTop)
            cell_cursor.insertBlock(top_align_format)
            cell_cursor.insertText(expense.expense_date)
            
            # Detail
            cell = exp_table.cellAt(row, 2)
            cell_cursor = cell.firstCursorPosition()
            # Create block format for top alignment
            top_align_format = QTextBlockFormat()
            top_align_format.setAlignment(Qt.AlignTop)
            cell_cursor.insertBlock(top_align_format)
            cell_cursor.insertText(expense.detail)
            
            # Vendor
            cell = exp_table.cellAt(row, 3)
            cell_cursor = cell.firstCursorPosition()
            # Create block format for center-top alignment
            center_align_format = QTextBlockFormat()
            center_align_format.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Centered horizontally, top vertically
            cell_cursor.insertBlock(center_align_format)
            cell_cursor.insertText(expense.vendor)
            
            # Category
            cell = exp_table.cellAt(row, 4)
            cell_cursor = cell.firstCursorPosition()
            # Create block format for center-top alignment
            center_align_format = QTextBlockFormat()
            center_align_format.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Centered horizontally, top vertically
            cell_cursor.insertBlock(center_align_format)
            cell_cursor.insertText(expense.category)
            
            # Amount (center aligned)
            cell = exp_table.cellAt(row, 5)
            amount_block_format = QTextBlockFormat()
            amount_block_format.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Centered horizontally, top vertically
            cell_cursor = cell.firstCursorPosition()
            cell_cursor.insertBlock(amount_block_format)
            cell_cursor.insertText(f"{expense.amount:.2f}")
            
            # Currency
            cell = exp_table.cellAt(row, 6)
            cell_cursor = cell.firstCursorPosition()
            # Create block format for center-top alignment
            center_align_format = QTextBlockFormat()
            center_align_format.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Centered horizontally, top vertically
            cell_cursor.insertBlock(center_align_format)
            cell_cursor.insertText(expense.currency)
            
            # Receipt Type
            cell = exp_table.cellAt(row, 7)
            cell_cursor = cell.firstCursorPosition()
            # Create block format for center-top alignment
            center_align_format = QTextBlockFormat()
            center_align_format.setAlignment(Qt.AlignHCenter | Qt.AlignTop)  # Centered horizontally, top vertically
            cell_cursor.insertBlock(center_align_format)
            receipt_type = ""
            if expense.official_receipt:
                receipt_type = "Official Receipt"
            elif expense.non_official_receipt:
                receipt_type = "Non-Official Receipt"
            cell_cursor.insertText(receipt_type)
            
        # 5. Summary and Issued By sections in one box
        cursor.movePosition(QTextCursor.End)
        cursor.insertBlock()
        # cursor.insertBlock()
        
        # Create the outer frame for both sections - reduced vertical margins
        summary_frame_format = QTextFrameFormat()
        summary_frame_format.setBorder(1)
        summary_frame_format.setPadding(2)  # Reduced from 10
        summary_frame_format.setMargin(2)  # Reduced from 5
        summary_frame = cursor.insertFrame(summary_frame_format)
        
        summary_cursor = QTextCursor(summary_frame)
        
        # Create table for Summary and Issued By sections inside the frame
        summary_table_format = QTextTableFormat()
        summary_table_format.setBorderStyle(QTextTableFormat.BorderStyle_None)
        summary_table_format.setCellPadding(2)  # Reduced from 5
        summary_table_format.setCellSpacing(2)  # Reduced from 10
        summary_table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        
        summary_table = summary_cursor.insertTable(1, 2, summary_table_format)
        
        # Summary section (left side)
        summary_cell = summary_table.cellAt(0, 0)
        summary_cursor = summary_cell.firstCursorPosition()
        
        # Summary Header
        summary_cursor.insertText("Summary", header_char_format)
        summary_cursor.insertBlock()
        
        # Calculate expense totals by currency
        total_expenses_thb = 0
        currency_totals = {}
        for expense in self.form_data.expenses:
            if expense.currency not in currency_totals:
                currency_totals[expense.currency] = 0
            currency_totals[expense.currency] += expense.amount
            
            # Calculate equivalent in THB
            if expense.currency == "THB":
                total_expenses_thb += expense.amount
            elif expense.currency == "USD" and self.form_data.thb_usd > 0:
                total_expenses_thb += expense.amount * self.form_data.thb_usd
            elif expense.currency != "THB" and expense.currency != "USD" and self.form_data.third_currency_usd > 0 and self.form_data.thb_usd > 0:
                usd_amount = expense.amount / self.form_data.third_currency_usd
                total_expenses_thb += usd_amount * self.form_data.thb_usd
        
        # Total Expenses
        summary_cursor.insertText("Total Expenses:", detail_format)
        summary_cursor.insertText("\t", detail_format)
        summary_cursor.insertText(f"{total_expenses_thb:.2f} THB", detail_format)
        summary_cursor.insertBlock()
        
        # Remaining Funds
        remaining = self.form_data.fund_thb - total_expenses_thb
        summary_cursor.insertText("Remaining Funds:", detail_format)
        summary_cursor.insertText("\t", detail_format)
        summary_cursor.insertText(f"{remaining:.2f} THB", detail_format)
        
        # Issued By section (right side)
        issued_cell = summary_table.cellAt(0, 1)
        issued_cursor = issued_cell.firstCursorPosition()
        
        # Issued By Header
        issued_cursor.insertText("Issued By", header_char_format)
        issued_cursor.insertBlock()
        issued_cursor.insertBlock()
        
        # Name
        issued_cursor.insertText("Name:", detail_format)
        issued_cursor.insertText("\t", detail_format)
        issued_cursor.insertText(f"{self.form_data.issued_by}", detail_format)
        issued_cursor.insertBlock()
        
        # Date
        issued_cursor.insertText("Date:", detail_format)
        issued_cursor.insertText("\t", detail_format)
        issued_cursor.insertText(f"{self.form_data.issue_date}", detail_format)
        
        # 6. Signature section at the bottom
        cursor.insertBlock()
        cursor.insertBlock()
        cursor.insertBlock()
        
        # Create signature table
        signature_table_format = QTextTableFormat()
        signature_table_format.setBorderStyle(QTextTableFormat.BorderStyle_None)
        signature_table_format.setCellPadding(10)
        signature_table_format.setCellSpacing(30)
        signature_table_format.setWidth(QTextLength(QTextLength.PercentageLength, 100))
        
        signature_table = cursor.insertTable(2, 3, signature_table_format)
        
        signatures = ["Requestor", "Manager", "Finance"]
        for col, sig in enumerate(signatures):
            # Add signature line first
            cell = signature_table.cellAt(0, col)
            cell_cursor = cell.firstCursorPosition()
            
            # Center alignment for signature line
            line_block_format = QTextBlockFormat()
            line_block_format.setAlignment(Qt.AlignCenter)
            cell_cursor.insertBlock(line_block_format)
            cell_cursor.insertText("_____________________", detail_format)
            
            # Then add role name below
            cell = signature_table.cellAt(1, col)
            cell_cursor = cell.firstCursorPosition()
            
            # Center alignment for role name
            name_block_format = QTextBlockFormat()
            name_block_format.setAlignment(Qt.AlignCenter)
            cell_cursor.insertBlock(name_block_format)
            cell_cursor.insertText(sig, detail_format)
    def setup_editing_tab(self, form_id):
        """Setup the editing tab - similar to form tab but for editing existing forms"""
        # Remove any existing editing tab
        if self.editing_tab is not None:
            tab_index = self.tab_widget.indexOf(self.editing_tab)
            if tab_index != -1:
                self.tab_widget.removeTab(tab_index)
        
        # Create a new tab
        self.editing_tab = QWidget()
        editing_layout = QVBoxLayout(self.editing_tab)
        
        # Top section with project and currency info side by side
        top_layout = QHBoxLayout()
        
        # Project information group
        project_group = QGroupBox("Project Information")
        project_layout = QFormLayout(project_group)
        
        self.edit_project_name_input = QLineEdit()
        self.edit_work_location_combo = QComboBox()
        self.edit_work_location_combo.addItems(["Thailand", "Abroad"])
        self.edit_work_location_combo.currentIndexChanged.connect(self.on_edit_work_location_changed)
        
        # Country selection for abroad work
        self.edit_country_combo = QComboBox()
        self.edit_country_combo.addItem("Thailand")  # Default country
        # Add all countries from pycountry
        for country in sorted(list(pycountry.countries), key=lambda x: x.name):
            self.edit_country_combo.addItem(country.name)
        self.edit_country_combo.setVisible(False)  # Initially hidden
        self.edit_country_combo.currentIndexChanged.connect(self.on_edit_country_changed)
        
        project_layout.addRow("Project Name:", self.edit_project_name_input)
        project_layout.addRow("Work Location:", self.edit_work_location_combo)
        project_layout.addRow("Work Country:", self.edit_country_combo)
        
        # Currency group
        currency_group = QGroupBox("Fund & Currency Information")
        currency_layout = QFormLayout(currency_group)
        
        self.edit_fund_thb_input = QDoubleSpinBox()
        self.edit_fund_thb_input.setRange(0, 1000000)
        self.edit_fund_thb_input.setDecimals(2)
        self.edit_fund_thb_input.setSingleStep(100)
        self.edit_fund_thb_input.valueChanged.connect(self.calculate_edit_totals)
        
        self.edit_receive_date_input = QDateEdit()
        self.edit_receive_date_input.setCalendarPopup(True)
        self.edit_receive_date_input.setDate(QDate.currentDate())
        
        currency_layout.addRow("Fund Amount (THB):", self.edit_fund_thb_input)
        currency_layout.addRow("Receive Date:", self.edit_receive_date_input)
        
        # Exchange rate widgets
        self.edit_thb_usd_input = QDoubleSpinBox()
        self.edit_thb_usd_input.setRange(0, 100)
        self.edit_thb_usd_input.setDecimals(2)
        self.edit_thb_usd_input.setSingleStep(0.1)
        self.edit_thb_usd_input.valueChanged.connect(self.calculate_edit_totals)
        currency_layout.addRow("THB to USD Rate:", self.edit_thb_usd_input)
        
        # Third currency (for abroad)
        self.edit_third_currency_combo = QComboBox()
        self.edit_third_currency_combo.addItems(["None"] + self.data_manager.settings.currencies)
        
        self.edit_third_currency_usd_input = QDoubleSpinBox()
        self.edit_third_currency_usd_input.setRange(0, 100000)
        self.edit_third_currency_usd_input.setDecimals(4)
        self.edit_third_currency_usd_input.setSingleStep(0.1)
        self.edit_third_currency_usd_input.valueChanged.connect(self.calculate_edit_totals)
        
        self.edit_currency_widgets = QWidget()
        currency_extra_layout = QFormLayout(self.edit_currency_widgets)
        currency_extra_layout.addRow("Third Currency:", self.edit_third_currency_combo)
        currency_extra_layout.addRow("Third Currency to USD Rate:", self.edit_third_currency_usd_input)
        self.edit_currency_widgets.setVisible(False)
        
        currency_layout.addWidget(self.edit_currency_widgets)
        
        # Add project and currency groups side by side
        top_layout.addWidget(project_group, 1)
        top_layout.addWidget(currency_group, 1)
        
        # Expense table
        expense_group = QGroupBox("Expenses")
        expense_layout = QVBoxLayout(expense_group)
        
        self.edit_expense_table = QTableWidget()
        self.edit_expense_table.setColumnCount(8)
        self.edit_expense_table.setHorizontalHeaderLabels([
            "Date", "Detail", "Vendor", "Category", "Amount", "Currency", 
            "Receipt Type", "Actions"
        ])
        
        header = self.edit_expense_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)
        
        # Add expense button
        self.edit_add_expense_button = QPushButton("Add Empty Row")
        self.edit_add_expense_button.clicked.connect(self.add_empty_edit_row)
        
        expense_layout.addWidget(self.edit_expense_table)
        expense_layout.addWidget(self.edit_add_expense_button)
        
        # Summary group
        summary_group = QGroupBox("Summary")
        summary_layout = QGridLayout(summary_group)
        
        self.edit_total_label = QLabel("0.00 THB")
        self.edit_total_label.setStyleSheet("font-weight: bold;")
        self.edit_remaining_label = QLabel("0.00 THB")
        self.edit_remaining_label.setStyleSheet("font-weight: bold;")
        
        summary_layout.addWidget(QLabel("Total Expenses:"), 0, 0)
        summary_layout.addWidget(self.edit_total_label, 0, 1)
        summary_layout.addWidget(QLabel("Remaining Funds:"), 1, 0)
        summary_layout.addWidget(self.edit_remaining_label, 1, 1)
        
        # Issued by section
        issued_group = QGroupBox("Issued By")
        issued_layout = QFormLayout(issued_group)
        
        self.edit_issued_by_input = QLineEdit()
        if self.user_info:
            self.edit_issued_by_input.setText(f"{self.user_info.get('first_name', '')} {self.user_info.get('last_name', '')}")
        
        self.edit_issue_date_input = QDateEdit()
        self.edit_issue_date_input.setCalendarPopup(True)
        self.edit_issue_date_input.setDate(QDate.currentDate())
        
        issued_layout.addRow("Name:", self.edit_issued_by_input)
        issued_layout.addRow("Date:", self.edit_issue_date_input)
        
        # Save button
        self.edit_save_button = QPushButton("Save Changes")
        self.edit_save_button.clicked.connect(self.save_edit_form)
        
        # Create bottom layout for summary and issued by sections side by side
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(summary_group, 1)
        bottom_layout.addWidget(issued_group, 1)
        
        # Add all groups to main layout
        editing_layout.addLayout(top_layout)
        editing_layout.addWidget(expense_group)
        editing_layout.addLayout(bottom_layout)
        editing_layout.addWidget(self.edit_save_button)
        
        # Add the tab
        self.editing_form_id = form_id
        tab_title = f"Editing: {form_id}"
        self.tab_widget.addTab(self.editing_tab, tab_title)
        
        # Switch to the new tab
        self.tab_widget.setCurrentWidget(self.editing_tab)

