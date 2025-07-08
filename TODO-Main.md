# TODO & Feature Ideas

## Web Overlay for Now Playing (OBS Integration)

### Stage 1: Basic Flask-SocketIO Server & WebSocket Overlay
- [x] Flask-SocketIO app in `services/web_overlay.py`
- [x] Basic routes: `/` (overlay page), WebSocket endpoint
- [x] Simple HTML template with artist, title, album display
- [x] JavaScript WebSocket client for real-time updates
- [x] Basic CSS styling (white text, grey outline, dark background)
- [x] Test with static data first

### Stage 2: GUI Integration & Data Source
- [ ] Start/Stop Overlay button in GUI with status indicator
- [ ] Integrate with existing now-playing data source
- [ ] Emit WebSocket events when song changes
- [ ] Handle "no song playing" state gracefully
- [ ] Test with real Traktor data

### Stage 3: Basic Transitions & Core Features
- [ ] Implement 2-3 basic CSS transitions (fade, slide)
- [ ] Always show artist & title; others optional
- [ ] Handle WebSocket connection/disconnection gracefully
- [ ] Error handling for server downtime

### Stage 4: Advanced Customization
- [ ] User-selectable transition in settings (crossfade, swipe, typewriter, etc.)
- [ ] Per-item visibility options (cover art, album, BPM, key, etc.) in settings
- [ ] Adjustable font size and color for each item
- [ ] Cover art integration (if available)

### Stage 5: Production Polish
- [ ] Optimize WebSocket performance
- [ ] Auto-reconnection on connection loss
- [ ] Graceful degradation when data unavailable
- [ ] Documentation for OBS Browser Source setup

## Visual Enhancement Features
- [ ] YouTube video integration for background visualizations
    - [ ] Research VLC -> NDI -> Spout pipeline for OBS (see: https://resolume.com/forum/viewtopic.php?t=14201, https://www.youtube.com/watch?v=LrNi3ZSNN6w)
    - [ ] Test local video player integration with `yt-dlp` + `opencv-python` or VLC
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


