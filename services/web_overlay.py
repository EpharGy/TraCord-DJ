"""
Flask-SocketIO Web Overlay Server for OBS Integration
Provides real-time now playing information via WebSocket
"""
from flask import Flask, render_template
from flask_socketio import SocketIO
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from tracord.core.events import EventTopic, subscribe_event
from utils.harmonic_keys import open_key_int_to_str
from utils.logger import get_logger


logger = get_logger(__name__)

@dataclass(slots=True)
class OverlaySong:
    artist: str
    title: str
    album: str
    bpm: str
    key: str
    genre: str
    audio_file_path: str
    coverart_base64: str
    timestamp: float

    @classmethod
    def from_song_info(cls, song_info: Dict[str, Any]) -> "OverlaySong":
        musical_key = song_info.get('musical_key', '')
        key_str = open_key_int_to_str(musical_key) if musical_key not in ('', None) else ''
        return cls(
            artist=song_info.get('artist', ''),
            title=song_info.get('title', ''),
            album=song_info.get('album', ''),
            bpm=str(song_info.get('bpm', '')),
            key=key_str,
            genre=song_info.get('genre', ''),
            audio_file_path=song_info.get('audio_file_path', ''),
            coverart_base64=song_info.get('coverart_base64', ''),
            timestamp=time.time(),
        )

    def to_payload(self) -> Dict[str, Any]:
        return {
            'artist': self.artist,
            'title': self.title,
            'album': self.album,
            'bpm': self.bpm,
            'key': self.key,
            'genre': self.genre,
            'audio_file_path': self.audio_file_path,
            'coverart_base64': self.coverart_base64,
            'timestamp': self.timestamp,
        }

    def masked_log(self) -> Dict[str, Any]:
        payload = self.to_payload()
        if payload.get('coverart_base64'):
            payload['coverart_base64'] = f"<base64 string, {len(self.coverart_base64)} bytes>"
        return payload


class WebOverlayServer:
    """Flask-SocketIO server for web overlay functionality"""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder='../web_overlay/templates')
        self.app.config['SECRET_KEY'] = 'tracord_dj_overlay_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode="threading")
        self.is_running = False
        self.server_thread = None  # type: Optional[threading.Thread]
        self.current_song = None  # type: Optional[OverlaySong]
        self._latest_payload = None  # type: Optional[Dict[str, Any]]
        self._event_unsubscribers: List[Callable[[], None]] = []

        self.setup_routes()
        self.setup_socket_events()
        self.setup_event_subscriptions()
        
    def setup_routes(self):
        """Set up Flask routes"""
        @self.app.route('/')
        def overlay():
            """Serve the main overlay page"""
            return render_template('default_overlay.html')
            
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'ok', 'message': 'Web overlay server is running'}
    
    def setup_socket_events(self):
        """Set up SocketIO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            logger.debug("WebSocket client connected")
            # Send current song data to newly connected client
            self.send_current_song()
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            logger.debug("WebSocket client disconnected")
    
    def setup_event_subscriptions(self):
        """Subscribe to song_played events from the Traktor listener"""
        self._event_unsubscribers.append(
            subscribe_event(EventTopic.SONG_PLAYED, self.on_song_played)
        )
        logger.info("[Overlay] Subscribed to song_played events")
        logger.debug("Web overlay subscribed to song_played events")
    
    def on_song_played(self, song_info: Optional[Dict[str, Any]]):
        """Handle song_played events and broadcast to overlay clients"""
        if not song_info:
            logger.warning("[Overlay] Received empty song_info")
            return

        overlay_song = OverlaySong.from_song_info(song_info)
        logger.debug(f"[Overlay] Received song_played event: {overlay_song.masked_log()}")
        self.current_song = overlay_song

        payload = overlay_song.to_payload()
        self._latest_payload = payload

        if not self.is_running:
            logger.debug("[Overlay] Received song update while server stopped; cached payload only")
            return

        self.socketio.emit('song_update', payload)
        logger.info(f"[Overlay] Broadcasting: {overlay_song.artist} - {overlay_song.title}")
    
    def start_server(self):
        """Start the web overlay server in a background thread"""
        if self.is_running:
            logger.warning("Web overlay server is already running")
            return
            
        self.is_running = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="WebOverlayServer"
        )
        self.server_thread.start()
        logger.info(f"Web overlay server starting on http://{self.host}:{self.port}")
        if self.current_song and not self._latest_payload:
            self._latest_payload = self.current_song.to_payload()
    
    def stop_server(self):
        """Stop the web overlay server"""
        if not self.is_running:
            return
            
        self.is_running = False
        logger.info("Web overlay server stopped")
        while self._event_unsubscribers:
            unsubscribe = self._event_unsubscribers.pop()
            unsubscribe()
    
    def _run_server(self):
        """Run the Flask-SocketIO server"""
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                log_output=False,
                allow_unsafe_werkzeug=True
            )
        except Exception as e:
            logger.error(f"Web overlay server error: {e}")
            self.is_running = False
    
    def send_current_song(self):
        """Send current song data to newly connected clients"""
        payload = self._latest_payload or (self.current_song.to_payload() if self.current_song else None)
        if payload:
            if payload is not self._latest_payload:
                self._latest_payload = payload
            self.socketio.emit('song_update', payload)
            logger.debug(f"Sent current song to new client: {payload['artist']} - {payload['title']}")
        else:
            # No current song, send empty data
            self.send_no_song_playing()
    
    def update_now_playing(self, song_data):
        """Update now playing information and broadcast to clients"""
        if not self.is_running:
            return
            
        # Format song data for overlay
        overlay_data = {
            'artist': song_data.get('artist', ''),
            'title': song_data.get('title', ''),
            'album': song_data.get('album', ''),
            'bpm': song_data.get('bpm', ''),
            'key': song_data.get('key', ''),
            'timestamp': time.time()
        }
        self._latest_payload = overlay_data
        self.socketio.emit('song_update', overlay_data)
        logger.debug(f"Broadcasting song update: {overlay_data['artist']} - {overlay_data['title']}")
    
    def send_no_song_playing(self):
        """Send empty/no song data to clients"""
        if not self.is_running:
            return
            
        empty_data = {
            'artist': '',
            'title': '',
            'album': '',
            'bpm': '',
            'key': '',
            'genre': '',
            'audio_file_path': '',
            'coverart_base64': '',
            'timestamp': time.time()
        }
        
        self._latest_payload = empty_data
        self.socketio.emit('song_update', empty_data)
        logger.debug("Broadcasting no song playing")

