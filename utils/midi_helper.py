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
            logger.info(f"Available MIDI output ports: {ports}")
            port_to_use = None
            if self.preferred_port_name:
                for p in ports:
                    if self.preferred_port_name.lower() in p.lower():
                        port_to_use = p
                        break
            if not port_to_use and ports:
                port_to_use = ports[0]
            if not port_to_use:
                self.error = "No MIDI output ports found."
                logger.warning(self.error)
                return False
            self.port = mido.open_output(port_to_use)
            self.enabled = True
            self.error = None
            logger.info(f"MIDI output enabled on port: {port_to_use}")
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

    def send_song_change(self):
        if not self.enabled or not self.port:
            return
        try:
            import time
            import random
            velocity = random.randint(1, 100)
            msg_on = mido.Message('note_on', note=60, velocity=velocity, channel=0)
            msg_off = mido.Message('note_off', note=60, velocity=0, channel=0)
            self.port.send(msg_on)
            logger.info(f"MIDI song change Note On sent (C4, vel={velocity})")
            time.sleep(0.5)  # 1 second delay
            self.port.send(msg_off)
            # info("MIDI song change Note Off sent (C4)")
        except Exception as e:
            self.error = f"Failed to send MIDI message: {e}"
            logger.error(self.error)
            self.disable()

    def get_error(self):
        return self.error
