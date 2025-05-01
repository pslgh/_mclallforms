"""
PDF Export module for Timesheet Service and Charge Summary.
Provides functions to generate PDF from timesheet data.
"""
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm, inch
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
    """
    Create the actual PDF file at the specified path with multi-page support.
    
    Args:
        timesheet_data: The timesheet data (dictionary from JSON or object)
        file_path: Path where to save the PDF
    """
    # First do a calculation pass to determine the actual number of pages
    # This is a simplified version of the calculation we'll do in the actual PDF generation
    time_entries = get_value(timesheet_data, 'time_entries', [])
    tool_usage = get_value(timesheet_data, 'tool_usage', [])
    
    # Base page count with adjustments for content volume
    base_pages = 3
    extra_time_pages = (len(time_entries) - 5) // 15 + 1 if len(time_entries) > 5 else 0
    extra_tool_pages = (len(tool_usage) - 5) // 15 + 1 if len(tool_usage) > 5 else 0
    
    # Calculate the actual total page count that will be generated
    actual_total_pages = base_pages + extra_time_pages + extra_tool_pages
    
    # This will be passed to each page - both first page and continuation pages
    print(f"Pre-calculated total pages: {actual_total_pages}")
    # Create PDF object
    pdf = canvas.Canvas(file_path, pagesize=A4)
    
    # Get page dimensions
    page_width, page_height = A4
    
    # Add page number to first page immediately
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(page_width - 0.75 * inch, page_height - 0.75 * inch, f"Page 1 of {actual_total_pages}")
    
    # Define margin and usable area
    margin = 0.75 * inch
    content_width = page_width - 2 * margin
    
    # Initialize page counting - will be calculated dynamically
    current_page = 1
    
    # Use the pre-calculated total page count from our calculation pass
    total_pages = actual_total_pages
    
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
        
    # Project Info Table Data
    project_data = [
        # Headers and values
        ["Purchasing Order #:", get_value(timesheet_data, 'purchasing_order_number', 'N/A')],
        ["Quotation #:", get_value(timesheet_data, 'quotation_number', 'N/A')],
        ["Under Contract Agreement?:", "Yes" if get_value(timesheet_data, 'under_contract_agreement', False) else "No"],
        ["Emergency Request?:", "Yes" if get_value(timesheet_data, 'emergency_request', False) else "No"],
        ["Client:", get_value(timesheet_data, 'client_company_name', 'N/A')],
        ["Client Representative:", get_value(timesheet_data, 'client_representative_name', 'N/A')],
        ["Address:", get_value(timesheet_data, 'client_address', 'N/A')],
        ["Phone Number:", get_value(timesheet_data, 'client_representative_phone', 'N/A')],
        ["Project Name:", project_name],
        ["Email:", get_value(timesheet_data, 'client_representative_email', 'N/A')],
        ["Project Description:", project_desc],
        ["Service Engineer:", 
         f"{get_value(timesheet_data, 'service_engineer_name', '')} {get_value(timesheet_data, 'service_engineer_surname', '')}".strip() or 'N/A'],
        ["Work Type:", get_value(timesheet_data, 'work_type', 'N/A')]
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
    ]
    
    # Find index of project name and description rows
    project_name_index = -1
    project_desc_index = -1
    for i, row in enumerate(project_data):
        if row[0] == "Project Name:":
            project_name_index = i
        elif row[0] == "Project Description:":
            project_desc_index = i
    
    # Add special styling for project name and description
    if project_name_index >= 0:
        # Add more padding for project name to accommodate multiple lines
        table_style.append(('BOTTOMPADDING', (1, project_name_index), (1, project_name_index), 6))
        table_style.append(('TOPPADDING', (1, project_name_index), (1, project_name_index), 6))
    
    if project_desc_index >= 0:
        # Add even more padding for project description to accommodate multiple lines
        table_style.append(('BOTTOMPADDING', (1, project_desc_index), (1, project_desc_index), 10))
        table_style.append(('TOPPADDING', (1, project_desc_index), (1, project_desc_index), 10))
        # No special background - keeping consistent with other fields
    
    # Apply the styles
    table.setStyle(TableStyle(table_style))
    
    # Draw the table
    table_width, table_height = table.wrap(content_width, 500)  # 500 is arbitrary max height
    table.drawOn(pdf, margin, y - table_height)
    
    # Update Y position
    y -= table_height + 20
    
    # Check if we have space for the Time Entries section
    estimated_time_table_height = 0.4 * inch * len(get_value(timesheet_data, 'time_entries', []))
    min_space_needed = estimated_time_table_height + 1 * inch
    
    # If not enough space, start a new page
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
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
        ('ALIGN', (0, 1), (5, -1), 'CENTER'),  # Center-align data cells except description
        ('ALIGN', (6, 1), (6, -1), 'LEFT'),   # Left-align description
    ]))
    
    # Draw the time entries table
    time_table_width, time_table_height = time_table.wrap(content_width, 400)  # 400 is arbitrary max height
    time_table.drawOn(pdf, margin, y - time_table_height)
    
    # Update Y position
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
        # Check if we have space for the Tools section
        estimated_tool_table_height = 0.4 * inch * (len(tool_usage) + 1)  # +1 for header
        min_space_needed = estimated_tool_table_height + 1 * inch
        
        # If not enough space, start a new page
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
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),  # Vertical alignment
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Left-align tool names
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),  # Center-align other data
        ]))
        
        # Draw the tools table
        tools_table_width, tools_table_height = tools_table.wrap(content_width, 300)
        tools_table.drawOn(pdf, margin, y - tools_table_height)
        
        # Update Y position
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
                    summary_text += f"Tools Used: {tools_used}   "
                
                if total_days > 0:
                    summary_text += f"Total Days: {total_days}"
                
                pdf.drawString(margin + 20, y - 5, summary_text)
                y -= 20
    
    # Add Service Rates and Time Summary section
    # Always force a page break here to show rates and calculation details on a new page
    # This ensures the content isn't cut off and is properly displayed
    current_page += 1
    y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    # Create two-column layout for rates and time summary
    rates_time_y = y
    col_width = (content_width - 0.5*inch) / 2  # Two equal columns with 0.5 inch between
    
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
    
    # ------ RIGHT COLUMN: Time Summary ------
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin + col_width + 0.5*inch, rates_time_y + 25, "Time Summary")
    
    # Draw a horizontal line under the section title
    pdf.line(margin + col_width + 0.5*inch, rates_time_y + 20, 
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
    
    # Update the overall Y position to the lowest of the two columns
    y = min(current_y, summary_y) - 20  # Add extra space after both sections
    
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
    
    # Check if we have space for the calculation table
    # Rough estimate of table height based on number of items
    estimated_table_height = 0.4 * inch * 10  # Assuming about 10 rows
    min_space_needed = estimated_table_height + 1 * inch
    
    # If not enough space, start a new page
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
        
        # Draw the cost table
        cost_table_width, cost_table_height = cost_table.wrap(content_width, 300)  # 300 is arbitrary max height
        cost_table.drawOn(pdf, (page_width - cost_table_width) / 2, y - cost_table_height)
        
        # Update Y position
        y -= cost_table_height + 20
    
    # Check if we need to add the detailed calculation breakdown (which can be long)
    detailed_breakdown = get_value(timesheet_data, 'detailed_calculation_breakdown', '')
    
    # Minimum space needed for signatures
    min_space_for_signatures = 3 * inch
    
    # Always start a new page for the detailed breakdown to ensure it's shown completely
    if detailed_breakdown:
        current_page += 1
        y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
    
    # Add detailed calculation breakdown if available
    if detailed_breakdown:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(margin, y, "Detailed Calculation Breakdown")
        y -= 15
        
        # Split the breakdown text into lines
        pdf.setFont("Courier", 8)  # Monospaced font for alignment
        
        # Process detailed breakdown line by line
        for i, line in enumerate(detailed_breakdown.split('\n')):
            # Check if we need a new page
            if y < (margin + 20):
                current_page += 1
                y = new_page(pdf, page_width, page_height, margin, current_page, total_pages, logo_path)
                pdf.setFont("Courier", 8)  # Reset font after new page
            
            # Draw the line
            pdf.drawString(margin + 10, y, line)
            y -= 12  # Space between lines
        
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
    
    pdf.drawString(page_width - margin - 2*inch, signature_y - 40, "\n___________________")
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

def new_page(pdf, page_width, page_height, margin, page_count, estimated_total_pages, logo_path=None):
    """
    Create a new page in the PDF and add standard headers
    
    Args:
        pdf: The PDF canvas object
        page_width, page_height: Page dimensions
        margin: Page margin
        page_count: Current page number
        estimated_total_pages: Estimated total number of pages
        logo_path: Optional path to logo image
        
    Returns:
        New Y position after adding headers
    """
    # Save current page and start a new one
    pdf.showPage()
    
    # Add page number
    pdf.setFont("Helvetica", 8)
    pdf.drawRightString(page_width - margin, page_height - margin, f"Page {page_count} of {estimated_total_pages}")
    
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