# TODO & Feature Ideas

## Overlay - Basic Transitions & Themes

- [ ] Implement 2-3 basic CSS transitions (fade, slide)
- [ ] Implement 2-3 basic CSS themes
- [ ] User-selectable themes / transitions in settings
- [ ] Per-item visibility options (cover art, album, BPM, key, etc.) in settings

## Visual Enhancement Features

Potentially use an api to pull an image or video based on the current track's metadata (artist, title, album, genre, etc.) to display in the overlay or as a background in OBS, or via Spout.

- [ ] YouTube video integration for background visualizations
  - [ ] Research VLC -> NDI -> Spout pipeline for OBS (see: <https://resolume.com/forum/viewtopic.php?t=14201>, <https://www.youtube.com/watch?v=LrNi3ZSNN6w>)
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
