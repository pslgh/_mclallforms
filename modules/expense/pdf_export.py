from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Image, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
import os
import json
import tempfile
from pathlib import Path
from datetime import datetime

# PySide6 imports for file dialog
from PySide6.QtWidgets import QFileDialog, QWidget, QMessageBox
from PySide6.QtCore import Qt

# Import PDF preview module
from modules.expense.pdf_preview import create_and_preview_pdf

def load_expense_form_by_id(form_id):
    """
    Load expense form data from the JSON file based on the form ID.
    
    Args:
        form_id: The ID of the expense form to load
        
    Returns:
        dict: The expense form data, or None if not found
    """
    try:
        # Get path to expense forms JSON file
        project_root = Path(__file__).resolve().parents[2]
        expense_forms_file = project_root / "data" / "expenses" / "expense_forms.json"
        
        # Check if file exists
        if not expense_forms_file.exists():
            print(f"Expense forms file not found: {expense_forms_file}")
            return None
        
        # Load JSON data
        with open(expense_forms_file, 'r', encoding='utf-8') as f:
            expense_data = json.load(f)
        
        # Find form with matching ID
        for form in expense_data.get('forms', []):
            if form.get('id') == form_id:
                return form
        
        # Form not found
        print(f"Expense form with ID '{form_id}' not found.")
        return None
    
    except Exception as e:
        print(f"Error loading expense form: {e}")
        return None

def generate_expense_form_pdf(form_id_or_data, parent_widget=None):
    """
    Generate a PDF from an expense form, allowing the user to preview and select the save location.
    
    Args:
        form_id_or_data: Either the ID of the expense form or the expense form data object
        parent_widget: Parent widget for the preview dialog (optional)
        
    Returns:
        str: Path to the generated PDF file, or None if the user cancels
    """
    # Determine if we have a form ID or form data
    if isinstance(form_id_or_data, str):
        # We have a form ID, load the data
        form_data = load_expense_form_by_id(form_id_or_data)
        if not form_data:
            if parent_widget:
                QMessageBox.warning(parent_widget, "Form Not Found", 
                                   f"Expense form with ID '{form_id_or_data}' not found.")
            return None
    else:
        # We already have form data object
        form_data = form_id_or_data
        
    # Extract form ID to use as default filename
    form_id = form_data.get('id') if isinstance(form_data, dict) else getattr(form_data, 'id', None)
    if not form_id:
        # Generate a default ID using current timestamp
        issued_by = form_data.get('issued_by') if isinstance(form_data, dict) else getattr(form_data, 'issued_by', 'unknown')
        form_id = f"EXP-{issued_by}-{datetime.now().strftime('%Y-%m-%d-%H%M%S')}"
    
    # Construct default filename
    default_filename = f"{form_id}.pdf"
    
    # Use the preview dialog to show PDF before saving
    try:
        # This will create a temporary PDF, show it in a preview dialog,
        # then let the user save it to their chosen location
        saved_path = create_and_preview_pdf(
            create_pdf_func=create_expense_pdf,
            data=form_data,
            parent_widget=parent_widget,
            suggested_filename=default_filename
        )
        
        if saved_path:
            print(f"PDF saved to: {saved_path}")
            return saved_path
        else:
            print("PDF export cancelled by user")
            return None
            
    except Exception as e:
        print(f"Error in PDF preview/export: {e}")
        if parent_widget:
            QMessageBox.warning(
                parent_widget,
                "PDF Export Error",
                f"Error creating or previewing PDF: {str(e)}"
            )
        return None

def get_value(data, key, default=None):
    """
    Helper function to get value from either a dictionary or an object
    
    Args:
        data: Dictionary or object to extract data from
        key: Key to lookup
        default: Default value if key is not found
        
    Returns:
        Value from the data or default if not found
    """
    if isinstance(data, dict):
        return data.get(key, default)
    else:
        return getattr(data, key, default)

