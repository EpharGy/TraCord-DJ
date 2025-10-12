# TraCord DJ GUI Modernization & Core Refactor Plan

Branch: `ref_gui`

Target GUI Platform: **PySide6 (Qt)** (modernized modular desktop shell).

---

## 1. High-Level Goals

- Modernize UI (improved layout clarity, responsiveness, DPI awareness, theming).
- Decouple core logic (bot + collection + overlay + stats) from presentation layer.
- Prepare for optional future web / Tauri / remote control surface.
- Improve performance in search, collection loading, and log/event handling.
- Reduce tech debt: remove Tkinter-specific patterns (queue polling hacks, ad-hoc event propagation).
- Harden packaging path (later: Nuitka + signing).

## 2. UX Direction (Not 1:1 Port)

### Current Issues

- Dense vertical stacking, mixed font sizes.
- Manual sizing constants; hard-coded geometry.
- Log + Now Playing share cramped space.
- Action affordances (refresh, reset, listener toggle) not grouped logically.
- Status feedback is text-only with color; could be semantic icons + subtle badges.

### Proposed Structure (Modular Dynamic Layout)

1. **Left Sidebar (Navigation/Status)**
   - Sections: Bot Status, Listener Status, Session Stats, Total Stats, Controls.
   - Collapsible groups or accordion.
2. **Center Panel**
   - Tabs: Now Playing | Requests | Logs.
   - Now Playing shows cover art (adaptive size), metadata, harmonic key, BPM.
   - Requests: interactive list with filters, moderation (future), queue.
3. **Dynamic Attachment Zone (Right Expansion)**
   - Optional panels attach in activation order (user toggle sequence) or fallback to default ordering.
   - Overlay preview (render cover + meta as OBS-style bounding region).
   - Quick toggles: Spout, Overlay Server, MIDI.

### Dynamic Panel System (New Design)

We introduce a Panel Manager that controls optional sections as attachable modules to the right of a stable core column.

Core window (always visible):

- Status (bot + listener)
- Core controls (start/stop, refresh, reset stats)
- Compact stats summary
- Log (either embedded or tabbed)

Attachment zone (horizontally expanding):

- Panels enabled by toolbar / toggle buttons.
- Order = click order (append); persisted between sessions.
- Each panel defines: `id`, `title`, `factory()`, `preferred_width`, `min_width`.

Implementation approach:

- Base layout: QHBoxLayout with left core + QSplitter (hidden when empty) for dynamic panels.
- On enable: create widget via factory, add to splitter, apply size distribution.
- On disable: remove widget, if no panels left hide splitter & shrink window via `adjustSize()`.
- Persistence: QSettings keys `panels/enabled`, `panels/order`, `panels/sizes`.
- Future animations (optional): slide in/out using `QPropertyAnimation` on `maximumWidth`.

Panel candidates:

- now_playing
- requests
- overlay_preview
- advanced_stats (later)
- settings (remains a dialog for now; convert only if inline editing desired)

Benefits:

- Avoids overwhelming initial layout.
- User-driven customization without complex docking UI.
- Natural path to remote or web mirroring (panel contracts already formalized).

### Visual Enhancements

- Use Qt palette + dark mode toggle.
- Icon set (SVG) for actions (Start, Stop, Listener, Overlay, Spout, MIDI, Refresh, Reset stats).
- Non-blocking toasts (QSystemTrayIcon messages or custom transient widgets) for ephemeral actions.
- Progress overlay (scrim + spinner) for collection import.

## 3. Architectural Migration Strategy

