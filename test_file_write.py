"""
Direct file writing test to verify JSON saving functionality
"""
import json
import os
from pathlib import Path

def test_direct_file_write():
    """Test direct file writing to the timesheet entries JSON file"""
    # Path to the timesheet entries JSON file
    file_path = Path("data/timesheet/timesheet_entries.json")
    abs_path = file_path.absolute()
    
    print(f"Testing file write to: {abs_path}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"File exists: {file_path.exists()}")
    
    # Create a test entry
    test_data = {
        "entries": [
            {
                "entry_id": "TEST-DIRECT-001",
                "client": "Direct Test Client",
                "creation_date": "2025/04/30",
                "status": "draft"
            }
        ]
    }
    
    # Ensure parent directory exists
    os.makedirs(file_path.parent, exist_ok=True)
    
    # Try different methods of writing to the file
    try:
        # Method 1: Using json.dump directly
        print("\nMethod 1: Using json.dump...")
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Verify file was written
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"File content (first 100 chars): {content[:100]}...")
                print(f"File size: {len(content)} bytes")
        else:
            print("File does not exist after Method 1 write!")
    except Exception as e:
        print(f"Error in Method 1: {e}")
    
    # Method 2: Write string first, then write to file
    try:
        print("\nMethod 2: Using string conversion...")
        json_str = json.dumps(test_data, indent=2)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(json_str)
        
        # Verify file was written
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                print(f"File content (first 100 chars): {content[:100]}...")
                print(f"File size: {len(content)} bytes")
        else:
            print("File does not exist after Method 2 write!")
    except Exception as e:
        print(f"Error in Method 2: {e}")
    
    # Method 3: Use a temporary file first
    try:
        print("\nMethod 3: Using a temporary file...")
        temp_path = Path("data/timesheet/temp_entries.json")
        
        # Write to temp file first
        with open(temp_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, indent=2)
        
        # Check if temp file was created
        if temp_path.exists():
            print(f"Temp file created: {temp_path}, size: {temp_path.stat().st_size} bytes")
            
            # Now move the temp file to the target file
            import shutil
            shutil.move(str(temp_path), str(file_path))
            
            # Verify file was written
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"File content (first 100 chars): {content[:100]}...")
                    print(f"File size: {len(content)} bytes")
            else:
                print("File does not exist after Method 3 write!")
        else:
            print("Temp file was not created!")
    except Exception as e:
        print(f"Error in Method 3: {e}")
    
    print("\nTest completed.")

if __name__ == "__main__":
    test_direct_file_write()
