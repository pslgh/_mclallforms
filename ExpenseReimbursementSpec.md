# Expense Reimbursement Application Specification

## Overview
This document provides specifications for converting the existing Vue.js-based expense reimbursement application into a Python+PySide6 module that integrates with the main engineering services application.

## Features to Implement

### 1. Core Expense Management
- **Expense Entry**: Form for adding new expense items with details
- **Currency Handling**: Support for multiple currencies with conversion
- **Receipt Management**: Track official and non-official receipts
- **Expense Categories**: Predefined categories (Fuel, Hotel, Meals, etc.)
- **Historical Records**: View, edit, and delete past expense reports

### 2. User Interface Components
- **Main Form**: Project information, currency settings, and expense table
- **Expense Table**: Interactive table for expense entries
- **Summary Section**: Calculated totals and remaining funds
- **Report View**: Formatted view of expense reports for review
- **Context Menu**: Right-click options for historical reports

### 3. Report Generation
- **PDF Export**: Generate professional PDF reports
- **Print Functionality**: Direct printing of expense reports
- **Signatures**: Support for digital signatures

## UI Structure

### 1. Main Expense Form
- Project name input
- Work location selection (Thailand/Abroad)
- Currency management section
  - Fund amount in THB
  - Receive date
  - Currency exchange rates (when abroad)
- Expense data table with columns:
  - Date
  - Detail
  - Vendor
  - Category
  - Amount
  - Currency
  - Official Receipt checkbox
  - Non-Official Receipt checkbox
  - Actions
- Add Expense button
- Total and remaining calculations
- Save button

### 2. Historical Records Panel
- List of saved expense reports
- Search/filter functionality
- Context menu for view/edit/delete operations

### 3. Report View
- Company logo
- Report header with project information
- Currency information
- Expense table with all entries
- Summary calculations
- Signature area

## Data Structure

### Expense Form Data
```python
class ExpenseFormData:
    """Data model for expense reimbursement forms"""
    def __init__(self):
        self.id = ""  # Unique identifier
        self.project_name = ""
        self.work_location = "Thailand"  # Thailand or Abroad
        self.fund_thb = 0.0
        self.receive_date = ""
        self.thb_usd = 0.0  # Exchange rate
        self.third_currency = "None"
        self.third_currency_usd = 0.0
        self.expenses = []  # List of ExpenseItem objects
        self.issued_by = ""
        self.issue_date = ""
        
class ExpenseItem:
    """Individual expense entry"""
    def __init__(self):
        self.expense_date = ""
        self.detail = ""
        self.vendor = ""
        self.category = ""
        self.amount = 0.0
        self.currency = "THB"
        self.official_receipt = False
        self.non_official_receipt = False
```

### JSON Storage Format
```json
{
  "forms": [
    {
      "id": "EXP-2025-001",
      "project_name": "Client XYZ Site Survey",
      "work_location": "Thailand",
      "fund_thb": 5000.0,
      "receive_date": "2025-04-10",
      "thb_usd": 35.2,
      "third_currency": "None",
      "third_currency_usd": 0.0,
      "expenses": [
        {
          "expense_date": "2025-04-11",
          "detail": "Site transportation",
          "vendor": "Taxi service",
          "category": "Taxi",
          "amount": 450.0,
          "currency": "THB",
          "official_receipt": true,
          "non_official_receipt": false
        },
        // More expense items...
      ],
      "issued_by": "Employee Name",
      "issue_date": "2025-04-14"
    },
    // More forms...
  ]
}
```

## Functionality Specifications

### 1. Form Validation
- Required fields: project_name, issued_by, issue_date
- Every expense must have date, detail, amount, and category
- Currency conversion rates required when using foreign currencies
- Prevent duplicate form IDs

### 2. Currency Conversion
- Convert all expenses to THB for totaling
- THB is the base currency
- Support for USD as secondary currency
- Support for third currency when working abroad
- Store exchange rates with each report

### 3. Calculations
- Total expense in THB
- Remaining funds (Fund amount - Total expense)
- Categorized expense subtotals

### 4. Historical Data Management
- Load all previous forms on startup
- Right-click context menu for actions
- Confirmation dialog for delete operations
- Form editing with history preservation

## Implementation Guidelines

### 1. Main Expense Widget
```python
class ExpenseReimbursementWidget(QWidget):
    """Main widget for expense reimbursement functionality"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.load_historical_forms()
        
    def setup_ui(self):
        # Create form layout
        # Add expense table
        # Create buttons and actions
        
    def add_expense(self):
        # Add new row to expense table
        
    def remove_expense(self, index):
        # Remove row from expense table
        
    def calculate_totals(self):
        # Update total and remaining amounts
        
    def save_form(self):
        # Validate and save form to JSON
        
    def load_historical_forms(self):
        # Load previous forms from JSON
```

### 2. Data Management Class
```python
class ExpenseDataManager:
    """Handles all data operations for expense module"""
    def __init__(self, data_path):
        self.data_path = data_path
        self.ensure_data_file()
        
    def ensure_data_file(self):
        # Create data file if it doesn't exist
        
    def load_all_forms(self):
        # Load all forms from JSON file
        
    def save_form(self, form_data):
        # Save new or updated form
        
    def delete_form(self, form_id):
        # Remove form from data
        
    def get_form(self, form_id):
        # Retrieve specific form
```

### 3. PDF Generator
```python
class ExpensePDFGenerator:
    """Generates PDF reports from expense data"""
    def __init__(self, form_data):
        self.form_data = form_data
        
    def generate_pdf(self, output_path):
        # Create PDF with formatting
        # Include tables, calculations, etc.
```

## Integration with Main Application

### 1. Module Registration
- Register as a module in the main application
- Define sidebar menu entry and icon
- Implement module interface for loading/unloading

### 2. Shared Resources
- Use common styling from main application
- Access shared user information
- Utilize common PDF generation utilities

### 3. Data Access
- Store data in the module's dedicated JSON files
- Follow the application's data access patterns
- Prepare for future MongoDB migration

## Transition from Vue.js Implementation

### 1. UI Migration Strategy
- Recreate all Vue components as PySide6 widgets
- Match existing styling with Qt Style Sheets
- Preserve all functionality with equivalent Python code

### 2. Data Compatibility
- Ensure new JSON format is compatible with existing data
- Provide data migration utility if needed
- Preserve historical records

### 3. Functionality Improvements
- Address any limitations from the Vue implementation
- Add offline capabilities
- Improve performance with native Python