| Layer | Current | Target Abstraction | Notes |
|-------|---------|--------------------|-------|
| GUI Framework | Tkinter | PySide6 (Qt Widgets) | Keep entrypoint separate (`run_gui_qt.py`). |
| Event System | Custom singleton (not thread-safe) | Thread-safe EventBus + Qt signal bridge | Use adapter pattern. |
| Logging | Custom logger + GUI callback | Stdlib logging + Qt handler | Keep emoji severity markers. |
| Collection Search | JSON scan | Abstraction `SearchBackend` (JSON first, FTS later) | Enables SQLite upgrade later. |
| Cover Art Extraction | Duplicated logic | `utils/coverart.py` | Returns thumb + base64 + (optional spout img). |
| Stats | File read/write each mutation | In-memory cache + periodic flush | Debounce via QTimer. |
| Spout Sender | Tk-thread-managed | Background worker + signal callbacks | Safe stop on shutdown. |
| Overlay Server | Autostart in GUI ctor | Explicit service controller | Allow headless mode. |

## 4. Phased Plan

### Phase 0 – Foundations (No user-visible change)

- Add `utils/coverart.py` (unify extraction logic).
- Introduce `core/events.py` (thread-safe, typed events).
- Add `search/backend.py` with base class + current JSON implementation.
- Wrap existing logger with stdlib logging (preserve old API temporarily).

### Phase 1 – PySide6 Skeleton

- Add dependency (document in `requirements.txt`).
- New entrypoint `run_gui_qt.py`.
- Create `ui_qt/` package:
  - `app.py` (QApplication bootstrap)
  - `main_window.py` (QMainWindow + central tab widget)
  - `panels/` (status_panel.py, now_playing.py, requests_panel.py, log_panel.py, overlay_panel.py)
  - `signals.py` (Qt Signals typed wrapper)
- Implement: window frame, log panel (live updates), status panel (bot state), Start/Stop buttons.
- Bridge logger → Qt via custom `LogSignalEmitter`.

### Phase 2 – Feature Parity

- Port Now Playing (cover art, metadata, harmonic key).
- Port Requests panel (list + add/remove events hookup).
- Integrate Traktor Listener controls.
- Stats auto-refresh and manual resets.
- Overlay / Spout / MIDI toggles.

### Phase 3 – Enhancements

- Async collection refresh (progress bar + cancel).
- SQLite FTS backend prototype (optional flag in settings).
- Live overlay preview (rendered QPixmap from same data path).
- Non-blocking modal dialogs (replace blocking messageboxes with layered toasts / notifications).

### Phase 4 – Optional Extensions

- Expose WebSocket endpoint for events (optional remote control / future web shell).
- Add REST endpoints for control actions.
- Advanced panel persistence features (layout presets, export/import).
- Optional remote overlay panel inspector.

## 5. Sequence Dependencies

| Task | Depends On |
|------|------------|
| Qt app skeleton | None |
| Log bridge | Qt skeleton |
| Status panel | Bot control adapter |
| Now Playing panel | Cover art helper |
| Requests panel | EventBus + SearchBackend |
| Stats panel | Stats cache refactor |
| Overlay preview | Now Playing + cover art base64 |
| FTS backend | Stable JSON abstraction |

## 6. Data & Event Flow (Target)

```text
DiscordBot / TraktorListener / SearchBackend
        │
  (domain events emit via EventBus)
        │
 EventBus Thread-Safe Core  ──▶ QtAdapter (subscribes; re-emits as Qt Signals)
        │                                 │
        └────────────── StatsCache ◀──────┘
```

- Logger -> QtLogHandler -> LogSignal.
- CoverArtExtractor returns namedtuple: (thumb_qimage, spout_image, base64_str, metadata).

## 7. Concurrency Model

- Heavy tasks (collection parse, cover art extraction) -> QThreadPool (QRunnable) or `concurrent.futures` with signal dispatch.
- EventBus ensures thread-safe append & iteration (Lock + snapshot copying on emit to minimize lock hold time).
- GUI updates only via queued Qt signals (no direct cross-thread widget mutation).

## 8. Testing Plan

| Test Type | Focus |
|-----------|-------|
| Unit | Cover art extraction (mock audio paths), JSON search ordering, stats reset. |
| Integration | Bot ready -> signal propagation -> status panel update. |
| Performance | Collection import timing (baseline vs optimized). |
| UI Smoke (optional) | Launch + verify main panels create without exceptions. |

## 9. Success Metrics

