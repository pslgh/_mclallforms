"""
History tab for the expense reimbursement module.
This tab displays a list of all saved expense forms and allows viewing, editing and deleting them.
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt, Signal

class HistoryTab(QWidget):
    """Tab for displaying and managing historical expense forms"""
    
    # Signals
    view_form_requested = Signal(str)  # When view is requested (emits form ID)
    edit_form_requested = Signal(str)  # When edit is requested (emits form ID)
    form_deleted = Signal(str)         # When a form is deleted (emits form ID)
    
    def __init__(self, parent=None, data_manager=None):
        super().__init__(parent)
        self.data_manager = data_manager
        
        # Create UI components
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the history tab UI"""
        history_layout = QVBoxLayout(self)
        
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
        
    def load_historical_forms(self):
        """Load and display historical forms"""
        if not self.data_manager:
            return
            
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
            view_button.clicked.connect(self._on_view_clicked)
            
            edit_button = QPushButton("Edit")
            edit_button.setProperty("form_id", form.id)
            edit_button.clicked.connect(self._on_edit_clicked)
            
            delete_button = QPushButton("Delete")
            delete_button.setProperty("form_id", form.id)
            delete_button.clicked.connect(self._on_delete_clicked)
            
            action_layout.addWidget(view_button)
            action_layout.addWidget(edit_button)
            action_layout.addWidget(delete_button)
            
            self.history_table.setCellWidget(row, 4, action_widget)
    
    def _on_view_clicked(self):
        """Handle View button click"""
        sender = self.sender()
        form_id = sender.property("form_id")
        self.view_form_requested.emit(form_id)
    
    def _on_edit_clicked(self):
        """Handle Edit button click"""
        sender = self.sender()
        form_id = sender.property("form_id")
        self.edit_form_requested.emit(form_id)
    
    def _on_delete_clicked(self):
        """Handle Delete button click"""
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
            # Delete form
            if self.data_manager:
                try:
                    self.data_manager.delete_form(form_id)
                    self.form_deleted.emit(form_id)
                    
                    # Reload the table
                    self.load_historical_forms()
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to delete form: {str(e)}")
