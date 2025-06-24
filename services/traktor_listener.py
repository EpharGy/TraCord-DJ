import threading
import socketserver
import http.server
import io
import os
import struct
import codecs
import queue
import sys
from typing import Optional
from utils.logger import info, warning, error

def create_traktor_handler(status_queue, shutdown_event):
    class TraktorListenerHandler(http.server.BaseHTTPRequestHandler):
        def do_SOURCE(self):
            if status_queue:
                status_queue.put('listening')
            self.send_response(200)
            self.end_headers()
            info("[Traktor Listener] Traktor connected, receiving stream...")
            try:
                while not shutdown_event.is_set():
                    header_data = self.rfile.read(27)
                    if not header_data or len(header_data) < 27:
                        break
                    header = struct.unpack('<4sBBqIIiB', header_data)
                    oggs, version, flags, pos, serial, pageseq, crc, segments = header
                    if oggs != b'OggS' or version != 0:
                        break
                    segsizes = struct.unpack('B'*segments, self.rfile.read(segments))
                    total = 0
                    for segsize in segsizes:
                        total += segsize
                        if total < 255:
                            self.rfile.read(total)
                            total = 0
                    if total != 0:
                        if total % 255 == 0:
                            self.rfile.read(total)
                        else:
                            self.rfile.read(total)
            except Exception as e:
                warning(f"[Traktor Listener] Handler error: {e}")

        def log_request(self, code='-', size='-'):
            pass
        def log_error(self, format, *args):
            pass
    return TraktorListenerHandler

class TraktorBroadcastListener:
    def __init__(self, port, status_callback=None):
        self.port = port
        self.status_callback = status_callback
        self.httpd = None
        self.thread = None
        self.status_queue = queue.Queue()
        self.shutdown_event = threading.Event()
        self.running = False

    def start(self):
        if self.running:
            return
        self.running = True
        self.shutdown_event.clear()
        handler_cls = create_traktor_handler(self.status_queue, self.shutdown_event)
        self.httpd = socketserver.TCPServer(("", self.port), handler_cls)
        self.httpd.timeout = 1
        self.thread = threading.Thread(target=self._serve, daemon=True)
        self.thread.start()
        if self.status_callback:
            self.status_callback('starting')

    def _serve(self):
        try:
            while not self.shutdown_event.is_set():
                self.httpd.handle_request()  # type: ignore[union-attr]
        except Exception as e:
            error(f"[Traktor Listener] Listener error: {e}")
        finally:
            self.running = False
            if self.status_callback:
                self.status_callback('offline')

    def stop(self):
        if self.httpd:
            self.shutdown_event.set()
            self.httpd.server_close()
            self.httpd = None
        self.running = False
        if self.status_callback:
            self.status_callback('offline')

    def poll_status(self):
        try:
            while True:
                status = self.status_queue.get_nowait()
                if self.status_callback:
                    self.status_callback(status)
        except queue.Empty:
            pass
