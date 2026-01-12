# Harmonic Mixing Helper – Design & Implementation Plan

## Goals
- Suggest harmonically valid song transitions using Open Key + straight key, optionally considering BPM changes.
- Support key-only mode (no BPM) and BPM-aware mode with tolerance input (default 5%, per-session, not persisted).
- Allow same-key hops (e.g., 1A → 1A) to make BPM adjustments within a chain; prioritize shortest transition chain over closest BPM.
- Provide a GUI-only popup to manage Song A/B selection, run matching, and browse per-hop candidates; no web/overlay/Discord surface.
- Add quick-set A/B buttons on song request rows; allow Song A to be set from current playing track when bpm/key are present (button disabled otherwise).
- Save/clear playlists in data/harmonic_playlists.json using the existing safe_write_json pattern.

## Data & Inputs
- Collection: data/collection.json entries carry `artist`, `title`, `album`, `bpm` (int), `musical_key` (Traktor Open Key int 0–23), etc.; loaded via utils.traktor.load_collection_json.
- Now playing: emitted payload includes `artist`, `title`, `album`, `bpm`, `key` (Open Key string), `musical_key` (int) when matched; unmatched tracks have empty bpm/key.
- Current BPM from MIDI clock via EventTopic.MIDI_BPM; GUI should show current BPM if available.
- Song requests: data/song_requests.json with Artist/Title/Album/BPM fields for A/B quick-set buttons.

## Key Representations
- Keep existing Open Key mapping in utils/harmonic_keys.py.
- Add straight-key single-name mapping (e.g., C, G#, A) and conversion helpers OpenKey ↔ straight ↔ Camelot (string forms).
- Provide compatibility helpers returning key-int neighbors including: same key, ±1, relative major/minor; expose string variants for UI.

## Matching Modes & Rules
- Modes: (a) Key-only (ignore BPM entirely), (b) BPM-aware (use tolerance %, default 5). UI toggle/switch.
- Allow same-key transitions to permit BPM stepping without key change.
- Compatible key steps: same key, ±1 on wheel, relative maj/min. Wrap-around applies.
- Path validity: require at least one song for each hop’s key (and BPM window when BPM-aware); unmatched tracks are ignored.
- Sorting: prefer shortest transition chain; secondary sort by total BPM offset magnitude when ties.
- BPM-aware details: adjusted BPM = base BPM * (1 ± tol); adjusted key derived from BPM shift; reject songs outside tolerance; show BPM offset (+/-%, resulting BPM) and adjusted key in results.

## Matcher Shape (new module)
- Inputs: Song A (artist/title/album/id), Song B, mode (key-only/BPM-aware), BPM tolerance %, optional current BPM reference, filters (artist/title substring, album/release substring), optional tag filter placeholder.
- Steps:
  - Resolve Song A/B to collection entries; fail fast if missing required bpm/key for BPM-aware.
  - Build compatible key graph (Open Key ints) with same-key edges included.
  - BFS/Dijkstra for shortest key chain from A to B; allow multiple valid chains.
  - For each hop, fetch candidate songs matching that hop key (and BPM window when BPM-aware); prune chains with empty hops.
  - Return structured results: list of chains; each chain has hops with key labels (Open Key + straight), candidate songs with artist/title/album/original bpm/key, bpm offset %, adjusted bpm, adjusted key.

## UI Design (new popup)
- Access: add a “Harmonic Mix” button (show/hide) near the Song Requests controls area (top-right column) or Controls panel; opens a non-modal, always-on-top dialog held by controller.
- Sections:
  1) Header: current BPM display; BPM tolerance numeric input (default 5%); mode toggle (Key-only vs BPM-aware).
  2) Song selectors: search field + results list + “Set as A” / “Set as B”; buttons for “Use Current Track for A” (disabled when now-playing lacks bpm/key); display selected A/B with Open Key + straight key + BPM.
  3) Filters: artist/title substring; album/release substring; (genre placeholder text only, not implemented).
  4) Actions: “Find Transitions” triggers matcher; “Clear Results”; “Save to Playlist” and “Clear Playlist”.
  5) Results: grouped by transition chain. Each chain shows keys sequence (e.g., 11m → 12m → 1m → 1a) and per-hop candidate tables (song, artist, album, orig BPM/key, BPM offset %, adjusted BPM/key).
- Requests integration: add compact “A” and “B” toolbuttons beside each request row (panel + popup) to populate Song A/B in the harmonic popup (communicate via controller).

## State & Storage
- Controller should cache last now-playing payload + a boolean flag `has_key_bpm` (True when bpm and musical_key are present) to drive the “Use Current Track” button enabled state.
- Playlists: JSON file data/harmonic_playlists.json using safe_write_json; store list of selections (e.g., chain id, ordered track ids/artist+title, timestamp); provide clear/reset.

## Events/Wiring
- Controller: expose methods to open/close harmonic popup, set Song A/B (including from current track), run matcher, and save/clear playlists.
- Popup: request controller to run searches; controller returns structured results for rendering.
- Requests panel/popup: emit signals to controller when A/B buttons clicked; controller updates popup state if open.

## Edge Cases
- Disable “Use Current Track” when bpm/key missing; no hint text.
- Key-only mode should not require BPM; still allow same-key chain of length 1 (A→A) as valid.
- Handle collection load failures gracefully; show empty results with inline text, no crashes.

## Future Iterations
- Track songs played in the current session and filter matches to avoid repeats; would require persisting a session play log separate from playlists.

## Open Issues / Next Fixes
- Now-playing cache lacks `musical_key` in some payloads, causing “Use Current Track” to stay disabled; ensure song events carry `musical_key` and the cache checks it.
- A/B from requests should resolve BPM/key via collection lookup (requests JSON currently lacks key); optionally store key on new requests.
- Key-only compatibility should follow Camelot/Open Key neighbors (e.g., 1A valid: 1A/1B/2A/12A); adjust compatibility graph to use Camelot numbers before mapping back to Open Key.
- Popup display polish: show only values (no labels) with the format:
  - A: `Artist - Title` / `Release` / `Original BPM | Original Key -> Current Key (at current BPM)`
  - B: `Artist - Title` / `Release` / `Original BPM -> BPM Deviation | Original Key -> Current Key (at current BPM)`
- Search UI: single search box that ANDs keywords across artist/title/album; render list as `[BPM] | [KEY] | Artist - Title [Album]`.

## Implementation Checklist
1) Update utils/harmonic_keys.py with straight-key mapping and compatibility helpers returning both Open Key and straight labels.
2) Add matcher module (e.g., utils/harmonic_mixer.py) implementing chain search and candidate retrieval for key-only and BPM-aware modes.
3) Extend controller: cache last song payload + has_key_bpm flag; add actions for setting A/B, running matcher, saving/clearing playlists, opening popup.
4) Build Harmonic Mixing popup UI and wiring; add “Use Current Track for A” button (disabled when has_key_bpm is False); add tolerance input (default 5%); mode toggle; results view.
5) Add A/B toolbuttons to song requests panel + popup and signal through controller to update harmonic popup selections.
6) Add playlist persistence to data/harmonic_playlists.json using safe_write_json; include clear/reset action in popup.
7) Smoke test: open popup, set A from current track (with bpm/key), set B via search, run key-only and BPM-aware searches, save/clear playlist.
