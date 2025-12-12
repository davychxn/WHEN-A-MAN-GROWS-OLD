import shutil
import sys
from datetime import datetime
from pathlib import Path

# Add back_office/py to path for imports
sys.path.insert(0, str(Path(__file__).parent / "back_office" / "py"))
from file_filters import get_files_of_interest, get_next_serial_number


def start_note():
    """
    Check noting_area folder, if anything there:
    1. Create a new folder in drafts with DATE_XXX format
    2. Copy contents from noting_area to the new folder
    3. Clear noting_area
    4. Copy template contents to noting_area
    """
    # Define paths
    base_dir = Path(__file__).parent
    noting_area = base_dir / "noting_area"
    drafts_folder = base_dir / "back_office" / "drafts"
    template_folder = base_dir / "back_office" / "template"
    
    # Check if noting_area has any contents (only README.md and assets folder)
    noting_area_contents = get_files_of_interest(noting_area)
    
    if not noting_area_contents:
        print("noting_area is empty. Nothing to archive.")
    else:
        print(f"Found {len(noting_area_contents)} item(s) in noting_area. Archiving...")
        
        # Get current date and serial number
        date_str = datetime.now().strftime("%Y%m%d")
        serial = get_next_serial_number(drafts_folder, date_str)
        new_folder_name = f"{date_str}_{serial:03d}"
        new_folder_path = drafts_folder / new_folder_name
        
        # Create new folder in drafts
        new_folder_path.mkdir(parents=True, exist_ok=True)
        print(f"Created folder: {new_folder_name}")
        
        # Copy contents from noting_area to new folder
        for item in noting_area_contents:
            dest = new_folder_path / item.name
            if item.is_file():
                shutil.copy2(item, dest)
                print(f"  Copied: {item.name}")
            elif item.is_dir():
                shutil.copytree(item, dest)
                print(f"  Copied directory: {item.name}")
        
        # Clear noting_area
        for item in noting_area_contents:
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)
        print("Cleared noting_area")
    
    # Copy template contents to noting_area
    template_contents = list(template_folder.iterdir())
    for item in template_contents:
        dest = noting_area / item.name
        if item.is_file():
            shutil.copy2(item, dest)
        elif item.is_dir():
            shutil.copytree(item, dest)
    
    print("\n✅ Good to go! Start writing your note for today.")


if __name__ == "__main__":
    start_note()
