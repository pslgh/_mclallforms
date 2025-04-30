"""
Standard Service Rate Tab - Configure service rates for different work types
"""
import sys
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QGridLayout,
    QPushButton, QDoubleSpinBox, QComboBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QSizePolicy
)
from PySide6.QtCore import Qt, Signal

# Add parent directory to path so we can import our models
sys.path.append(str(Path(__file__).resolve().parents[3]))
from utils.path_utils import get_data_path

# Default rates for different work types in USD and THB
DEFAULT_RATES = {
    "USD": {
        "Special Field Services": {
            "Normal Service Hour Rate": 220.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 750.00,
            "< 80 km T&L Rate": 100.00,
            "> 80 km T&L Rate": 420.00,
            "Addition Day Rate for Offshore Work": 550.00,
            "Emergency Request (<24H notification) Rate": 660.00,
            "Other Transportation Charge": 0.00
        },
        "Regular Field Services": {
            "Normal Service Hour Rate": 220.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 750.00,
            "< 80 km T&L Rate": 100.00,
            "> 80 km T&L Rate": 420.00,
            "Addition Day Rate for Offshore Work": 550.00,
            "Emergency Request (<24H notification) Rate": 660.00,
            "Other Transportation Charge": 0.00
        },
        "Consultation": {
            "Normal Service Hour Rate": 220.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 750.00,
            "< 80 km T&L Rate": 100.00,
            "> 80 km T&L Rate": 420.00,
            "Addition Day Rate for Offshore Work": 550.00,
            "Emergency Request (<24H notification) Rate": 660.00,
            "Other Transportation Charge": 0.00
        },
        "Emergency Support": {
            "Normal Service Hour Rate": 220.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 750.00,
            "< 80 km T&L Rate": 100.00,
            "> 80 km T&L Rate": 420.00,
            "Addition Day Rate for Offshore Work": 550.00,
            "Emergency Request (<24H notification) Rate": 660.00,
            "Other Transportation Charge": 0.00
        },
        "Other": {
            "Normal Service Hour Rate": 220.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 750.00,
            "< 80 km T&L Rate": 100.00,
            "> 80 km T&L Rate": 420.00,
            "Addition Day Rate for Offshore Work": 550.00,
            "Emergency Request (<24H notification) Rate": 660.00,
            "Other Transportation Charge": 0.00
        }
    },
    "THB": {
        "Special Field Services": {
            "Normal Service Hour Rate": 6500.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 25000.00,
            "< 80 km T&L Rate": 2500.00,
            "> 80 km T&L Rate": 7500.00,
            "Addition Day Rate for Offshore Work": 17500.00,
            "Emergency Request (<24H notification) Rate": 16000.00,
            "Other Transportation Charge": 0.00
        },
        "Regular Field Services": {
            "Normal Service Hour Rate": 6500.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 25000.00,
            "< 80 km T&L Rate": 2500.00,
            "> 80 km T&L Rate": 7500.00,
            "Addition Day Rate for Offshore Work": 17500.00,
            "Emergency Request (<24H notification) Rate": 16000.00,
            "Other Transportation Charge": 0.00
        },
        "Consultation": {
            "Normal Service Hour Rate": 6500.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 25000.00,
            "< 80 km T&L Rate": 2500.00,
            "> 80 km T&L Rate": 7500.00,
            "Addition Day Rate for Offshore Work": 17500.00,
            "Emergency Request (<24H notification) Rate": 16000.00,
            "Other Transportation Charge": 0.00
        },
        "Emergency Support": {
            "Normal Service Hour Rate": 6500.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 25000.00,
            "< 80 km T&L Rate": 2500.00,
            "> 80 km T&L Rate": 7500.00,
            "Addition Day Rate for Offshore Work": 17500.00,
            "Emergency Request (<24H notification) Rate": 16000.00,
            "Other Transportation Charge": 0.00
        },
        "Other": {
            "Normal Service Hour Rate": 6500.00,
            "Data Acquisition, Diagnostics Instrument Usage Rate": 25000.00,
            "< 80 km T&L Rate": 2500.00,
            "> 80 km T&L Rate": 7500.00,
            "Addition Day Rate for Offshore Work": 17500.00,
            "Emergency Request (<24H notification) Rate": 16000.00,
            "Other Transportation Charge": 0.00
        }
    }
}

