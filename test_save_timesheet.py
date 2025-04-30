"""
Test script to directly debug the timesheet saving functionality
"""
import os
import json
from pathlib import Path
import datetime
import traceback

def test_timesheet_save():
    """Direct test of timesheet saving to diagnose the issue"""
    # Target JSON file
    json_file = Path("data/timesheet/timesheet_entries.json")
    abs_path = json_file.absolute()
    print(f"Test saving to: {abs_path}")
    
    # Ensure the directory exists
    os.makedirs(json_file.parent, exist_ok=True)
    
    # Create a simple test timesheet
    timesheet = {
        'entry_id': f"TS-test-{datetime.datetime.now().strftime('%Y%m%d')}-01",
        'client': "Test Client Company",
        'work_type': "Regular Service",
        'tier': "Tier 1",
        'engineer_name': "Test",
        'engineer_surname': "Engineer",
        'creation_date': datetime.datetime.now().strftime("%Y/%m/%d"),
        'status': "draft",
        'time_entries': [
            {
                'date': datetime.datetime.now().strftime("%Y/%m/%d"),
                'start_time': "0900",
                'end_time': "1700",
                'rest_hours': 1,
                'description': "Test time entry",
                'overtime_rate': "Regular",
                'offshore': False,
                'travel_count': False,
                'travel_far_distance': False
            }
        ],
        'tool_usage': [
            {
                'tool_name': "Test Tool",
                'amount': 1,
                'start_date': datetime.datetime.now().strftime("%Y/%m/%d"),
                'end_date': datetime.datetime.now().strftime("%Y/%m/%d"),
                'total_days': 1
            }
        ],
        'report_description': "Test report",
        'report_hours': 1,
        'emergency_request': False,
        'currency': "THB",
        'service_hour_rate': 6500.0,
        'tool_usage_rate': 25000.0,
        'tl_rate_short': 2500.0,
        'tl_rate_long': 7500.0,
        'offshore_day_rate': 17500.0,
        'emergency_rate': 16000.0,
        'other_transport_charge': 0.0,
        'other_transport_note': "",
        'total_service_charge': 50000.0
    }
    
    # Test 1: Direct file reading
    print("\nStep 1: Reading existing file")
    try:
        if json_file.exists() and json_file.stat().st_size > 0:
            with open(json_file, 'r', encoding='utf-8') as f:
                current_data = json.load(f)
                entries = current_data.get('entries', [])
                print(f"Read {len(entries)} entries from file")
                print(f"First 100 chars: {json.dumps(current_data)[:100]}...")
        else:
            print("File doesn't exist or is empty, starting with empty data")
            current_data = {'entries': []}
    except Exception as e:
        print(f"Error reading file: {e}")
        traceback.print_exc()
        current_data = {'entries': []}
    
    # Test 2: Add our new entry
    print("\nStep 2: Adding new entry")
    try:
        # Check if an entry with this ID already exists
        entry_ids = [entry.get('entry_id') for entry in current_data.get('entries', [])]
        if timesheet['entry_id'] in entry_ids:
            # Replace the existing entry
            print(f"Entry with ID {timesheet['entry_id']} already exists, replacing")
            for i, entry in enumerate(current_data['entries']):
                if entry.get('entry_id') == timesheet['entry_id']:
                    current_data['entries'][i] = timesheet
                    break
        else:
            # Add as a new entry
            print(f"Adding new entry with ID: {timesheet['entry_id']}")
            current_data['entries'].append(timesheet)
        
        print(f"Data now has {len(current_data['entries'])} entries")
    except Exception as e:
        print(f"Error adding entry: {e}")
        traceback.print_exc()
    
    # Test 3: Write back to file
    print("\nStep 3: Writing to file")
    try:
        # Create a temp file first
        temp_file = json_file.with_suffix('.temp')
        print(f"Writing to temp file: {temp_file}")
        
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)
        
        print(f"Temp file created, size: {temp_file.stat().st_size} bytes")
        
        # Move temp file to actual file
        if json_file.exists():
            backup_file = json_file.with_suffix('.bak')
            print(f"Creating backup: {backup_file}")
            import shutil
            shutil.copy2(json_file, backup_file)
            
        print(f"Moving temp file to: {json_file}")
        import os
        if json_file.exists():
            os.remove(json_file)
        os.rename(temp_file, json_file)
        
        print(f"File saved successfully, size: {json_file.stat().st_size} bytes")
        
        # Verify the file contains the expected data
        with open(json_file, 'r', encoding='utf-8') as f:
            verify_data = json.load(f)
            verify_entries = verify_data.get('entries', [])
            print(f"Verified file contains {len(verify_entries)} entries")
            
            # Check if our entry is in there
            entry_found = False
            for entry in verify_entries:
                if entry.get('entry_id') == timesheet['entry_id']:
                    entry_found = True
                    print(f"Entry {timesheet['entry_id']} found in saved data")
                    break
            
            if not entry_found:
                print(f"WARNING: Entry {timesheet['entry_id']} NOT found in saved data!")
    except Exception as e:
        print(f"Error writing file: {e}")
        traceback.print_exc()
    
    print("\nTest completed")

if __name__ == "__main__":
    test_timesheet_save()
