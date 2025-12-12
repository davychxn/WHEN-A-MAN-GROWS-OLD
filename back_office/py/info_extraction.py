"""
Shared module for extracting information from notes.
"""
import re


def extract_weather_from_note(note_file):
    """
    Extract weather and temperature from the note file (line with ### after first image link).
    
    Args:
        note_file: Path to the note README.md file
        
    Returns:
        tuple: (temperature, weather) as strings
    """
    try:
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find first image link
        img_pattern = r'!\[.*?\]\(.*?\)'
        img_match = re.search(img_pattern, content)
        
        if img_match:
            # Find the ### line after the image
            after_img = content[img_match.end():]
            header_pattern = r'###\s+(.+)'
            header_match = re.search(header_pattern, after_img)
            
            if header_match:
                header_line = header_match.group(1).strip()
                # Parse: Date, Temperature, Weather, Location
                parts = [p.strip() for p in header_line.split(',')]
                if len(parts) >= 3:
                    temperature = parts[1]  # Temperature is the second part
                    weather = parts[2]      # Weather is the third part
                    return temperature, weather
        
        return "Inconnu", "Inconnu"
    except Exception as e:
        print(f"Warning: Could not extract weather/temperature: {e}")
        return "Inconnu", "Inconnu"


def extract_natural_info(note_file, max_length=45):
    """
    Extract natural information of the day from the note (first line with ### after picture).
    Truncates to max_length characters if needed.
    
    Args:
        note_file: Path to the note README.md file
        max_length: Maximum length of the returned string (default 40)
        
    Returns:
        str: Natural information line, truncated if necessary with "..." appended
    """
    try:
        with open(note_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find first image link (PICTURE OF THE DAY)
        img_pattern = r'!\[.*?\]\(.*?\)'
        img_match = re.search(img_pattern, content)
        
        if img_match:
            # Find the ### line after the image
            after_img = content[img_match.end():]
            header_pattern = r'###\s+(.+)'
            header_match = re.search(header_pattern, after_img)
            
            if header_match:
                info_line = header_match.group(1).strip()
                
                # Truncate if exceeds max_length
                if len(info_line) > max_length:
                    # Truncate to leave room for "..."
                    truncated = info_line[:max_length - 3].strip()
                    return f"{truncated}..."
                
                return info_line
        
        return "Information non disponible"
    except Exception as e:
        print(f"Warning: Could not extract natural info: {e}")
        return "Information non disponible"


def get_referenced_assets(readme_file):
    """
    Get list of asset files referenced in the README.md.
    
    Args:
        readme_file: Path to the README.md file
        
    Returns:
        set: Set of asset filenames that are referenced
    """
    try:
        with open(readme_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find all image and video references
        # Pattern for ![...](./assets/filename) and [![...](./assets/filename)]
        asset_pattern = r'!\[.*?\]\(./assets/([^)]+)\)'
        matches = re.findall(asset_pattern, content)
        
        return set(matches)
    except Exception as e:
        print(f"Warning: Could not read README for asset references: {e}")
        return set()


def get_french_weekday(date):
    """
    Get French weekday name.
    
    Args:
        date: datetime object
        
    Returns:
        str: French weekday name
    """
    french_days = {
        0: "Lundi",
        1: "Mardi",
        2: "Mercredi",
        3: "Jeudi",
        4: "Vendredi",
        5: "Samedi",
        6: "Dimanche"
    }
    return french_days[date.weekday()]


def get_french_date(date):
    """
    Get French date format without year (e.g., '2 Decembre').
    
    Args:
        date: datetime object
        
    Returns:
        str: French formatted date without year
    """
    french_months = {
        1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Aout",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Decembre"
    }
    return f"{date.day} {french_months[date.month]}"


def get_french_month(month_num):
    """
    Get French month name.
    
    Args:
        month_num: Month number (1-12)
        
    Returns:
        str: French month name
    """
    french_months = {
        1: "Janvier", 2: "Fevrier", 3: "Mars", 4: "Avril",
        5: "Mai", 6: "Juin", 7: "Juillet", 8: "Aout",
        9: "Septembre", 10: "Octobre", 11: "Novembre", 12: "Decembre"
    }
    return french_months[month_num]
