# type: ignore
"""
MIDI helper for TraCord DJ: optional MIDI out for song change events and MIDI clock input.
Uses mido (with python-rtmidi backend) if available.
"""

import threading
import time
from collections import deque
from typing import Callable, Optional

from utils.logger import get_logger

try:
    import mido
    MIDI_AVAILABLE = True
except ImportError:
    mido = None
    MIDI_AVAILABLE = False

logger = get_logger(__name__)


class MidiClockListener:
    def __init__(self, preferred_port_name: Optional[str] = None, *, window: int = 96, timeout: float = 10.0, on_bpm: Optional[Callable[[Optional[float]], None]] = None, min_emit_interval: float = 1.5):
        self.preferred_port_name = preferred_port_name
        self.window = max(4, window)
        self.timeout = max(0.5, timeout)
        self.min_emit_interval = max(0.1, min_emit_interval)
        self.on_bpm = on_bpm
        self._port = None
        self._enabled = False
        self._times = deque(maxlen=self.window)
        self._last_ts = 0.0
        self._current_bpm: Optional[float] = None
        self._stop = threading.Event()
        self._watchdog_thread: Optional[threading.Thread] = None
        self._tick_count = 0
        self._last_tick_log = 0.0
        self._start_ts = 0.0
        self._no_tick_logged = False
        self._port_name: str | None = None
        self._last_emit_ts = 0.0
        self._last_bpm_log_ts = 0.0
        self._smoothed_bpm: Optional[float] = None

    def _select_input_port(self):
        ports = mido.get_input_names()
        logger.info(f"Available MIDI input ports: {ports}")
        if self.preferred_port_name:
            needle = self.preferred_port_name.strip().lower()
            for p in ports:
                if p.strip().lower() == needle:
                    return p
            for p in ports:
                if needle in p.strip().lower():
                    return p
        return ports[0] if ports else None

    def _handle_message(self, msg):
        if not msg or msg.type != "clock":
            return
        now = time.monotonic()
        self._times.append(now)
        self._last_ts = now
        self._tick_count += 1
        if self._tick_count == 1:
            logger.debug(f"MIDI clock first tick on {self._port_name or 'unknown port'}")
        # Throttle tick logging: first tick, then every 15s
        if (self._tick_count == 1) or ((now - self._last_tick_log) >= 15.0):
            logger.debug(f"MIDI clock tick #{self._tick_count} at {now:.3f}")
            self._last_tick_log = now
        if len(self._times) < 3:
            return
        # Compute BPM from average interval of recent pulses (24 clocks per quarter)
        intervals = [self._times[i] - self._times[i - 1] for i in range(1, len(self._times)) if self._times[i] >= self._times[i - 1]]
        if not intervals:
            return
        avg_interval = sum(intervals) / len(intervals)
        if avg_interval <= 0:
            return
        # Correct MIDI clock formula: 24 pulses per quarter note
        bpm = 60.0 / (avg_interval * 24.0)
        # Clamp to reasonable DJ ranges
        if bpm < 60 or bpm > 330:
            return

        # Smooth with EMA to reduce single-tick jitter
        if self._smoothed_bpm is None:
            self._smoothed_bpm = bpm
        else:
            alpha = 0.25  # weight for new sample
            self._smoothed_bpm = (alpha * bpm) + ((1 - alpha) * self._smoothed_bpm)

        bpm_display = round(self._smoothed_bpm, 1)
        now = time.monotonic()

        # Emit only if change is meaningful and interval passed
        if (self._current_bpm is None or abs(bpm_display - self._current_bpm) >= 0.5) and (now - self._last_emit_ts) >= self.min_emit_interval:
            self._current_bpm = bpm_display
            self._last_emit_ts = now
            if (self._last_bpm_log_ts == 0.0) or ((now - self._last_bpm_log_ts) >= 15.0):
                logger.debug(f"MIDI clock BPM updated: {bpm_display}")
                self._last_bpm_log_ts = now
            if self.on_bpm:
                try:
                    self.on_bpm(bpm_display)
                except Exception:
                    pass

    def _watchdog(self):
        while not self._stop.is_set():
            time.sleep(0.25)
            now = time.monotonic()
            if self._tick_count == 0 and not self._no_tick_logged and (now - self._start_ts) > 3.0:
                logger.info(f"MIDI clock: no ticks received after 3s on {self._port_name or 'unknown port'}")
                self._no_tick_logged = True
            if self._current_bpm is not None and (now - self._last_ts) > self.timeout:
                logger.debug("MIDI clock timeout; clearing BPM")
                self._current_bpm = None
                self._last_emit_ts = now
                self._last_bpm_log_ts = now
                if self.on_bpm:
                    try:
                        self.on_bpm(None)
                    except Exception:
                        pass

    def start(self) -> bool:
        if self._enabled:
            return True
        if not MIDI_AVAILABLE:
            logger.warning("MIDI packages not installed. Please install 'mido' and 'python-rtmidi'.")
            return False
        port_name = self._select_input_port()
        if not port_name:
            logger.warning("No MIDI input ports found.")
            return False
        try:
            self._port_name = port_name
            self._port = mido.open_input(port_name, callback=self._handle_message)
            # Ensure timing (clock) messages are not filtered by backend defaults
            ignored_set = False
            try:
                # rtmidi backend
                self._port._port.ignore_types(sysex=False, timing=False, sensing=False)  # type: ignore[attr-defined]
                ignored_set = True
            except Exception:
                try:
                    self._port._rtmidi.ignore_types(sysex=False, timing=False, sensing=False)  # type: ignore[attr-defined]
                    ignored_set = True
                except Exception:
                    pass
            if ignored_set:
                logger.info("MIDI clock listener: timing messages unignored (sysex=False, timing=False, sensing=False)")
            else:
                logger.info("MIDI clock listener: could not adjust ignore_types; relying on backend defaults")
            self._enabled = True
            self._stop.clear()
            self._start_ts = time.monotonic()
            self._tick_count = 0
            self._no_tick_logged = False
            self._last_emit_ts = 0.0
            self._last_bpm_log_ts = 0.0
            self._smoothed_bpm = None
            self._watchdog_thread = threading.Thread(target=self._watchdog, daemon=True)
            self._watchdog_thread.start()
            logger.info(f"MIDI clock listening on port: {port_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to open MIDI input port: {e}")
            self._enabled = False
            self._port = None
            return False

    def stop(self) -> None:
        self._stop.set()
        if self._watchdog_thread and self._watchdog_thread.is_alive():
            self._watchdog_thread.join(timeout=1.0)
        self._watchdog_thread = None
        try:
            if self._port:
                self._port.close()
        except Exception:
            pass
        self._port = None
        self._enabled = False
        self._current_bpm = None

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def bpm(self) -> Optional[float]:
        return self._current_bpm


