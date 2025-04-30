"""
Test script to verify timesheet data saving functionality
"""
import os
import sys
from pathlib import Path
from modules.timesheet.models.timesheet_data import TimesheetDataManager, TimesheetEntry
from utils.path_utils import get_data_path

def main():
    # Create a test data file path
    data_file_path = get_data_path("timesheet/timesheet_entries.json")
    print(f"Test using data file: {data_file_path}")
    
    # Create the data manager
    manager = TimesheetDataManager(data_file_path)
    
    # Create a test entry
    test_entry = {
        'entry_id': 'TEST-ENTRY-001',
        'client': 'Test Client',
        'work_type': 'Test Work',
        'tier': 'Test Tier',
        'engineer_name': 'Test',
        'engineer_surname': 'Engineer',
        'creation_date': '2025/04/30',
        'time_entries': [
            {
                'date': '2025/04/30',
                'start_time': '0800',
                'end_time': '1700',
                'rest_hours': 1,
                'description': 'Test time entry',
                'overtime_rate': 'Regular',
                'offshore': False,
                'travel_count': False,
                'travel_far_distance': False
            }
        ],
        'tool_usage': [],
        'report_description': 'Test report',
        'report_hours': 0,
        'emergency_request': False,
        'currency': 'THB',
        'service_hour_rate': 6500.0,
        'tool_usage_rate': 25000.0,
        'tl_rate_short': 2500.0,
        'tl_rate_long': 7500.0,
        'offshore_day_rate': 17500.0,
        'emergency_rate': 16000.0,
        'other_transport_charge': 0.0,
        'other_transport_note': '',
        'total_service_charge': 52000.0
    }
    
    # Try to save the entry
    print("Saving test entry...")
    result = manager.save_timesheet(test_entry)
    print(f"Save result: {result}")
    
    # Try to read the file directly
    print("\nTrying to read file directly...")
    try:
        with open(data_file_path, 'r') as f:
            content = f.read()
            print(f"File content (first 100 chars): {content[:100]}...")
            print(f"File size: {len(content)} bytes")
    except Exception as e:
        print(f"Error reading file: {e}")
    
    # Try to load the entries
    print("\nLoading entries...")
    entries = manager.load_entries()
    print(f"Loaded {len(entries)} entries")
    
    if entries:
        print(f"First entry: ID={entries[0].entry_id}, Client={entries[0].client}")
    
    print("\nTest completed")

if __name__ == "__main__":
    main()
