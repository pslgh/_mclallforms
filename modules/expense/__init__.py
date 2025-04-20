"""
Expense Module for MCL All Forms
This module provides expense reimbursement functionality.
"""

from modules.expense.expense_reimbursement_widget import ExpenseReimbursementWidget

# For backward compatibility
from modules.expense.models.expense_data import ExpenseFormData, ExpenseDataManager

__all__ = [
    'ExpenseReimbursementWidget',
    'ExpenseFormData',
    'ExpenseDataManager'
]
