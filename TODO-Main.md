# TODO & Feature Ideas

## Song Requests GUI Integration
- [X] Display current song requests in the GUI (popup window or main panel)
- [X] Show who requested each song
- [X] Option to toggle song requests display for a cleaner view (for OBS)
- [X] Management controls: remove individual requests, clear all requests

## NowPlaying Replacement
- [ ] Replicate NowPlaying functionality within the bot/GUI
    - [ ] Listen to Traktor output/port for song data
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
