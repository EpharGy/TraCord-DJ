"""
Test script for Web Overlay Server with Real Event Integration
This connects to your actual event system and listens for real song changes
"""
import sys
import os
import time
import threading

# Add the parent directory to the path so we can import from services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.web_overlay import WebOverlayServer
from utils.events import emit

def simulate_manual_song_changes(server):
    """Manually trigger song events for testing (if needed)"""
    time.sleep(5)  # Wait for server to start
    
    # Simulate a song_played event like your Traktor listener would
    sample_song_info = {
        'artist': 'Test Artist',
        'title': 'Test Song',
        'album': 'Test Album',
        'bpm': '128',
        'musical_key': 'Am',
        'genre': 'Electronic',
        'audio_file_path': '/path/to/song.mp3'
    }
    
    print("Manually triggering song_played event...")
    emit("song_played", sample_song_info)

if __name__ == "__main__":
    print("Web Overlay Server - Real Event Integration Test")
    print("=" * 50)
    print("This test connects to your actual event system.")
    print("Start Traktor and play songs to see real-time updates!")
    print()
    print("Server starting on http://127.0.0.1:5000")
    print("Open this URL in OBS Browser Source or web browser")
    print("Press Ctrl+C to stop")
    print()
    
    # Create and start the server (it will auto-subscribe to song_played events)
    server = WebOverlayServer(host='127.0.0.1', port=5000)
    server.start_server()
    
    # Optional: simulate a manual event after 5 seconds for testing
    sim_thread = threading.Thread(target=simulate_manual_song_changes, args=(server,), daemon=True)
    sim_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop_server()
        print("Server stopped.")
