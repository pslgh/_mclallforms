"""
Timesheet Data Models
Classes for representing and managing timesheet entries
"""
import json
import uuid
import datetime
from pathlib import Path
from PySide6.QtCore import QObject, Signal

# Add parent directory to path so we can import our services and utils
import sys
sys.path.append(str(Path(__file__).resolve().parents[3]))
from utils.path_utils import get_data_path, ensure_directory

class TimesheetEntry:
    """Class representing a single timesheet entry"""
    
    def __init__(self, entry_data=None):
        """Initialize a timesheet entry from data or with defaults"""
        data = entry_data or {}
        
        # Identifiers
        self.entry_id = data.get('entry_id', str(uuid.uuid4()))
        
        # Client details
        self.client = data.get('client', '')
        self.work_type = data.get('work_type', '')
        self.tier = data.get('tier', '')
        
        # Engineer details
        self.created_by = data.get('created_by', '')
        self.engineer_name = data.get('engineer_name', '')
        self.engineer_surname = data.get('engineer_surname', '')
        
        # Dates and status
        self.creation_date = data.get('creation_date', datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.status = data.get('status', 'draft')  # draft, submitted, approved, rejected
        
        # Time entries as list of dictionaries
        # Each time entry contains: date, start_time, end_time, description, overtime_rate, overtime_hours, rest_hours,
        # offshore, travel_count (boolean), travel_far_distance
        self.time_entries = data.get('time_entries', [])
        
        # Tool usage entries as list of dictionaries
        # Each tool entry contains: tool_name, amount, start_date, end_date, total_days
        self.tool_usage = data.get('tool_usage', [])
        
        # Report preparation information
        self.report_description = data.get('report_description', '')
        self.report_hours = data.get('report_hours', 0)
        
        # Emergency request flag
        self.emergency_request = data.get('emergency_request', False)
        
        # Service charge calculation fields
        self.currency = data.get('currency', 'THB')
        self.service_hour_rate = data.get('service_hour_rate', 0)
        self.tool_usage_rate = data.get('tool_usage_rate', 0)
        self.tl_rate_short = data.get('tl_rate_short', 0)  # < 80 km
        self.tl_rate_long = data.get('tl_rate_long', 0)    # > 80 km
        self.offshore_day_rate = data.get('offshore_day_rate', 0)
        self.emergency_rate = data.get('emergency_rate', 0)
        self.other_transport_charge = data.get('other_transport_charge', 0)
        self.other_transport_note = data.get('other_transport_note', '')
        self.total_service_charge = data.get('total_service_charge', 0)
        
    def to_dict(self):
        """Convert timesheet entry to dictionary for JSON serialization"""
        return {
            'entry_id': self.entry_id,
            'client': self.client,
            'work_type': self.work_type,
            'tier': self.tier,
            'created_by': self.created_by,
            'engineer_name': self.engineer_name,
            'engineer_surname': self.engineer_surname,
            'creation_date': self.creation_date,
            'status': self.status,
            'time_entries': self.time_entries,
            'tool_usage': self.tool_usage,
            'report_description': self.report_description,
            'report_hours': self.report_hours,
            'emergency_request': self.emergency_request,
            'currency': self.currency,
            'service_hour_rate': self.service_hour_rate,
            'tool_usage_rate': self.tool_usage_rate,
            'tl_rate_short': self.tl_rate_short,
            'tl_rate_long': self.tl_rate_long,
            'offshore_day_rate': self.offshore_day_rate,
            'emergency_rate': self.emergency_rate,
            'other_transport_charge': self.other_transport_charge,
            'other_transport_note': self.other_transport_note,
            'total_service_charge': self.total_service_charge
        }
    
    def calculate_total_hours(self):
        """Calculate total regular and overtime hours"""
        regular_hours = 0
        ot1_hours = 0
        ot15_hours = 0
        ot2_hours = 0
        
        for entry in self.time_entries:
            # Parse times (assuming format like "0800")
            start_time = entry.get('start_time', '')
            end_time = entry.get('end_time', '')
            
            try:
                # Convert to hours and minutes
                start_hours = int(start_time[:2])
                start_minutes = int(start_time[2:]) if len(start_time) > 2 else 0
                end_hours = int(end_time[:2])
                end_minutes = int(end_time[2:]) if len(end_time) > 2 else 0
                
                # Calculate duration in hours
                start_decimal = start_hours + (start_minutes / 60)
                end_decimal = end_hours + (end_minutes / 60)
                
                # Handle overnight entries
                if end_decimal < start_decimal:
                    duration = (24 - start_decimal) + end_decimal
                else:
                    duration = end_decimal - start_decimal
                
                # Categorize by overtime rate
                overtime_rate = entry.get('overtime_rate', 'OT1')
                if overtime_rate == 'OT1':
                    ot1_hours += duration
                elif overtime_rate == 'OT1.5':
                    ot15_hours += duration
                elif overtime_rate == 'OT2.0':
                    ot2_hours += duration
                else:
                    regular_hours += duration
                    
            except (ValueError, IndexError):
                # Skip if time format is invalid
                continue
                
        return {
            'regular': regular_hours,
            'ot1': ot1_hours,
            'ot15': ot15_hours,
            'ot2': ot2_hours,
            'total': regular_hours + ot1_hours + ot15_hours + ot2_hours
        }
    
    def add_time_entry(self, date, start_time, end_time, description, overtime_rate="Regular", rest_hours=0,
                       offshore=False, travel_count=False, travel_far_distance=False):
        """Add a new time entry to the timesheet"""
        entry = {
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'description': description,
            'overtime_rate': overtime_rate,
            'rest_hours': rest_hours,
            'offshore': offshore,
            'travel_count': travel_count,
            'travel_far_distance': travel_far_distance
        }
        self.time_entries.append(entry)

class TimesheetDataManager(QObject):
    """Manager class for timesheet entries"""
    
    data_changed = Signal()
    
    def __init__(self, data_file_path=None):
        """Initialize with data file path"""
        super().__init__()
        self.data_file_path = Path(data_file_path) if data_file_path else get_data_path("timesheet/timesheet_entries.json")
        
        # Ensure the directory exists
        ensure_directory(self.data_file_path.parent)
        
        # Create file if it doesn't exist
        if not self.data_file_path.exists():
            self.save_entries([])
    
    def load_entries(self):
        """Load all timesheet entries from the data file"""
        try:
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return [TimesheetEntry(entry_data) for entry_data in data.get('entries', [])]
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error loading timesheet entries: {e}")
            return []
    
    def save_entries(self, entries):
        """Save timesheet entries to the data file"""
        try:
            data = {
                'entries': [entry.to_dict() for entry in entries]
            }
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # Emit signal that data has changed
            self.data_changed.emit()
            return True
        except Exception as e:
            print(f"Error saving timesheet entries: {e}")
            return False
    
    def get_entry_by_id(self, entry_id):
        """Get a specific timesheet entry by ID"""
        entries = self.load_entries()
        for entry in entries:
            if entry.entry_id == entry_id:
                return entry
        return None
    
    def add_entry(self, entry):
        """Add a new timesheet entry"""
        entries = self.load_entries()
        entries.append(entry)
        return self.save_entries(entries)
    
    def update_entry(self, updated_entry):
        """Update an existing timesheet entry"""
        entries = self.load_entries()
        
        # Find and replace the entry with matching ID
        for i, entry in enumerate(entries):
            if entry.entry_id == updated_entry.entry_id:
                entries[i] = updated_entry
                return self.save_entries(entries)
        
        # Entry not found
        return False
    
    def delete_entry(self, entry_id):
        """Delete a timesheet entry by ID"""
        entries = self.load_entries()
        original_count = len(entries)
        
        # Remove the entry with matching ID
        entries = [entry for entry in entries if entry.entry_id != entry_id]
        
        if len(entries) < original_count:
            return self.save_entries(entries)
        
        # Entry not found
        return False
    
    def save_timesheet(self, timesheet_data):
        """Save a new timesheet from the data dictionary
        
        This method converts the dictionary into a TimesheetEntry object
        and then adds it to the list of entries.
        """
        # Create a new timesheet entry from the data
        entry = TimesheetEntry(timesheet_data)
        
        # Add it to the list of entries
        return self.add_entry(entry)
    
    def get_entries_by_client(self, client):
        """Get all entries for a specific client"""
        entries = self.load_entries()
        return [entry for entry in entries if entry.client.lower() == client.lower()]
    
    def get_entries_by_date_range(self, start_date, end_date):
        """Get all entries within a date range"""
        entries = self.load_entries()
        filtered_entries = []
        
        try:
            # Support both dash and slash date formats
            if "/" in start_date:
                start = datetime.datetime.strptime(start_date, "%Y/%m/%d")
            else:
                start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
                
            if "/" in end_date:
                end = datetime.datetime.strptime(end_date, "%Y/%m/%d")
            else:
                end = datetime.datetime.strptime(end_date, "%Y-%m-%d")
            
            for entry in entries:
                # Check each time entry date
                for time_entry in entry.time_entries:
                    date_str = time_entry.get('date', '')
                    # Support both dash and slash date formats
                    if "/" in date_str:
                        entry_date = datetime.datetime.strptime(date_str, "%Y/%m/%d")
                    else:
                        entry_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
                    if start <= entry_date <= end:
                        filtered_entries.append(entry)
                        break  # Add entry once if any time entry is in range
        except ValueError:
            # Date parsing error
            return []
            
        return filtered_entries
