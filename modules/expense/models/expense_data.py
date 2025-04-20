import json
import os
import datetime
from pathlib import Path
import uuid

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
    
    @classmethod
    def from_dict(cls, data):
        """Create ExpenseItem from dictionary"""
        item = cls()
        item.expense_date = data.get("expense_date", "")
        item.detail = data.get("detail", "")
        item.vendor = data.get("vendor", "")
        item.category = data.get("category", "")
        item.amount = float(data.get("amount", 0.0))
        item.currency = data.get("currency", "THB")
        item.official_receipt = data.get("official_receipt", False)
        item.non_official_receipt = data.get("non_official_receipt", False)
        return item
    
    def to_dict(self):
        """Convert ExpenseItem to dictionary"""
        return {
            "expense_date": self.expense_date,
            "detail": self.detail,
            "vendor": self.vendor,
            "category": self.category,
            "amount": self.amount,
            "currency": self.currency,
            "official_receipt": self.official_receipt,
            "non_official_receipt": self.non_official_receipt
        }

class ExpenseFormData:
    """Data model for expense reimbursement forms"""
    def __init__(self):
        """Initialize ExpenseFormData with default values"""
        self.id = ""
        self.project_name = ""
        self.work_location = "Thailand"  # Thailand or Abroad
        self.work_country = "Thailand"    # Country when abroad
        self.fund_thb = 0.0
        self.receive_date = ""
        self.thb_usd = 0.0  # Exchange rate
        self.third_currency = "None"
        self.third_currency_usd = 0.0
        self.expenses = []  # List of ExpenseItem objects
        self.total_expense_thb = 0.0  # Total expenses in THB
        self.remaining_funds_thb = 0.0  # Remaining funds in THB
        self.issued_by = ""
        self.issue_date = ""
    
    @classmethod
    def from_dict(cls, data):
        """Create ExpenseFormData from dictionary"""
        form = cls()
        form.id = data.get("id", "")
        form.project_name = data.get("project_name", "")
        form.work_location = data.get("work_location", "Thailand")
        form.work_country = data.get("work_country", "Thailand")
        form.fund_thb = float(data.get("fund_thb", 0.0))
        form.receive_date = data.get("receive_date", "")
        form.thb_usd = float(data.get("thb_usd", 0.0))
        form.third_currency = data.get("third_currency", "None")
        form.third_currency_usd = float(data.get("third_currency_usd", 0.0))
        
        # Convert expense dictionaries to ExpenseItem objects
        form.expenses = [ExpenseItem.from_dict(item) for item in data.get("expenses", [])]
        
        # Load total expense and remaining funds
        form.total_expense_thb = float(data.get("total_expense_thb", 0.0))
        form.remaining_funds_thb = float(data.get("remaining_funds_thb", 0.0))
        
        form.issued_by = data.get("issued_by", "")
        form.issue_date = data.get("issue_date", "")
        return form
    
    def to_dict(self):
        """Convert ExpenseFormData to dictionary"""
        return {
            "id": self.id,
            "project_name": self.project_name,
            "work_location": self.work_location,
            "work_country": self.work_country,
            "fund_thb": self.fund_thb,
            "receive_date": self.receive_date,
            "thb_usd": self.thb_usd,
            "third_currency": self.third_currency,
            "third_currency_usd": self.third_currency_usd,
            "expenses": [expense.to_dict() for expense in self.expenses],
            "total_expense_thb": self.total_expense_thb,
            "remaining_funds_thb": self.remaining_funds_thb,
            "issued_by": self.issued_by,
            "issue_date": self.issue_date
        }
    
    def calculate_total_thb(self):
        """Calculate total expenses in THB"""
        total = 0.0
        for expense in self.expenses:
            if expense.currency == "THB":
                total += expense.amount
            elif expense.currency == "USD" and self.thb_usd > 0:
                total += expense.amount * self.thb_usd
            elif expense.currency == self.third_currency and self.third_currency_usd > 0 and self.thb_usd > 0:
                # Convert from third currency to USD first, then from USD to THB
                usd_amount = expense.amount / self.third_currency_usd  # Convert to USD (dividing by third_currency/USD rate)
                total += usd_amount * self.thb_usd  # Convert from USD to THB
        return total
    
    def calculate_remaining_funds(self):
        """Calculate remaining funds in THB"""
        total_expenses = self.calculate_total_thb()
        return self.fund_thb - total_expenses
    
    def categorize_expenses(self):
        """Group expenses by category with subtotals in THB"""
        categories = {}
        for expense in self.expenses:
            category = expense.category
            if category not in categories:
                categories[category] = 0.0
            
            # Calculate amount in THB
            amount_thb = expense.amount
            if expense.currency == "USD" and self.thb_usd > 0:
                amount_thb = expense.amount * self.thb_usd
            elif expense.currency == self.third_currency and self.third_currency_usd > 0 and self.thb_usd > 0:
                amount_thb = expense.amount * self.third_currency_usd * self.thb_usd
            
            categories[category] += amount_thb
        
        return categories

