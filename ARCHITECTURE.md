# TraCord DJ — Future Architecture Blueprint

> Drafted: 2025-10-12  
> Scope: Applicable whether we continue the in-place refactor or spin up a fresh repo.

## Goals

- Deliver a cohesive, maintainable platform for Traktor-driven DJ workflows.  
- Support existing capabilities (Discord requests, overlays, Spout/NestDrop, stats) while enabling advanced planning tools.  
- Isolate subsystems behind clear interfaces so UI, services, and automation can evolve independently.  
- Provide predictable structure for contributions (human or Copilot-driven) and testing.

## Layered Structure

```text
tracord/
├─ core/                 # Domain models & services (logic without IO)
│   ├─ models.py         # Track, Request, SessionStats, PlannerConstraints, etc.
│   ├─ services/
│   │   ├─ requests.py   # Request manager (enqueue/clear/history)
│   │   ├─ stats.py      # Aggregation + persistence orchestration
│   │   ├─ planner.py    # Harmonic/BPM graph traversal, set recommendations
│   │   └─ now_playing.py# Domain wrapper for current track state
│   └─ ports.py          # Interfaces describing external systems (Traktor, Discord, Overlay, Spout, NestDrop)
├─ infra/                # Implementations of ports + shared infrastructure
│   ├─ traktor/
│   │   ├─ parser.py     # XML/NML parsing, collection normalization
│   │   └─ broadcaster.py# Listener for Traktor broadcast events
│   ├─ storage/
│   │   ├─ sqlite_index.py # FTS + metadata store
│   │   └─ stats_store.py  # Session/global stats persistence (atomic writes)
│   ├─ discord/
│   │   ├─ bot.py        # discord.py setup, cog wiring, background tasks
│   │   └─ commands.py   # Slash/prefix command adapters talking to core services
│   ├─ overlay/
│   │   ├─ server.py     # Web overlay server (Flask/FastAPI)
│   │   └─ templates/    # HTML/CSS/JS for OBS pickup
│   ├─ spout/
│   │   └─ sender.py     # Cover art to Spout stream
│   ├─ nestdrop/
│   │   └─ midi_bridge.py# BPM clock + song-change triggers
│   ├─ logging.py        # Stdlib logging setup + Rich/UI handlers
│   ├─ settings.py       # Typed config loader (pydantic) + env overrides
│   └─ events.py         # Thread-safe event bus (publisher/subscriber)
├─ ui/
│   ├─ qt/
│   │   ├─ app.py        # QApplication bootstrap + dependency injection
│   │   ├─ main_window.py# Core frame with status/log panels
│   │   ├─ panels/
│   │   │   ├─ requests_panel.py   # Request queue w/ requester & timestamps
│   │   │   ├─ now_playing_panel.py# Metadata & cover art
│   │   │   ├─ planner_panel.py    # Harmonic/BPM recommendations (future)
│   │   │   ├─ stats_panel.py      # Session/global stats view
│   │   │   └─ overlay_panel.py    # Spout/overlay controls
│   │   └─ panel_manager.py        # Optional panel attachments + persistence
│   └─ cli/
│       └─ headless.py   # Headless mode for server deployments
├─ apps/
│   ├─ gui_qt.py         # Entry point for desktop control panel
│   └─ headless.py       # Entry point for bot-only operation
├─ utils/
│   ├─ coverart.py       # Unified extraction/resizing/encoding helpers
│   ├─ time.py           # Time formatting utilities (timestamps, durations)
│   └─ constants.py      # Common constants (default ports, icon paths, etc.)
└─ tests/
    ├─ fixtures/
    │   ├─ traktor_collection_small.xml
    │   └─ tracks.json
    ├─ test_planner.py
    ├─ test_requests.py
    ├─ test_traktor_parser.py
    └─ ...
```

## Key Architectural Elements

### Domain (core/)

- **Pure business logic** that can be unit-tested without Discord/Traktor running.  
- `core.ports` defines abstract interfaces; infra implements them.  
- Planner logic built around a graph of tracks keyed by harmonic key + BPM (with tolerances).

### Infrastructure (infra/)

- Each adapter implements a corresponding port and handles IO, threads, async loops.  
- `storage/sqlite_index.py` provides search, harmonic/BPM lookups, and supports future set-planner queries.  
- `events.py` offers a thread-safe event bus so UI and services can subscribe without tight coupling.  
- Logging & settings centralized to avoid side effects on import.

### UI (ui/)

- **Qt shell** using PanelManager to attach optional panels in user-selected order.  
- Panels consume domain services via dependency injection (e.g., pass a `RequestsService` instance).  
- Headless CLI for deployments needing only Discord/overlay services.

### Applications (apps/)

- Thin entry points wiring together settings, logging, infrastructure adapters, and UI or headless loop.  
- Keeps `__main__` scripts minimal and declarative.

### Tests

- Unit tests for planner, requests, stats, parser.  
- Integration tests exercising Discord commands via mocks and verifying events/updates.  
- Fixtures for Traktor samples and track metadata.

## Migration Strategy (if staying in current repo)

1. **Scaffold structure**: create `tracord/` package with subfolders and move current modules gradually.  
2. **Phase 0 parity**: implement `utils/coverart`, `infra/events`, `infra/logging`, `infra/settings`.  
3. **Move Traktor + storage** into new modules, exposing domain-facing interfaces.  
4. **Introduce PanelManager** and PySide6 skeleton using new services.  
5. **Refactor stats/search** to use SQLite backend.  
6. **Add planner service + UI** once search/index foundation is in place.  
7. **Retire legacy modules** after equivalent functionality lives under `tracord/`.

## If Starting Fresh Repository

- Apply same directory layout.  
- Port modules incrementally (parser, Discord adapter, overlay) into the new structure.  
- Maintain automated tests to ensure feature parity as we migrate.

## Coding Guidelines

- Favor dependency injection: pass service instances into panels/cogs instead of direct imports.  
- Keep async boundaries explicit (e.g., Discord adapter owns its loop; domain functions stay sync).  
- Use typed dataclasses/pydantic models for settings and domain entities.  
- Document new modules with module-level docstrings and brief README sections.  
- Require tests accompanying planner logic and major adapters.

## Next Steps

- Convert this blueprint into actionable issues/milestones.  
- Update `REFACTOR.md` checklist items to reference new module names.  
- Begin with Phase 0 tasks (cover art helper, event bus, logging, settings) to unblock further refactoring.

---
This document should evolve as architecture decisions solidify; add changelog entries or link ADRs for significant deviations.
