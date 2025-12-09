import os
import shutil
import re
from datetime import datetime
from pathlib import Path


def get_latest_note_folder(notes_base, year_str, month_str):
    """Find the latest note folder for today or specified date."""
    month_folder = notes_base / year_str / month_str
    
    if not month_folder.exists():
        return None
    
    # Get all date folders and sort them
    date_folders = [f for f in month_folder.iterdir() if f.is_dir() and f.name.isdigit()]
    
    if not date_folders:
        return None
    
    # Sort by name (YYYYMMDD format sorts correctly)
    date_folders.sort(reverse=True)
    
    return date_folders[0]


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


def get_next_serial_number(drafts_folder, date_str):
    """Get the next incremental serial number for the given date."""
    if not drafts_folder.exists():
        return 1
    
    existing_folders = [f for f in drafts_folder.iterdir() 
                       if f.is_dir() and f.name.startswith(date_str)]
    
    if not existing_folders:
        return 1
    
    # Extract serial numbers from existing folders
    serials = []
    for folder in existing_folders:
        try:
            # Format: DATE_XXX where XXX is the serial number
            serial = int(folder.name.split('_')[1])
            serials.append(serial)
        except (IndexError, ValueError):
            continue
    
    return max(serials) + 1 if serials else 1


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
    
    # Step 1: Archive noting_area contents if anything there
    noting_area_contents = list(noting_area.iterdir())
    
    if noting_area_contents:
        print(f"Found {len(noting_area_contents)} item(s) in noting_area. Archiving to drafts...")
        
        # Get serial number and create draft folder
        serial = get_next_serial_number(drafts_folder, date_str)
        draft_folder_name = f"{date_str}_{serial:03d}"
        draft_folder_path = drafts_folder / draft_folder_name
        
        draft_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Created draft folder: {draft_folder_name}")
        
        # Copy contents to draft folder
        for item in noting_area_contents:
            dest = draft_folder_path / item.name
            if item.is_file():
                shutil.copy2(item, dest)
                print(f"  Archived: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, dest)
                print(f"  Archived directory: {item.name}")
        
        # Clear noting_area
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
    
    print(f"Found latest note: {latest_note.relative_to(base_dir)}")
    
    # Step 3: Copy note contents back to noting_area
    for item in latest_note.iterdir():
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
