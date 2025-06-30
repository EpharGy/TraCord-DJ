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
from utils.events import emit
from utils.song_matcher import get_song_info
from utils.stats import increment_stat
import json
from datetime import datetime
from config.settings import Settings

COLLECTION_PATH = Settings.COLLECTION_JSON_FILE

def create_traktor_handler(status_queue, shutdown_event):
    class TraktorListenerHandler(http.server.BaseHTTPRequestHandler):
        def do_SOURCE(self):
            if status_queue:
                status_queue.put('listening')
            self.send_response(200)
            self.end_headers()
            info("[Traktor] Traktor connected, receiving stream...")
            try:
                # Load collection once per connection.
                try:
                    with open(COLLECTION_PATH, 'r', encoding='utf-8') as f:
                        collection = json.load(f)
                except Exception as e:
                    collection = []
                    warning(f"[Traktor] Could not load collection.json: {e}")
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
                            packet = self.rfile.read(total)
                            # Check for Vorbis comment block
                            if packet[:7] == b"\x03vorbis":
                                walker = io.BytesIO(packet)
                                walker.seek(7, os.SEEK_CUR)
                                # Parse Vorbis comments
                                try:
                                    vendor_length = struct.unpack('I', walker.read(4))[0]
                                    walker.seek(vendor_length, os.SEEK_CUR)
                                    elements = struct.unpack('I', walker.read(4))[0]
                                    tags = {}
                                    for _ in range(elements):
                                        length = struct.unpack('I', walker.read(4))[0]
                                        try:
                                            keyvalpair = codecs.decode(walker.read(length), 'UTF-8')
                                        except UnicodeDecodeError:
                                            continue
                                        if '=' in keyvalpair:
                                            key, value = keyvalpair.split('=', 1)
                                            tags[key.upper()] = value
                                    # Only process as a song if there is at least one tag other than ENCODER
                                    tag_keys = set(tags.keys())
                                    info(f"[Traktor] Parsed tags: {tags}")
                                    # Only skip if the ONLY tag is ENCODER
                                    if tag_keys == {"ENCODER"}:
                                        total = 0
                                        continue
                                    artist = tags.get('ARTIST', '').strip()
                                    title = tags.get('TITLE', '').strip()
                                    # Skip if both artist and title are missing or empty
                                    if not artist and not title:
                                        total = 0
                                        continue
                                    # Try to match in collection
                                    from utils.song_matcher import find_song_in_collection
                                    match = find_song_in_collection(artist, title, collection)
                                    song_info = get_song_info(artist, title, collection)
                                    if match:
                                        info(f"[Traktor] Song Played: {song_info['artist']} - {song_info['title']} [{song_info.get('album','')}]" )
                                    else:
                                        warning(f"[Traktor] Unable to Match Song: {artist} | {title}")
                                        try:
                                            dt = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
                                            unmatched_path = os.path.join(Settings.USER_DATA_DIR, "Debug_unmatched_songs.txt")
                                            with open(unmatched_path, "a", encoding="utf-8") as f:
                                                f.write(f"{dt} ARTIST: {artist or '[MISSING]'} | TITLE: {title or '[MISSING]'}\n")
                                        except Exception as e:
                                            warning(f"[Traktor] Could not write unmatched song: {e}")
                                    emit("song_played", song_info)
                                    increment_stat("total_song_plays", 1)
                                    increment_stat("session_song_plays", 1)
                                except Exception as e:
                                    warning(f"[Traktor] Error parsing Vorbis comment: {e}")
                            total = 0
                    if total != 0:
                        if total % 255 == 0:
                            self.rfile.read(total)
                        else:
                            self.rfile.read(total)
            except Exception as e:
                warning(f"[Traktor] Handler error: {e}")

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
            error(f"[Traktor] Listener error: {e}")
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
