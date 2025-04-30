"""
Direct fix for timesheet saving issues
"""
import sys
import os
import json
from pathlib import Path

def fix_timesheet_save():
    """Fix the timesheet saving functionality"""
    # Path to the JSON file
    file_path = Path("data/timesheet/timesheet_entries.json")
    
    print(f"Checking file: {file_path.absolute()}")
    
    # Ensure directory exists
    os.makedirs(file_path.parent, exist_ok=True)
    
    # Create a simple test entry
    test_entry = {
        "entry_id": "TS-FIXED-20250430-01",
        "client": "Fix Test Client",
        "work_type": "Regular Service",
        "tier": "Tier 1",
        "created_by": "",
        "engineer_name": "Fix Test",
        "engineer_surname": "Engineer",
        "creation_date": "2025/04/30",
        "status": "draft",
        "time_entries": [
            {
                "date": "2025/04/30",
                "start_time": "0900",
                "end_time": "1700",
                "rest_hours": 1,
                "description": "Fix test time entry",
                "overtime_rate": "Regular",
                "offshore": False,
                "travel_count": False,
                "travel_far_distance": False
            }
        ],
        "tool_usage": [],
        "report_description": "Fix test report",
        "report_hours": 0,
        "emergency_request": False,
        "currency": "THB",
        "service_hour_rate": 6500.0,
        "tool_usage_rate": 25000.0,
        "tl_rate_short": 2500.0,
        "tl_rate_long": 7500.0,
        "offshore_day_rate": 17500.0,
        "emergency_rate": 16000.0,
        "other_transport_charge": 0.0,
        "other_transport_note": "",
        "total_service_charge": 52000.0
    }
    
    # Load existing data
    existing_entries = []
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                existing_entries = data.get('entries', [])
                print(f"Loaded {len(existing_entries)} existing entries")
        else:
            print("File doesn't exist, creating new file")
    except Exception as e:
        print(f"Error loading existing file: {e}")
        print("Will create new file with empty entries")
    
    # Append our test entry
    existing_entries.append(test_entry)
    print(f"Added test entry, now have {len(existing_entries)} entries")
    
    # Save back to file
    try:
        data = {'entries': existing_entries}
        
        # WRITE TO FILE
        print(f"Writing to file: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"File saved, size: {file_path.stat().st_size} bytes")
        
        # Verify
        if file_path.exists():
            print(f"File exists after save: {file_path}")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"Content (first 100 chars): {content[:100]}...")
                print(f"File size: {len(content)} bytes")
                
                # Parse the content to verify it's valid JSON
                data = json.loads(content)
                print(f"Verified: contains {len(data.get('entries', []))} entries")
                
                # Check if our test entry is in there
                for entry in data.get('entries', []):
                    if entry.get('entry_id') == test_entry['entry_id']:
                        print(f"Test entry found in file!")
                        break
                else:
                    print("WARNING: Test entry not found in file!")
        else:
            print("ERROR: File doesn't exist after save!")
            
    except Exception as e:
        print(f"Error saving file: {e}")
        import traceback
        traceback.print_exc()
    
    print("\nFix complete")

if __name__ == "__main__":
    fix_timesheet_save()