class RatesTab(QWidget):
    """Standard Service Rate Tab allows configuration of service rates by work type"""
    
    # Signal to emit when rates are updated
    rates_updated = Signal(dict)
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.parent = parent
        self.data_manager = data_manager
        
        # Try to load saved rates, or use defaults
        self.rates = self.load_rates() or DEFAULT_RATES
        
        # Initialize UI
        self.setup_ui()
        
    def setup_ui(self):
        """Create the UI components"""
        main_layout = QVBoxLayout(self)
        
        # Create selector controls for currency and work type
        selection_group = QGroupBox("Select Rate Configuration")
        selection_layout = QHBoxLayout(selection_group)
        
        # Work Type selector - now placed first
        work_type_label = QLabel("Work Type:")
        self.work_type_selector = QComboBox()
        self.work_type_selector.addItems([
            "Special Field Services", 
            "Regular Field Services", 
            "Consultation", 
            "Emergency Support", 
            "Other"
        ])
        self.work_type_selector.currentTextChanged.connect(self.update_rate_display)
        
        # Currency selector
        currency_label = QLabel("Currency:")
        self.currency_selector = QComboBox()
        self.currency_selector.addItems(["USD", "THB"])
        self.currency_selector.currentTextChanged.connect(self.update_rate_display)
        
        # Add to selection layout
        selection_layout.addWidget(work_type_label)
        selection_layout.addWidget(self.work_type_selector)
        selection_layout.addSpacing(20)
        selection_layout.addWidget(currency_label)
        selection_layout.addWidget(self.currency_selector)
        selection_layout.addStretch(1)
        
        # Create rates table
        rates_group = QGroupBox("Service Rates")
        rates_layout = QVBoxLayout(rates_group)
        
        # Create table for displaying and editing rates
        self.rates_table = QTableWidget(7, 2)  # 7 rows (one per rate type), 2 columns (description, rate)
        self.rates_table.setHorizontalHeaderLabels(["Service", "Rate"])
        self.rates_table.verticalHeader().setVisible(False)
        self.rates_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        
        # Set a fixed row height to ensure all rows are visible
        for i in range(7):
            self.rates_table.setRowHeight(i, 40)
            
        # Set minimum height for the table to fit all rows comfortably
        self.rates_table.setMinimumHeight(400)
        
        # Ensure group box can expand to accommodate the table
        rates_group.setMinimumHeight(450)
        
        self.rates_table.setStyleSheet("""
            QTableWidget {
                gridline-color: #d0d0d0;
                background-color: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                font-size: 10pt;
            }
            QHeaderView::section {
                background-color: #f0f0f0;
                padding: 4px;
                font-weight: bold;
                border: 1px solid #d0d0d0;
                border-radius: 0px;
            }
            QTableWidget::item {
                border-bottom: 1px solid #d0d0d0;
                padding: 4px;
                color: black;
            }
            
            QTableWidget::item:selected,
            QTableWidget::item:focus {
                background-color: #e0e0e0;
                color: black;
            }
            
            /* Fix for editable cells to ensure text remains visible */
            QLineEdit {
                color: black;
                background-color: white;
                selection-background-color: #a6a6a6;
                selection-color: black;
            }
        """)
        
        # Set up the rate types in the first column (these are fixed)
        rate_types = [
            "Normal Service Hour Rate",
            "Data Acquisition, Diagnostics Instrument Usage Rate",
            "< 80 km T&L Rate",
            "> 80 km T&L Rate",
            "Addition Day Rate for Offshore Work",
            "Emergency Request (<24H notification) Rate",
            "Other Transportation Charge"
        ]
        
        for i, rate_type in enumerate(rate_types):
            item = QTableWidgetItem(rate_type)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)  # Make first column read-only
            self.rates_table.setItem(i, 0, item)
        
        rates_layout.addWidget(self.rates_table)
        
        # Add buttons for saving rates
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Rates")
        self.save_button.clicked.connect(self.save_rates)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self.reset_to_defaults)
        self.reset_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 8px 16px;
                min-height: 30px;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addSpacing(10)
        button_layout.addWidget(self.reset_button)
        button_layout.addStretch(1)
        
        # Add to main layout with adjusted heights
        selection_group.setMaximumHeight(100)  # Keep the selection group compact
        main_layout.addWidget(selection_group)
        main_layout.addWidget(rates_group, 1)  # Give the rates group more vertical space
        main_layout.addLayout(button_layout)
        main_layout.addStretch(1)
        
        # Update the display with initial values
        self.update_rate_display()
    
    def update_rate_display(self):
        """Update the rates displayed in the table based on current selection"""
        currency = self.currency_selector.currentText()
        work_type = self.work_type_selector.currentText()
        
        if currency in self.rates and work_type in self.rates[currency]:
            # Get the rates for the selected currency and work type
            selected_rates = self.rates[currency][work_type]
            
            # Update the table with these rates
            for i in range(self.rates_table.rowCount()):
                rate_type = self.rates_table.item(i, 0).text()
                
                if rate_type in selected_rates:
                    # Create editable rate item
                    rate_value = selected_rates[rate_type]
                    rate_item = QTableWidgetItem(f"{rate_value:.2f}")
                    rate_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    rate_item.setForeground(Qt.black)  # Explicitly set text color to black
                    self.rates_table.setItem(i, 1, rate_item)
    
    def save_rates(self):
        """Save the current rates to the rates dictionary"""
        currency = self.currency_selector.currentText()
        work_type = self.work_type_selector.currentText()
        
        # Ensure the nested dictionaries exist
        if currency not in self.rates:
            self.rates[currency] = {}
        if work_type not in self.rates[currency]:
            self.rates[currency][work_type] = {}
        
        # Update rates from the table
        for i in range(self.rates_table.rowCount()):
            rate_type = self.rates_table.item(i, 0).text()
            rate_item = self.rates_table.item(i, 1)
            
            if rate_item:
                try:
                    # Get the rate value from the item
                    rate_value = float(rate_item.text())
                    self.rates[currency][work_type][rate_type] = rate_value
                except (ValueError, TypeError):
                    # Invalid input, show error message
                    QMessageBox.warning(
                        self,
                        "Invalid Rate",
                        f"Invalid rate for {rate_type}. Please enter a valid number."
                    )
                    return
        
        # Save rates to storage (implement this based on your data storage mechanism)
        self.save_rates_to_storage()
        
        # Emit signal that rates have been updated
        self.rates_updated.emit(self.rates)
        
        # Show success message
        QMessageBox.information(
            self,
            "Rates Saved",
            f"Service rates for {work_type} in {currency} have been saved successfully."
        )
    
    def reset_to_defaults(self):
        """Reset the current view to default rates"""
        currency = self.currency_selector.currentText()
        work_type = self.work_type_selector.currentText()
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Reset Rates",
            f"Are you sure you want to reset {work_type} rates in {currency} to defaults?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Reset to defaults
            if currency in DEFAULT_RATES and work_type in DEFAULT_RATES[currency]:
                if currency not in self.rates:
                    self.rates[currency] = {}
                    
                self.rates[currency][work_type] = DEFAULT_RATES[currency][work_type].copy()
                
                # Update the display
                self.update_rate_display()
                
                # Save to storage
                self.save_rates_to_storage()
                
                # Emit signal that rates have been updated
                self.rates_updated.emit(self.rates)
                
                # Show success message
                QMessageBox.information(
                    self,
                    "Rates Reset",
                    f"Service rates for {work_type} in {currency} have been reset to defaults."
                )
    
    def load_rates(self):
        """Load rates from storage"""
        try:
            # Load from file or database
            # For now, return None to use defaults
            return None
        except Exception as e:
            print(f"Error loading rates: {str(e)}")
            return None
    
    def save_rates_to_storage(self):
        """Save rates to storage"""
        try:
            # Save to file or database
            # This is a placeholder for actual storage implementation
            print("Rates saved to storage")
        except Exception as e:
            print(f"Error saving rates: {str(e)}")
            QMessageBox.warning(
                self,
                "Error Saving Rates",
                f"Could not save rates: {str(e)}"
            )
