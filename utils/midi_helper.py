# type: ignore
"""
MIDI helper for TraCord DJ: optional MIDI out for song change events.
Uses mido (with python-rtmidi backend) if available.
"""

import threading

from utils.logger import get_logger

try:
    import mido
    MIDI_AVAILABLE = True
except ImportError:
    mido = None
    MIDI_AVAILABLE = False

logger = get_logger(__name__)


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
