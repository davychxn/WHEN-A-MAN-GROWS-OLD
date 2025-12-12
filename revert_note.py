import shutil
import re
import sys
from datetime import datetime
from pathlib import Path

# Add back_office/py to path for imports
sys.path.insert(0, str(Path(__file__).parent / "back_office" / "py"))
from file_filters import get_files_of_interest, get_next_serial_number, get_latest_folder_by_date


def get_latest_note_folder(notes_base, year_str, month_str):
    """Find the latest note folder for specified year and month."""
    month_folder = notes_base / year_str / month_str
    return get_latest_folder_by_date(month_folder)


def get_latest_backup_folder(backup_base):
    """Find the latest backup folder."""
    if not backup_base.exists():
        return None
    
    backup_folders = [f for f in backup_base.iterdir() if f.is_dir()]
    
    if not backup_folders:
        return None
    
    # Sort by name (YYYYMMDD_XXX format)
    backup_folders.sort(reverse=True)
    
    return backup_folders[0]


def extract_note_link_from_readme(readme_path, date_folder_name):
    """Extract and remove the note link from year's README."""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the link pattern for the date folder
    link_pattern = rf'\[_.*?\]\(\./\d{{2}}/{date_folder_name}/\)'
    
    # Search for the link
    match = re.search(link_pattern, content)
    
    if not match:
        return content, False
    
    # Get the line containing the match
    link_line = match.group(0)
    
    # Find the full line (including newline before and after)
    start_pos = match.start()
    
    # Find the start of the line (look backwards for newline)
    line_start = content.rfind('\n', 0, start_pos)
    if line_start == -1:
        line_start = 0
    else:
        line_start += 1  # Move past the newline
    
    # Find the end of the line (look forward for newline)
    line_end = content.find('\n', match.end())
    if line_end == -1:
        line_end = len(content)
    else:
        line_end += 1  # Include the newline
    
    # Check if there's a blank line before this entry
    check_pos = line_start - 1
    if check_pos > 0 and content[check_pos] == '\n':
        # Check if the line before the blank line is not a header
        prev_line_start = content.rfind('\n', 0, check_pos - 1)
        if prev_line_start != -1:
            prev_line = content[prev_line_start + 1:check_pos].strip()
            if not prev_line.startswith('##'):
                line_start = check_pos  # Include the blank line in removal
    
    # Remove the line
    new_content = content[:line_start] + content[line_end:]
    
    # Check if the month section is now empty and remove it
    # Find month headers
    month_pattern = r'## \w+'
    month_matches = list(re.finditer(month_pattern, new_content))
    
    for i, month_match in enumerate(month_matches):
        month_start = month_match.start()
        month_end = month_match.end()
        
        # Find the next section (next month or <br/>)
        if i + 1 < len(month_matches):
            next_section_start = month_matches[i + 1].start()
        else:
            next_section_start = new_content.find('\n<br/>', month_end)
            if next_section_start == -1:
                next_section_start = len(new_content)
        
        # Get the section content
        section_content = new_content[month_end:next_section_start].strip()
        
        # If section has no note entries, remove the entire month section
        if not any(line.strip().startswith('[_') for line in section_content.split('\n')):
            # Remove from month header to start of next section (including blank lines)
            new_content = new_content[:month_start] + new_content[next_section_start:]
            break
    
    return new_content, True


def remove_empty_directories(path):
    """Recursively remove empty directories."""
    if not path.exists() or not path.is_dir():
        return
    
    # First, try to remove empty subdirectories
    for item in path.iterdir():
        if item.is_dir():
            remove_empty_directories(item)
    
    # Then try to remove this directory if it's empty
    try:
        if not any(path.iterdir()):
            path.rmdir()
            print(f"  Removed empty directory: {item.relative_to(Path(__file__).parent)}")
    except:
        pass


