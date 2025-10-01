# Collaborative MindMap Backend

This backend has been enhanced to support collaborative mindmapping with room codes. Multiple users can now join the same room and contribute to a shared mindmap in real-time, even while speaking simultaneously.

## New Features

### 🏠 Room-Based Collaboration
- **Room Codes**: Users join rooms using 6-character alphanumeric codes
- **Shared MindMaps**: Each room has one shared mindmap that all users contribute to
- **Real-time Sync**: All users in a room see updates instantly
- **Concurrent Speech**: Multiple users can speak and transcribe simultaneously

### 🔒 Thread-Safe Operations
- **Atomic Operations**: All mindmap modifications are thread-safe
- **Race Condition Prevention**: Concurrent users won't corrupt the mindmap data
- **Statistics Engine**: Per-room statistics engine that runs on speech timeouts

## API Endpoints

### REST API
- `POST /api/create-room` - Create a new room and get a room code
- `GET /api/room-stats` - Get statistics about all active rooms

### WebSocket Events

#### Client → Server
- `join_room` - Join a room with a room code
  ```json
  { "room_code": "ABC123" }
  ```
- `leave_room` - Leave the current room
- `audio_chunk` - Send audio data for transcription (binary)
- `get_room_info` - Get current room information

#### Server → Client
- `connection_status` - Connection confirmation
- `room_joined` - Successfully joined a room
  ```json
  {
    "room_code": "ABC123",
    "user_count": 2,
    "mindmap": {...},
    "message": "Successfully joined room ABC123"
  }
  ```
- `room_left` - Successfully left a room
- `room_error` - Error with room operations
- `user_joined` - Another user joined the room
- `user_left` - Another user left the room
- `node_instruction` - MindMap updates (add/modify/delete nodes)
  ```json
  {
    "action": "add",
    "content": "Hello World",
    "speakerID": "1",
    "connectTo": "0",
    "id": "123",
    "room_code": "ABC123",
    "from_user": "user_session_id"
  }
  ```

## Usage Flow

### 1. Connect to Server
```javascript
const socket = io('http://localhost:2500');
```

### 2. Join or Create Room
```javascript
// Create a new room
fetch('/api/create-room', { method: 'POST' })
  .then(r => r.json())
  .then(data => {
    socket.emit('join_room', { room_code: data.room_code });
  });

// Or join existing room
socket.emit('join_room', { room_code: 'ABC123' });
```

### 3. Start Audio Recording
```javascript
// Get microphone access and send audio chunks
navigator.mediaDevices.getUserMedia({ audio: true })
  .then(stream => {
    const mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) {
        event.data.arrayBuffer().then(buffer => {
          socket.emit('audio_chunk', buffer);
        });
      }
    };
    mediaRecorder.start(100); // Send chunks every 100ms
  });
```

### 4. Listen for MindMap Updates
```javascript
socket.on('node_instruction', (data) => {
  if (data.action === 'add') {
    // Add new node to UI
    addNodeToMindMap(data);
  } else if (data.action === 'modify') {
    // Update existing node
    updateNode(data);
  } else if (data.action === 'delete') {
    // Remove node
    removeNode(data);
  }
});
```

## Architecture

### Room Management
- **RoomManager**: Global singleton managing all rooms
- **Room**: Individual room with shared mindmap and user list
- **Thread Safety**: All mindmap operations use locks to prevent race conditions

### Session Management
- **SessionState**: Per-user session handling GPT processing and Deepgram connection
- **Room Assignment**: Each session is associated with one room
- **Graceful Cleanup**: Sessions properly leave rooms on disconnect

### Audio Processing Pipeline
1. **Client**: Records audio and sends chunks via WebSocket
2. **Deepgram**: Processes audio and returns transcriptions
3. **GPT**: Analyzes transcriptions and generates mindmap actions
4. **Room**: Applies actions to shared mindmap (thread-safe)
5. **Broadcast**: Sends updates to all users in the room

## Running the Server

### Prerequisites
```bash
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file with:
```
API_KEY=your_deepgram_api_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

### Start Server
```bash
python app.py
```

The server will start on `http://localhost:2500`

## Testing

### Run Unit Tests
```bash
python test_rooms.py
```

### Manual Testing
1. Open `http://localhost:2500` in multiple browser tabs
2. Create a room in one tab
3. Join the same room in other tabs using the room code
4. Start recording in multiple tabs simultaneously
5. Verify that all users see the same mindmap updates

## Concurrency Handling

### Multiple Speakers
- Each user can record audio simultaneously
- Deepgram processes each audio stream independently
- GPT processes transcriptions from different users in parallel
- Room-level locks ensure thread-safe mindmap updates
- Statistics engine runs per-room with proper synchronization

### Race Condition Prevention
- All mindmap operations use `threading.Lock()`
- Atomic operations for node addition/modification/deletion
- Safe transcript updates with proper synchronization
- Room cleanup happens atomically when last user leaves

## Scalability Considerations

### Current Limitations
- In-memory storage (rooms are lost on server restart)
- Single server instance
- No persistent chat history

### Future Improvements
- Database persistence for rooms and mindmaps
- Redis for distributed room management
- Load balancing across multiple server instances
- Room persistence and recovery
- User authentication and room permissions

## Error Handling

### Room Errors
- Invalid room codes
- Room not found
- User already in room
- Maximum room capacity (if implemented)

### Audio Errors
- Microphone access denied
- Deepgram connection issues
- Audio processing failures
- Network connectivity problems

### Recovery Mechanisms
- Automatic reconnection for WebSocket
- Graceful degradation when services are unavailable
- Clear error messages to users
- Proper cleanup on failures
