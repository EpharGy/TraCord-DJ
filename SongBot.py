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

# Create a bot instance
intents = discord.Intents.default()
bot = commands.Bot(command_prefix='!', intents=intents, application_id=APPLICATION_ID)

@bot.tree.command(name="srbcol", description="Refresh the Traktor collection file")
async def srbcol(interaction: discord.Interaction):
    if interaction.user.id not in ALLOWED_USER_IDS:
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    # Copy the Traktor collection file to the current directory with the correct filename
    copied_file_path = os.path.join(os.getcwd(), "collection.nml")
    shutil.copyfile(TRAKTOR_PATH, copied_file_path)
    print(f"{interaction.user} triggered Collection update")  # Print the user, search query, and total matches
    await interaction.response.send_message("Traktor collection file copied successfully.")

@bot.tree.command(name="song", description="Search for a song in the Traktor collection")
@app_commands.describe(search="search query")
async def song(interaction: discord.Interaction, search: str):
    if interaction.channel.id not in CHANNEL_IDS:
        await interaction.response.send_message("This command can only be used in the designated channels.", ephemeral=True)
        return

    # Use the copied file path instead of the original file path
    copied_file_path = os.path.join(os.getcwd(), "collection.nml")
    results, total_matches = parse_traktor_collection(copied_file_path, search)
    if results:
        await interaction.response.send_message("\n".join(results))
        print(f"{interaction.user}'s search '{search}' matched {total_matches} songs")  # Print the user, search query, and total matches
    else:
        await interaction.response.send_message("No matching results found.")
        print(f"{interaction.user}'s search '{search}' matched 0 songs")  # Print the user, search query, and total matches

def parse_traktor_collection(copied_file_path, search_query):
    # Check if the file exists
    if not os.path.exists(copied_file_path):
        return [f"File not found: {copied_file_path}"]

    # Parse the copied XML file
    try:
        tree = ET.parse(copied_file_path)
        root = tree.getroot()
    except ET.ParseError as e:
        return [f"Error parsing XML file: {e}"]

    # Initialize a list to store search results
    results = []

    # Split the search query into keywords
    search_keywords = search_query.lower().split()

    # Iterate through each ENTRY in the collection
    for entry in root.findall(".//ENTRY"):
        artist = entry.get("ARTIST")
        title = entry.get("TITLE")
        album_element = entry.find(".//ALBUM")
        album_title = album_element.get("TITLE") if album_element is not None else None

        # Initialize priority score and sort key
        priority_score = 0
        sort_key = ""

        # Check if all search keywords match any field and assign priority score and sort key
        if title and all(keyword in title.lower() for keyword in search_keywords):
            priority_score = 1
            sort_key = title.lower()
        elif artist and artist is not None and all(keyword in artist.lower() for keyword in search_keywords):
            priority_score = 2
            sort_key = artist.lower()
        elif album_title and all(keyword in album_title.lower() for keyword in search_keywords):
            priority_score = 3
            sort_key = album_title.lower()

        # If there's a match, format the result and add to results list
        if priority_score > 0:
            if album_title:
                result_str = f"{artist} - {title} *[{album_title}]*"
            else:
                result_str = f"{artist} - {title}"
            results.append((priority_score, sort_key, result_str))

    # Sort results based on priority score and then alphabetically within each priority score bucket
    results.sort(key=lambda x: (x[0], x[1]))

    # Extract the formatted result strings and add sequential numbers
    sorted_results = [f"{i + 1} | {result[2].replace('_', '')}" for i, result in enumerate(results[:15])]

    # Add a message if there are more than 15 results
    if len(results) > 15:
        sorted_results.append(f"**15 of {len(results)} matches found for {search_query}, please refine your search if needed.**")

    return sorted_results, len(results)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')
    await bot.tree.sync()
    # Announce that the bot is online
    # for channel_id in CHANNEL_IDS:
    #     channel = bot.get_channel(channel_id)
    #     if channel:
    #         await channel.send("The Song Bot is now online!")

    # Copy the Traktor collection file to the current directory with the correct filename
    copied_file_path = os.path.join(os.getcwd(), "collection.nml")
    shutil.copyfile(TRAKTOR_PATH, copied_file_path)
    print("Traktor collection file copied successfully.")

async def main():
    print("Starting bot...")
    async with bot:
        await bot.start(TOKEN)

# Run the bot
asyncio.run(main())
