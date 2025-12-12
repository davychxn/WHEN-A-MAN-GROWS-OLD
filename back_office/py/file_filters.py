"""
Shared module for filtering files of interest in noting_area.
"""
import os
from pathlib import Path


def is_file_of_interest(item):
    """
    Check if a file or folder is of interest for note operations.
    
    Args:
        item: A Path object representing a file or folder
        
    Returns:
        bool: True if the item is README.md or assets folder (case-insensitive)
    """
    return item.name.lower() == "readme.md" or item.name.lower() == "assets"


def get_files_of_interest(folder_path):
    """
    Get list of files/folders of interest from a given folder.
    
    Args:
        folder_path: A Path object representing the folder to scan
        
    Returns:
        list: List of Path objects for items of interest (README.md and assets folder)
    """
    return [
        item for item in folder_path.iterdir() 
        if is_file_of_interest(item)
    ]


def get_next_serial_number(base_folder, date_str):
    """
    Get the next incremental serial number for the given date.
    
    Args:
        base_folder: Path to the folder containing dated folders
        date_str: Date string in YYYYMMDD format
        
    Returns:
        int: Next available serial number (starts from 1)
    """
    if not os.path.exists(base_folder):
        return 1
    
    existing_folders = [f for f in os.listdir(base_folder) 
                       if os.path.isdir(os.path.join(base_folder, f)) 
                       and f.startswith(date_str)]
    
    if not existing_folders:
        return 1
    
    # Extract serial numbers from existing folders
    serials = []
    for folder in existing_folders:
        try:
            # Format: DATE_XXX where XXX is the serial number
            serial = int(folder.split('_')[1])
            serials.append(serial)
        except (IndexError, ValueError):
            continue
    
    return max(serials) + 1 if serials else 1


def get_latest_folder_by_date(base_folder):
    """
    Get the latest folder sorted by name (assuming YYYYMMDD format).
    
    Args:
        base_folder: Path object to search in
        
    Returns:
        Path object of the latest folder, or None if no folders found
    """
    if not base_folder.exists():
        return None
    
    # Get all folders that look like dates (8 digits)
    date_folders = [f for f in base_folder.iterdir() 
                   if f.is_dir() and f.name.isdigit() and len(f.name) == 8]
    
    if not date_folders:
        return None
    
    # Sort by name (YYYYMMDD format sorts correctly)
    date_folders.sort(reverse=True)
    
    return date_folders[0]

