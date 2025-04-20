import sys
import os
from pathlib import Path
import datetime
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QGridLayout,
    QLabel, QLineEdit, QComboBox, QDateEdit, QTableWidget, QTableWidgetItem,
    QPushButton, QCheckBox, QTabWidget, QSplitter, QGroupBox,
    QHeaderView, QMessageBox, QMenu, QDialog, QFileDialog, QSpinBox, QDoubleSpinBox,
    QRadioButton
)
from PySide6.QtCore import Qt, Signal, Slot, QDate
from PySide6.QtGui import QIcon, QAction, QColor

# Add parent directory to path so we can import our services and utils
sys.path.append(str(Path(__file__).resolve().parents[2]))
from utils.path_utils import get_data_path
from services.data_service import DataService
from modules.expense.models.expense_data import ExpenseItem, ExpenseFormData, ExpenseDataManager

class ExpenseItemDialog(QDialog):
    """Dialog for adding/editing an expense item"""
    
    def __init__(self, expense_item=None, currencies=None, categories=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Expense Entry")
        self.setMinimumWidth(400)
        
        self.expense_item = expense_item or ExpenseItem()
        self.currencies = currencies or ["THB", "USD"]
        self.categories = categories or [
            "Fuel", "Hotel", "Meals", "Taxi", "Transport", "Materials", 
            "Tools", "Office", "Communication", "Entertainment", "Other"
        ]
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        
        form_layout = QFormLayout()
        
        # Date input
        self.date_input = QDateEdit()
        self.date_input.setCalendarPopup(True)
        self.date_input.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_input)
        
        # Detail input
        self.detail_input = QLineEdit()
        form_layout.addRow("Detail:", self.detail_input)
        
        # Vendor input
        self.vendor_input = QLineEdit()
        form_layout.addRow("Vendor:", self.vendor_input)
        
        # Category selection
        self.category_combo = QComboBox()
        self.category_combo.addItems(self.categories)
        form_layout.addRow("Category:", self.category_combo)
        
        # Amount input
        self.amount_input = QDoubleSpinBox()
        self.amount_input.setRange(0, 1000000)
        self.amount_input.setDecimals(2)
        self.amount_input.setSingleStep(10)
        form_layout.addRow("Amount:", self.amount_input)
        
        # Currency selection
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(self.currencies)
        form_layout.addRow("Currency:", self.currency_combo)
        
        # Receipt radio buttons (mutually exclusive)
        self.receipt_type_group = QGroupBox("Receipt Type")
        receipt_layout = QHBoxLayout(self.receipt_type_group)
        
        self.official_receipt_radio = QRadioButton("Official Receipt")
        self.non_official_receipt_radio = QRadioButton("Non-Official Receipt")
        self.official_receipt_radio.setChecked(True)  # Default to official receipt
        
        receipt_layout.addWidget(self.official_receipt_radio)
        receipt_layout.addWidget(self.non_official_receipt_radio)
        form_layout.addRow("", self.receipt_type_group)
        
        main_layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_expense)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.cancel_button)
        button_layout.addWidget(self.save_button)
        
        main_layout.addLayout(button_layout)
    
    def load_data(self):
        """Load expense item data into the form"""
        if self.expense_item.expense_date:
            date = QDate.fromString(self.expense_item.expense_date, "yyyy-MM-dd")
            if date.isValid():
                self.date_input.setDate(date)
        
        self.detail_input.setText(self.expense_item.detail)
        self.vendor_input.setText(self.expense_item.vendor)
        
        # Set category
        index = self.category_combo.findText(self.expense_item.category)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)
        
        self.amount_input.setValue(self.expense_item.amount)
        
        # Set currency
        index = self.currency_combo.findText(self.expense_item.currency)
        if index >= 0:
            self.currency_combo.setCurrentIndex(index)
        
        if self.expense_item.official_receipt:
            self.official_receipt_radio.setChecked(True)
        elif self.expense_item.non_official_receipt:
            self.non_official_receipt_radio.setChecked(True)
        else:
            self.official_receipt_radio.setChecked(True)  # Default
    
    def save_expense(self):
        """Save data to expense item"""
        # Validate inputs
        if not self.detail_input.text().strip():
            QMessageBox.warning(self, "Validation Error", "Detail is required.")
            return
        
        if self.amount_input.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Amount must be greater than zero.")
            return
        
        # Update expense item
        self.expense_item.expense_date = self.date_input.date().toString("yyyy-MM-dd")
        self.expense_item.detail = self.detail_input.text().strip()
        self.expense_item.vendor = self.vendor_input.text().strip()
        self.expense_item.category = self.category_combo.currentText()
        self.expense_item.amount = self.amount_input.value()
        self.expense_item.currency = self.currency_combo.currentText()
        self.expense_item.official_receipt = self.official_receipt_radio.isChecked()
        self.expense_item.non_official_receipt = self.non_official_receipt_radio.isChecked()
        
        # Close dialog with success
        self.accept()
