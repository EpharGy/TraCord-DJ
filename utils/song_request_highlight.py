# song_request_highlight.py
# Utility for tracking and managing highlight state for song requests in the GUI

import threading

class SongRequestHighlighter:
    def __init__(self):
        self._highlighted = {}  # key: request id, value: timer/thread
        self._lock = threading.Lock()

    def highlight(self, request_id, callback, duration=5, color=None):
        """Highlight a request for a duration, then call callback to revert."""
        with self._lock:
            if request_id in self._highlighted:
                self._highlighted[request_id].cancel()
            timer = threading.Timer(duration, lambda: self._finish(request_id, callback))
            self._highlighted[request_id] = timer
            timer.start()
        return color

    def _finish(self, request_id, callback):
        with self._lock:
            if request_id in self._highlighted:
                del self._highlighted[request_id]
        callback(request_id)

    def cancel(self, request_id):
        with self._lock:
            if request_id in self._highlighted:
                self._highlighted[request_id].cancel()
                del self._highlighted[request_id]

    def clear(self):
        with self._lock:
            for timer in self._highlighted.values():
                timer.cancel()
            self._highlighted.clear()

highlighter = SongRequestHighlighter()