| Metric | Target |
|--------|--------|
| Cold GUI startup | < 1.2s (without initial collection parse) |
| Collection refresh (JSON parse) | Same or faster vs Tk baseline |
| Log latency | < 50 ms from emit to GUI |
| Memory overhead vs Tk | + < 15% acceptable |
| User actions (start/stop) responsiveness | < 150 ms perceived |

## 10. Potential Pitfalls & Mitigations

| Risk | Mitigation |
|------|-----------|
| Mixed async (discord.py) + Qt event loops | Keep bot in its own thread; use thread-safe signals. |
| Race on shutdown (closing while parse running) | Add `ShutdownToken` checked in workers. |
| Duplicate event emissions | Centralize emitting points (document). |
| Large cover art memory spikes | Downscale early; cache LRU last N images. |

## 11. Incremental Commit Outline

1. `refactor(core): add coverart helper + event bus`
2. `feat(qt): add PySide6 skeleton app + logging bridge`
3. `feat(qt): add status + log panels`
4. `feat(qt): now playing panel + cover art integration`
5. `feat(qt): stats panel + cache refactor`
6. `feat(qt): requests panel (basic)`
7. `feat(core): search backend abstraction`
8. `feat(core): optional sqlite fts backend`
9. `feat(qt): overlay/spout/midi controls`
10. `chore(build): nuitka packaging script`

## 12. Configuration Adjustments

- Add `GUI_MODE` setting: `tk` | `qt` (transitional).
- Add `USE_SQLITE_SEARCH`: bool.
- Add `OVERLAY_PREVIEW_ENABLED`: bool.

## 13. Forward Compatibility (Generic Remote / Web Hooks)

Design contracts now (agnostic of any specific framework):

- Event serialization schema (JSON): `{type, timestamp, payload}`.
- Control actions mapping: `POST /control/{action}` (start_bot, stop_bot, refresh_collection, reset_stats).
- WebSocket channel `/ws/events` for NowPlaying, StatsUpdate, RequestsChange.
- Panel state sync endpoint: `GET /panels` returns enabled/order; `PUT /panels` updates arrangement.

## 14. Open Questions (To Resolve Later)

- Do we persist user layout (panel sizes)? (Qt: QSettings)
- Should requests panel support drag reordering? (phase 3+)
- Provide theme switch (dark/light)? (phase 2+)

## 15. Task Checklist

(Will update as we progress)

- [ ] Phase 0: Add `utils/coverart.py` helper
- [x] Phase 0: Add thread-safe `core/event_bus.py`
- [ ] Phase 0: Introduce `search/backend.py` abstraction (no behavior change)
- [ ] Phase 0: Replace logger with stdlib logging adapter (keep old API wrappers)
- [ ] Phase 1: Add PySide6 to requirements (optional extras section)
- [ ] Phase 1: Create `ui_qt` package & skeleton window
- [ ] Phase 1: Log bridge (Qt signal handler)
- [ ] Phase 1: Bot status panel (start/stop)
- [ ] Phase 2: Now Playing panel + cover art integration
- [ ] Phase 2: Stats cache refactor + panel
- [ ] Phase 2: Requests panel (list + events)
- [ ] Phase 2: Traktor listener + spout/midi toggles
- [ ] Phase 3: Overlay preview widget
- [ ] Phase 3: Async collection refresh with progress UI
- [ ] Phase 3: SQLite FTS backend (optional)
- [ ] Phase 3: Packaging script (Nuitka) + doc update
- [ ] Phase 4 (optional): WebSocket event server for future Tauri

## 16. Rollback Strategy

- Keep existing Tkinter entrypoint usable until Phase 2 parity reached.
- Feature flag new search backend; fallback to legacy JSON path.
- Maintain `--tk-fallback` CLI flag during migration period.

## 17. Documentation Updates

- Update README after Phase 2 with new screenshots + usage.
- Add `DEV_GUIDE.md` for signals & event contracts.
- Add packaging instructions (Nuitka) under `docs/packaging.md`.

---

Prepared in branch `ref_gui`. Update this file as each checklist item completes (convert to [x]).
