"""
Traktor-specific utilities for collection management and parsing
"""
import os
import json
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

from config.settings import Settings
from utils.logger import get_logger

logger = get_logger(__name__)


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
        logger.error(f"Error parsing XML file: {e}")
        return 0


def parse_traktor_collection(collection_file_path: str, search_query: str, 
                           excluded_items: dict, max_songs: int, debug_mode: bool = False) -> Tuple[List[str], int]:
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
                  max_songs: int, debug_mode: bool = False) -> Tuple[List[str], int]:
    """
    Get newly added songs from the Traktor collection within the specified number of days.
    Returns a tuple of (formatted_results, total_new_songs).
    """
    if not os.path.exists(collection_file_path):
        if debug_mode:
            logger.warning(f"File not found: {collection_file_path}")
        return [f"File not found: {collection_file_path}"], 0
    
    try:
        tree = ET.parse(collection_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        if debug_mode:
            logger.error(f"Error parsing XML file: {e}")
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
            if debug_mode:
                logger.error(f"Error parsing date {import_date_str}: {ve}")
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
            
            if debug_mode:
                logger.debug(f"Adding song: {result_str}")
                
            results.append((import_date, artist, title, result_str))
            total_new_songs += 1
    
    if debug_mode:
        logger.debug(f"Total new songs added: {total_new_songs}")
    
    # Sort results by date (descending), then by artist and title
    results.sort(key=lambda x: (-x[0].timestamp(), x[1] if x[1] is not None else '', x[2] if x[2] is not None else ''))
    sorted_results = [result[3] for result in results[:max_songs]]
    
    if total_new_songs > max_songs:
        sorted_results.append(f"**Displaying latest {max_songs} songs of {total_new_songs} recently imported songs.**")
    
    if debug_mode:
        logger.debug(f"Sorted results: {sorted_results}")
    
    return sorted_results, total_new_songs


def convert_collection_xml_to_json(xml_file_path: str, json_file_path: str, excluded_items: Optional[dict] = None, debug_mode: bool = False) -> int:
    """
    Convert Traktor XML collection to optimized JSON format for faster searching.
    Returns the number of songs processed.
    """
    if not os.path.exists(xml_file_path):
        raise FileNotFoundError(f"XML file not found: {xml_file_path}")
    if excluded_items is None:
        excluded_items = Settings.EXCLUDED_ITEMS
    try:
        if debug_mode:
            logger.debug(f"🔄 Parsing XML file: {xml_file_path}")
        
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        songs = []
        processed_count = 0
        
        for entry in root.findall(".//COLLECTION/ENTRY"):
            location = entry.find(".//LOCATION")
            if location is None:
                continue
            file_path = location.get("FILE", "")
            dir_path = location.get("DIR", "")
            volume = location.get("VOLUME", "")
            # Exclude samples and unwanted items
            if (any(pattern in file_path for pattern in excluded_items['FILE']) or
                any(pattern in dir_path for pattern in excluded_items['DIR'])):
                continue
            # Compose full audio file path
            dir_clean = dir_path.replace(":", os.sep).replace("/", os.sep).replace("\\", os.sep).strip(os.sep)
            audio_file_path = os.path.join(volume + os.sep, dir_clean, file_path) if volume and dir_clean and file_path else ""
            
            artist = entry.get("ARTIST", "").strip()
            title = entry.get("TITLE", "").strip()
            
            # Get album information
            album_element = entry.find(".//ALBUM")
            album_title = album_element.get("TITLE", "").strip() if album_element is not None else ""
            
            # Get cover art ID, genre, and import date from INFO
            info = entry.find(".//INFO")
            genre = info.get("GENRE", "").strip() if info is not None else ""
            import_date = info.get("IMPORT_DATE", "") if info is not None else ""
            
            # Get BPM from TEMPO (as int)
            tempo = entry.find(".//TEMPO")
            bpm_str = tempo.get("BPM", "") if tempo is not None else ""
            try:
                bpm = int(float(bpm_str)) if bpm_str else None
            except ValueError:
                bpm = None
            
            # Get musical key from MUSICAL_KEY
            musical_key = entry.find(".//MUSICAL_KEY")
            key_value = musical_key.get("VALUE", "") if musical_key is not None else ""
            try:
                key = int(key_value) if key_value else None
            except ValueError:
                key = None
            
            # Create song record (no cover_art_id, no cover art path)
            song_record = {
                "artist": artist or "Unknown Artist",
                "title": title or "Unknown Title",
                "album": album_title,
                "import_date": import_date,
                "genre": genre,
                "bpm": bpm,
                "musical_key": key,
                "audio_file_path": audio_file_path
            }
            
            songs.append(song_record)
            processed_count += 1
            
            if debug_mode and processed_count % 1000 == 0:
                logger.debug(f"Processed {processed_count} songs...")
        
        # Write to JSON file
        if debug_mode:
            logger.debug(f"💾 Writing {len(songs)} songs to JSON: {json_file_path}")
            
        from utils.helpers import safe_write_json
        safe_write_json(json_file_path, songs)
        
        if debug_mode:
            logger.debug(f"✅ Successfully converted {processed_count} songs to JSON")
            
        return processed_count
        
    except ET.ParseError as e:
        raise ValueError(f"Error parsing XML file: {e}")
    except Exception as e:
        raise ValueError(f"Error converting XML to JSON: {e}")


def refresh_collection_json(original_traktor_path: str, json_file_path: str, excluded_items: dict, debug_mode: bool = False) -> int:
    """
    Complete refresh workflow: copy XML -> convert to JSON -> cleanup
    Returns the number of songs processed.
    """
    temp_xml_path = "collection_temp.nml"
    working_nml_path = "collection.nml"  # The .nml file that gets created in working directory
    
    try:
        logger.debug(f"Looking for Traktor collection at: {original_traktor_path}")

        # Step 1: Copy the original collection file to temp location
        logger.debug("Copying collection.nml to temporary file")
        shutil.copyfile(original_traktor_path, temp_xml_path)

        # Step 2: Convert XML to JSON
        logger.debug("Converting XML to JSON format")
        song_count = convert_collection_xml_to_json(temp_xml_path, json_file_path, excluded_items, debug_mode)
        logger.debug(f"Processed {song_count} tracks from collection")

        # Step 3: Clean up temporary XML file
        logger.debug("Cleaning up temporary files")
        if os.path.exists(temp_xml_path):
            os.remove(temp_xml_path)
            logger.debug("Removed temporary collection file")
          # Step 4: Clean up working directory .nml file if it exists
        # (This file sometimes gets created during processing and is no longer needed)
        if os.path.exists(working_nml_path):
            os.remove(working_nml_path)
            logger.debug("Removed working directory collection.nml file (no longer needed)")
        
        # Return count for caller to handle success messaging
        logger.debug(f"Collection refresh completed successfully: {song_count} songs processed")
        return song_count
        
    except Exception as e:
        logger.error(f"Collection import failed: {e}")
        # Clean up any temp files if they exist
        for cleanup_path in [temp_xml_path, working_nml_path]:
            if os.path.exists(cleanup_path):
                try:
                    os.remove(cleanup_path)
                    logger.debug(f"Cleaned up {cleanup_path} after error")
                except:
                    pass
        raise e


def load_collection_json(json_file_path: str) -> List[Dict[str, Any]]:
    """
    Load the collection JSON file.
    Returns the list of song records.
    """
    if not os.path.exists(json_file_path):
        logger.warning(f"Collection JSON file not found: {json_file_path}")
        return []
        
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Error loading collection JSON: {e}")
        return []


def search_collection_json(songs: List[Dict[str, Any]], search_query: str, max_songs: Optional[int] = None) -> Tuple[List[str], int]:
    """
    Search the JSON collection for songs matching the query.
    Returns a tuple of (formatted_results, total_matches).
    If max_songs is None or greater than matches found, returns all matches.
    """
    logger.debug(f"Searching for '{search_query}' in {len(songs)} songs")
    
    if not songs:
        logger.warning("No songs loaded in collection")
        return ["Collection not loaded"], 0
    
    results = []
    search_keywords = search_query.lower().split()
    
    songs_checked = 0
    matches_found = 0
    
    for song in songs:
        songs_checked += 1
        
        artist = song.get("artist", "").lower()
        title = song.get("title", "").lower()
        album = song.get("album", "").lower()
        
        # Determine priority and sort key
        priority_score = 0
        sort_key = ""
        
        if artist and all(keyword in artist for keyword in search_keywords):
            priority_score = 1
            sort_key = (artist, title)
        elif title and all(keyword in title for keyword in search_keywords):
            priority_score = 2
            sort_key = title
        elif album and all(keyword in album for keyword in search_keywords):
            priority_score = 3
            sort_key = (album, artist, title)
        
        if priority_score > 0:
            matches_found += 1
            # Escape markdown characters for Discord
            display_artist = song["artist"].replace('*', '\\*')
            display_title = song["title"].replace('*', '\\*') 
            display_album = song["album"].replace('*', '\\*') if song["album"] else None

            bpm_val = song.get("bpm")
            suffix_parts = []
            if bpm_val not in (None, "", []):
                suffix_parts.append(f"[{int(bpm_val)}]")
            if display_album:
                suffix_parts.append(f"[{display_album}]")

            result_core = f"{display_artist} - {display_title}"
            if suffix_parts:
                result_str = f"{result_core} | {' '.join(suffix_parts)}"
            else:
                result_str = result_core
            results.append((priority_score, sort_key, result_str))
    
    logger.debug(f"Search complete. Found {matches_found} matches out of {songs_checked} songs")
    
    # Sort results by priority and then by sort key
    results.sort(key=lambda x: (x[0], x[1]))
    
    # Format results for display - limit only if max_songs is specified and smaller than total
    limit = min(max_songs, len(results)) if max_songs is not None else len(results)
    sorted_results = [
        f"{i + 1} | {result[2]}" for i, result in enumerate(results[:limit])
    ]
    
    logger.debug(f"Returning {len(sorted_results)} formatted results out of {len(results)} total matches")
    return sorted_results, len(results)


def count_songs_in_collection_json(songs: List[Dict[str, Any]]) -> int:
    """Count the total number of songs in the JSON collection"""
    return len(songs)


def get_new_songs_json(songs: List[Dict[str, Any]], days: int, max_songs: int, debug_mode: bool = False) -> Tuple[List[str], int]:
    """
    Get newly added songs from the JSON collection within the specified number of days.
    Returns a tuple of (formatted_results, total_new_songs).
    """
    if not songs:
        return ["Collection not loaded"], 0
    
    results = []
    cutoff_date = datetime.now() - timedelta(days=days)
    total_new_songs = 0
    
    for song in songs:
        import_date_str = song.get("import_date", "")
        if not import_date_str:
            continue
            
        try:
            import_date = datetime.strptime(import_date_str, "%Y/%m/%d")
        except ValueError:
            if debug_mode:
                logger.error(f"Error parsing date {import_date_str}")
            continue
        
        if import_date >= cutoff_date:
            artist = song.get("artist", "Unknown Artist")
            title = song.get("title", "Unknown Title")
            album = song.get("album", "")
            
            # Escape markdown characters
            display_artist = artist.replace('*', '\\*')
            display_title = title.replace('*', '\\*')
            display_album = album.replace('*', '\\*') if album else None
            
            result_str = f"{import_date_str} | {display_artist} - {display_title} [{display_album}]" if display_album else f"{import_date_str} | {display_artist} - {display_title}"
            
            if debug_mode:
                logger.debug(f"Adding new song: {result_str}")
                
            results.append((import_date, artist, title, result_str))
            total_new_songs += 1
    
    if debug_mode:
        logger.debug(f"Total new songs found: {total_new_songs}")
    
    # Sort results by date (descending), then by artist and title
    results.sort(key=lambda x: (-x[0].timestamp(), x[1], x[2]))
    sorted_results = [result[3] for result in results[:max_songs]]
    
    if total_new_songs > max_songs:
        sorted_results.append(f"**Displaying latest {max_songs} songs of {total_new_songs} recently imported songs.**")
    
    if debug_mode:
        logger.debug(f"Sorted results: {sorted_results}")
    
    return sorted_results, total_new_songs


def get_collection_import_date(collection_file: str):
    """Get the modification date and time of the collection.json file."""
    try:
        if os.path.exists(collection_file):
            mod_time = os.path.getmtime(collection_file)
            dt = datetime.fromtimestamp(mod_time)
            date_str = dt.strftime("%Y-%m-%d")
            time_str = dt.strftime("%H:%M:%S")
            return date_str, time_str
        else:
            return "Not available", ""
    except Exception as e:
        logger.error(f"Error getting collection import date: {e}")
        return "Error", ""


def initialize_collection(traktor_path, collection_json_file, excluded_items, new_songs_days, max_songs, debug_mode=False):
    """
    Initialize the Traktor collection: refresh from .nml, load stats, and return results.
    Returns a dict with keys: success, total_songs, total_new_songs, date_str, time_str, error_msg
    """
    try:
        logger.info("🔄 Importing collection from Traktor...")
        logger.info("📁 Converting XML to optimized JSON format...")
        song_count = refresh_collection_json(
            traktor_path,
            collection_json_file,
            excluded_items,
            debug_mode=debug_mode
        )
        logger.info(f"✅ Collection imported successfully - {song_count:,} songs processed")
        songs = load_collection_json(collection_json_file)
        if songs:
            total_songs = count_songs_in_collection_json(songs)
            _, total_new_songs = get_new_songs_json(songs, new_songs_days, max_songs, debug_mode)
            date_str, time_str = get_collection_import_date(collection_json_file)
            return {
                "success": True,
                "total_songs": total_songs,
                "total_new_songs": total_new_songs,
                "date_str": date_str,
                "time_str": time_str,
                "error_msg": None
            }
        else:
            return {
                "success": False,
                "error_msg": "Collection JSON is empty or could not be loaded",
                "total_songs": 0,
                "total_new_songs": 0,
                "date_str": "Not available",
                "time_str": ""
            }
    except Exception as e:
        error_msg = f"Error initializing collection: {e}"
        logger.error(f"❌ {error_msg}")
        return {
            "success": False,
            "error_msg": error_msg,
            "total_songs": 0,
            "total_new_songs": 0,
            "date_str": "Error",
            "time_str": ""
        }