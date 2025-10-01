# room_manager.py
import threading
import mindmap
from typing import Dict, Set
import uuid
import queue

class Room:
    def __init__(self, room_code: str):
        self.room_code = room_code
        self.mindmap = mindmap.MindMap(f"Room {room_code} MindMap")
        self.users: Set[str] = set()  # Set of user session IDs
        self.mindmap_lock = threading.Lock()
        self.statistics_queue = queue.Queue()
        self.statistics_timer = None
        
    def add_user(self, user_sid: str):
        """Add a user to this room"""
        self.users.add(user_sid)
        
    def remove_user(self, user_sid: str):
        """Remove a user from this room"""
        self.users.discard(user_sid)
        
    def get_user_count(self) -> int:
        """Get the number of users in this room"""
        return len(self.users)
        
    def is_empty(self) -> bool:
        """Check if the room has no users"""
        return len(self.users) == 0
        
    def update_transcript(self, transcript: str):
        """Thread-safe method to update the mindmap transcript"""
        with self.mindmap_lock:
            self.mindmap.updateTranscript(transcript)
            
    def add_node_safe(self, content: str, speaker_id: int, parent_id: int) -> int:
        """Thread-safe method to add a node to the mindmap"""
        with self.mindmap_lock:
            return self.mindmap.addNode(content, speaker_id, parent_id)
            
    def delete_node_safe(self, node_id: int):
        """Thread-safe method to delete a node from the mindmap"""
        with self.mindmap_lock:
            self.mindmap.delete_by_id(node_id)
            
    def modify_node_safe(self, new_content: str, new_speaker_id: int, node_id: int):
        """Thread-safe method to modify a node in the mindmap"""
        with self.mindmap_lock:
            self.mindmap.modify_by_id(new_content, new_speaker_id, node_id)
            
    def set_title_safe(self, new_title: str):
        """Thread-safe method to set the mindmap title"""
        with self.mindmap_lock:
            self.mindmap.title = new_title
            
    def get_mindmap_json(self) -> str:
        """Thread-safe method to get the mindmap as JSON"""
        with self.mindmap_lock:
            return self.mindmap.to_json()
            
    def reset_statistics_timer(self, socketio, timeout_secs=5.0):
        """Reset the statistics timer for this room"""
        if self.statistics_timer is not None:
            self.statistics_timer.cancel()
        
        def run_statistics():
            try:
                # TODO: Re-enable statistics engine once eventlet issues are resolved
                print(f"Statistics timer triggered for room {self.room_code}")
                # with self.mindmap_lock:
                #     result = statisticsGPTEngine.GPTCall(self.mindmap.to_json())
                #     if result and result.content:
                #         new_id = self.mindmap.addNode(result.content, result.speakerID, result.parentID)
                #         
                #         # Emit to all users in the room
                #         socketio.emit("node_instruction", {
                #             "action": "add",
                #             "content": "StatisticsEngine: " + result.content,
                #             "speakerID": str(result.speakerID),
                #             "connectTo": str(result.parentID),
                #             "id": str(new_id),
                #             "room_code": self.room_code
                #         }, room=self.room_code)
            except Exception as e:
                print(f"Statistics Engine Error for room {self.room_code}:", e)
                
        self.statistics_timer = threading.Timer(timeout_secs, run_statistics)
        self.statistics_timer.start()

class RoomManager:
    def __init__(self):
        self.rooms: Dict[str, Room] = {}
        self.user_to_room: Dict[str, str] = {}  # user_sid -> room_code
        self.lock = threading.Lock()
        
    def generate_room_code(self) -> str:
        """Generate a unique 6-character room code"""
        while True:
            # Generate a 6-character alphanumeric code
            code = str(uuid.uuid4()).replace('-', '')[:6].upper()
            if code not in self.rooms:
                return code
                
    def create_room(self, room_code: str = None) -> str:
        """Create a new room and return the room code"""
        with self.lock:
            if room_code is None:
                room_code = self.generate_room_code()
            elif room_code in self.rooms:
                raise ValueError(f"Room code {room_code} already exists")
                
            self.rooms[room_code] = Room(room_code)
            return room_code
            
    def join_room(self, user_sid: str, room_code: str) -> Room:
        """Join a user to a room. Create room if it doesn't exist."""
        with self.lock:
            # Remove user from previous room if they were in one
            if user_sid in self.user_to_room:
                old_room_code = self.user_to_room[user_sid]
                if old_room_code in self.rooms:
                    self.rooms[old_room_code].remove_user(user_sid)
                    # Clean up empty rooms
                    if self.rooms[old_room_code].is_empty():
                        del self.rooms[old_room_code]
                        
            # Create room if it doesn't exist
            if room_code not in self.rooms:
                self.rooms[room_code] = Room(room_code)
                
            # Add user to new room
            room = self.rooms[room_code]
            room.add_user(user_sid)
            self.user_to_room[user_sid] = room_code
            
            return room
            
    def leave_room(self, user_sid: str) -> bool:
        """Remove a user from their current room"""
        with self.lock:
            if user_sid not in self.user_to_room:
                return False
                
            room_code = self.user_to_room[user_sid]
            if room_code in self.rooms:
                self.rooms[room_code].remove_user(user_sid)
                # Clean up empty rooms
                if self.rooms[room_code].is_empty():
                    # Cancel any pending statistics timer
                    if self.rooms[room_code].statistics_timer:
                        self.rooms[room_code].statistics_timer.cancel()
                    del self.rooms[room_code]
                    
            del self.user_to_room[user_sid]
            return True
            
    def get_user_room(self, user_sid: str) -> Room:
        """Get the room that a user is currently in"""
        with self.lock:
            if user_sid not in self.user_to_room:
                return None
            room_code = self.user_to_room[user_sid]
            return self.rooms.get(room_code)
            
    def get_room(self, room_code: str) -> Room:
        """Get a room by room code"""
        with self.lock:
            return self.rooms.get(room_code)
            
    def get_room_stats(self) -> Dict:
        """Get statistics about all rooms"""
        with self.lock:
            return {
                room_code: {
                    "user_count": room.get_user_count(),
                    "users": list(room.users)
                }
                for room_code, room in self.rooms.items()
            }
