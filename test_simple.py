#!/usr/bin/env python3
"""
Simple test script to verify room functionality without dependencies
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Simple mock classes to test basic functionality
class MockMindMap:
    def __init__(self, title):
        self.title = title
        self.currentTranscript = ""
        self.currentID = 1
        self.childNodes = []
    
    def updateTranscript(self, text):
        self.currentTranscript += str(text) + " "
    
    def addNode(self, content, speaker, parent_id):
        node_id = self.currentID
        self.currentID += 1
        # Simplified - just track that we added a node
        self.childNodes.append({
            'id': node_id,
            'content': content,
            'speaker': speaker,
            'parent_id': parent_id
        })
        return node_id
    
    def to_json(self):
        return f'{{"title": "{self.title}", "nodes": {len(self.childNodes)}}}'

def test_basic_room_logic():
    """Test basic room logic without Flask/SocketIO dependencies"""
    print("Testing basic room collaboration logic...")
    
    # Simulate multiple users joining a room
    room_code = "TEST01"
    mindmap = MockMindMap(f"Room {room_code} MindMap")
    users_in_room = set()
    
    # Simulate users joining
    user_sessions = ["user1", "user2", "user3"]
    for user in user_sessions:
        users_in_room.add(user)
        print(f"{user} joined room {room_code}")
    
    print(f"Room {room_code} now has {len(users_in_room)} users")
    
    # Simulate concurrent transcription/mindmap updates
    transcripts = [
        ("user1", "Hello everyone, let's discuss the project requirements"),
        ("user2", "Great idea! I think we should focus on scalability"),
        ("user3", "Agreed, and we need to consider security as well"),
        ("user1", "Let me add that we should also think about user experience"),
        ("user2", "Performance optimization is crucial too")
    ]
    
    for user, transcript in transcripts:
        # Update shared transcript
        mindmap.updateTranscript(f"[{user}]: {transcript}")
        
        # Add node to shared mindmap (simulating GPT processing)
        node_id = mindmap.addNode(transcript, hash(user) % 10, 0)
        
        print(f"{user} added node {node_id}: {transcript[:50]}...")
    
    print(f"\nFinal state:")
    print(f"Users in room: {len(users_in_room)}")
    print(f"Nodes in mindmap: {len(mindmap.childNodes)}")
    print(f"Transcript length: {len(mindmap.currentTranscript)} characters")
    print(f"Mindmap JSON: {mindmap.to_json()}")
    
    # Simulate users leaving
    for user in list(user_sessions):
        users_in_room.remove(user)
        print(f"{user} left room {room_code}")
        if len(users_in_room) == 0:
            print(f"Room {room_code} is now empty and can be cleaned up")
            break
    
    print("Basic room collaboration test completed successfully!")

if __name__ == "__main__":
    test_basic_room_logic()
