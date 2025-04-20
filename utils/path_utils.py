import os
from pathlib import Path

def get_app_root():
    """
    Get the root directory of the application.
    This helps in creating paths relative to the application root,
    which is important for cross-platform compatibility.
    """
    return Path(".")

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
    if subpath:
        return data_path / subpath
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