def revert_note():
    """
    Revert the operations done by finish_note.py:
    1. If noting_area has content, archive it to back_office/drafts
    2. Find the latest note folder
    3. Copy its contents back to noting_area
    4. Restore the year README from backup (replace existing)
    5. Delete the note folder
    6. Delete the backup folder
    7. Clean up empty directories
    """
    base_dir = Path(__file__).parent
    noting_area = base_dir / "noting_area"
    notes_base = base_dir / "notes"
    backup_base = base_dir / "back_office" / "notes_backup" / "year_notes"
    drafts_folder = base_dir / "back_office" / "drafts"
    
    # Get current date
    now = datetime.now()
    year_str = now.strftime("%Y")
    month_str = now.strftime("%m")
    date_str = now.strftime("%Y%m%d")
    
    # Step 1: Archive noting_area contents if anything there (only files of interest)
    noting_area_contents = get_files_of_interest(noting_area)
    
    if noting_area_contents:
        print(f"Found {len(noting_area_contents)} item(s) in noting_area. Archiving to drafts...")
        
        # Get serial number and create draft folder
        serial = get_next_serial_number(drafts_folder, date_str)
        draft_folder_name = f"{date_str}_{serial:03d}"
        draft_folder_path = drafts_folder / draft_folder_name
        
        draft_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Created draft folder: {draft_folder_name}")
        
        # Copy contents to draft folder (only files of interest)
        for item in noting_area_contents:
            dest = draft_folder_path / item.name
            if item.is_file():
                shutil.copy2(item, dest)
                print(f"  Archived: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, dest)
                print(f"  Archived directory: {item.name}")
        
        # Clear noting_area (only files of interest)
        for item in noting_area_contents:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        print("Cleared noting_area")
    
    # Step 2: Find the latest note folder
    latest_note = get_latest_note_folder(notes_base, year_str, month_str)
    
    if not latest_note:
        print("No note found to revert.")
        return
    
    # Check if the note is within 24 hours - only revert recent notes
    try:
        # Parse the date from the folder name (YYYYMMDD format)
        note_date_str = latest_note.name
        note_date = datetime.strptime(note_date_str, "%Y%m%d")
        
        # Calculate time difference
        time_diff = now - note_date
        
        if time_diff.total_seconds() > 24 * 60 * 60:  # 24 hours in seconds
            print(f"Latest note ({note_date_str}) is older than 24 hours.")
            print("Only notes created within the last 24 hours can be reverted. Aborting.")
            return
    except ValueError:
        print(f"Could not parse date from folder name: {latest_note.name}. Aborting.")
        return
    
    print(f"Found latest note: {latest_note.relative_to(base_dir)}")
    
    # Step 3: Copy note contents back to noting_area (only files of interest)
    for item in latest_note.iterdir():
        # Only restore files of interest
        if item.name.lower() == "readme.md" or item.name.lower() == "assets":
            dest = noting_area / item.name
            if item.is_file():
                shutil.copy2(item, dest)
                print(f"  Restored: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, dest)
                print(f"  Restored directory: {item.name}")
    
    # Step 4: Restore the year README from backup
    latest_backup = get_latest_backup_folder(backup_base)
    
    if latest_backup:
        backup_readme = latest_backup / "README.md"
        year_readme = notes_base / year_str / "README.md"
        
        if backup_readme.exists():
            # Delete existing README and replace with backup
            if year_readme.exists():
                year_readme.unlink()
                print(f"Deleted current year README")
            
            shutil.copy2(backup_readme, year_readme)
            print(f"Restored year README from backup: {latest_backup.name}")
        
        # Step 5: Delete the backup folder
        shutil.rmtree(latest_backup)
        print(f"Deleted backup folder: {latest_backup.relative_to(base_dir)}")
    else:
        print("Warning: No backup found. Year README not restored.")
    
    # Step 6: Delete the note folder
    shutil.rmtree(latest_note)
    print(f"Deleted note folder: {latest_note.relative_to(base_dir)}")
    
    # Step 7: Clean up empty directories
    print("Cleaning up empty directories...")
    month_folder = notes_base / year_str / month_str
    remove_empty_directories(month_folder)
    
    year_folder = notes_base / year_str
    remove_empty_directories(year_folder)
    
    print("\n✅ Note reverted successfully!")


if __name__ == "__main__":
    revert_note()