def create_expense_pdf(expense_form, file_path):
    """
    Create the actual PDF file at the specified path.
    
    Args:
        expense_form: The expense form data (dictionary from JSON or object)
        file_path: Path where to save the PDF
    """
    # Create PDF object
    pdf = canvas.Canvas(file_path, pagesize=A4)
    
    # Get page dimensions
    page_width, page_height = A4
    
    # Add logo at top-center
    logo_path = os.path.join("c:\\", "pythonprojects", "_mclallforms", "assets", "logo", "mcllogo.png")
    
    try:
        if os.path.exists(logo_path):
            # Logo dimensions
            logo_width = 2 * inch
            logo_height = 0.8 * inch
            
            # Calculate center position
            logo_x = (page_width - logo_width) / 2
            logo_y = page_height - logo_height - 0.5 * inch
            
            # Draw the logo
            pdf.drawInlineImage(
                logo_path,
                logo_x, 
                logo_y,
                width=logo_width,
                height=logo_height
            )
    except Exception as e:
        print(f"Error adding logo: {e}")
    
    # Add form ID (top-left header)
    form_id = get_value(expense_form, 'id', 'Unknown ID')
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, page_height - 30, f"Form ID: {form_id}")
    
    # Add title
    pdf.setFont("Helvetica-Bold", 16)
    title = "Expense Reimbursement Report"
    title_width = pdf.stringWidth(title, "Helvetica-Bold", 16)
    # Position title closer to logo (0.7 inch instead of 0.9)
    pdf.drawString((page_width - title_width) / 2, page_height - logo_height - 0.7*inch, title)
    
    # Add date and time (top-right header)
    pdf.setFont("Helvetica", 10)
    date_time_text = f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    pdf.drawRightString(page_width - 30, page_height - 30, date_time_text)
    
    # Add project information section with side-by-side boxes
    y_position = page_height - logo_height - 1.1 * inch  # Reduced spacing below title
    
    # Define dimensions for the two boxes
    box_width = (page_width - 60) / 2  # Width of each box
    row_height = 20  # Height of each row
    padding = 15  # Padding at top and bottom of boxes
    left_box_x = 30  # Left margin
    right_box_x = left_box_x + box_width + 15  # Position for right box with 15pt margin
    
    # Set up fonts and styles
    pdf.setStrokeColorRGB(0.7, 0.7, 0.7)  # Light gray for borders
    pdf.setLineWidth(0.5)  # Thin lines
    
    # --- Project Information data preparation ---
    # Get project details from form data
    project_name = get_value(expense_form, 'project_name', "Unknown Project")
    work_location = get_value(expense_form, 'work_location', "Thailand")
    
    # Project details list
    field_data = [
        ("Project Name:", project_name),
        ("Work Location:", work_location),
    ]
    
    # Add Work Country field if abroad
    if work_location == "Abroad":
        work_country = get_value(expense_form, 'work_country', "Unknown")
        field_data.append(("Work Country:", work_country))
        third_currency = get_value(expense_form, 'third_currency', "Unknown")
        field_data.append(("Third Currency:", third_currency))
    
    # Calculate left box height based on content
    left_box_height = (len(field_data) * row_height) + padding + 20  # 20 for title section
    content_x = left_box_x + 10  # Left margin within box
    label_width = 95  # Fixed width for labels
    
    # --- Left Box: Project Information ---
    # Draw the box with calculated height
    pdf.roundRect(left_box_x, y_position - left_box_height, box_width, left_box_height, 8, stroke=1, fill=0)
    
    # Draw the title bar
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(left_box_x + 10, y_position - 15, "Project Information")
    
    # Draw line under title
    pdf.line(left_box_x, y_position - 20, left_box_x + box_width, y_position - 20)
    
    # Starting position for content
    content_y = y_position - 40
    
    # Draw fields
    for label, value in field_data:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(content_x, content_y, label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(content_x + label_width, content_y, str(value))
        content_y -= row_height
    
    # --- Currency Information data preparation ---
    # Get currency details from form data
    fund_thb = get_value(expense_form, 'fund_thb', 0.0)
    receive_date = get_value(expense_form, 'receive_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Format the fund amount with 2 decimal places
    fund_thb_formatted = f"{float(fund_thb):.2f} THB" if fund_thb else "0.00 THB"
    
    # Currency details list
    currency_data = [
        ("Fund Amount (THB):", fund_thb_formatted),
        ("Receive Date:", receive_date),
    ]
    
    # Add exchange rate info if applicable
    if work_location == "Abroad":
        # Get THB to USD rate
        thb_usd_rate = get_value(expense_form, 'thb_usd', 0.0)
        if thb_usd_rate:
            currency_data.append(("THB to USD Rate:", f"{float(thb_usd_rate):.4f}"))
        
        # Get third currency rate info if available 
        third_rate = get_value(expense_form, 'third_currency_usd', 0.0)
        if third_rate:
            currency_data.append(("Third Currency to USD Rate:", f"{float(third_rate):.4f}"))

    # Calculate right box height based on content
    right_box_height = (len(currency_data) * row_height) + padding + 20  # 20 for title section
    
    # Make both boxes the same height - use taller of the two
    box_height = max(left_box_height, right_box_height)
    
    # Redraw left box with adjusted height if needed
    if box_height > left_box_height:
        pdf.roundRect(left_box_x, y_position - box_height, box_width, box_height, 8, stroke=1, fill=0)
    
    # --- Right Box: Fund & Currency Information ---
    # Draw the box with calculated height
    pdf.roundRect(right_box_x, y_position - box_height, box_width, box_height, 8, stroke=1, fill=0)
    
    # Draw the title bar
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(right_box_x + 10, y_position - 15, "Fund & Currency Information")
    
    # Draw line under title
    pdf.line(right_box_x, y_position - 20, right_box_x + box_width, y_position - 20)
    
    # Add fund and currency details
    content_y = y_position - 40  # Reset for right box
    content_x = right_box_x + 10
    label_width = 125  # Wider for currency labels
    
    # Draw fields
    for label, value in currency_data:
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(content_x, content_y, label)
        pdf.setFont("Helvetica", 9)
        pdf.drawString(content_x + label_width, content_y, str(value))
        content_y -= row_height
    
    # --- Expense Detail Table ---
    # Get expenses data from form
    expenses = get_value(expense_form, 'expenses', [])
    
    # Only create table if there are expenses
    if expenses:
        # Position for expense table (below the info boxes)
        table_y = y_position - box_height - 25
        
        # Add section title
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(30, table_y, "Expense Details")
        
        # Define column widths based on content (adjust as needed)
        col_widths = [20, 60, 130, 80, 60, 60, 60, 60]
        
        # Create table header
        table_data = [[
            "#", "Date", "Details", "Vendor", "Category", "Amount", "Currency", "Receipt Type"
        ]]
        
        # Create text wrapping styles for Details and Vendor columns
        styles = getSampleStyleSheet()
        
        # Custom style for wrapped text in tables
        wrapped_style = ParagraphStyle(
            'WrappedText',
            parent=styles['Normal'],
            fontSize=8,
            leading=10,  # Line height
            alignment=0  # 0=left, 1=center, 2=right
        )
        
        # Format and add expense data rows
        for i, expense in enumerate(expenses, start=1):
            # Extract data from expense entry
            date = get_value(expense, 'expense_date', '')
            detail_text = get_value(expense, 'detail', '')
            vendor_text = get_value(expense, 'vendor', '')
            category = get_value(expense, 'category', '')
            amount = get_value(expense, 'amount', 0.0)
            currency = get_value(expense, 'currency', 'THB')
            
            # Convert detail and vendor to Paragraph objects for proper wrapping
            detail = Paragraph(detail_text, wrapped_style)
            vendor = Paragraph(vendor_text, wrapped_style)
            
            # Determine receipt type
            official_receipt = get_value(expense, 'official_receipt', False)
            non_official_receipt = get_value(expense, 'non_official_receipt', False)
            
            if official_receipt:
                receipt_type = "Official"
            elif non_official_receipt:
                receipt_type = "Non-Official"
            else:
                receipt_type = "None"
            
            # Format amount with proper decimal places
            amount_formatted = f"{float(amount):.2f}"
            
            # Add row to table data with row number
            table_data.append([
                str(i), date, detail, vendor, category, amount_formatted, currency, receipt_type
            ])
        
        # Create a simplified table approach
        # First, make sure all rows have the same number of columns
        for row in table_data:
            while len(row) < 8:  # We need 8 columns
                row.append("")  # Add empty cells if needed
        
        # Create the table with explicitly defined column widths
        table = Table(table_data, colWidths=col_widths)
        
        # Apply basic styling
        basic_style = [
            # Header
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            
            # Table grid and alignment
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            
            # Body text
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            
            # Column alignment
            ('ALIGN', (0, 1), (1, -1), 'CENTER'),  # Center # and Date
            ('ALIGN', (2, 1), (2, -1), 'LEFT'),    # Left align Details
            ('ALIGN', (3, 1), (3, -1), 'LEFT'),    # Left align Vendor
            ('ALIGN', (4, 1), (4, -1), 'CENTER'),  # Center Category
            ('ALIGN', (5, 1), (5, -1), 'RIGHT'),   # Right align Amount
            ('ALIGN', (6, 1), (7, -1), 'CENTER'),  # Center Currency and Receipt
            
                # Word wrapping for text columns - force line breaking with custom leading
            ('WORDWRAP', (2, 1), (2, -1), True),   # Details
            ('WORDWRAP', (3, 1), (3, -1), True),   # Vendor
            ('LEFTPADDING', (2, 1), (3, -1), 3),   # Less padding for text columns
            ('RIGHTPADDING', (2, 1), (3, -1), 3),  # Less padding for text columns
            ('LEADING', (2, 1), (3, -1), 8),      # Line spacing for wrapped text
            
            # Alternating row colors
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey.clone(alpha=0.2)])
        ]
        
        table.setStyle(TableStyle(basic_style))
        
        # Position and draw the table with fixed height calculation
        table_width = sum(col_widths)
        table_x = (page_width - table_width) / 2
        
        # Let Paragraph objects automatically handle row heights
        
        # Get table dimensions from ReportLab with proper wrapping considered
        w, h = table.wrapOn(pdf, page_width - 80, page_height)
        
        # Draw the table at a fixed position
        table.drawOn(pdf, table_x, table_y - h - 10)
        
        # Add summary section - position it right below the table with proper spacing
        summary_y = table_y - 20 - h - 20  # Position below table
        
        # Calculate totals by currency
        currency_totals = {}
        for expense in expenses:
            amount = float(get_value(expense, 'amount', 0.0))
            currency = get_value(expense, 'currency', 'THB')
            
            if currency not in currency_totals:
                currency_totals[currency] = 0
            
            currency_totals[currency] += amount
        
        # Add summary title
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(30, summary_y - 20, "Summary:")
        
        # Display totals by currency
        pdf.setFont("Helvetica", 9)
        summary_x = 100
        currency_y = summary_y - 20
        for currency, total in currency_totals.items():
            pdf.drawString(summary_x, currency_y, f"Total {currency}: {total:.2f}")
            summary_x += 120  # Space between currency totals
            
        # Add horizontal line
        pdf.setLineWidth(0.5)
        pdf.line(30, currency_y - 15, page_width - 30, currency_y - 15)
        
        # Get total expense and remaining funds from form data
        total_expense_thb = get_value(expense_form, 'total_expense_thb', 0.0)
        remaining_funds_thb = get_value(expense_form, 'remaining_funds_thb', 0.0)
        
        # Display total expense and remaining funds
        total_y = currency_y - 30
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(30, total_y, "Total Expense:")
        pdf.drawString(150, total_y, f"{float(total_expense_thb):.2f} THB")
        
        # Display remaining funds
        remaining_y = total_y - 15
        pdf.drawString(30, remaining_y, "Remaining Funds:")
        pdf.drawString(150, remaining_y, f"{float(remaining_funds_thb):.2f} THB")
        
        # Add signature section right after total and remaining funds
        signature_y = remaining_y - 100  # Position below remaining funds
        
        # Draw signature lines
        line_width = 150
        
        pdf.setFont("Helvetica", 9)
        
        # Requester signature
        pdf.line(100, signature_y, 100 + line_width, signature_y)
        pdf.drawString(100, signature_y - 15, "Issuer")
        issued_by = get_value(expense_form, 'issued_by', "")
        if issued_by:
            pdf.drawString(100, signature_y - 30, f"({issued_by})")
        
        # Approver signature
        pdf.line(page_width - 100 - line_width, signature_y, page_width - 100, signature_y)
        pdf.drawString(page_width - 100 - line_width, signature_y - 15, "Approved By")
    else:
        # If there are no expenses, still add signature section
        signature_y = table_y - 100
        
        # Draw signature lines
        line_width = 150
        
        pdf.setFont("Helvetica", 9)
        
        # Requester signature
        pdf.line(100, signature_y, 100 + line_width, signature_y)
        pdf.drawString(100, signature_y - 15, "Issuer")
        issued_by = get_value(expense_form, 'issued_by', "")
        if issued_by:
            pdf.drawString(100, signature_y - 30, f"({issued_by})")
        
        # Approver signature
        pdf.line(page_width - 100 - line_width, signature_y, page_width - 100, signature_y)
        pdf.drawString(page_width - 100 - line_width, signature_y - 15, "Approved By")
    
    # Save the PDF
    pdf.save()
    
    print(f"PDF saved to: {file_path}")