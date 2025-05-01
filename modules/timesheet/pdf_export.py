"""
PDF Export module for Timesheet Service and Charge Summary.
Provides functions to generate PDF from timesheet data.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
import os
import json
from pathlib import Path
from datetime import datetime

# PySide6 imports for file dialog
from PySide6.QtWidgets import QMessageBox

# Import PDF preview module
from modules.timesheet.pdf_preview import create_and_preview_pdf

def load_timesheet_by_id(entry_id):
    """
    Load timesheet data from the JSON file based on the entry ID.
    
    Args:
        entry_id: The ID of the timesheet to load
        
    Returns:
        dict: The timesheet data, or None if not found
    """
    try:
        # Get path to timesheet entries JSON file
        project_root = Path(__file__).resolve().parents[2]
        timesheet_file = project_root / "data" / "timesheet" / "timesheet_entries.json"
        
        # Check if file exists
        if not timesheet_file.exists():
            print(f"Timesheet entries file not found: {timesheet_file}")
            return None
        
        # Load JSON data
        with open(timesheet_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Find entry with matching ID
        for entry in data.get('entries', []):
            if entry.get('entry_id') == entry_id:
                return entry
        
        # Entry not found
        print(f"Timesheet entry with ID '{entry_id}' not found.")
        return None
    
    except Exception as e:
        print(f"Error loading timesheet: {e}")
        return None

def generate_timesheet_pdf(entry_id_or_data, parent_widget=None):
    """
    Generate a PDF from a timesheet entry, allowing the user to preview and select the save location.
    
    Args:
        entry_id_or_data: Either the ID of the timesheet or the timesheet data object
        parent_widget: Parent widget for the preview dialog (optional)
        
    Returns:
        str: Path to the generated PDF file, or None if the user cancels
    """
    # Determine if we got an ID or data object
    timesheet_data = None
    
    if isinstance(entry_id_or_data, str):
        # It's an ID, load the data
        timesheet_data = load_timesheet_by_id(entry_id_or_data)
    else:
        # It's already a data object
        timesheet_data = entry_id_or_data
    
    if not timesheet_data:
        if parent_widget:
            QMessageBox.warning(
                parent_widget,
                "Data Error",
                "Could not load timesheet data."
            )
        return None
    
    # Prepare suggested filename based on data
    suggested_filename = f"Timesheet_{get_value(timesheet_data, 'entry_id', 'unknown')}.pdf"
    
    # Use the preview module to create and preview the PDF
    return create_and_preview_pdf(
        create_timesheet_pdf,  # The function that creates the PDF
        timesheet_data,        # The data to pass to the function
        parent_widget,         # Parent widget for the dialog
        suggested_filename     # Suggested filename
    )

def get_value(data, key, default=None, fallback_keys=None):
    """
    Enhanced helper function to get value from either a dictionary or an object
    with support for fallback keys and nested data
    
    Args:
        data: Dictionary or object to extract data from
        key: Primary key to lookup
        default: Default value if key is not found
        fallback_keys: List of alternative keys to try if primary key is not found
        
    Returns:
        Value from the data or default if not found
    """
    # Try to get the value directly
    value = None
    
    # If data is a dictionary
    if isinstance(data, dict):
        # Try direct key
        value = data.get(key)
        
        # If value not found and data has _raw_data attribute (for TimesheetEntry objects)
        if value is None and '_raw_data' in data and isinstance(data['_raw_data'], dict):
            value = data['_raw_data'].get(key)
    
    # If data is an object
    else:
        # Try direct attribute
        value = getattr(data, key, None)
        
        # If value not found and object has _raw_data attribute
        if value is None and hasattr(data, '_raw_data') and isinstance(data._raw_data, dict):
            value = data._raw_data.get(key)
    
    # If value is still None and fallback_keys provided, try them
    if value is None and fallback_keys:
        for fallback_key in fallback_keys:
            # Try with dictionary
            if isinstance(data, dict):
                value = data.get(fallback_key)
                if value is not None:
                    break
                    
                # Try in _raw_data if present
                if '_raw_data' in data and isinstance(data['_raw_data'], dict):
                    value = data['_raw_data'].get(fallback_key)
                    if value is not None:
                        break
            
            # Try with object
            else:
                value = getattr(data, fallback_key, None)
                if value is not None:
                    break
                    
                # Try in _raw_data if present
                if hasattr(data, '_raw_data') and isinstance(data._raw_data, dict):
                    value = data._raw_data.get(fallback_key)
                    if value is not None:
                        break
    
    # Return the value or default
    return value if value is not None else default

def create_timesheet_pdf(timesheet_data, file_path):
    """Create a PDF file from timesheet data
    
    Args:
        timesheet_data: The timesheet data (dictionary from JSON or object)
        file_path: Path where to save the PDF
    """
    # Try to use the two-pass approach if PyPDF2 is available
    try:
        # Check if PyPDF2 is available without importing it yet
        import importlib.util
        has_pypdf2 = importlib.util.find_spec("PyPDF2") is not None
        
        if has_pypdf2:
            # Two-pass approach: First pass determines actual page count, second pass creates the final PDF
            import tempfile
            import os
            from PyPDF2 import PdfReader
            
            # Function to count how many pages are actually generated during PDF creation
            def count_pages_in_pdf():
                # Create a temporary PDF in memory to count pages
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
                temp_file.close()
                
                try:
                    # Generate the PDF exactly as we would in the main function, but with a dummy page count
                    generate_pdf_content(timesheet_data, temp_file.name, total_pages=999)
                    
                    # Count the actual pages in the generated PDF
                    pdf_reader = PdfReader(temp_file.name)
                    actual_pages = len(pdf_reader.pages)
                    return actual_pages
                finally:
                    # Always clean up the temporary file
                    try:
                        os.unlink(temp_file.name)
                    except:
                        pass
            
            # Call the counting function to get the actual page count
            total_pages = count_pages_in_pdf()
            print(f"PyPDF2 is working: Using two-pass approach for exact page count")
            print(f"Actual total pages determined: {total_pages}")
            
            # Now generate the final PDF with the correct page count
            generate_pdf_content(timesheet_data, file_path, total_pages)
            return
    except Exception as e:
        print(f"Two-pass PDF generation not available: {str(e)}")
    
    # Fallback to the original approach if PyPDF2 is not available or if an error occurred
    print("Using fallback single-pass PDF generation approach")
    
    # Calculate page count using a simple formula
    time_entries = get_value(timesheet_data, 'time_entries', [])
    tool_usage = get_value(timesheet_data, 'tool_usage', [])
    
    # Start with 2 as base (1 for project info, 1 for rates and calculation)
    base_pages = 2
    
    # Estimate Time Entries pages
    time_entries_per_page = 30
    time_entry_pages = max(1, (len(time_entries) + 1) // time_entries_per_page) if time_entries else 0
    
    # Estimate Tool Usage pages
    tool_entries_per_page = 30
    tool_usage_pages = max(1, (len(tool_usage) + 1) // tool_entries_per_page) if tool_usage else 0
    
    # Final calculation - add 1 for signature page
    total_pages = base_pages + time_entry_pages + tool_usage_pages + 1
    
    print(f"Estimated total pages: {total_pages}")
    
    # Generate PDF with the estimated page count
    generate_pdf_content(timesheet_data, file_path, total_pages)


def generate_pdf_content(timesheet_data, file_path, total_pages):
    """Generate the PDF content with the correct page count
    
    Args:
        timesheet_data: The timesheet data (dictionary from JSON or object)
        file_path: Path where to save the PDF
        total_pages: Total number of pages that will be in the PDF
    """
    # Get the time entries and tool usage for calculations
    time_entries = get_value(timesheet_data, 'time_entries', [])
    tool_usage = get_value(timesheet_data, 'tool_usage', [])
    
    # Create PDF object
    pdf = canvas.Canvas(file_path, pagesize=A4)
    
    # Get page dimensions
    page_width, page_height = A4
    
    # Add page number to first page immediately
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(page_width - 0.75 * inch, page_height - 0.75 * inch, f"Page 1 of {total_pages}")
    
    # Define margin and usable area
    margin = 0.75 * inch
    content_width = page_width - 2 * margin
    
    # Initialize page counting - will be calculated dynamically
    current_page = 1
    
    # Get currency for formatting - defined at the top to be available to all nested functions
    currency = get_value(timesheet_data, 'currency', 'THB')
    
    # Get project base directory for assets
    project_root = Path(__file__).resolve().parents[2] 
    logo_path = os.path.join(project_root, "assets", "logo", "mcllogo.png")
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=14,
        alignment=1,  # Center alignment
        spaceAfter=12
    )
    heading_style = ParagraphStyle(
        'Heading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        spaceAfter=6
    )
    normal_style = styles['Normal']
    label_style = ParagraphStyle(
        'Label',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=9
    )
    value_style = ParagraphStyle(
        'Value',
        parent=styles['Normal'],
        fontSize=9
    )
    
    # Current Y position (start at top of page minus margin)
    y = page_height - margin
    
    # Add logo
    try:
        if os.path.exists(logo_path):
            # Logo dimensions
            logo_width = 2 * inch
            logo_height = 0.8 * inch
            
            # Calculate center position
            logo_x = (page_width - logo_width) / 2
            logo_y = y - logo_height
            
            # Draw the logo
            pdf.drawInlineImage(
                logo_path,
                logo_x, 
                logo_y,
                width=logo_width,
                height=logo_height
            )
            
            # Update Y position
            y = logo_y - 12
    except Exception as e:
        print(f"Error adding logo: {e}")
    
    # Set default text color to black for all content
    pdf.setFillColor(colors.black)
    
    # Add title
    title_text = "SERVICE TIMESHEET AND CHARGE SUMMARY"
    pdf.setFont("Helvetica-Bold", 16)
    title_width = pdf.stringWidth(title_text, "Helvetica-Bold", 16)
    pdf.drawString((page_width - title_width) / 2, y - 20, title_text)
    
    # Update Y position
    y -= 30
    
    # Draw a line below the title
    pdf.setStrokeColor(colors.black)
    pdf.line(margin, y - 5, page_width - margin, y - 5)
    
    # Update Y position
    y -= 25
    
    # Add timesheet info - entry ID and date
    entry_id = get_value(timesheet_data, 'entry_id', 'Unknown')
    creation_date = get_value(timesheet_data, 'creation_date', datetime.now().strftime('%Y-%m-%d'))
    
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, y, f"Report ID: {entry_id}")
    pdf.drawRightString(page_width - margin, y, f"Date: {creation_date}")
    
    # Add page number (top-right)
    # pdf.drawRightString(page_width - margin, page_height - margin, "Page 1 of 1")
    
    # Update Y position
    y -= 25
    
    # Draw Project Information section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "Project Information")
    
    # Draw a horizontal line under the section title
    pdf.line(margin, y - 5, page_width - margin, y - 5)
    
    # Update Y position
    y -= 25
    
    # For project name and description, try multiple possible field names
    # Project name with fallbacks using the enhanced get_value function
    fallback_keys_for_name = ['Project Name', 'ProjectName', 'Name', 'project']
    project_name = get_value(timesheet_data, 'project_name', 'N/A', fallback_keys=fallback_keys_for_name)
    
    # Project description with fallbacks using the enhanced get_value function
    fallback_keys_for_desc = ['Project Description', 'ProjectDescription', 'Description', 'description']
    project_desc = get_value(timesheet_data, 'project_description', 'N/A', fallback_keys=fallback_keys_for_desc)
        
    # Get address with proper line handling for wrapping
    address = get_value(timesheet_data, 'client_address', 'N/A')
    
    # Create text style for wrapping paragraphs
    normal_style = ParagraphStyle(
        'normal',
        fontName='Helvetica',
        fontSize=9,
        leading=11  # Line spacing
    )
    
    # Handle project name and description for wrapping
    project_name_para = Paragraph(project_name, normal_style)
    project_desc_para = Paragraph(project_desc, normal_style)
    
    # Prepare service engineer name
    service_engineer = f"{get_value(timesheet_data, 'service_engineer_name', '')} {get_value(timesheet_data, 'service_engineer_surname', '')}".strip() or 'N/A'
    
    # Project Info Table Data
    project_data = [
        # Headers and values
        ["Purchasing Order #:", get_value(timesheet_data, 'purchasing_order_number', 'N/A')],
        ["Quotation #:", get_value(timesheet_data, 'quotation_number', 'N/A')],
        ["Contract Agreement?:", "Yes" if get_value(timesheet_data, 'under_contract_agreement', False) else "No"],
        ["Emergency Request?:", "Yes" if get_value(timesheet_data, 'emergency_request', False) else "No"],
        ["Client:", get_value(timesheet_data, 'client_company_name', 'N/A')],
        ["Address:", Paragraph(address, normal_style)],        
        ["Client Representative:", get_value(timesheet_data, 'client_representative_name', 'N/A')],
        ["Email:", get_value(timesheet_data, 'client_representative_email', 'N/A')],
        ["Phone Number:", get_value(timesheet_data, 'client_representative_phone', 'N/A')],
        ["Project Name:", project_name_para],
        ["Project Description:", project_desc_para],
        ["Work Type:", get_value(timesheet_data, 'work_type', 'N/A')],
        ["Service Engineer:", service_engineer],
    ]
    
    # Create and style the table with special handling for project name and description
    col_widths = [1.5*inch, content_width - 1.5*inch]
    table = Table(project_data, colWidths=col_widths)
    
    # Basic table style
    table_style = [
        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),  # Right-align labels
        ('ALIGN', (1, 0), (1, -1), 'LEFT'),   # Left-align values
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),  # Bold labels
        ('FONTSIZE', (0, 0), (-1, -1), 9),    # Font size
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),  # Padding
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('VALIGN', (0, 0), (0, -1), 'TOP'),   # Top-align labels
        ('VALIGN', (1, 0), (1, -1), 'TOP'),   # Top-align values
    ]
    
    # Find index of project name, description, and address rows
    project_name_index = -1
    project_desc_index = -1
    address_index = -1
    for i, row in enumerate(project_data):
        if row[0] == "Project Name:":
            project_name_index = i
        elif row[0] == "Project Description:":
            project_desc_index = i
        elif row[0] == "Address:":
            address_index = i
    
    # Add special styling for project name, description, and address
    if project_name_index >= 0:
        # Add more padding for project name to accommodate multiple lines
        table_style.append(('BOTTOMPADDING', (1, project_name_index), (1, project_name_index), 6))
        table_style.append(('TOPPADDING', (1, project_name_index), (1, project_name_index), 6))
    
    if project_desc_index >= 0:
        # Add even more padding for project description to accommodate multiple lines
        table_style.append(('BOTTOMPADDING', (1, project_desc_index), (1, project_desc_index), 10))
        table_style.append(('TOPPADDING', (1, project_desc_index), (1, project_desc_index), 10))
    
    if address_index >= 0:
        # Add padding for address to accommodate multiple lines
        table_style.append(('BOTTOMPADDING', (1, address_index), (1, address_index), 8))
        table_style.append(('TOPPADDING', (1, address_index), (1, address_index), 8))
        # No special background - keeping consistent with other fields
    
    # Apply the styles
    table.setStyle(TableStyle(table_style))
    
    # Draw the table
    table_width, table_height = table.wrap(content_width, 500)  # 500 is arbitrary max height
    table.drawOn(pdf, margin, y - table_height)
    
    # Update Y position
    y -= table_height + 20
    
    # Check if we have space for the Time Entries section heading (at least 1 inch from bottom margin)
    min_space_needed = margin + 1 * inch
    
    # If less than 1 inch space remains, start a new page
    if y < min_space_needed:
        current_page += 1
        y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    # Draw Time Entries section
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "Time Entries")
    
    # Draw a horizontal line under the section title
    pdf.line(margin, y - 5, page_width - margin, y - 5)
    
    # Update Y position
    y -= 25
    
    # Time Entries Table Header
    time_header = ['Date', 'Start', 'End', 'Rest', 'Hours', 'OT Rate', 'Description']
    
    # Time Entries Table Data
    time_data = [time_header]
    
    # Extract time entries
    time_entries = get_value(timesheet_data, 'time_entries', [])
    for entry in time_entries:
        # Calculate equivalent hours if not provided
        equivalent_hours = get_value(entry, 'equivalent_hours', None)
        if equivalent_hours is None:
            # Try to calculate from times
            start_time = get_value(entry, 'start_time', '')
            end_time = get_value(entry, 'end_time', '')
            rest_hours = float(get_value(entry, 'rest_hours', 0))
            
            try:
                if start_time and end_time and len(start_time) >= 4 and len(end_time) >= 4:
                    start_hour = int(start_time[:2])
                    start_min = int(start_time[2:4]) if len(start_time) >= 4 else 0
                    end_hour = int(end_time[:2])
                    end_min = int(end_time[2:4]) if len(end_time) >= 4 else 0
                    
                    start_decimal = start_hour + start_min/60
                    end_decimal = end_hour + end_min/60
                    
                    hours = end_decimal - start_decimal - rest_hours
                    equivalent_hours = max(0, hours)
                else:
                    equivalent_hours = 0
            except:
                equivalent_hours = 0
        
        time_data.append([
            get_value(entry, 'date', 'N/A'),
            get_value(entry, 'start_time', 'N/A'),
            get_value(entry, 'end_time', 'N/A'),
            str(get_value(entry, 'rest_hours', 0)),
            str(equivalent_hours),
            get_value(entry, 'overtime_rate', '1'),
            get_value(entry, 'description', '')
        ])
    
    # Add a row if no entries
    if len(time_data) == 1:
        time_data.append(['No time entries', '', '', '', '', '', ''])
    
    # Create and style the time entries table
    col_widths = [0.8*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, 0.5*inch, content_width - 3.3*inch]
    time_table = Table(time_data, colWidths=col_widths)
    time_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center-align header
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
        ('FONTSIZE', (0, 0), (-1, -1), 8),    # Font size
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Table grid
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top vertical alignment for all cells
        ('ALIGN', (0, 1), (5, -1), 'CENTER'),  # Center-align data cells except description
        ('ALIGN', (6, 1), (6, -1), 'LEFT'),   # Left-align description
    ]))
    
    # Calculate available space on current page
    available_space = y - margin - 20  # Leave some bottom margin
    
    # Check if the table fits on the current page
    time_table_width, time_table_height = time_table.wrap(content_width, available_space)
    
    # If table doesn't fit, we need to split it across pages
    if time_table_height > available_space and len(time_data) > 2:  # More than header + one row
        # Calculate how many rows we can fit on this page
        # Approximate height per row: table height / number of rows
        row_height = time_table_height / len(time_data)
        rows_per_page = max(2, int(available_space / row_height))  # At least header + 1 row
        
        # Process all rows across multiple pages as needed
        start_row = 0
        while start_row < len(time_data):
            # Determine end row for this page
            end_row = min(start_row + rows_per_page, len(time_data))
            
            # Create a subtable for just these rows
            # Always include the header row (row 0)
            if start_row == 0:
                # First page includes header
                current_data = time_data[0:end_row]
            else:
                # Continuation pages include header + rows for this page
                current_data = [time_data[0]] + time_data[start_row:end_row]
            
            # Create and style the table for this page
            current_table = Table(current_data, colWidths=col_widths)
            current_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center-align header
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
                ('FONTSIZE', (0, 0), (-1, -1), 8),    # Font size
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Table grid
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top vertical alignment for all cells
                ('ALIGN', (0, 1), (5, -1), 'CENTER'),  # Center-align data cells except description
                ('ALIGN', (6, 1), (6, -1), 'LEFT'),   # Left-align description
            ]))
            
            # Calculate height of current table
            current_width, current_height = current_table.wrap(content_width, available_space)
            
            # Draw the table
            current_table.drawOn(pdf, margin, y - current_height)
            
            # Update for next page if needed
            if end_row < len(time_data):
                # Start a new page
                current_page += 1
                y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
                available_space = y - margin - 20
                
                # On continuation pages, we might fit more rows since we have a full page
                rows_per_page = max(2, int((y - margin - 20) / row_height))
            
            # Move to next set of rows
            start_row = end_row
            
        # Update Y position after all tables are drawn
        if end_row == len(time_data):
            y -= current_height + 20
    else:
        # Table fits on current page, draw it normally
        time_table.drawOn(pdf, margin, y - time_table_height)
        y -= time_table_height + 20
    
    # Draw Time Summary
    time_summary = get_value(timesheet_data, 'time_summary', {})
    if time_summary:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin, y, "Time Summary")
        
        # Create summary text
        summary_text = f"Regular Hours: {get_value(time_summary, 'total_regular_hours', 0):.1f}   "
        summary_text += f"OT 1.5X Hours: {get_value(time_summary, 'total_ot_1_5x_hours', 0):.1f}   "
        summary_text += f"OT 2.0X Hours: {get_value(time_summary, 'total_ot_2_0x_hours', 0):.1f}   "
        summary_text += f"Total Equivalent Hours: {get_value(time_summary, 'total_equivalent_hours', 0):.1f}"
        
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin + 20, y - 15, summary_text)
        
        # Update Y position
        y -= 35
    
    # Add Tool Usage section if available
    tool_usage = get_value(timesheet_data, 'tool_usage', [])
    if tool_usage:
        # Check if we have space for the Tools section heading (at least 1 inch from bottom margin)
        min_space_needed = margin + 1 * inch
        
        # If less than 1 inch space remains, start a new page
        if y < min_space_needed:
            current_page += 1
            y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
            
        # Draw Tools Used section
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, y, "Tools Used")
        
        # Draw a horizontal line under the section title
        pdf.line(margin, y - 5, page_width - margin, y - 5)
        
        # Update Y position
        y -= 25
        
        # Tools Table Header
        tools_header = ['Tool Name', 'Amount', 'Start Date', 'End Date', 'Total Days']
        
        # Tools Table Data
        tools_data = [tools_header]
        
        for tool in tool_usage:
            tools_data.append([
                get_value(tool, 'tool_name', 'N/A'),
                str(get_value(tool, 'amount', 1)),
                get_value(tool, 'start_date', 'N/A'),
                get_value(tool, 'end_date', 'N/A'),
                str(get_value(tool, 'total_days', 0))
            ])
        
        # Create and style the tools table
        col_widths = [2*inch, 0.7*inch, 1*inch, 1*inch, 0.8*inch]
        tools_table = Table(tools_data, colWidths=col_widths)
        tools_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center-align header
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
            ('FONTSIZE', (0, 0), (-1, -1), 8),    # Font size
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Table grid
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top vertical alignment for all cells
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left-align tool names
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center-align other data
        ]))
        
        # Calculate available space on current page
        available_space = y - margin - 20  # Leave some bottom margin
        
        # Check if the table fits on the current page
        tools_table_width, tools_table_height = tools_table.wrap(content_width, available_space)
        
        # If table doesn't fit, we need to split it across pages
        if tools_table_height > available_space and len(tools_data) > 2:  # More than header + one row
            # Calculate how many rows we can fit on this page
            # Approximate height per row: table height / number of rows
            row_height = tools_table_height / len(tools_data)
            rows_per_page = max(2, int(available_space / row_height))  # At least header + 1 row
            
            # Process all rows across multiple pages as needed
            start_row = 0
            while start_row < len(tools_data):
                # Determine end row for this page
                end_row = min(start_row + rows_per_page, len(tools_data))
                
                # Create a subtable for just these rows
                # Always include the header row (row 0)
                if start_row == 0:
                    # First page includes header
                    current_data = tools_data[0:end_row]
                else:
                    # Continuation pages include header + rows for this page
                    current_data = [tools_data[0]] + tools_data[start_row:end_row]
                
                # Create and style the table for this page
                current_table = Table(current_data, colWidths=col_widths)
                current_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # Center-align header
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
                    ('FONTSIZE', (0, 0), (-1, -1), 8),    # Font size
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Table grid
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),  # Top vertical alignment for all cells
                    ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left-align tool names
                    ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center-align other data
                ]))
                
                # Calculate height of current table
                current_width, current_height = current_table.wrap(content_width, available_space)
                
                # Draw the table
                current_table.drawOn(pdf, margin, y - current_height)
                
                # Update for next page if needed
                if end_row < len(tools_data):
                    # Start a new page
                    current_page += 1
                    y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
                    available_space = y - margin - 20
                    
                    # On continuation pages, we might fit more rows since we have a full page
                    rows_per_page = max(2, int((y - margin - 20) / row_height))
                
                # Move to next set of rows
                start_row = end_row
                
            # Update Y position after all tables are drawn
            if end_row == len(tools_data):
                y -= current_height + 20
        else:
            # Table fits on current page, draw it normally
            tools_table.drawOn(pdf, margin, y - tools_table_height)
            y -= tools_table_height + 20
        
        # Add tool usage summary if available
        tool_summary = get_value(timesheet_data, 'tool_usage_summary', None)
        if tool_summary:
            total_days = get_value(tool_summary, 'total_tool_usage_days', 0)
            tools_used = get_value(tool_summary, 'tools_used', '')
            
            if total_days > 0 or tools_used:
                pdf.setFont("Helvetica", 9)
                
                summary_text = ""
                if tools_used:
                    summary_text += f"Tools Used: {tools_used} |"
                
                if total_days > 0:
                    summary_text += f"   Total Days: {total_days}"
                
                pdf.drawString(margin + 20, y - 5, summary_text)
                y -= 20
    
    # Add Service Rates and Time Summary section
    # Always force a page break here to show rates and calculation details on a new page
    # This ensures the content isn't cut off and is properly displayed
    current_page += 1
    y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    # Create three-column layout for rates, time summary, and tool usage summary
    rates_time_y = y
    col_width = (content_width - 1*inch) / 3  # Three equal columns with 0.5 inch between each
    
    # ------ LEFT COLUMN: Service Rates ------
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, rates_time_y, "Service Rates")
    
    # Draw a horizontal line under the section title
    pdf.line(margin, rates_time_y - 5, margin + col_width, rates_time_y - 5)
    
    rates_time_y -= 25
    
    # Draw service rates
    pdf.setFont("Helvetica-Bold", 9)
    
    # Create a helper function to add rate items
    def add_rate_item(label, value, y_pos):
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(margin + 5, y_pos, f"{label}:")
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin + 1.5*inch, y_pos, f"{currency} {value:,.2f}")
        return y_pos - 15  # Return new Y position
    
    current_y = rates_time_y
    
    # Add service rates
    current_y = add_rate_item("Service Hour Rate", get_value(timesheet_data, 'service_hour_rate', 0), current_y)
    current_y = add_rate_item("Tool Usage Rate", get_value(timesheet_data, 'tool_usage_rate', 0), current_y)
    current_y = add_rate_item("T&L Rate (<80km)", get_value(timesheet_data, 'tl_rate_short', 0), current_y)
    current_y = add_rate_item("T&L Rate (>80km)", get_value(timesheet_data, 'tl_rate_long', 0), current_y)
    current_y = add_rate_item("Offshore Day Rate", get_value(timesheet_data, 'offshore_day_rate', 0), current_y)
    current_y = add_rate_item("Emergency Rate", get_value(timesheet_data, 'emergency_rate', 0), current_y)
    
    # ------ MIDDLE COLUMN: Time Summary ------
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin + col_width + 0.5*inch, rates_time_y + 25, "Time Summary")
    
    # Draw a horizontal line under the section title
    pdf.line(margin + col_width + 0.5*inch, rates_time_y + 20, 
             margin + 2*col_width + 0.5*inch, rates_time_y + 20)
             
    # ------ RIGHT COLUMN: Tool Usage Summary ------
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin + 2*col_width + 1*inch, rates_time_y + 25, "Tool Usage Summary")
    
    # Draw a horizontal line under the section title
    pdf.line(margin + 2*col_width + 1*inch, rates_time_y + 20, 
             page_width - margin, rates_time_y + 20)
    
    # Helper function to add time summary items
    def add_summary_item(label, value, is_bold, y_pos):
        x_start = margin + col_width + 0.5*inch + 5
        if is_bold:
            pdf.setFont("Helvetica-Bold", 9)
        else:
            pdf.setFont("Helvetica", 9)
            
        pdf.drawString(x_start, y_pos, f"{label}:")
        
        if is_bold:
            pdf.setFont("Helvetica-Bold", 9)
        else:
            pdf.setFont("Helvetica", 9)
        
        pdf.drawString(x_start + 1.5*inch, y_pos, f"{value:.1f}" if isinstance(value, (int, float)) else value)
        return y_pos - 15  # Return new Y position
        
    # Helper function to add tool usage summary items
    def add_tool_summary_item(label, value, is_bold, y_pos):
        x_start = margin + 2*col_width + 1*inch + 5
        if is_bold:
            pdf.setFont("Helvetica-Bold", 9)
        else:
            pdf.setFont("Helvetica", 9)
            
        pdf.drawString(x_start, y_pos, f"{label}:")
        
        if is_bold:
            pdf.setFont("Helvetica-Bold", 9)
        else:
            pdf.setFont("Helvetica", 9)
        
        # If value is a string (tools list), we may need to wrap it
        if isinstance(value, str):
            pdf.drawString(x_start + 0.1*inch, y_pos, value)
        else:
            pdf.drawString(x_start + 1.5*inch, y_pos, f"{value}" if isinstance(value, int) else f"{value:.1f}")
        
        return y_pos - 15  # Return new Y position
    
    # Get time summary data
    time_summary = get_value(timesheet_data, 'time_summary', {})
    
    summary_y = rates_time_y
    
    if time_summary:
        # Regular hours
        reg_hours = get_value(time_summary, 'total_regular_hours', 0)
        summary_y = add_summary_item("Regular Hours", reg_hours, False, summary_y)
        
        # OT hours 1.5x
        ot_15x_hours = get_value(time_summary, 'total_ot_1_5x_hours', 0)
        summary_y = add_summary_item("OT 1.5X Hours", ot_15x_hours, False, summary_y)
        
        # OT hours 2.0x
        ot_2x_hours = get_value(time_summary, 'total_ot_2_0x_hours', 0)
        summary_y = add_summary_item("OT 2.0X Hours", ot_2x_hours, False, summary_y)
        
        # Total equivalent hours
        equiv_hours = get_value(time_summary, 'total_equivalent_hours', 0)
        summary_y = add_summary_item("Total Hours", equiv_hours, True, summary_y)
        
        # Travel days
        tl_short = get_value(time_summary, 'total_tl_short_days', 0)
        if tl_short > 0:
            summary_y = add_summary_item("T&L (<80km) Days", tl_short, False, summary_y)
        
        tl_long = get_value(time_summary, 'total_tl_long_days', 0)
        if tl_long > 0:
            summary_y = add_summary_item("T&L (>80km) Days", tl_long, False, summary_y)
        
        # Offshore days
        offshore_days = get_value(time_summary, 'total_offshore_days', 0)
        if offshore_days > 0:
            summary_y = add_summary_item("Offshore Days", offshore_days, False, summary_y)
    else:
        # No time summary available
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin + col_width + 0.5*inch + 5, summary_y, "No time summary available")
        
    # Get tool usage summary data
    tool_summary_y = rates_time_y
    tool_usage_summary = get_value(timesheet_data, 'tool_usage_summary', {})
    
    if tool_usage_summary:
        # Get the tools used string
        tools_used = get_value(tool_usage_summary, 'tools_used', "None")
        
        # Format the tools list for display
        if tools_used and tools_used.lower() != "none":
            # Display Tools Used header
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(margin + 2*col_width + 1*inch + 5, tool_summary_y, "Tools Used:")
            tool_summary_y -= 15
            
            # Display the tool list with proper wrapping for better readability
            # Split the tool list by commas to get individual tool entries
            tool_entries = tools_used.split(", ")
            
            # Set indent for tool entries
            x_start = margin + 2*col_width + 1*inch + 15
            pdf.setFont("Helvetica", 9)
            
            # Draw each tool on a separate line
            for tool in tool_entries:
                pdf.drawString(x_start, tool_summary_y, f"• {tool}")
                tool_summary_y -= 15
                
            # Add some extra space after the tool list
            tool_summary_y -= 5
        else:
            # Display Tools Used header with None value
            pdf.setFont("Helvetica-Bold", 9)
            pdf.drawString(margin + 2*col_width + 1*inch + 5, tool_summary_y, "Tools Used:")
            tool_summary_y -= 15
            
            # Display None value with indent
            x_start = margin + 2*col_width + 1*inch + 15
            pdf.setFont("Helvetica", 9)
            pdf.drawString(x_start, tool_summary_y, "None")
            tool_summary_y -= 15
        
        # Total Tool Usage Days
        total_days = get_value(tool_usage_summary, 'total_tool_usage_days', 0)
        tool_summary_y = add_tool_summary_item("Total Usage Days", total_days, True, tool_summary_y)
    else:
        # No tool usage summary available
        pdf.setFont("Helvetica", 9)
        pdf.drawString(margin + 2*col_width + 1*inch + 5, tool_summary_y, "No tool usage data available")
    
    # Update the overall Y position to the lowest of all three columns
    y = min(current_y, summary_y, tool_summary_y) - 20  # Add extra space after all sections
    
    # Draw Calculation Results section
    # Check if we need to start a new page
    if y < 3 * inch:  # Need at least 3 inches for the calculation section
        current_page += 1
        y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, "Calculation Results")
    
    # Draw a horizontal line under the section title
    pdf.line(margin, y - 5, page_width - margin, y - 5)
    
    # Update Y position
    y -= 25
    
    # Get total service charge
    total_charge = get_value(timesheet_data, 'total_service_charge', 0)
    
    # Draw total service charge
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawCentredString(page_width/2, y, f"Total Service Charge: {currency} {total_charge:,.2f}")
    
    # Update Y position
    y -= 20
    
    # Calculate cost components
    cost_calc = get_value(timesheet_data, 'total_cost_calculation', {})
    
    # Check if we have space for the calculation table (at least 1 inch from bottom margin)
    min_space_needed = margin + 1 * inch
    
    # If less than 1 inch space remains, start a new page
    if y < min_space_needed:
        current_page += 1
        y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    if cost_calc:
        # Create cost table header
        cost_data = [['Item', 'Amount']]
        
        # Add cost components to table
        service_cost = get_value(cost_calc, 'service_hours_cost', 0)
        if service_cost > 0:
            cost_data.append(['Service Hours', f"{currency} {service_cost:,.2f}"])
        
        report_cost = get_value(cost_calc, 'report_preparation_cost', 0)
        if report_cost > 0:
            cost_data.append(['Report Preparation', f"{currency} {report_cost:,.2f}"])
        
        tool_cost = get_value(cost_calc, 'tool_usage_cost', 0)
        if tool_cost > 0:
            cost_data.append(['Tool Usage', f"{currency} {tool_cost:,.2f}"])
        
        transport_short = get_value(cost_calc, 'transportation_short_cost', 0)
        if transport_short > 0:
            cost_data.append(['T&L (<80km)', f"{currency} {transport_short:,.2f}"])
        
        transport_long = get_value(cost_calc, 'transportation_long_cost', 0)
        if transport_long > 0:
            cost_data.append(['T&L (>80km)', f"{currency} {transport_long:,.2f}"])
        
        offshore_cost = get_value(cost_calc, 'offshore_cost', 0)
        if offshore_cost > 0:
            cost_data.append(['Offshore Work', f"{currency} {offshore_cost:,.2f}"])
        
        emergency_cost = get_value(cost_calc, 'emergency_cost', 0)
        if emergency_cost > 0:
            cost_data.append(['Emergency Charge', f"{currency} {emergency_cost:,.2f}"])
        
        other_transport = get_value(cost_calc, 'other_transport_cost', 0)
        if other_transport > 0:
            cost_data.append(['Other Transport', f"{currency} {other_transport:,.2f}"])
        
        # Subtotal
        subtotal = get_value(cost_calc, 'subtotal', 0)
        cost_data.append(['Subtotal', f"{currency} {subtotal:,.2f}"])
        
        # VAT
        vat_amount = get_value(cost_calc, 'vat_amount', 0)
        vat_percent = get_value(cost_calc, 'vat_percent', 0)
        if vat_amount > 0:
            cost_data.append([f"VAT ({vat_percent:.2f}%)", f"{currency} {vat_amount:,.2f}"])
        
        # Discount
        discount = get_value(cost_calc, 'discount_amount', 0)
        if discount > 0:
            cost_data.append(['Discount', f"{currency} {discount:,.2f}"])
        
        # Create and style the cost table
        cost_col_widths = [2*inch, 1.5*inch]
        cost_table = Table(cost_data, colWidths=cost_col_widths)
        cost_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),  # Header background
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left-align item column
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),  # Right-align amount column
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),  # Bold header
            ('FONTSIZE', (0, 0), (-1, -1), 9),    # Font size
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),  # Table grid
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
            # Subtotal row bold
            ('FONTNAME', (0, -3), (-1, -3), 'Helvetica-Bold') if len(cost_data) > 3 else [],
            # Total row bold
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            # Background color for even rows
            ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
            # Replace whitesmoke with white for odd rows
            *[('BACKGROUND', (0, i), (-1, i), colors.white) for i in range(2, len(cost_data), 2)],
        ]))
        
        # Calculate available space on current page
        available_space = y - margin - 20  # Leave some bottom margin
        
        # Check if the table fits on the current page
        cost_table_width, cost_table_height = cost_table.wrap(content_width, available_space)
        
        # Always draw the cost table centered
        table_x = (page_width - cost_table_width) / 2
        
        # If table doesn't fit, we might need to start a new page
        if cost_table_height > available_space:
            # Start a new page
            current_page += 1
            y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
            available_space = y - margin - 20
            
            # Recalculate table dimensions with new available space
            cost_table_width, cost_table_height = cost_table.wrap(content_width, available_space)
        
        # Draw the table
        cost_table.drawOn(pdf, table_x, y - cost_table_height)
        
        # Update Y position
        y -= cost_table_height + 20
    
    # Check if we need to add the detailed calculation breakdown (which can be long)
    detailed_breakdown = get_value(timesheet_data, 'detailed_calculation_breakdown', '')
    
    # Minimum space needed for signatures
    min_space_for_signatures = 3 * inch
    
    # Handle the detailed calculation breakdown if available
    if detailed_breakdown:
        # Start a new page only if there's not enough space on the current page
        # Check if we have at least 2 inches for the breakdown title and a few lines
        if y < margin + 2 * inch:
            current_page += 1
            y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
        
        # Draw the section title
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin, y, "Detailed Calculation Breakdown")
        y -= 15
        
        # Split the breakdown text into lines
        pdf.setFont("Courier", 8)  # Monospaced font for alignment
        
        # Get all lines from the detailed breakdown
        breakdown_lines = detailed_breakdown.split('\n')
        
        # Calculate how many lines we can fit per page
        # Leave space for margins at top and bottom
        line_height = 12  # Space between lines in points
        usable_page_height = page_height - (2 * margin)
        lines_per_page = int(usable_page_height / line_height) - 4  # Subtract a few lines for headers
        
        # Process all lines across multiple pages
        line_position = 0
        page_start_y = y
        
        # Process detailed breakdown line by line
        for i, line in enumerate(breakdown_lines):
            # Check if we need a new page - use consistent 1-inch space rule
            if line_position >= lines_per_page or y < (margin + 1 * inch):
                current_page += 1
                y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
                pdf.setFont("Courier", 8)  # Reset font after new page
                
                # If this is a continuation page, add a continuation header
                if i > 0:
                    pdf.setFont("Helvetica-Bold", 10)
                    pdf.drawString(margin, y, "Detailed Calculation Breakdown (Continued)")
                    y -= 15
                    pdf.setFont("Courier", 8)  # Return to monospaced font
                
                # Reset line position counter for the new page
                line_position = 0
                page_start_y = y
            
            # Draw the line with proper indentation
            pdf.drawString(margin + 10, y, line)
            y -= line_height  # Space between lines
            line_position += 1
        
        # Add some space after the breakdown
        y -= 20
        
        # Draw a line to separate the detailed breakdown
        pdf.setStrokeColor(colors.black)
        pdf.line(margin, y, page_width - margin, y)
        y -= 20
    
    # Check if we have enough space for signatures
    if y < min_space_for_signatures:
        # Not enough space, start a new page
        current_page += 1
        y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    # Draw signature fields
    # Dynamically calculate signature_y based on current y position
    # but ensure there's enough space at the bottom of the page
    signature_y = max(y - 30, 2.5 * inch)  # Use either current position or minimum height
    
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(margin, signature_y, "Prepared By:")
    pdf.drawString(page_width - margin - 2*inch, signature_y, "Approved By:")
    
    # Signature lines
    pdf.line(margin, signature_y - 30, margin + 2*inch, signature_y - 30)
    pdf.line(page_width - margin - 2*inch, signature_y - 30, page_width - margin, signature_y - 30)
    
    # Add preparer and approver labels
    eng_name = get_value(timesheet_data, 'service_engineer_name', '')
    eng_surname = get_value(timesheet_data, 'service_engineer_surname', '')
    full_name = f"{eng_name} {eng_surname}".strip()
    
    pdf.setFont("Helvetica", 8)
    pdf.drawString(margin, signature_y - 40, full_name)
    pdf.drawString(margin, signature_y - 50, "Service Engineer")

    pdf.drawString(page_width - margin - 2*inch, signature_y - 40, "                   ")
    pdf.drawString(page_width - margin - 2*inch, signature_y - 40, "___________________")
    pdf.drawString(page_width - margin - 2*inch, signature_y - 50, "Client Representative")
    
    # Add footer
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawCentredString(page_width / 2, 20, "Marine & Control Lloyd (Thailand) Ltd.")
    
    # Update total page count
    # This would require a two-pass approach to be exact, but we'll use our final estimate
    estimated_total_pages = current_page
    
    # The page number on the first page was already added at the beginning of the function
    # using the pre-calculated total page count (actual_total_pages)
    
    # Save the PDF
    pdf.save()

def new_page(pdf, page_width, page_height, margin, page_count, total_pages, logo_path=None):
    """
    Create a new page in the PDF and add standard headers
    
    Args:
        pdf: The PDF canvas object
        page_width, page_height: Page dimensions
        margin: Page margin
        page_count: Current page number
        total_pages: Total number of pages (accurately calculated)
        logo_path: Optional path to logo image
        
    Returns:
        New Y position after adding headers
    """
    # Save current page and start a new one
    pdf.showPage()
    
    # Add page number
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(page_width - margin, page_height - margin, f"Page {page_count} of {total_pages}")
    
    # Add minimal header with logo if provided
    current_y = page_height - margin
    
    if logo_path and os.path.exists(logo_path):
        try:
            # Add small logo in top left (positioned higher on the page)
            logo_width = 1.2 * inch
            logo_height = 0.5 * inch
            
            # Position logo higher on the page so it's clearly above the title and separator line
            logo_y_position = page_height - margin + 10  # Positioned at the top margin plus extra space
            
            pdf.drawInlineImage(
                logo_path,
                margin, 
                logo_y_position,
                width=logo_width,
                height=logo_height
            )
        except Exception as e:
            print(f"Error adding logo to continuation page: {e}")
    
    # Add title
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawCentredString(page_width / 2, current_y - 15, "SERVICE TIMESHEET AND CHARGE SUMMARY (Continued)")
    
    # Add separator line
    pdf.setStrokeColor(colors.black)
    pdf.line(margin, current_y - 25, page_width - margin, current_y - 25)
    
    # Return new Y position below the header
    return current_y - 40