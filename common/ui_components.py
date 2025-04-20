from PySide6.QtWidgets import (
    QWidget, QPushButton, QLabel, QLineEdit, QDateEdit, 
    QComboBox, QTableWidget, QTableWidgetItem, QVBoxLayout, 
    QHBoxLayout, QFormLayout, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QDate

class LabeledInput(QWidget):
    """A reusable labeled input field"""
    
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label = QLabel(label_text)
        self.label.setFixedWidth(150)
        
        # Create input field
        self.input = QLineEdit()
        
        # Add to layout
        layout.addWidget(self.label)
        layout.addWidget(self.input)
    
    def get_value(self):
        """Get the input value"""
        return self.input.text()
    
    def set_value(self, value):
        """Set the input value"""
        self.input.setText(str(value))


class LabeledComboBox(QWidget):
    """A reusable labeled combo box"""
    
    def __init__(self, label_text, items=None, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label = QLabel(label_text)
        self.label.setFixedWidth(150)
        
        # Create combo box
        self.combo = QComboBox()
        if items:
            self.combo.addItems(items)
        
        # Add to layout
        layout.addWidget(self.label)
        layout.addWidget(self.combo)
    
    def get_value(self):
        """Get the selected value"""
        return self.combo.currentText()
    
    def set_value(self, value):
        """Set the selected value"""
        index = self.combo.findText(value)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            
    def add_items(self, items):
        """Add items to the combo box"""
        self.combo.addItems(items)


class LabeledDateEdit(QWidget):
    """A reusable labeled date editor"""
    
    def __init__(self, label_text, parent=None):
        super().__init__(parent)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create label
        self.label = QLabel(label_text)
        self.label.setFixedWidth(150)
        
        # Create date edit
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        
        # Add to layout
        layout.addWidget(self.label)
        layout.addWidget(self.date_edit)
    
    def get_value(self):
        """Get the selected date as string (YYYY-MM-DD)"""
        return self.date_edit.date().toString("yyyy-MM-dd")
    
    def set_value(self, date_str):
        """Set the date from string (YYYY-MM-DD)"""
        date = QDate.fromString(date_str, "yyyy-MM-dd")
        if date.isValid():
            self.date_edit.setDate(date)


class StandardTable(QTableWidget):
    """A standard table widget with consistent styling"""
    
    def __init__(self, headers, parent=None):
        super().__init__(parent)
        
        # Set up table
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.verticalHeader().setVisible(False)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        
        # Apply styling
        self.setStyleSheet("""
            QTableWidget {
                border: 1px solid #d3d3d3;
                background-color: #ffffff;
                alternate-background-color: #f9f9f9;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                border: 1px solid #d3d3d3;
                font-weight: bold;
            }
        """)
    
    def add_row(self, row_data):
        """Add a row of data to the table"""
        row = self.rowCount()
        self.insertRow(row)
        
        for col, data in enumerate(row_data):
            item = QTableWidgetItem(str(data))
            self.setItem(row, col, item)
            
        return row


class ActionButton(QPushButton):
    """Standard styled action button"""
    
    def __init__(self, text, is_primary=False, parent=None):
        super().__init__(text, parent)
        
        if is_primary:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #2980b9;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #3498db;
                }
                QPushButton:pressed {
                    background-color: #1a5276;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #e0e0e0;
                    color: #333333;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #d0d0d0;
                }
                QPushButton:pressed {
                    background-color: #b0b0b0;
                }
            """)
