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

def create_timesheet_pdf(timesheet_data, file_path):
    """
    Create the actual PDF file at the specified path.
    
    Args:
        timesheet_data: The timesheet data (dictionary from JSON or object)
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
    
    # Set default text color to black for all content
    pdf.setFillColor(colors.black)
    
    # Add entry ID (top-left header)
    entry_id = get_value(timesheet_data, 'entry_id', 'Unknown ID')
    pdf.setFont("Helvetica-Bold", 10)
    pdf.drawString(30, page_height - 30, f"Report ID: {entry_id}")
    
    # Add page number (top-right header)
    pdf.drawRightString(page_width - 30, page_height - 30, "Page 1 of 1")
    
    # Add title
    pdf.setFont("Helvetica-Bold", 16)
    title = "SERVICE TIMESHEET AND CHARGE SUMMARY"
    title_width = pdf.stringWidth(title, "Helvetica-Bold", 16)
    pdf.drawString((page_width - title_width) / 2, page_height - 1.5 * inch, title)
    
    # Draw a line below the title
    pdf.setStrokeColor(colors.black)
    pdf.line(30, page_height - 1.7 * inch, page_width - 30, page_height - 1.7 * inch)
    
    # Start position for form content
    y_position = page_height - 2 * inch
    
    # Add date line (right-aligned)
    creation_date = get_value(timesheet_data, 'creation_date', datetime.now().strftime('%Y-%m-%d'))
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawRightString(page_width - 30, page_height - 1.9 * inch, f"Date: {creation_date}")
    
    # CLIENT INFORMATION SECTION
    y_position -= 30
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(30, y_position, "Project Information")
    
    # Draw a rounded rectangle around project info
    pdf.setStrokeColor(colors.black)
    pdf.setFillColor(colors.white)
    pdf.roundRect(30, y_position - 75, page_width - 60, 120, 6, stroke=1, fill=1)
    
    # Project information - left column
    y_position -= 25
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(40, y_position, "Client:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    # Try all possible client field names
    client = 'N/A'
    for field in ['client_company_name', 'Client', 'client']:
        client_value = get_value(timesheet_data, field, None)
        if client_value:
            client = client_value
            break
    pdf.drawString(120, y_position, client)
    
    # Client Address
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(40, y_position, "Address:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    # Try all possible client address field names
    client_address = 'N/A'
    for field in ['client_address', 'Client Address']:
        address_value = get_value(timesheet_data, field, None)
        if address_value:
            client_address = address_value
            break
    pdf.drawString(120, y_position, client_address)
    
    # Client Representative
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(40, y_position, "Representative:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    # Try all possible client representative field names
    client_rep = 'N/A'
    for field in ['client_representative_name', 'Client Representative Name', 'client_representative']:
        rep_value = get_value(timesheet_data, field, None)
        if rep_value:
            client_rep = rep_value
            break
    pdf.drawString(120, y_position, client_rep)
    
    # Add client representative contact details to bottom of client info
    # Phone
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(40, y_position, "Rep. Phone:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    # Try all possible phone field names
    client_rep_phone = 'N/A'
    for field in ['client_representative_phone', 'Phone Number']:
        phone_value = get_value(timesheet_data, field, None)
        if phone_value:
            client_rep_phone = phone_value
            break
    pdf.drawString(120, y_position, client_rep_phone)
    
    # Email
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(40, y_position, "Rep. Email:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    # Try all possible email field names
    client_rep_email = 'N/A'
    for field in ['client_representative_email', 'Email']:
        email_value = get_value(timesheet_data, field, None)
        if email_value:
            client_rep_email = email_value
            break
    pdf.drawString(120, y_position, client_rep_email)
    
    # Work Type
    y_position -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(40, y_position, "Work Type:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    # Try all possible work type field names
    work_type = 'N/A'
    for field in ['work_type', 'Work Type']:
        work_type_value = get_value(timesheet_data, field, None)
        if work_type_value:
            work_type = work_type_value
            break
    pdf.drawString(120, y_position, work_type)
    
    # Project information - right column
    y_right = y_position + 60  # Reset to top of project info
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(300, y_right, "Engineer:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    
    # Combine engineer name and surname
    engineer_name = get_value(timesheet_data, 'engineer_name', '')
    engineer_surname = get_value(timesheet_data, 'engineer_surname', '')
    engineer_full = f"{engineer_name} {engineer_surname}".strip() or 'N/A'
    pdf.drawString(380, y_right, engineer_full)
    
    # Engineer Phone
    y_right -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(300, y_right, "Phone:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    engineer_phone = get_value(timesheet_data, 'engineer_phone', 'N/A')
    pdf.drawString(380, y_right, engineer_phone)
    
    # Engineer Email
    y_right -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(300, y_right, "Email:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    engineer_email = get_value(timesheet_data, 'engineer_email', 'N/A')
    pdf.drawString(380, y_right, engineer_email)
    
    # Emergency Request
    y_right -= 20
    pdf.setFont("Helvetica-Bold", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(300, y_right, "Emergency:")
    pdf.setFont("Helvetica", 10)
    pdf.setFillColor(colors.black)  # Ensure text is black
    emergency = "Yes" if get_value(timesheet_data, 'emergency_request', False) else "No"
    pdf.drawString(380, y_right, emergency)
    
    # Update y_position to continue after the project info box
    y_position = y_position - 55
    
    # TIME ENTRIES SECTION
    time_entries = get_value(timesheet_data, 'time_entries', [])
    if time_entries:
        y_position -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(30, y_position, "Time Entries")
        y_position -= 15
        
        # Create the table data
        table_data = [
            ["Date", "Start", "End", "Break (hrs)", "Description", "OT Rate", "Offshore", "Travel", "Equiv. Hours"]
        ]
        
        # Add time entries to table
        for entry in time_entries:
            date = entry.get('date', '')
            
            # Format start and end times
            start_time = entry.get('start_time', '')
            end_time = entry.get('end_time', '')
            start_display = f"{start_time[:2]}:{start_time[2:]}" if len(start_time) >= 4 else start_time
            end_display = f"{end_time[:2]}:{end_time[2:]}" if len(end_time) >= 4 else end_time
            
            rest_hours = entry.get('rest_hours', 0)
            description = entry.get('description', '')
            ot_rate = entry.get('overtime_rate', '1')
            offshore = "Yes" if entry.get('offshore', False) else "No"
            
            # Format travel info
            travel_info = "No"
            if entry.get('travel_count', False):
                if entry.get('travel_short_distance', False):
                    travel_info = "<80km"
                elif entry.get('travel_far_distance', False):
                    travel_info = ">80km"
                else:
                    travel_info = "Yes"
            
            equivalent_hours = entry.get('equivalent_hours', 0)
            
            # Add row to table data
            table_data.append([
                date, start_display, end_display, str(rest_hours), description,
                str(ot_rate), offshore, travel_info, str(equivalent_hours)
            ])
        
        # Create the table
        table = Table(table_data)
        
        # Style the table with more spacing between header and content
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (4, 1), (4, -1), 'LEFT'),  # Description column left-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # More padding below header
            ('TOPPADDING', (0, 1), (-1, 1), 8),      # More padding above first data row
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),  # Thicker line below header
        ])
        table.setStyle(style)
        
        # Draw the table
        table_width = min(page_width - 60, 520)  # Limit table width
        table.wrapOn(pdf, table_width, 400)
        table.drawOn(pdf, 30, y_position - len(table_data) * 15)
        
        # Update y position
        y_position = y_position - len(table_data) * 15 - 15
    
    # TOOL USAGE SECTION
    tool_usage = get_value(timesheet_data, 'tool_usage', [])
    if tool_usage:
        y_position -= 20
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(30, y_position, "Special Tool Usage")
        y_position -= 15
        
        # Create the table data
        table_data = [
            ["Tool Name", "Amount", "Start Date", "End Date", "Total Days"]
        ]
        
        # Add tool usage entries to table
        for tool in tool_usage:
            tool_name = tool.get('tool_name', '')
            amount = tool.get('amount', 1)
            start_date = tool.get('start_date', '')
            end_date = tool.get('end_date', '')
            total_days = tool.get('total_days', 0)
            
            # Add row to table data
            table_data.append([
                tool_name, str(amount), str(start_date), str(end_date), str(total_days)
            ])
        
        # Create the table
        table = Table(table_data)
        
        # Style the table with more spacing between header and content
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),  # Tool name column left-aligned
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),  # More padding below header
            ('TOPPADDING', (0, 1), (-1, 1), 8),      # More padding above first data row
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LINEBELOW', (0, 0), (-1, 0), 2, colors.black),  # Thicker line below header
        ])
        table.setStyle(style)
        
        # Draw the table
        table_width = min(page_width - 60, 520)
        table.wrapOn(pdf, table_width, 200)
        table.drawOn(pdf, 30, y_position - len(table_data) * 15)
        
        # Update y position
        y_position = y_position - len(table_data) * 15 - 15
    
    # RATES AND SUMMARY SECTION (SIDE BY SIDE)
    y_position -= 20
    
    # If y_position is too close to bottom, start a new page
    if y_position < 200:  # Leave about 200 points for rates and summary + tool summary
        pdf.showPage()
        y_position = page_height - inch
    
    # Draw two columns: rates and time summary
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(30, y_position, "Service Rates")
    pdf.drawString(300, y_position, "Time Summary")
    y_position -= 15
    
    # Draw rounded rectangles around both sections
    pdf.setStrokeColor(colors.black)
    pdf.setFillColor(colors.white)
    pdf.roundRect(30, y_position - 140, 240, 135, 6, stroke=1, fill=1)  # Rates
    pdf.roundRect(300, y_position - 140, 240, 135, 6, stroke=1, fill=1)  # Summary
    
    # Service Rates
    y_rates = y_position - 20
    currency = get_value(timesheet_data, 'currency', 'THB')
    
    rates = [
        ("Service Hour Rate:", f"{currency} {get_value(timesheet_data, 'service_hour_rate', 0):,.2f}"),
        ("Tool Usage Rate:", f"{currency} {get_value(timesheet_data, 'tool_usage_rate', 0):,.2f}"),
        ("T&L Rate (<80km):", f"{currency} {get_value(timesheet_data, 'tl_rate_short', 0):,.2f}"),
        ("T&L Rate (>80km):", f"{currency} {get_value(timesheet_data, 'tl_rate_long', 0):,.2f}"),
        ("Offshore Day Rate:", f"{currency} {get_value(timesheet_data, 'offshore_day_rate', 0):,.2f}"),
        ("Emergency Rate:", f"{currency} {get_value(timesheet_data, 'emergency_rate', 0):,.2f}")
    ]
    
    for label, value in rates:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(40, y_rates, label)
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(160, y_rates, value)
        y_rates -= 20
    
    # Time Summary
    y_summary = y_position - 20
    
    # Calculate hours
    hours = {}
    try:
        # Try to use calculate_total_hours method if available
        if hasattr(timesheet_data, 'calculate_total_hours'):
            hours = timesheet_data.calculate_total_hours()
        else:
            # Manual calculation
            hours = {'regular': 0, 'ot1': 0, 'ot15': 0, 'ot2': 0, 'total': 0}
            if time_entries:
                for entry in time_entries:
                    equiv_hours = float(entry.get('equivalent_hours', 0))
                    ot_rate = entry.get('overtime_rate', '1')
                    
                    if ot_rate == '1' or ot_rate == 1:
                        hours['regular'] += equiv_hours
                    elif ot_rate == '1.5' or ot_rate == 1.5:
                        hours['ot15'] += equiv_hours
                    elif ot_rate == '2' or ot_rate == 2:
                        hours['ot2'] += equiv_hours
                    else:
                        hours['ot1'] += equiv_hours
                        
                hours['total'] = hours['regular'] + hours['ot1'] + hours['ot15'] + hours['ot2']
    except Exception as e:
        print(f"Error calculating hours: {e}")
    
    summary = [
        ("Regular Hours:", f"{hours.get('regular', 0):.1f}"),
        ("OT 1.0X Hours:", f"{hours.get('ot1', 0):.1f}"),
        ("OT 1.5X Hours:", f"{hours.get('ot15', 0):.1f}"),
        ("OT 2.0X Hours:", f"{hours.get('ot2', 0):.1f}"),
        ("Total Hours:", f"{hours.get('total', 0):.1f}")
    ]
    
    for label, value in summary:
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(310, y_summary, label)
        
        # Make the total hours bold
        if label == "Total Hours:":
            pdf.setFont("Helvetica-Bold", 10)
        else:
            pdf.setFont("Helvetica", 10)
        
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(430, y_summary, value)
        y_summary -= 20
    
    # Create a separate Tool Usage Summary section if we have tool usage
    if tool_usage:
        # Tool Summary Section - move down from the Time Summary and Service Rates
        y_position = min(y_rates, y_summary) - 20
        
        # Add Tool Usage Summary Header
        pdf.setFont("Helvetica-Bold", 12)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(30, y_position, "Tool Usage Summary")
        y_position -= 15
        
        # Draw rounded rectangle for tool summary
        pdf.setStrokeColor(colors.black)
        pdf.setFillColor(colors.white)
        pdf.roundRect(30, y_position - 60, page_width - 60, 55, 6, stroke=1, fill=1)  # Tool Summary
        
        # Calculate tool summary
        total_days = sum(tool.get('total_days', 0) for tool in tool_usage)
        tool_names = [f"{tool.get('amount', 1)} {tool.get('tool_name', '')}" for tool in tool_usage]
        
        # Tool Usage Summary Content
        y_tool = y_position - 20
        
        # If the list of tool names is too long, truncate and add "..."
        tool_text = ", ".join(tool_names)
        if len(tool_text) > 50:  # Increased character limit for better display
            tool_text = tool_text[:47] + "..."
        
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(40, y_tool, "Tools Used:")
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(140, y_tool, tool_text)
        
        y_tool -= 20
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(40, y_tool, "Total Tool Days:")
        pdf.setFont("Helvetica", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        pdf.drawString(140, y_tool, str(total_days))
        
        # Update y_position for the next section
        y_position = y_tool - 40
    else:
        # If no tool usage, just update y_position for the next section
        y_position = min(y_rates, y_summary) - 30
    
    # CALCULATION RESULT
    # Note: y_position is already updated based on whether we had tool usage or not
    
    pdf.setFont("Helvetica-Bold", 12)
    pdf.setFillColor(colors.black)  # Ensure text is black
    pdf.drawString(30, y_position, "Calculation Result")
    y_position -= 15
    
    # Draw rounded rectangle around calculation result
    pdf.setStrokeColor(colors.black)
    pdf.setFillColor(colors.lightgrey)
    pdf.roundRect(30, y_position - 80, page_width - 60, 70, 6, stroke=1, fill=1)
    
    # Add total service charge
    y_position -= 30
    total_charge = get_value(timesheet_data, 'total_service_charge', 0)
    pdf.setFont("Helvetica-Bold", 14)
    pdf.setFillColor(colors.black)  # Ensure text is black
    total_text = f"Total Service Charge: {currency} {total_charge:,.2f}"
    pdf.drawCentredString(page_width / 2, y_position, total_text)
    
    # Add additional charges if any
    other_transport_charge = get_value(timesheet_data, 'other_transport_charge', 0)
    if other_transport_charge > 0:
        y_position -= 25
        pdf.setFont("Helvetica-Bold", 10)
        pdf.setFillColor(colors.black)  # Ensure text is black
        transport_text = f"Additional Transport Charge: {currency} {other_transport_charge:,.2f}"
        pdf.drawCentredString(page_width / 2, y_position, transport_text)
        
        # Add transport note if any
        transport_note = get_value(timesheet_data, 'other_transport_note', '')
        if transport_note:
            y_position -= 20
            pdf.setFont("Helvetica", 9)
            pdf.setFillColor(colors.black)  # Ensure text is black
            note_text = f"Note: {transport_note}"
            pdf.drawCentredString(page_width / 2, y_position, note_text)
    
    # Add footer
    pdf.setFont("Helvetica", 8)
    pdf.setFillColor(colors.black)  # Ensure text is black
    footer_text = f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    pdf.drawCentredString(page_width / 2, 20, footer_text)
    
    # Save the PDF
    pdf.save()
