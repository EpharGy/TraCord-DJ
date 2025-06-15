##############################
# Packages
import os
import shutil
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import asyncio
from datetime import datetime, timedelta
import json
from pathlib import Path
import re

##############################
# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TRAKTOR_LOCATION = os.getenv('TRAKTOR_LOCATION')
TRAKTOR_COLLECTION_FILENAME = os.getenv('TRAKTOR_COLLECTION_FILENAME')
APPLICATION_ID = os.getenv('APPLICATION_ID')
CHANNEL_IDS_ENV = os.getenv('CHANNEL_IDS')
ALLOWED_USER_IDS_ENV = os.getenv('ALLOWED_USER_IDS')
NOWPLAYING_CONFIG_JSON_PATH = os.getenv('NOWPLAYING_CONFIG_JSON_PATH')
SONG_REQUESTS_FILE = os.path.join(os.getcwd(), os.getenv('SONG_REQUESTS_FILE') or 'song_requests.json')
DISCORD_LIVE_NOTIFICATION_ROLES = os.getenv('DISCORD_LIVE_NOTIFICATION_ROLES')

##############################
# Define the variables for the number of returned songs and new songs days
MAX_SONGS = 20
NEW_SONGS_DAYS = 7
DEBUG = False
TIMEOUT = 45.0
EXCLUDED_ITEMS = {
    'FILE': ['.stem.'],
    'DIR': [':ContentImport/', ':Samples/']
}


##############################
# Split Applicable Variables if multiple
CHANNEL_IDS: list[int] = [int(id) for id in CHANNEL_IDS_ENV.split(',')] if CHANNEL_IDS_ENV else []
ALLOWED_USER_IDS: list[int] = [int(id) for id in ALLOWED_USER_IDS_ENV.split(',')] if ALLOWED_USER_IDS_ENV else []

# Split Live Notification Roles if multiple (optional)
DISCORD_LIVE_NOTIFICATION_ROLES = [role.strip() for role in DISCORD_LIVE_NOTIFICATION_ROLES.split(',')] if DISCORD_LIVE_NOTIFICATION_ROLES else []

##############################
# Check if all environment variables are loaded
required_env_vars = [TOKEN, TRAKTOR_LOCATION, TRAKTOR_COLLECTION_FILENAME, APPLICATION_ID, NOWPLAYING_CONFIG_JSON_PATH, SONG_REQUESTS_FILE]
if any(var is None for var in required_env_vars):
    raise ValueError("One or more required environment variables are missing.")


##############################
# Definitions
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

# Get the full path to the latest Traktor collection file
try:
    if not TRAKTOR_LOCATION or not TRAKTOR_COLLECTION_FILENAME:
        raise ValueError("TRAKTOR_LOCATION and TRAKTOR_COLLECTION_FILENAME must be set")
    latest_traktor_folder = get_latest_traktor_folder(TRAKTOR_LOCATION)
    TRAKTOR_PATH = os.path.join(latest_traktor_folder, TRAKTOR_COLLECTION_FILENAME)
    if not os.path.exists(TRAKTOR_PATH):
        raise ValueError(f"Collection file not found: {TRAKTOR_PATH}")
except Exception as e:
    print(f"Error setting up Traktor path: {e}")
    raise

def check_permissions(user_id, allowed_user_ids):
    return user_id in allowed_user_ids

def count_songs_in_collection(copied_file_path):
    if not os.path.exists(copied_file_path):
        return 0
    try:
        tree = ET.parse(copied_file_path)
        root = tree.getroot()
        count = 0
        for entry in root.findall(".//COLLECTION/ENTRY"):
            location = entry.find(".//LOCATION")
            if location is None:
                continue
            file_path = location.get("FILE", "")
            dir_path = location.get("DIR", "")
            # Skip if it's an excluded item
            if (any(pattern in file_path for pattern in EXCLUDED_ITEMS['FILE']) or
                any(pattern in dir_path for pattern in EXCLUDED_ITEMS['DIR'])):
                continue
            count += 1
        return count
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return 0

##############################
# Create a bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)

