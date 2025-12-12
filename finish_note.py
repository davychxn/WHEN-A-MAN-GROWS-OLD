import shutil
import filecmp
import sys
from datetime import datetime
from pathlib import Path

# Add back_office/py to path for imports
sys.path.insert(0, str(Path(__file__).parent / "back_office" / "py"))
from file_filters import get_files_of_interest, get_next_serial_number
from info_extraction import (
    extract_weather_from_note,
    extract_natural_info,
    get_referenced_assets,
    get_french_weekday,
    get_french_month
)


def has_changes(noting_area, template_folder):
    """Check if noting_area has any changes compared to template."""
    # Only check files of interest
    noting_files = {item.name for item in get_files_of_interest(noting_area)}
    template_files = {item.name for item in get_files_of_interest(template_folder)}
    
    # If file lists differ, there are changes
    if noting_files != template_files:
        return True
    
    # Compare file contents for files of interest
    for item in get_files_of_interest(noting_area):
        noting_file = noting_area / item.name
        template_file = template_folder / item.name
        
        # Skip if not both files
        if not (noting_file.is_file() and template_file.is_file()):
            if noting_file.is_file() != template_file.is_file():
                return True
            continue
        
        # Compare files
        if not filecmp.cmp(noting_file, template_file, shallow=False):
            return True
    
    return False


def copy_with_asset_filter(noting_area, dest_folder):
    """Copy contents from noting_area to dest_folder, filtering unreferenced assets and only copying files of interest."""
    readme_file = noting_area / "README.md"
    referenced_assets = get_referenced_assets(readme_file) if readme_file.exists() else set()
    
    copied_count = 0
    skipped_count = 0
    
    # Only copy files of interest (README.md and assets folder)
    for item in get_files_of_interest(noting_area):
        dest = dest_folder / item.name
        
        if item.name.lower() == "assets" and item.is_dir():
            # Handle assets folder with filtering
            dest.mkdir(exist_ok=True)
            for asset_file in item.iterdir():
                if asset_file.name in referenced_assets:
                    shutil.copy2(asset_file, dest / asset_file.name)
                    print(f"  Copied asset: {asset_file.name}")
                    copied_count += 1
                else:
                    print(f"  Skipped unreferenced asset: {asset_file.name}")
                    skipped_count += 1
        elif item.is_file():
            shutil.copy2(item, dest)
            print(f"  Copied: {item.name}")
            copied_count += 1
        elif item.is_dir():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(item, dest)
            print(f"  Copied directory: {item.name}")
            copied_count += 1
    
    if skipped_count > 0:
        print(f"  Total skipped unreferenced assets: {skipped_count}")
    
    return copied_count