class MidiHelper:
    def __init__(self, preferred_port_name=None):
        self.enabled = False
        self.port = None
        self.lock = threading.Lock()
        self.error = None
        self.preferred_port_name = preferred_port_name

    def enable(self):
        if not MIDI_AVAILABLE:
            self.error = "MIDI packages not installed. Please install 'mido' and 'python-rtmidi'."
            logger.warning(self.error)
            return False
        try:
            ports = mido.get_output_names()
            # Log once via tracord logger; avoid duplicate root prints
            logger.info(f"Available MIDI output ports: {ports}")
            port_to_use = None
            # Prefer exact match when a preferred name is provided
            if self.preferred_port_name:
                for p in ports:
                    if p.strip().lower() == self.preferred_port_name.strip().lower():
                        port_to_use = p
                        break
                # If no exact match, try substring match as a fallback
                if not port_to_use:
                    for p in ports:
                        if self.preferred_port_name.strip().lower() in p.strip().lower():
                            port_to_use = p
                            break
            if not port_to_use and ports:
                port_to_use = ports[0]
            if not port_to_use:
                self.error = "No MIDI output ports found."
                logger.warning(self.error)
                return False
            self.port = mido.open_output(port_to_use)
            # Avoid duplicate enable logs if already enabled on same port
            if not self.enabled:
                logger.info(f"MIDI output enabled on port: {port_to_use}")
            self.enabled = True
            self.error = None
            return True
        except Exception as e:
            self.error = f"Failed to open MIDI port: {e}"
            logger.error(self.error)
            return False

    def disable(self):
        with self.lock:
            if self.port:
                try:
                    self.port.close()
                    logger.info("MIDI output port closed.")
                except Exception as e:
                    logger.warning(f"Error closing MIDI port: {e}")
            self.port = None
            self.enabled = False

    def send_song_change(self, *, note: int = 60, channel: int = 0, duration: float = 0.3) -> None:
        """Send a short Note On/Off pulse (C4 by default) without blocking the UI.

        note: MIDI note number (default C4=60)
        channel: MIDI channel (0-15)
        duration: seconds between Note On and Note Off
        """
        if not self.enabled or not self.port:
            return
        try:
            import random

            velocity = random.randint(1, 100)
            msg_on = mido.Message('note_on', note=note, velocity=velocity, channel=channel)
            msg_off = mido.Message('note_off', note=note, velocity=0, channel=channel)

            def _send_pulse():
                try:
                    import time
                    self.port.send(msg_on)
                    logger.info(f"MIDI Note On sent (note={note}, ch={channel+1}, vel={velocity})")
                    time.sleep(max(0.01, duration))
                    self.port.send(msg_off)
                except Exception as inner_e:
                    self.error = f"Failed to send MIDI message: {inner_e}"
                    logger.error(self.error)
                    self.disable()

            threading.Thread(target=_send_pulse, daemon=True).start()
        except Exception as e:
            self.error = f"Failed to prepare MIDI message: {e}"
            logger.error(self.error)
            self.disable()

    def get_error(self):
        return self.error