##############################
# Command - srbtraktorrefresh - Refresh the Traktor collection file
@bot.tree.command(name="srbtraktorrefresh", description="Refresh the Traktor collection file")
async def srbtraktorrefresh(interaction: discord.Interaction):
    if not check_permissions(interaction.user.id, ALLOWED_USER_IDS):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    try:
        # Copy the Traktor collection file to the current directory with the correct filename
        copied_file_path = os.path.join(os.getcwd(), "collection.nml")
        shutil.copyfile(TRAKTOR_PATH, copied_file_path)
        
        # Count the number of songs in the collection
        song_count = count_songs_in_collection(copied_file_path)
        
        # Count the number of new songs
        new_songs, total_new_songs = get_new_songs(copied_file_path, NEW_SONGS_DAYS)
        
        print(f"{interaction.user} triggered Collection update. Total number of songs: {song_count}")
        print(f"{total_new_songs} songs classed as new (added in the last {NEW_SONGS_DAYS} days)")
        await interaction.response.send_message(
            f"Traktor collection file copied successfully.\n"
            f"Total number of songs in the collection: {song_count}.\n"
            f"Total number of songs added in the last {NEW_SONGS_DAYS} days: {total_new_songs}"
        )
    except Exception as e:
        print(f"{interaction.user} triggered a Collection update, but there was an error copying file")
        await interaction.response.send_message(f"Error copying file: {e}", ephemeral=True)

##############################
# Command - srbnew - Display newly added songs from the last {NEW_SONGS_DAYS}
@bot.tree.command(name="srbnew", description=f"Display newly added songs from the last {NEW_SONGS_DAYS}")
@app_commands.describe(days=f"Number of days to look back for new songs (default is {NEW_SONGS_DAYS} days)")
async def srbnew(interaction: discord.Interaction, days: int = NEW_SONGS_DAYS):
    if not interaction.channel or not CHANNEL_IDS or interaction.channel.id not in CHANNEL_IDS:
        await interaction.response.send_message("This command can only be used in the designated channels.", ephemeral=True)
        return
    
    await interaction.response.send_message(f"Displaying songs from the last {days} days.")
    
    copied_file_path = os.path.join(os.getcwd(), "collection.nml")
    results, total_new_songs = get_new_songs(copied_file_path, days)
    
    if DEBUG:
        print(f"Total new songs found: {total_new_songs}")
        print(f"Results: {results}")
    
    if results:
        response = "\n".join(results)
        # Ensure the message length doesn't exceed Discord's limit
        if len(response) > 2000:
            response = response[:1997] + "..."
        await interaction.followup.send(response)
        print(f"{interaction.user} requested new songs from the last {days} days, found {total_new_songs} songs")
    else:
        await interaction.followup.send("No new songs found.")
        print(f"{interaction.user} requested new songs from the last {days} days, found 0 songs")