class ExpenseSettings:
    """Settings for the expense module"""
    def __init__(self, config_path=None):
        """Initialize with settings from config file or defaults"""
        # Default categories if config file is not available
        default_categories = [
            "Fuel", "Hotel", "Meals", "Taxi", "Transport", "Materials", 
            "Tools", "Office", "Communication", "Entertainment", "Other"
        ]
        
        self.categories = default_categories
        
        # Try to load categories from config file
        config_path = config_path or Path("data/expenses/expense_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    self.categories = config_data.get("categories", default_categories)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading expense config: {e}")
        
    @classmethod
    def from_dict(cls, data):
        """Create ExpenseSettings from dictionary"""
        settings = cls()
        settings.categories = data.get("categories", settings.categories)
        return settings
        
    def to_dict(self):
        """Convert ExpenseSettings to dictionary"""
        return {
            "categories": self.categories
        }

class ExpenseDataManager:
    """Handles all data operations for expense module"""
    def __init__(self, data_path=None, settings_path=None, config_path=None):
        self.data_path = data_path or Path("data/expenses/expense_forms.json")
        self.settings_path = settings_path or Path("data/expenses/settings.json")
        self.config_path = config_path or Path("data/expenses/expense_config.json")
        self.ensure_data_file()
        self.ensure_settings_file()
        self.settings = self.load_settings()
    
    def ensure_data_file(self):
        """Create data file if it doesn't exist"""
        os.makedirs(self.data_path.parent, exist_ok=True)
        if not self.data_path.exists():
            with open(self.data_path, 'w', encoding='utf-8') as f:
                json.dump({"forms": []}, f, indent=2, ensure_ascii=False)
    
    def ensure_settings_file(self):
        """Create settings file if it doesn't exist"""
        os.makedirs(self.settings_path.parent, exist_ok=True)
        if not self.settings_path.exists():
            # Create default settings
            settings = ExpenseSettings()
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
    
    def load_settings(self):
        """Load settings from file"""
        try:
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Create settings object with categories from config file
                settings = ExpenseSettings(config_path=self.config_path)
                # Apply any customizations from settings file
                settings.categories = data.get("categories", settings.categories)
                return settings
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading expense settings: {e}")
            return ExpenseSettings(config_path=self.config_path)
    
    def save_settings(self, settings):
        """Save settings to file"""
        with open(self.settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings.to_dict(), f, indent=2, ensure_ascii=False)
        self.settings = settings
    
    def load_all_forms(self):
        """Load all forms from JSON file"""
        try:
            with open(self.data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [ExpenseFormData.from_dict(form) for form in data.get("forms", [])]
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Error loading expense forms: {e}")
            return []
    
    def save_form(self, form_data, username="user"):
        """Save form to JSON file"""
        # Ensure form has an ID
        if not form_data.id:
            # Generate a new ID in the format EXP-Username-YYYY-MM-DD-hhmmss
            now = datetime.datetime.now()
            date_str = now.strftime("%Y-%m-%d-%H%M%S")
            form_data.id = f"EXP-{username}-{date_str}"
        
        # Load existing forms
        forms = self.load_all_forms()
        
        # Update existing form or add new one
        updated = False
        for i, form in enumerate(forms):
            if form.id == form_data.id:
                forms[i] = form_data
                updated = True
                break
                
        if not updated:
            forms.append(form_data)
        
        # Save all forms back to file
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump({"forms": [form.to_dict() for form in forms]}, f, indent=2, ensure_ascii=False)
        
        return form_data.id
    
    def delete_form(self, form_id):
        """Delete a form by ID"""
        forms = self.load_all_forms()
        forms = [form for form in forms if form.id != form_id]
        
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump({"forms": [form.to_dict() for form in forms]}, f, indent=2, ensure_ascii=False)
        
        return True
    
    def get_form_by_id(self, form_id):
        """Get a specific form by ID"""
        forms = self.load_all_forms()
        for form in forms:
            if form.id == form_id:
                return form
        return None
