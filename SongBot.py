import os
import shutil
import discord
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
import xml.etree.ElementTree as ET
import asyncio

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TRAKTOR_PATH = os.getenv('TRAKTOR_COLLECTION')
APPLICATION_ID = os.getenv('APPLICATION_ID')
CHANNEL_IDS = os.getenv('CHANNEL_IDS')
ALLOWED_USER_IDS = os.getenv('ALLOWED_USER_IDS')

if CHANNEL_IDS:
    CHANNEL_IDS = [int(id) for id in CHANNEL_IDS.split(',')]
else:
    CHANNEL_IDS = []

if ALLOWED_USER_IDS:
    ALLOWED_USER_IDS = [int(id) for id in ALLOWED_USER_IDS.split(',')]
else:
    ALLOWED_USER_IDS = []

# Check if all environment variables are loaded
required_env_vars = [TOKEN, TRAKTOR_PATH, APPLICATION_ID]
if any(var is None for var in required_env_vars):
    raise ValueError("One or more required environment variables are missing.")

# Create a bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)

def check_permissions(user_id, allowed_user_ids):
    return user_id in allowed_user_ids

@bot.tree.command(name="srbcol", description="Refresh the Traktor collection file")
async def srbcol(interaction: discord.Interaction):
    if not check_permissions(interaction.user.id, ALLOWED_USER_IDS):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    try:
        # Copy the Traktor collection file to the current directory with the correct filename
        copied_file_path = os.path.join(os.getcwd(), "collection.nml")
        shutil.copyfile(TRAKTOR_PATH, copied_file_path)
        print(f"{interaction.user} triggered Collection update")
        await interaction.response.send_message("Traktor collection file copied successfully.")
    except Exception as e:
        print(f"{interaction.user} triggered Collection update, but there was an error copying file")
        await interaction.response.send_message(f"Error copying file: {e}", ephemeral=True)

@bot.tree.command(name="song", description="Search for a song in the Traktor collection")
@app_commands.describe(search="search query")
async def song(interaction: discord.Interaction, search: str):
    if interaction.channel.id not in CHANNEL_IDS:
        await interaction.response.send_message("This command can only be used in the designated channels.", ephemeral=True)
        return

    copied_file_path = os.path.join(os.getcwd(), "collection.nml")
    results, total_matches = parse_traktor_collection(copied_file_path, search)
    if results:
        await interaction.response.send_message("\n".join(results))
        print(f"{interaction.user}'s search '{search}' matched {total_matches} songs")
    else:
        await interaction.response.send_message("No matching results found.")
        print(f"{interaction.user}'s search '{search}' matched 0 songs")

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

    for entry in root.findall(".//ENTRY"):
        artist = entry.get("ARTIST")
        title = entry.get("TITLE")
        album_element = entry.find(".//ALBUM")
        album_title = album_element.get("TITLE") if album_element is not None else None

        priority_score = 0
        sort_key = ""

        if title and all(keyword in title.lower() for keyword in search_keywords):
            priority_score = 1
            sort_key = title.lower()
        elif artist and artist is not None and all(keyword in artist.lower() for keyword in search_keywords):
            priority_score = 2
            sort_key = artist.lower()
        elif album_title and all(keyword in album_title.lower() for keyword in search_keywords):
            priority_score = 3
            sort_key = album_title.lower()

        if priority_score > 0:
            result_str = f"{artist} - {title} *[{album_title}]*" if album_title else f"{artist} - {title}"
            results.append((priority_score, sort_key, result_str))

    results.sort(key=lambda x: (x[0], x[1]))
    sorted_results = [f"{i + 1} | {result[2].replace('_', '')}" for i, result in enumerate(results[:15])]

    if len(results) > 15:
        sorted_results.append(f"**15 of {len(results)} matches found for {search_query}, please refine your search if needed.**")

    return sorted_results, len(results)

@bot.event
async def on_ready():
    print('------')
    print(f'Loaded {os.path.basename(__file__)}')
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.tree.sync()

    try:
        copied_file_path = os.path.join(os.getcwd(), "collection.nml")
        shutil.copyfile(TRAKTOR_PATH, copied_file_path)
        print("Traktor collection file copied successfully.")
    except Exception as e:
        print(f"Error copying file: {e}")

async def main():
    print("Starting bot...")
    async with bot:
        await bot.start(TOKEN)

# Run the bot
asyncio.run(main())