def get_new_songs(copied_file_path, days):
    if not os.path.exists(copied_file_path):
        if DEBUG:
            print(f"File not found: {copied_file_path}")
        return [f"File not found: {copied_file_path}"], 0
    try:
        tree = ET.parse(copied_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        if DEBUG:
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
        if (any(pattern in file_path for pattern in EXCLUDED_ITEMS['FILE']) or
            any(pattern in dir_path for pattern in EXCLUDED_ITEMS['DIR'])):
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
            if DEBUG:
                print(f"Error parsing date {import_date_str}: {ve}")
            continue
        if import_date >= cutoff_date:
            artist = entry.get("ARTIST") or "Unknown Artist"
            title = entry.get("TITLE") or "Unknown Title"
            album_element = entry.find(".//ALBUM")
            album_title = album_element.get("TITLE") if album_element is not None else None
            artist = artist.replace('*', '\\*') if artist else artist
            title = title.replace('*', '\\*') if title else title
            album_title = album_title.replace('*', '\\*') if album_title else album_title
            result_str = f"{import_date_str} | {artist} - {title} [{album_title}]" if album_title else f"{import_date_str} | {artist} - {title}"
            if DEBUG:
                print(f"Adding song: {result_str}")
            results.append((import_date, artist, title, result_str))
            total_new_songs += 1
    if DEBUG:
        print(f"Total new songs added: {total_new_songs}")
    # Sort results by date (descending), then by artist (ascending), then by title (ascending)
    results.sort(key=lambda x: (-x[0].timestamp(), x[1] if x[1] is not None else '', x[2] if x[2] is not None else ''))
    sorted_results = [result[3] for result in results[:MAX_SONGS]]
    if total_new_songs > MAX_SONGS:
        sorted_results.append(f"**Displaying latest {MAX_SONGS} songs of {total_new_songs} recently imported songs.**")
    if DEBUG:
        print(f"Sorted results: {sorted_results}")
    return sorted_results, total_new_songs

##############################
# Command - srbnpclear - Backup and clear track history in NowPlaying config.json
@bot.tree.command(name="srbnpclear", description="Backup and clear track history in NowPlaying config.json")
async def srbnpclear(interaction: discord.Interaction):
    if not NOWPLAYING_CONFIG_JSON_PATH:
        await interaction.response.send_message("Config file path not set in environment variable NOWPLAYING_CONFIG_JSON_PATH.", ephemeral=True)
        return

    if not check_permissions(interaction.user.id, ALLOWED_USER_IDS):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    try:
        # Backup config.json
        backup_path = NOWPLAYING_CONFIG_JSON_PATH + ".bak"
        shutil.copyfile(NOWPLAYING_CONFIG_JSON_PATH, backup_path)

        # Load config.json
        with open(NOWPLAYING_CONFIG_JSON_PATH, "r", encoding="utf-8") as file:
            config = json.load(file)

        # Clear specific fields in currentTrack
        for field in ["title", "artist", "comment", "label", "album", "artwork"]:
            config["currentTrack"][field] = ""

        # Clear specific fields in playlistHistory
        for track in config["playlistHistory"]:
            for field in ["title", "artist", "comment", "label", "album", "artwork"]:
                track[field] = ""

        # Save modified config.json
        with open(NOWPLAYING_CONFIG_JSON_PATH, "w", encoding="utf-8") as file:
            json.dump(config, file, indent=4)

        await interaction.response.send_message("NowPlaying Track history cleared.")
        print(f"{interaction.user} cleared NowPlaying History")
    except Exception as e:
        await interaction.response.send_message(f"Error clearing NowPlaying History: {e}")
        print(f"Error clearing NowPlaying History")

##############################
# Command - song - Search for a song in the Traktor collection and optionally select one.
@bot.tree.command(name="song", description="Search for a song in the Traktor collection and optionally select one by replying.")
@app_commands.describe(search="search query")
async def song(interaction: discord.Interaction, search: str):
    if not interaction.channel or not CHANNEL_IDS or interaction.channel.id not in CHANNEL_IDS:
        await interaction.response.send_message("This command can only be used in the designated channels.", ephemeral=True)
        return

    copied_file_path = os.path.join(os.getcwd(), "collection.nml")
    results, total_matches = parse_traktor_collection(copied_file_path, search)

    if not results:
        await interaction.response.send_message("No matching results found.")
        print(f"{interaction.user}'s search '{search}' matched 0 songs")
        return

    # Limit the results to MAX_SONGS for display
    displayed_results = results[:MAX_SONGS]
    instruction_message = "\n\nTo request a song, immediately REPLY with the # of the song, e.g. 6."
    results_message = "Search Results:\n" + "\n".join(displayed_results) + instruction_message

    # Add a note if there are more matches than MAX_SONGS
    if len(results) > MAX_SONGS:
        results_message += f"\n\n**{MAX_SONGS} of {total_matches} matches displayed. Refine your search if needed.**"

    await interaction.response.send_message(results_message)
    print(f"{interaction.user}'s search '{search}' matched {total_matches} songs")

    # Store only the displayed results in the result_dict
    result_dict = {str(i + 1): result.split(" | ", 1)[1] for i, result in enumerate(displayed_results)}

    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel and m.content in result_dict.keys()

    try:
        # Wait for user input with a timeout
        msg = await bot.wait_for("message", timeout=TIMEOUT, check=check)
        selected_song = result_dict[msg.content]

        # Save the selected song request to a JSON file
        if SONG_REQUESTS_FILE:
            try:
                # Load existing requests or initialize an empty list
                if os.path.exists(SONG_REQUESTS_FILE):
                    with open(SONG_REQUESTS_FILE, "r", encoding="utf-8") as file:
                        try:
                            song_requests = json.load(file)
                        except json.JSONDecodeError:
                            song_requests = []  # Start fresh if JSON is invalid
                else:
                    song_requests = []

                # Determine the next request number
                next_request_num = len(song_requests) + 1

                # Get the current system date and time
                current_time = datetime.now().strftime("%Y-%m-%d")

                # Construct request object
                new_request = {
                    "RequestNumber": next_request_num,
                    "Date": current_time,
                    "User": str(interaction.user),
                    "Song": selected_song
                }

                # Append the new request to the list
                song_requests.append(new_request)

                # Save back to the JSON file
                with open(SONG_REQUESTS_FILE, "w", encoding="utf-8") as file:
                    json.dump(song_requests, file, indent=4)

                print(f"{interaction.user} selected and saved the song: {selected_song}")
                await interaction.followup.send(f"Added the song to the Song Request List: {selected_song}")
            except Exception as e:
                print(f"Error saving song request: {e}")
    except asyncio.TimeoutError:
        # await interaction.followup.send("No song selected.")
        print(f"{interaction.user} did not respond in time for song selection.")
    except KeyError:
        await interaction.followup.send("Invalid input for song selection.")
        print(f"{interaction.user} entered invalid input for song selection.")

def parse_traktor_collection(copied_file_path, search_query):
    if not os.path.exists(copied_file_path):
        return [f"File not found: {copied_file_path}"]
    try:
        tree = ET.parse(copied_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return [f"Error parsing XML file: {e}"]
    
    results = []
    search_keywords = search_query.lower().split()
    
    for entry in root.findall(".//COLLECTION/ENTRY"):
        location = entry.find(".//LOCATION")
        if location is None:
            continue
        file_path = location.get("FILE", "")
        dir_path = location.get("DIR", "")
        if (any(pattern in file_path for pattern in EXCLUDED_ITEMS['FILE']) or
            any(pattern in dir_path for pattern in EXCLUDED_ITEMS['DIR'])):
            continue
        
        artist = entry.get("ARTIST")
        title = entry.get("TITLE")
        album_element = entry.find(".//ALBUM")
        album_title = album_element.get("TITLE") if album_element is not None else None
        
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
            artist = artist.replace('*', '\\*') if artist else "Unknown Artist"
            title = title.replace('*', '\\*') if title else "Unknown Title"
            album_title = album_title.replace('*', '\\*') if album_title else None
            
            result_str = f"{artist} - {title} [{album_title}]" if album_title else f"{artist} - {title}"
            results.append((priority_score, sort_key, result_str))
    
    results.sort(key=lambda x: (x[0], x[1]))
    
    sorted_results = [
        f"{i + 1} | {result[2].replace('_', '')}" for i, result in enumerate(results[:MAX_SONGS])
    ]
    if len(results) > MAX_SONGS:
        sorted_results.append(
            f"**{MAX_SONGS} of {len(results)} matches found for {search_query}, please refine your search if needed.**\n"
                
        )
    return sorted_results, len(results)

##############################
# Command - srbreqs - Display all songs in the song request list
@bot.tree.command(name="srbreqlist", description="Display all songs currently in the song request list")
async def srbreqlist(interaction: discord.Interaction):
    if not SONG_REQUESTS_FILE or not os.path.exists(SONG_REQUESTS_FILE):
        await interaction.response.send_message("Song requests file not found or not set.", ephemeral=True)
        return

    try:
        # Load the song request list from the JSON file
        with open(SONG_REQUESTS_FILE, "r", encoding="utf-8") as file:
            try:
                song_requests = json.load(file)
            except json.JSONDecodeError:
                song_requests = []  # Fallback if the file has invalid JSON

        # Format the output
        if song_requests:
            formatted_requests = [
                f"{entry['RequestNumber']} | {entry['Date']} | {entry['User']} | {entry['Song']}" for entry in song_requests
            ]
            response = "\n".join(formatted_requests)
            
            # Ensure the message length doesn't exceed Discord's limit
            if len(response) > 2000:
                response = response[:1958] + "..." + "\nDisplaying oldest requested songs only"
            await interaction.response.send_message(response)
        else:
            await interaction.response.send_message("No song requests found.")

        print(f"{interaction.user} viewed the song request list.")
    except Exception as e:
        print(f"Error loading song request list: {e}")
        await interaction.response.send_message(f"Error loading song request list: {e}", ephemeral=True)

##############################
# Command - srbreqdel - Delete a song request by RequestNumber or delete all requests
@bot.tree.command(name="srbreqdel", description="Delete a song request by RequestNumber, 'all', 'self', or a specific user")
@app_commands.describe(request_number="RequestNumber to delete, 'all', 'self', or a specific user")
async def srbreqdel(interaction: discord.Interaction, request_number: str):
    if not SONG_REQUESTS_FILE or not os.path.exists(SONG_REQUESTS_FILE):
        await interaction.response.send_message("Song requests file not found or not set.", ephemeral=True)
        return

    try:
        # Load the song request list from the JSON file
        with open(SONG_REQUESTS_FILE, "r", encoding="utf-8") as file:
            try:
                song_requests = json.load(file)
            except json.JSONDecodeError:
                song_requests = []  # Fallback if the file has invalid JSON

        if not song_requests:
            await interaction.response.send_message("Song Request List is empty.")
            return

        if request_number.lower() == "all":
            # Check if the user has permission to delete all
            if interaction.user.id not in ALLOWED_USER_IDS:
                await interaction.response.send_message("You do not have permission to delete all song requests.", ephemeral=True)
                return

            # Clear all requests
            song_requests = []
            with open(SONG_REQUESTS_FILE, "w", encoding="utf-8") as file:
                json.dump(song_requests, file, indent=4)

            await interaction.response.send_message("All song requests have been deleted.")
            print(f"{interaction.user} deleted all song requests.")
            return

        if request_number.lower() == "self":
            # Remove all requests where the requesting user is the "User" of the JSON entry
            user_requests = [req for req in song_requests if req["User"] == str(interaction.user)]
            if not user_requests:
                await interaction.response.send_message("You have no song requests to delete.")
                return

            # Filter out the user's requests
            song_requests = [req for req in song_requests if req["User"] != str(interaction.user)]

            # Update RequestNumbers
            for i, req in enumerate(song_requests):
                req["RequestNumber"] = i + 1            # Save the updated list back to the JSON file
            with open(SONG_REQUESTS_FILE, "w", encoding="utf-8") as file:
                json.dump(song_requests, file, indent=4)

            # Format the updated song list
            if song_requests:
                formatted_requests = [
                    f"{entry['RequestNumber']} | {entry['Date']} | {entry['User']} | {entry['Song']}" for entry in song_requests
                ]
                updated_list = "\n".join(formatted_requests)
            else:
                updated_list = "No song requests remaining."

            await interaction.response.send_message(f"All your song requests have been deleted.\nUpdated Song Request List:")
            print(f"{interaction.user} deleted all their song requests.")
            await interaction.followup.send(f"{updated_list}")
            return# Check if the input is numeric (for individual song deletion)
        if request_number.isdigit():
            request_num = int(request_number)

            # Validate the request_number
            if request_num < 1 or request_num > len(song_requests):
                await interaction.response.send_message("RequestNumber not found.")
                return

            request_to_delete = song_requests[request_num - 1]

            # Check if the user has permission to delete the specific request
            if interaction.user.id not in ALLOWED_USER_IDS and str(interaction.user) != request_to_delete["User"]:
                await interaction.response.send_message("You do not have permission to delete this song request.", ephemeral=True)
                return

            # Remove the request and update RequestNumbers
            song_requests.pop(request_num - 1)
            for i in range(request_num - 1, len(song_requests)):
                song_requests[i]["RequestNumber"] -= 1

            # Save the updated list back to the JSON file
            with open(SONG_REQUESTS_FILE, "w", encoding="utf-8") as file:
                json.dump(song_requests, file, indent=4)

            # Format the deleted song details
            deleted_song_details = f"#{request_number} | {request_to_delete['Date']} | {request_to_delete['User']} | {request_to_delete['Song']} has been deleted."

            # Format the updated song list
            if song_requests:
                formatted_requests = [
                    f"{entry['RequestNumber']} | {entry['Date']} | {entry['User']} | {entry['Song']}" for entry in song_requests
                ]
                updated_list = "\n".join(formatted_requests)
            else:
                updated_list = "No song requests remaining."

            # Send the response
            await interaction.response.send_message(f"Deleting Song Request\n({deleted_song_details})\nUpdated Song Request List:")
            print(f"{interaction.user} deleted song request #{request_number}.")
            await interaction.followup.send(f"{updated_list}")
            return

        # Handle specific user deletion
        target_user = request_number
        if target_user:
            # Check if the requesting user has permission to delete another user's requests
            if interaction.user.id not in ALLOWED_USER_IDS and str(interaction.user) != target_user:
                await interaction.response.send_message("You do not have permission to delete all requests from this user.", ephemeral=True)
                return

            # Find all requests by the target user
            user_requests = [req for req in song_requests if req["User"] == target_user]
            if not user_requests:
                await interaction.response.send_message(f"No song requests found for user '{target_user}'.")
                return

            # Filter out the target user's requests
            song_requests = [req for req in song_requests if req["User"] != target_user]

            # Update RequestNumbers
            for i, req in enumerate(song_requests):
                req["RequestNumber"] = i + 1            # Save the updated list back to the JSON file
            with open(SONG_REQUESTS_FILE, "w", encoding="utf-8") as file:
                json.dump(song_requests, file, indent=4)

            # Format the updated song list
            if song_requests:
                formatted_requests = [
                    f"{entry['RequestNumber']} | {entry['Date']} | {entry['User']} | {entry['Song']}" for entry in song_requests
                ]
                updated_list = "\n".join(formatted_requests)
            else:
                updated_list = "No song requests remaining."

            await interaction.response.send_message(f"All song requests from user '{target_user}' have been deleted.\nUpdated Song Request List:")
            print(f"{interaction.user} deleted all song requests from user '{target_user}'.")
            await interaction.followup.send(f"{updated_list}")
            return

    except Exception as e:
        print(f"Error deleting song request: {e}")
        await interaction.response.send_message(f"Error deleting song request: {e}", ephemeral=True)

##############################
# Going Live - Send a live notification message with optional role mentions
@bot.tree.command(name="srblive", description="Sends a live notification message with optional role mentions")
@app_commands.describe(message="The message to send with the notification")
async def srblive(interaction: discord.Interaction, message: str):
    # Check if user has permission
    if not check_permissions(interaction.user.id, ALLOWED_USER_IDS):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return
    
    try:
        # Check if live notification roles are configured
        if not DISCORD_LIVE_NOTIFICATION_ROLES:
            # No roles configured, send message without mentions
            notification = f"Going Live: {message}"
            await interaction.response.send_message(notification)
            print(f"{interaction.user} sent live notification (no roles configured): {message}")
            return
          # Get all configured roles from the guild
        role_mentions = []
        missing_roles = []
        
        if not interaction.guild:
            await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)
            return
        
        for role_name in DISCORD_LIVE_NOTIFICATION_ROLES:
            role = discord.utils.get(interaction.guild.roles, name=role_name)
            if role:
                role_mentions.append(role.mention)
            else:
                missing_roles.append(role_name)
        
        # Create the notification message
        if role_mentions:
            # Include role mentions if found
            roles_text = " ".join(role_mentions)
            notification = f"{roles_text} - Going Live: {message}"
            await interaction.response.send_message(notification, allowed_mentions=discord.AllowedMentions(roles=True))
            print(f"{interaction.user} sent live notification to roles {DISCORD_LIVE_NOTIFICATION_ROLES}: {message}")
            
            # Log missing roles if any (but don't warn the user)
            if missing_roles:
                print(f"Note: Some configured roles not found: {', '.join(missing_roles)}")
        else:
            # No roles found, send without mentions
            notification = f"Going Live: {message}"
            await interaction.response.send_message(notification)
            print(f"{interaction.user} sent live notification (configured roles not found): {message}")
            
    except Exception as e:
        print(f"Error sending live notification: {e}")
        await interaction.response.send_message("Error sending notification message. (/srblive)", ephemeral=True)

##############################
# Bot Startup Feedback
@bot.event
async def on_ready():
    print('------')
    print(f'Loaded {os.path.basename(__file__)}')
    print(f'Logged in as {bot.user} (ID: {bot.user.id if bot.user else "Unknown"})')
    print('------')
    await bot.tree.sync()

    try:
        copied_file_path = os.path.join(os.getcwd(), "collection.nml")
        shutil.copyfile(TRAKTOR_PATH, copied_file_path)
        print("Traktor collection file copied successfully.")
        
        # Count the number of songs in the collection and print it
        total_songs = count_songs_in_collection(copied_file_path)
        _, total_new_songs = get_new_songs(copied_file_path, NEW_SONGS_DAYS)
        print(f"Max song returned: {MAX_SONGS}")
        print(f"Default Days for New Songs: {NEW_SONGS_DAYS}")
        print(f"Total number of songs in the collection: {total_songs}")
        print(f"Total number of songs added in the last {NEW_SONGS_DAYS} days: {total_new_songs}")
    except Exception as e:
        print(f"Error copying file: {e}")

##############################
# Bot Start
async def main():
    if not TOKEN:
        print("ERROR: DISCORD_TOKEN not found in environment variables!")
        return
    
    print("Starting bot...")
    async with bot:
        await bot.start(TOKEN)

asyncio.run(main())
