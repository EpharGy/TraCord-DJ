"""
Test script for Web Overlay Server
Run this to test the overlay functionality with sample data
"""
import sys
import os
import time
import threading

# Add the parent directory to the path so we can import from services
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.web_overlay import WebOverlayServer

def simulate_song_changes(server):
    """Simulate song changes for testing"""
    sample_songs = [
        {
            'artist': 'Daft Punk',
            'title': 'One More Time',
            'album': 'Discovery',
            'bpm': 123,
            'key': 'F# Minor'
        },
        {
            'artist': 'Justice',
            'title': 'Genesis',
            'album': 'Cross',
            'bpm': 120,
            'key': 'G Major'
        },
        {
            'artist': 'Deadmau5',
            'title': 'Strobe',
            'album': 'For Lack of a Better Name',
            'bpm': 128,
            'key': 'Db Major'
        }
    ]
    
    time.sleep(3)  # Wait for server to start
    
    for i, song in enumerate(sample_songs):
        print(f"Sending song {i+1}: {song['artist']} - {song['title']}")
        server.update_now_playing(song)
        time.sleep(10)  # Wait 10 seconds between songs
    
    # Test no song playing
    print("Sending no song playing")
    server.send_no_song_playing()

if __name__ == "__main__":
    # Create and start the server
    server = WebOverlayServer(host='127.0.0.1', port=5000)
    server.start_server()
    
    print("Web Overlay Server Test")
    print("=" * 30)
    print("Server starting on http://127.0.0.1:5000")
    print("Open this URL in OBS Browser Source or web browser")
    print("Press Ctrl+C to stop")
    print()
    
    # Start song simulation in background
    sim_thread = threading.Thread(target=simulate_song_changes, args=(server,), daemon=True)
    sim_thread.start()
    
    try:
        # Keep the main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.stop_server()
        print("Server stopped.")
