"""
Event system for TraCord DJ
Allows different components to communicate without direct dependencies
"""
from typing import Callable, Dict, List, Any
from utils.logger import debug

class EventSystem:
    """Simple event system for communication between components"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventSystem, cls).__new__(cls)
            cls._instance._subscribers = {}
        return cls._instance
        
    def __init__(self):
        # Initialize subscribers dict if it doesn't exist
        if not hasattr(self, "_subscribers"):
            self._subscribers = {}

    def subscribe(self, event_name: str, callback: Callable) -> None:
        """Subscribe to an event"""
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []
        self._subscribers[event_name].append(callback)
        debug(f"Subscribed to event: {event_name}")
    
    def unsubscribe(self, event_name: str, callback: Callable) -> None:
        """Unsubscribe from an event"""
        if event_name in self._subscribers and callback in self._subscribers[event_name]:
            self._subscribers[event_name].remove(callback)
            debug(f"Unsubscribed from event: {event_name}")
    
    def emit(self, event_name: str, data: Any = None) -> None:
        """Emit an event with optional data"""
        if event_name in self._subscribers:
            for callback in self._subscribers[event_name]:
                try:
                    callback(data)
                except Exception as e:
                    debug(f"Error in event subscriber: {e}")

# Create a singleton instance
event_system = EventSystem()

# Convenience functions
def subscribe(event_name: str, callback: Callable) -> None:
    """Subscribe to an event"""
    event_system.subscribe(event_name, callback)

def unsubscribe(event_name: str, callback: Callable) -> None:
    """Unsubscribe from an event"""
    event_system.unsubscribe(event_name, callback)

def emit(event_name: str, data: Any = None) -> None:
    """Emit an event with optional data"""
    event_system.emit(event_name, data)
