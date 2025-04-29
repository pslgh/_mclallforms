import os
import sys
from pathlib import Path

def get_app_root():
    """
    Get the root directory of the application.
    This helps in creating paths relative to the application root,
    which is important for cross-platform compatibility.
    """
    # Return the absolute path to the app root directory
    # This ensures file operations work regardless of where the app is run from
    return Path(os.path.abspath(os.path.dirname(sys.argv[0])))

def ensure_directory(directory_path):
    """
    Ensure that a directory exists, creating it if necessary.
    
    Args:
        directory_path: The path to check/create, can be string or Path
    
    Returns:
        Path object for the directory
    """
    path = Path(directory_path)
    os.makedirs(path, exist_ok=True)
    return path

def get_data_path(subpath=None):
    """
    Get the path to the data directory.
    
    Args:
        subpath: Optional subdirectory or file within the data directory
        
    Returns:
        Path object for the requested data location
    """
    data_path = get_app_root() / "data"
    
    # Ensure the data directory exists
    os.makedirs(data_path, exist_ok=True)
    
    if subpath:
        # If a subpath is provided, ensure its parent directory exists
        full_path = data_path / subpath
        os.makedirs(full_path.parent, exist_ok=True)
        return full_path
    
    return data_path

def get_resource_path(subpath=None):
    """
    Get the path to a resource file (images, icons, etc.)
    
    Args:
        subpath: Optional subdirectory or file within the resources
        
    Returns:
        Path object for the requested resource
    """
    # Use 'assets' for now, but prepare for possible migration to 'resources'
    resource_path = get_app_root() / "assets"
    if subpath:
        return resource_path / subpath
    return resource_path
