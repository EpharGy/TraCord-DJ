"""
Flask-SocketIO Web Overlay Server for OBS Integration
Provides real-time now playing information via WebSocket
"""
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
import threading
import time
from utils.logger import info, debug, warning, error
from utils.events import subscribe, unsubscribe

class WebOverlayServer:
    """Flask-SocketIO server for web overlay functionality"""
    
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.app = Flask(__name__, template_folder='../web_overlay/templates')
        self.app.config['SECRET_KEY'] = 'tracord_dj_overlay_secret'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        self.is_running = False
        self.server_thread = None
        self.current_song = None  # Store current song data
        self.setup_routes()
        self.setup_socket_events()
        self.setup_event_subscriptions()
        
    def setup_routes(self):
        """Set up Flask routes"""
        @self.app.route('/')
        def overlay():
            """Serve the main overlay page"""
            return render_template('overlay.html')
            
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            return {'status': 'ok', 'message': 'Web overlay server is running'}
    
    def setup_socket_events(self):
        """Set up SocketIO event handlers"""
        @self.socketio.on('connect')
        def handle_connect():
            debug("WebSocket client connected")
            # Send current song data to newly connected client
            self.send_current_song()
            
        @self.socketio.on('disconnect')
        def handle_disconnect():
            debug("WebSocket client disconnected")
    
    def setup_event_subscriptions(self):
        """Subscribe to song_played events from the Traktor listener"""
        subscribe("song_played", self.on_song_played)
        info("[Overlay] Subscribed to song_played events")
        debug("Web overlay subscribed to song_played events")
    
    def on_song_played(self, song_info):
        """Handle song_played events and broadcast to overlay clients"""
        # Log song info without full coverart_base64
        log_info = dict(song_info)
        if 'coverart_base64' in log_info:
            log_info['coverart_base64'] = f"<base64 string, {len(log_info['coverart_base64'])} bytes>"
        debug(f"[Overlay] Received song_played event: {log_info}")
        
        if not song_info:
            warning("[Overlay] Received empty song_info")
            return
            
        self.current_song = song_info
        
        # Format song data for overlay
        overlay_data = {
            'artist': song_info.get('artist', ''),
            'title': song_info.get('title', ''),
            'album': song_info.get('album', ''),
            'bpm': song_info.get('bpm', ''),
            'key': song_info.get('musical_key', ''),  # Note: using 'musical_key' from your data
            'genre': song_info.get('genre', ''),
            'audio_file_path': song_info.get('audio_file_path', ''),
            'coverart_base64': song_info.get('coverart_base64', ''),
            'timestamp': time.time()
        }
        
        # Log overlay_data without full coverart_base64
        overlay_log = dict(overlay_data)
        if 'coverart_base64' in overlay_log:
            overlay_log['coverart_base64'] = f"<base64 string, {len(overlay_log['coverart_base64'])} bytes>"
        debug(f"[Overlay] Formatted data: {overlay_log}")
        
        # Broadcast to all connected clients
        if self.is_running:
            self.socketio.emit('song_update', overlay_data)
            info(f"[Overlay] Broadcasting: {overlay_data['artist']} - {overlay_data['title']}")
        else:
            warning("[Overlay] Server not running, skipping broadcast")
    
    def start_server(self):
        """Start the web overlay server in a background thread"""
        if self.is_running:
            warning("Web overlay server is already running")
            return
            
        self.is_running = True
        self.server_thread = threading.Thread(
            target=self._run_server,
            daemon=True,
            name="WebOverlayServer"
        )
        self.server_thread.start()
        info(f"Web overlay server starting on http://{self.host}:{self.port}")
    
    def stop_server(self):
        """Stop the web overlay server"""
        if not self.is_running:
            return
            
        # Unsubscribe from events
        unsubscribe("song_played", self.on_song_played)
        
        self.is_running = False
        info("Web overlay server stopped")
    
    def _run_server(self):
        """Run the Flask-SocketIO server"""
        try:
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                log_output=False
            )
        except Exception as e:
            error(f"Web overlay server error: {e}")
            self.is_running = False
    
    def send_current_song(self):
        """Send current song data to newly connected clients"""
        if self.current_song:
            # Send the current song to newly connected client
            overlay_data = {
                'artist': self.current_song.get('artist', ''),
                'title': self.current_song.get('title', ''),
                'album': self.current_song.get('album', ''),
                'bpm': self.current_song.get('bpm', ''),
                'key': self.current_song.get('musical_key', ''),
                'genre': self.current_song.get('genre', ''),
                'audio_file_path': self.current_song.get('audio_file_path', ''),
                'coverart_base64': self.current_song.get('coverart_base64', ''),
                'timestamp': time.time()
            }
            self.socketio.emit('song_update', overlay_data)
            debug(f"Sent current song to new client: {overlay_data['artist']} - {overlay_data['title']}")
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
        
        self.socketio.emit('song_update', overlay_data)
        debug(f"Broadcasting song update: {overlay_data['artist']} - {overlay_data['title']}")
    
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
            'timestamp': time.time()
        }
        
        self.socketio.emit('song_update', empty_data)
        debug("Broadcasting no song playing")
