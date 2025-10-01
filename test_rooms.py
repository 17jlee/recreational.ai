#!/usr/bin/env python3
"""
Test script for the collaborative mindmap room system.
This script tests the room management functionality.
"""

from room_manager import RoomManager
import threading
import time

def test_room_manager():
    """Test the basic room management functionality"""
    print("Testing Room Manager...")
    
    rm = RoomManager()
    
    # Test room creation
    room_code1 = rm.create_room()
    print(f"Created room: {room_code1}")
    
    room_code2 = rm.create_room("TEST01")
    print(f"Created room with custom code: {room_code2}")
    
    # Test joining rooms
    room1 = rm.join_room("user1", room_code1)
    room2 = rm.join_room("user2", room_code1)  # Same room
    room3 = rm.join_room("user3", room_code2)  # Different room
    
    print(f"Room {room_code1} has {room1.get_user_count()} users")
    print(f"Room {room_code2} has {room3.get_user_count()} users")
    
    # Test mindmap operations
    node_id1 = room1.add_node_safe("Hello from user1", 1, 0)
    node_id2 = room1.add_node_safe("Hello from user2", 2, 0)
    print(f"Added nodes {node_id1} and {node_id2} to room {room_code1}")
    
    # Test thread safety with concurrent operations
    def add_nodes(room, user_id, count):
        for i in range(count):
            content = f"Node {i} from user {user_id}"
            node_id = room.add_node_safe(content, user_id, 0)
            print(f"User {user_id} added node {node_id}: {content}")
            time.sleep(0.1)  # Small delay to simulate real usage
    
    # Create threads to simulate concurrent users
    threads = []
    for user_id in [1, 2, 3]:
        thread = threading.Thread(target=add_nodes, args=(room1, user_id, 3))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    print("\nFinal mindmap state:")
    print(room1.get_mindmap_json())
    
    # Test leaving rooms
    rm.leave_room("user1")
    rm.leave_room("user2")
    print(f"After users left, room {room_code1} has {room1.get_user_count()} users")
    
    # Test room cleanup
    rm.leave_room("user3")  # This should clean up room2
    stats = rm.get_room_stats()
    print(f"Remaining rooms: {len(stats)}")
    print("Room stats:", stats)
    
    print("Room Manager test completed successfully!")

if __name__ == "__main__":
    test_room_manager()
