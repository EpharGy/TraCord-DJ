"""
Traktor-specific utilities for collection management and parsing
"""
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional


def get_latest_traktor_folder(root_path: str) -> str:
    """
    Find the latest Traktor version folder in the given root path.
    Returns the full path to the latest version folder.
    """
    try:
        # Get all directories that start with "Traktor "
        traktor_dirs = [d for d in Path(root_path).iterdir() 
                       if d.is_dir() and d.name.startswith("Traktor ")]
        
        if not traktor_dirs:
            raise ValueError(f"No Traktor folders found in {root_path}")
            
        # Extract version numbers and pair them with paths
        version_paths = []
        for path in traktor_dirs:
            # Extract version number from folder name (e.g., "Traktor 4.2.0" -> "4.2.0")
            version = path.name.replace("Traktor ", "").strip("\\")
            # Split version into numeric components
            version_nums = [int(x) for x in version.split(".")]
            version_paths.append((version_nums, path))
            
        # Sort by version numbers (newest first)
        version_paths.sort(key=lambda x: x[0], reverse=True)
        
        # Return the path of the newest version
        return str(version_paths[0][1])
        
    except Exception as e:
        raise ValueError(f"Error finding latest Traktor folder: {e}")


def count_songs_in_collection(collection_file_path: str, excluded_items: dict) -> int:
    """Count the total number of songs in the Traktor collection, excluding filtered items"""
    if not os.path.exists(collection_file_path):
        return 0
    
    try:
        tree = ET.parse(collection_file_path)
        root = tree.getroot()
        count = 0
        
        for entry in root.findall(".//COLLECTION/ENTRY"):
            location = entry.find(".//LOCATION")
            if location is None:
                continue
                
            file_path = location.get("FILE", "")
            dir_path = location.get("DIR", "")
            
            # Skip if it's an excluded item
            if (any(pattern in file_path for pattern in excluded_items['FILE']) or
                any(pattern in dir_path for pattern in excluded_items['DIR'])):
                continue
                
            count += 1
        return count
        
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return 0


def parse_traktor_collection(collection_file_path: str, search_query: str, 
                           excluded_items: dict, max_songs: int, debug: bool = False) -> Tuple[List[str], int]:
    """
    Parse the Traktor collection file and search for songs matching the query.
    Returns a tuple of (formatted_results, total_matches).
    """
    if not os.path.exists(collection_file_path):
        return [f"File not found: {collection_file_path}"], 0
        
    try:
        tree = ET.parse(collection_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return [f"Error parsing XML file: {e}"], 0
    
    results = []
    search_keywords = search_query.lower().split()
    
    for entry in root.findall(".//COLLECTION/ENTRY"):
        location = entry.find(".//LOCATION")
        if location is None:
            continue
            
        file_path = location.get("FILE", "")
        dir_path = location.get("DIR", "")
        
        # Skip excluded items
        if (any(pattern in file_path for pattern in excluded_items['FILE']) or
            any(pattern in dir_path for pattern in excluded_items['DIR'])):
            continue
        
        artist = entry.get("ARTIST")
        title = entry.get("TITLE")
        album_element = entry.find(".//ALBUM")
        album_title = album_element.get("TITLE") if album_element is not None else None
        
        # Determine priority and sort key
        priority_score = 0
        sort_key = ""
        
        if artist and all(keyword in artist.lower() for keyword in search_keywords):
            priority_score = 1
            sort_key = (artist.lower(), title.lower() if title else "")
        elif title and all(keyword in title.lower() for keyword in search_keywords):
            priority_score = 2
            sort_key = title.lower()
        elif album_title and all(keyword in album_title.lower() for keyword in search_keywords):
            priority_score = 3
            sort_key = (album_title.lower(), artist.lower() if artist else "", title.lower() if title else "")
        
        if priority_score > 0:
            # Escape markdown characters
            artist = artist.replace('*', '\\*') if artist else "Unknown Artist"
            title = title.replace('*', '\\*') if title else "Unknown Title"
            album_title = album_title.replace('*', '\\*') if album_title else None
            
            result_str = f"{artist} - {title} [{album_title}]" if album_title else f"{artist} - {title}"
            results.append((priority_score, sort_key, result_str))
    
    # Sort results by priority and then by sort key
    results.sort(key=lambda x: (x[0], x[1]))
    
    # Format results for display
    sorted_results = [
        f"{i + 1} | {result[2].replace('_', '')}" for i, result in enumerate(results[:max_songs])
    ]
    
    if len(results) > max_songs:
        sorted_results.append(
            f"**{max_songs} of {len(results)} matches found for {search_query}, please refine your search if needed.**"
        )
    
    return sorted_results, len(results)


def get_new_songs(collection_file_path: str, days: int, excluded_items: dict, 
                  max_songs: int, debug: bool = False) -> Tuple[List[str], int]:
    """
    Get newly added songs from the Traktor collection within the specified number of days.
    Returns a tuple of (formatted_results, total_new_songs).
    """
    if not os.path.exists(collection_file_path):
        if debug:
            print(f"File not found: {collection_file_path}")
        return [f"File not found: {collection_file_path}"], 0
    
    try:
        tree = ET.parse(collection_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        if debug:
            print(f"Error parsing XML file: {e}")
        return [f"Error parsing XML file: {e}"], 0
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    total_new_songs = 0
    
    for entry in root.findall(".//COLLECTION/ENTRY"):
        location = entry.find(".//LOCATION")
        if location is None:
            continue
            
        file_path = location.get("FILE", "")
        dir_path = location.get("DIR", "")
        
        # Skip excluded items
        if (any(pattern in file_path for pattern in excluded_items['FILE']) or
            any(pattern in dir_path for pattern in excluded_items['DIR'])):
            continue
        
        info = entry.find(".//INFO")
        if info is None:
            continue
            
        import_date_str = info.get("IMPORT_DATE")
        if import_date_str is None:
            continue
        
        try:
            import_date = datetime.strptime(import_date_str, "%Y/%m/%d")
        except ValueError as ve:
            if debug:
                print(f"Error parsing date {import_date_str}: {ve}")
            continue
        
        if import_date >= cutoff_date:
            artist = entry.get("ARTIST") or "Unknown Artist"
            title = entry.get("TITLE") or "Unknown Title"
            album_element = entry.find(".//ALBUM")
            album_title = album_element.get("TITLE") if album_element is not None else None
            
            # Escape markdown characters
            artist = artist.replace('*', '\\*') if artist else artist
            title = title.replace('*', '\\*') if title else title
            album_title = album_title.replace('*', '\\*') if album_title else album_title
            
            result_str = f"{import_date_str} | {artist} - {title} [{album_title}]" if album_title else f"{import_date_str} | {artist} - {title}"
            
            if debug:
                print(f"Adding song: {result_str}")
                
            results.append((import_date, artist, title, result_str))
            total_new_songs += 1
    
    if debug:
        print(f"Total new songs added: {total_new_songs}")
    
    # Sort results by date (descending), then by artist and title
    results.sort(key=lambda x: (-x[0].timestamp(), x[1] if x[1] is not None else '', x[2] if x[2] is not None else ''))
    sorted_results = [result[3] for result in results[:max_songs]]
    
    if total_new_songs > max_songs:
        sorted_results.append(f"**Displaying latest {max_songs} songs of {total_new_songs} recently imported songs.**")
    
    if debug:
        print(f"Sorted results: {sorted_results}")
    
    return sorted_results, total_new_songs
