"""
Timesheet Data Models
Classes for representing and managing timesheet entries
"""
import json
import uuid
import datetime
import os
import traceback
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
        
        print(f"TimesheetDataManager initialized with data file path: {self.data_file_path} (absolute: {self.data_file_path.absolute()})")
        
        # Ensure the directory exists
        ensure_directory(self.data_file_path.parent)
        print(f"Ensured directory exists: {self.data_file_path.parent}")
        
        # Create file if it doesn't exist
        if not self.data_file_path.exists():
            print(f"Data file does not exist, creating empty file: {self.data_file_path}")
            self.save_entries([])
        else:
            print(f"Data file already exists: {self.data_file_path}")
    
    def load_entries(self):
        """Load all timesheet entries from the data file"""
        try:
            # Check if file exists and has size greater than 0
            if not self.data_file_path.exists() or self.data_file_path.stat().st_size == 0:
                print(f"Data file does not exist or is empty: {self.data_file_path}")
                return []
                
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                # Read the entire file content for debugging
                file_content = f.read()
                print(f"File content (first 100 chars): {file_content[:100]}...")
                
                if not file_content.strip():
                    print("File is empty or contains only whitespace")
                    return []
                
                # Parse the JSON from the file content
                try:
                    data = json.loads(file_content)
                    if not isinstance(data, dict):
                        print(f"Data is not a dictionary, found: {type(data)}")
                        return []
                        
                    entries_data = data.get('entries', [])
                    print(f"Found {len(entries_data)} entries in JSON file")
                    
                    # Create TimesheetEntry objects from the data
                    entries = []
                    for entry_data in entries_data:
                        try:
                            entry = TimesheetEntry(entry_data)
                            entries.append(entry)
                            print(f"Loaded entry: {entry.entry_id}")
                        except Exception as entry_error:
                            print(f"Error creating entry from data: {entry_error}")
                            traceback.print_exc()
                    
                    return entries
                except json.JSONDecodeError as json_err:
                    print(f"JSON decode error: {json_err}")
                    print(f"Error at line {json_err.lineno}, column {json_err.colno}")
                    print(f"Error context: {json_err.doc[max(0, json_err.pos-20):json_err.pos+20]}")
                    traceback.print_exc()
                    return []
        except Exception as e:
            print(f"Unexpected error loading timesheet entries: {e}")
            traceback.print_exc()
            return []
    
    def save_entries(self, entries):
        """Save timesheet entries to the data file"""
        try:
            print(f"Saving {len(entries)} timesheet entries to: {self.data_file_path}")
            
            # Create list of entry dictionaries
            entry_dicts = []
            for entry in entries:
                entry_dict = entry.to_dict()
                entry_dicts.append(entry_dict)
                print(f"  - Entry ID: {entry_dict['entry_id']}, Client: {entry_dict['client']}")
            
            # Prepare data structure - ensure it's a proper dictionary
            data = {'entries': entry_dicts}
            
            # Ensure parent directory exists
            os.makedirs(self.data_file_path.parent, exist_ok=True)
            print(f"Ensured directory exists: {self.data_file_path.parent}")
            
            # First validate the JSON is serializable
            try:
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                print(f"Successfully serialized data with {len(json_str)} characters")
            except Exception as json_err:
                print(f"Error serializing JSON: {json_err}")
                traceback.print_exc()
                return False
            
            # Write to file
            print(f"Writing data to file: {self.data_file_path}")
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            # Verify file exists and has content
            if self.data_file_path.exists():
                file_size = self.data_file_path.stat().st_size
                print(f"File saved: {self.data_file_path}, size: {file_size} bytes")
                
                # Validate the saved file is readable as JSON
                try:
                    with open(self.data_file_path, 'r', encoding='utf-8') as check_f:
                        check_data = json.load(check_f)
                        entry_count = len(check_data.get('entries', []))
                        print(f"Verified file contains valid JSON with {entry_count} entries")
                except Exception as verify_err:
                    print(f"Warning: File was saved but verification failed: {verify_err}")
                    traceback.print_exc()
            else:
                print(f"Warning: File does not exist after save attempt: {self.data_file_path}")
            
            # Emit signal that data has changed
            self.data_changed.emit()
            print(f"Data change signal emitted")
            return True
        except Exception as e:
            print(f"Error saving timesheet entries: {e}")
            traceback.print_exc()
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
        print(f"\n[ADD] Adding entry ID: {entry.entry_id} for client: {entry.client}")
        entries = self.load_entries()
        print(f"[ADD] Loaded {len(entries)} existing entries")
        
        # Check if this entry ID already exists
        for i, existing in enumerate(entries):
            if existing.entry_id == entry.entry_id:
                print(f"[ADD] Entry with ID {entry.entry_id} already exists, replacing at index {i}")
                entries[i] = entry
                break
        else:
            # Entry doesn't exist, append it
            entries.append(entry)
            print(f"[ADD] Added new entry, now have {len(entries)} entries")
        
        # Force save and verify
        result = self._force_save_entries(entries)
        print(f"[ADD] Save result: {result}")
        return result
    
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
        print(f"\n[SAVE] Saving timesheet with ID: {timesheet_data.get('entry_id')}, Client: {timesheet_data.get('client')}")
        
        try:
            # Create a new timesheet entry from the data
            entry = TimesheetEntry(timesheet_data)
            print(f"[SAVE] Created TimesheetEntry object: {entry.entry_id}")
            
            # Load existing entries directly from file
            entries = []
            try:
                if self.data_file_path.exists() and self.data_file_path.stat().st_size > 0:
                    with open(self.data_file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        for entry_data in data.get('entries', []):
                            entries.append(TimesheetEntry(entry_data))
                    print(f"[SAVE] Loaded {len(entries)} existing entries from file")
                else:
                    print(f"[SAVE] No existing entries file found or file is empty")
            except Exception as load_err:
                print(f"[SAVE] Error loading existing entries: {load_err}")
                print(f"[SAVE] Starting with empty entries list")
                entries = []
            
            # Check for duplicate entry IDs and only add if unique
            entry_ids = [e.entry_id for e in entries]
            if entry.entry_id in entry_ids:
                # Replace the existing entry with this ID
                idx = entry_ids.index(entry.entry_id)
                print(f"[SAVE] Replacing existing entry at index {idx} with ID {entry.entry_id}")
                entries[idx] = entry
            else:
                # Add as new entry
                entries.append(entry)
                print(f"[SAVE] Added new entry, total entries: {len(entries)}")
                
            # Dump entry details for debugging
            for i, e in enumerate(entries):
                print(f"[SAVE] Entry {i}: ID={e.entry_id}, Client={e.client}")
            
            # Save all entries directly to file
            try:
                # Ensure the directory exists
                os.makedirs(self.data_file_path.parent, exist_ok=True)
                
                # Prepare the data structure
                print(f"[SAVE] Converting {len(entries)} entries to dictionary format")
                entry_dicts = []
                for e in entries:
                    try:
                        entry_dict = e.to_dict()
                        entry_dicts.append(entry_dict)
                        print(f"[SAVE] Converted entry: {entry_dict.get('entry_id')}")
                    except Exception as conv_err:
                        print(f"[SAVE ERROR] Failed to convert entry {e.entry_id}: {conv_err}")
                
                data = {'entries': entry_dicts}
                print(f"[SAVE] Final data structure has {len(entry_dicts)} entries")
                
                # Convert to JSON string
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                
                # First write to a temporary file to avoid corruption
                temp_file = self.data_file_path.with_suffix('.tmp')
                print(f"[SAVE] Writing to temporary file: {temp_file}")
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(json_str)
                
                # Verify temp file was created successfully
                if temp_file.exists() and temp_file.stat().st_size > 0:
                    print(f"[SAVE] Temporary file created successfully: {temp_file.stat().st_size} bytes")
                    # Now rename the temp file to the actual file
                    if self.data_file_path.exists():
                        # Create a backup of the existing file just in case
                        backup_file = self.data_file_path.with_suffix('.bak')
                        print(f"[SAVE] Creating backup of existing file: {backup_file}")
                        import shutil
                        shutil.copy2(self.data_file_path, backup_file)
                    
                    # Move the temp file to the actual file
                    import os
                    print(f"[SAVE] Moving temp file to actual file: {self.data_file_path}")
                    if self.data_file_path.exists():
                        os.remove(self.data_file_path)
                    os.rename(temp_file, self.data_file_path)
                else:
                    print(f"[SAVE ERROR] Temporary file creation failed")
                    raise IOError("Failed to create temporary file")
                
                print(f"[SAVE] Successfully saved {len(entries)} entries to {self.data_file_path}")
                print(f"[SAVE] File size: {len(json_str)} bytes")
                
                # Verify save
                if self.data_file_path.exists() and self.data_file_path.stat().st_size > 0:
                    print(f"[SAVE] Verified file exists with size: {self.data_file_path.stat().st_size} bytes")
                else:
                    print(f"[SAVE WARNING] File verification failed after save")
                
                # Emit signal that data has changed
                self.data_changed.emit()
                return True
            except Exception as save_err:
                print(f"[SAVE ERROR] Failed to save to file: {save_err}")
                traceback.print_exc()
                return False
        except Exception as e:
            print(f"[SAVE ERROR] Failed to process timesheet: {e}")
            traceback.print_exc()
            raise
    
    def _verify_save(self):
        """Verify that the data was saved correctly"""
        try:
            # Check if file exists
            if not self.data_file_path.exists():
                print(f"[VERIFY ERROR] Data file does not exist after save: {self.data_file_path}")
                return False
                
            # Check file size
            file_size = self.data_file_path.stat().st_size
            if file_size == 0:
                print(f"[VERIFY ERROR] Data file is empty: {self.data_file_path}")
                return False
                
            # Try to read the file and parse JSON
            with open(self.data_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                data = json.loads(content)
                entries_count = len(data.get('entries', []))
                print(f"[VERIFY] Successfully verified file: {self.data_file_path}, found {entries_count} entries")
                print(f"[VERIFY] First 100 chars of content: {content[:100]}...")
                return True
        except Exception as e:
            print(f"[VERIFY ERROR] Failed to verify save: {e}")
            traceback.print_exc()
            return False
            
    def _force_save_entries(self, entries):
        """Force save entries with multiple attempts"""
        # Try direct JSON serialization
        try:
            print(f"[FORCE SAVE] Forcing save of {len(entries)} entries to {self.data_file_path}")
            
            # Create data structure
            data = {'entries': [entry.to_dict() for entry in entries]}
            
            # Ensure the directory exists
            os.makedirs(self.data_file_path.parent, exist_ok=True)
            
            # Write directly with formatted JSON
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            with open(self.data_file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
                
            print(f"[FORCE SAVE] Successfully wrote {len(json_str)} bytes to {self.data_file_path}")
            
            # Emit signal
            self.data_changed.emit()
            return True
        except Exception as e:
            print(f"[FORCE SAVE ERROR] Failed to force save: {e}")
            traceback.print_exc()
            return False
    
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
                try:
                    # Handle different date formats
                    if "/" in entry.creation_date:
                        entry_date = datetime.datetime.strptime(entry.creation_date, "%Y/%m/%d")
                    else:
                        entry_date = datetime.datetime.strptime(entry.creation_date, "%Y-%m-%d")
                        
                    # Check if date is within range
                    if start <= entry_date <= end:
                        filtered_entries.append(entry)
                except ValueError:
                    # Skip entries with invalid dates
                    continue
        except ValueError:
            # Return empty list if date parsing fails
            return []
            
        return filtered_entries
