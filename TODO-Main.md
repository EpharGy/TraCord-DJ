# TODO & Feature Ideas

## NowPlaying Replacement
- [ ] Replicate NowPlaying functionality within the bot/GUI
    - [X] Listen to Traktor output/port for song data
    - [X] Display current playing track, artist, album, cover art, etc.
    - [ ] Generate a styled webpage (with CSS/animations) for OBS integration
    - [ ] Slide in/out animation for song changes

## Animated Popup Window for Now Playing
- [ ] Create animated popup window for clean cover art and song info display
- [ ] Implement slide transitions (old song slides down, new song slides up)
- [ ] Test different animation approaches:
    - [ ] Tkinter with `place()` and `after()` (30-40fps, good enough)
    - [ ] Pygame integration (60fps+, buttery smooth)
    - [ ] Web-based popup with CSS animations (60-120fps, professional grade)
- [ ] Add easing functions for smoother feel even at lower framerates

## Visual Enhancement Features
- [ ] YouTube video integration for background visualizations
    - [ ] Research YouTube API + embedded player approach
    - [ ] Test local video player integration with `yt-dlp` + `opencv-python`
    - [ ] Implement local caching system for downloaded videos
- [ ] Google Images integration as alternative/fallback
    - [ ] Set up Google Custom Search API
    - [ ] Implement image caching and random selection
    - [ ] Create franchise-based image organization
- [ ] Smart caching system:
    - [ ] Priority downloading for most-played tracks
    - [ ] Background downloads during idle time
    - [ ] Auto-cleanup of old/unused content
    - [ ] Size limits and storage management

## Additional Ideas & Suggestions
- [ ] Customizable appearance for the OBS overlay (themes, colors)
- [ ] Notification or sound when a new song is requested
- [ ] User request limits or cooldowns
- [ ] Integration with Discord for request notifications or commands

## Song Request Auto-Removal
- [ ] When a song is played (live or random), check if it matches any entry in the song request list.
    - [ ] Normalize both played song and request entry as "Artist - Title" (ignore album/extra info, use normalize_string logic).
    - [ ] If a match is found, call the standard delete function to remove the request (updates GUI and JSON, reorders RequestNumbers).
    - [ ] Ensure this works for both live and random playback.
    - [ ] (Future) Optionally send a Discord message to the requester when their song is played.

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


**(Plan added by Suzuya & Kumano, so you don’t forget, Admiral! Sleep tight~)**


