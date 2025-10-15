# TODO & Feature Ideas (In no particular order and may not be confirmed for implementation)

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

### Potentially manually curate a list of fallback images/videos for common genres/artists

- [ ] Ability to manually curate images/videos for artists/songs (genres?)
  - [ ] Use as fallback or override. Ie if a song is played and there is a matching video, play the video into spout or an overlay.

## Switch to a database backend

- [ ] Migrate from JSON to SQLite or another lightweight database for better data integrity and query capabilities.

## DJ Setlist capture

- [ ] Start/stop to Capture played songs. (artist, title, album, requested by etc). export / store as file.
  - [ ] Fancy html version with cover art? extra metadata? ie bpm, key, etc.
- [ ] Ability to view current setlist so far in bot command or an overlay.
- [ ] Option to auto-publish setlist to a channel or as a message when the set ends.
- [ ] Ability to view past setlists, gui interface.

## Stats & Analytics
As a data centric person (it's my day job), I love stats. I want to track and display various stats about song requests and plays, any other interesting data points.

- [ ] Track most requested songs, artists, albums, genres, requestors, etc.
- [ ] Track most played songs, artists, albums, genres, requestors songs, etc.
- [ ] could this be the basis of the DJ setlist capture?
- [ ] Database storage of stats, with gui interface to view.?

## Twitch Integration

- [ ] Twitch chat integration for song requests and notifications
- [ ] Twitch channel point redemptions for song requests

---
