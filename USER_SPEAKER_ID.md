# User-Specific Speaker ID System

## Overview
Each user in a room is now assigned a unique speaker ID that persists throughout their session. All mindmap nodes created from that user's speech will be tagged with their specific speaker ID, allowing for clear attribution of contributions.

## How It Works

### Speaker ID Assignment
- When a user **first joins a room**, they are automatically assigned a unique speaker ID
- Speaker IDs start at `1` and increment for each new user in the room
- Speaker IDs are **persistent**: Once assigned, a user keeps the same speaker ID even if they disconnect and rejoin the same room
- Each room has its own independent speaker ID space

### Speaker ID Mapping Flow

1. **User Joins Room**
   - User joins room `ABC123`
   - System checks if user already has a speaker ID in this room
   - If not, assigns next available speaker ID (e.g., `1`, `2`, `3`, etc.)
   - User's speaker ID is stored in `room.user_to_speaker_id` mapping

2. **Audio Processing**
   - User's audio is sent to Deepgram for transcription
   - Deepgram returns transcript with its own speaker diarization IDs (0, 1, 2, etc.)
   - System **overrides** Deepgram's speaker IDs with the user's assigned speaker ID
   - All speech from this user is tagged with their unique speaker ID

3. **Node Creation**
   - GPT processes the transcript with user-specific speaker IDs
   - When creating mindmap nodes, GPT uses the user's speaker ID
   - Nodes are stored with `speakerID` field matching the user's ID
   - Frontend can display nodes color-coded by speaker ID

### Special Speaker IDs

- **Speaker ID 0**: Reserved for system/title nodes
- **Speaker ID -41**: Reserved for Statistics Engine contributions
- **Speaker IDs 1+**: Assigned to actual users in sequential order

## Implementation Details

### Modified Files

#### 1. `room_manager.py`
```python
class Room:
    def __init__(self, room_code: str):
        self.user_to_speaker_id: Dict[str, int] = {}  # Maps user_sid -> speaker_id
        self.next_speaker_id = 1  # Increments for each new user
```

**New Methods:**
- `add_user()`: Assigns speaker ID when user joins
- `get_user_speaker_id(user_sid)`: Returns user's speaker ID

#### 2. `session.py`
```python
class SessionState:
    def __init__(self, sid, socketio, room_manager):
        self.user_speaker_id = None  # Set when joining room
```

**Changes:**
- `join_room()`: Gets and stores user's speaker ID
- `enqueue_transcript()`: Includes user_speaker_id with transcript
- `_gpt_worker()`: Maps Deepgram speaker IDs to user's speaker ID

#### 3. `app.py`
**Changes:**
- `handle_join_room()`: Sends `user_speaker_id` to frontend in `room_joined` event

### Data Flow Example

**Scenario**: Two users (Alice and Bob) join room `ABC123`

1. **Alice joins:**
   ```
   Alice (sid: "abc-123") joins room ABC123
   → Assigned speaker_id: 1
   → Frontend receives: { user_speaker_id: 1 }
   ```

2. **Bob joins:**
   ```
   Bob (sid: "def-456") joins room ABC123
   → Assigned speaker_id: 2
   → Frontend receives: { user_speaker_id: 2 }
   ```

3. **Alice speaks:**
   ```
   Deepgram transcription: [("Hello everyone", 0), ("How are you", 0)]
   → Mapped to: [("Hello everyone", 1), ("How are you", 1)]
   → GPT creates node with speakerID: 1
   ```

4. **Bob speaks:**
   ```
   Deepgram transcription: [("I'm doing great", 0), ("Thanks for asking", 0)]
   → Mapped to: [("I'm doing great", 2), ("Thanks for asking", 2)]
   → GPT creates node with speakerID: 2
   ```

5. **Mindmap Result:**
   ```json
   {
     "id": 1,
     "speaker": 1,  // Alice's contribution
     "content": "Greeting"
   },
   {
     "id": 2,
     "speaker": 2,  // Bob's contribution
     "content": "Response"
   }
   ```

## Frontend Integration

### Receiving Speaker ID

When a user joins a room, they receive:
```javascript
socket.on("room_joined", (data) => {
  console.log("My speaker ID:", data.user_speaker_id);
  // Store this for displaying current user's contributions differently
});
```

### Displaying Nodes

Each node in the mindmap has a `speakerID` field:
```javascript
{
  "id": 42,
  "speaker": 1,  // Speaker ID of the user who created this node
  "content": "Important point",
  "childNodes": []
}
```

You can use this to:
- Color-code nodes by speaker
- Show user avatars/names
- Filter nodes by speaker
- Highlight current user's contributions

## Benefits

1. **Clear Attribution**: Every contribution is clearly attributed to a specific user
2. **Multi-User Support**: Multiple users in the same room can speak simultaneously
3. **Persistent Identity**: Users maintain their speaker ID across disconnects/reconnects
4. **Visual Distinction**: Frontend can color-code or style nodes by speaker
5. **Analytics**: Track individual user contributions and participation

## Limitations & Considerations

1. **Deepgram Diarization Ignored**: The system no longer uses Deepgram's speaker diarization within a single user's audio stream. If multiple people speak into the same user's microphone, they'll all be tagged with that user's speaker ID.

2. **Speaker ID Persistence**: Speaker IDs persist in the room even after a user leaves. This maintains historical accuracy but means speaker IDs may have gaps if users leave.

3. **Room-Specific IDs**: Speaker IDs are unique per room. The same user will have different speaker IDs in different rooms.

## Future Enhancements

- **User Names**: Associate display names with speaker IDs
- **Speaker Colors**: Predefined color palette for speaker visualization
- **Admin Controls**: Allow room admins to reassign or merge speaker IDs
- **Analytics Dashboard**: Track participation levels per speaker
- **Export with Attribution**: Export mindmaps with speaker names/IDs
