# TODO & Feature Ideas

## NowPlaying Replacement
- [ ] Replicate NowPlaying functionality within the bot/GUI
    - [X] Listen to Traktor output/port for song data
    - [ ] Display current playing track, artist, album, cover art, etc.
    - [ ] Generate a styled webpage (with CSS/animations) for OBS integration
    - [ ] Slide in/out animation for song changes

## Additional Ideas & Suggestions
- [ ] Customizable appearance for the OBS overlay (themes, colors)
- [ ] Notification or sound when a new song is requested
- [ ] User request limits or cooldowns
- [ ] Integration with Discord for request notifications or commands

---

## Technical Considerations
- **Thread Safety:** Ensure GUI updates (like song request list changes) are performed on the main thread to avoid tkinter crashes.
- **Data Sync:** Keep the GUI song request list in sync with the JSON file and Discord bot actions (add, remove, clear requests).
- **Performance:** Efficiently update the GUI when the song request list changes, especially with many requests.
- **Error Handling:** Gracefully handle file read/write errors, missing files, or malformed data.
- **User Feedback:** Provide clear feedback in the GUI for actions (success, errors, empty list, etc.).
- **Extensibility:** Design the GUI code so it’s easy to add features later (like search/filter, export/import, or OBS overlay integration).
- **Separation of Concerns:** Keep logic for data management, Discord integration, and GUI display modular and well-separated.
- **Cross-Platform:** Ensure file paths and GUI features work on both Windows and other OSes if needed.
- **Testing:** Consider how to test GUI features and data sync without breaking the bot or Discord integration.

---

## Traktor Cover Art Extraction & Display Plan

1. **File Path Construction**
   - Use the stored coverart string (e.g., `039/HNQ02OBHLMIWDCIJDEG0AVRGRPMB`) to build the full file path:
     `{TRAKTOR_LOCATION}\{latest_version}\Coverart\{folder}\{filename}000`
   - Use existing logic to find the latest Traktor version folder.

2. **File Format**
   - Traktor cover art files are Zstandard (Zstd) compressed, usually containing a JPEG or PNG image.
   - The `000` suffix is the largest version; `001`, `002`, etc. are smaller thumbnails.

3. **Decompression & Image Extraction**
   - Use the `zstandard` Python library to decompress the file.
   - Extract the image data (likely JPEG/PNG) from the decompressed bytes.
   - Use `Pillow` (PIL) to load/display the image from bytes.

4. **Display in GUI**
   - Show the cover art in the GUI near the current/selected song details.
   - If direct display isn’t possible, write the decompressed image to a temp file and load it.
   - Optionally cache decompressed images for performance.

5. **Fallbacks & Error Handling**
   - If the file isn’t Zstd or is corrupt, show a default "no cover art" image.
   - If the image format inside isn’t supported, try to detect and convert it.
   - Fallback to template image? 

6. **Python Tools Needed**
   - `zstandard` for decompression (`pip install zstandard`)
   - `Pillow` for image handling (`pip install pillow`)

7. **Next Steps**
   - Implement a utility function:
     - Input: coverart string, TRAKTOR_LOCATION
     - Output: PIL Image object (or path to temp image file)
   - Integrate with GUI for cover art display.

---

**(Plan added by Suzuya & Kumano, so you don’t forget, Admiral! Sleep tight~)**


