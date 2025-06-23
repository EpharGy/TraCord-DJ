# TODO & Feature Ideas

## Song Requests GUI Integration
- [ ] Display current song requests in the GUI (popup window or main panel)
- [ ] Show who requested each song
- [ ] Option to toggle song requests display for a cleaner view (for OBS)
- [ ] Management controls: remove individual requests, clear all requests

## NowPlaying Replacement
- [ ] Replicate NowPlaying functionality within the bot/GUI
    - [ ] Listen to Traktor output/port for song data
    - [ ] Display current playing track, artist, album, cover art, etc.
    - [ ] Generate a styled webpage (with CSS/animations) for OBS integration
    - [ ] Slide in/out animation for song changes

## Additional Ideas & Suggestions
- [ ] Option to export/import song requests list
- [ ] Customizable appearance for the OBS overlay (themes, colors)
- [ ] Notification or sound when a new song is requested
- [ ] Search/filter requests in the GUI
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

## Song Requests GUI Panel Implementation Plan
1. **Add Right-Side Panel Layout**
    - Add a new frame on the right side of the main GUI window, taking up 50% of the app’s height (top half for song requests).
2. **Display Song Requests List**
    - Load `song_requests.json` and display each request (with requester info) in the panel.
    - Add a small delete button next to each item.
3. **Delete Song Request**
    - Remove the request from the list and update `song_requests.json` when delete is clicked.
    - Refresh the GUI list after deletion.
4. **Detect New Song Requests**
    - Watch for changes to `song_requests.json` (file watcher or polling).
    - (Optionally) Listen for Discord command completions for real-time updates.
5. **Bring Window to Foreground on New Request**
    - When a new request is detected, bring the GUI window to the front.
6. **Auto-Refresh Song Requests Panel**
    - Periodically check for changes in `song_requests.json` and update the panel if needed.

**Suggested Order:**
1. Add panel and layout
2. Display list
3. Add delete logic
4. Add file change detection/auto-refresh
5. Add window foreground logic