def update_year_readme(readme_path, new_note_link, date, temperature, weather):
    """Update the year's README.md with the new note link."""
    with open(readme_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    month_name = get_french_month(date.month)
    month_header = f"## {month_name}"
    
    # Get French weekday
    weekday = get_french_weekday(date)
    
    # Create the new link entry (with temperature and weather)
    new_entry = f"[_{date.day}, {weekday}, {temperature}, {weather}_]({new_note_link})"
    
    # Find the month header
    if month_header in content:
        # Find the position after the month header
        month_pos = content.find(month_header)
        # Find the next line after the header
        next_line_pos = content.find('\n', month_pos) + 1
        
        # Find the last note entry for this month (before next ## or <br/>)
        # Look for the last line starting with '[_' after the month header
        search_start = next_line_pos
        # Find where this month section ends (next ## or <br/>)
        next_section = len(content)
        next_month_pos = content.find('\n##', search_start)
        next_br_pos = content.find('\n<br/>', search_start)
        
        if next_month_pos != -1:
            next_section = min(next_section, next_month_pos)
        if next_br_pos != -1:
            next_section = min(next_section, next_br_pos)
        
        month_section = content[search_start:next_section]
        
        # Find all note entries in this section
        note_lines = [line for line in month_section.split('\n') if line.strip().startswith('[_')]
        
        if note_lines:
            # Find position after the last note entry
            last_note = note_lines[-1]
            last_note_pos = content.find(last_note, search_start)
            insert_pos = content.find('\n', last_note_pos) + 1
            # Add line break before new entry
            content = content[:insert_pos] + '\n' + new_entry + '\n' + content[insert_pos:]
        else:
            # No existing notes, insert right after month header with blank line
            content = content[:next_line_pos] + '\n' + new_entry + '\n' + content[next_line_pos:]
    else:
        # Month doesn't exist, need to add it before <br/>
        br_pos = content.find('\n<br/>')
        if br_pos != -1:
            content = content[:br_pos] + f"\n## {month_name}\n\n{new_entry}\n" + content[br_pos:]
        else:
            # Fallback: add at the end before disclaimer
            disclaimer_pos = content.find('### Images Copyrights Disclaimer')
            if disclaimer_pos != -1:
                content = content[:disclaimer_pos] + f"## {month_name}\n\n{new_entry}\n\n<br/>\n\n" + content[disclaimer_pos:]
            else:
                content += f"\n## {month_name}\n\n{new_entry}\n"
    
    # Write back
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(content)


def finish_note():
    """
    Main function to finish and archive the note.
    """
    base_dir = Path(__file__).parent
    noting_area = base_dir / "noting_area"
    template_folder = base_dir / "back_office" / "template"
    notes_base = base_dir / "notes"
    backup_base = base_dir / "back_office" / "notes_backup" / "year_notes"
    
    # Check if noting_area has changes
    if not has_changes(noting_area, template_folder):
        print("No changes detected in noting_area compared to template. Nothing to finish.")
        return
    
    print("Changes detected. Processing note...")
    
    # Get current date
    now = datetime.now()
    year_str = now.strftime("%Y")
    month_str = now.strftime("%m")
    date_str = now.strftime("%Y%m%d")
    
    # Create folder structure: notes/YEAR/MONTH/DATE
    year_folder = notes_base / year_str
    month_folder = year_folder / month_str
    date_folder = month_folder / date_str
    
    date_folder.mkdir(parents=True, exist_ok=True)
    print(f"Created note folder: {date_folder.relative_to(base_dir)}")
    
    # Copy contents from noting_area to new folder (with asset filtering)
    copy_with_asset_filter(noting_area, date_folder)
    
    # Extract weather, temperature, and natural info from the note
    note_readme = date_folder / "README.md"
    temperature, weather = extract_weather_from_note(note_readme) if note_readme.exists() else ("Inconnu", "Inconnu")
    natural_info = extract_natural_info(note_readme, max_length=40) if note_readme.exists() else "Information non disponible"
    
    print(f"Extracted temperature: {temperature}, weather: {weather}")
    print(f"Natural info: {natural_info}")
    
    # Clear noting_area
    for item in noting_area.iterdir():
        if item.is_file():
            item.unlink()
        elif item.is_dir():
            shutil.rmtree(item)
    print("Cleared noting_area")
    
    # Create backup folder: back_office/notes_backup/year_notes/DATE_XXX
    backup_serial = get_next_serial_number(backup_base, date_str)
    backup_folder_name = f"{date_str}_{backup_serial:03d}"
    backup_folder = backup_base / backup_folder_name
    backup_folder.mkdir(parents=True, exist_ok=True)
    print(f"Created backup folder: {backup_folder.relative_to(base_dir)}")
    
    # Copy year's README to backup
    year_readme = year_folder / "README.md"
    if year_readme.exists():
        backup_readme = backup_folder / "README.md"
        shutil.copy2(year_readme, backup_readme)
        print(f"Backed up year README to: {backup_readme.relative_to(base_dir)}")
    
    # Update year's README with new note link
    if year_readme.exists():
        relative_link = f"./{month_str}/{date_str}/"
        update_year_readme(year_readme, relative_link, now, temperature, weather)
        print(f"Updated year README with new note link")
    else:
        print("Warning: Year README not found, skipping update")
    
    print("\n✅ Note finished and archived successfully!")


if __name__ == "__main__":
    finish_note()
