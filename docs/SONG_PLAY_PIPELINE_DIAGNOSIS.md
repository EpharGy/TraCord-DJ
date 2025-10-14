# SONG_PLAYED pipeline diagnosis plan

Goal: Ensure SONG_PLAYED events appear in the GUI Log panel reliably, and verify the entire path from Traktor to GUI.

## Scope

- Validate and instrument the event flow (service → event bus → GUI hub → MainWindow → Controller → GUI Log).
- Keep changes low-risk and easy to revert.

## Acceptance checklist

- When a real track plays in Traktor, the GUI log shows (at least):
  - GUI Hub: received SONG_PLAYED (or TRAKTOR_SONG)
  - GUI: on_song_played slot fired
  - tracord.ui_qt2.controller: [Traktor] Song Played: Artist - Title [Album]
- Ctrl+T debug injection produces the same 3 lines.

## Steps

1. Confirm GUI log bridge captures tracord logs

- We already see tracord.ui_qt2.controller logs in GUI, so the bridge functions for tracord.*
- Keep the handler attached to the `tracord` logger after QApplication is created.

1. Add temporary diagnostics (low-noise, purposeful)

- ui_qt2/signals.py
  - Subscribe to both SONG_PLAYED and TRAKTOR_SONG in `QtEventHub.start()`.
  - In the hub’s handler, log once per event: "GUI Hub: received {topic}".
- ui_qt2/main_window.py
  - In `on_song_played`, log: "GUI: on_song_played slot fired".
- ui_qt2/controller.py
  - Keep the controller’s "[Traktor] Song Played: ..." log in `handle_song_event`.

1. Quick synthetic test (no Traktor required)

- Press Ctrl+T to emit a demo SONG_PLAYED event.
- Expect all three GUI logs: hub received → window slot fired → controller song played.

1. If Ctrl+T works but live Traktor doesn’t

- Add a short INFO in `tracord.core.events.emit_event` when topic ∈ {SONG_PLAYED, TRAKTOR_SONG}, logging topic and a few fields (artist/title).
- Confirms the service is calling `emit_event` and which topic.

1. If emit_event logs show in terminal but not GUI

- Re-check handler install order (must be after QApplication) and only once on `logging.getLogger("tracord")`.
- Verify `tracord` logger level ≥ INFO.

1. If GUI hub receives but MainWindow doesn’t fire

- Verify a single QtEventHub instance: log id(hub) in both `get_event_hub()` and `MainWindow.__init__`.
- Ensure connections are made: `hub.songPlayed.connect(self.on_song_played)`.

1. If needed, confirm single event bus instance

- Temporarily log id(bus) in the `emit_event`/`subscribe_event` path to ensure the same bus is used by services and GUI.
- If not, unify import paths or centralize bus setup.

1. Cleanup

- Remove or downgrade temporary diagnostics to DEBUG after success.
- Keep the controller "Song Played" log; it’s useful and not noisy.
- Consider leaving TRAKTOR_SONG subscription in the hub (minimal cost, useful for future overlays).

## Notes

- Live listener transitions are logged in GUI: enabling, waiting, connected, disabled (no duplicates).
- If we want a heartbeat fallback (treat stale stream as disconnected), add a timer in the Traktor handler to set "waiting" after N seconds of no packets.

## Rollback plan

- All diagnostic logs added behind minimal conditionals are safe to remove in one revert.
- No schema or file format changes involved.
