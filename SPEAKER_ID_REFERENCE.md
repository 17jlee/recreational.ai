# User Speaker ID System - Quick Reference

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         ROOM: ABC123                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  User Mapping:                                                  │
│  ┌──────────────────────────────────────────────────┐          │
│  │ user_sid          → speaker_id                   │          │
│  │ "alice-session"   → 1                            │          │
│  │ "bob-session"     → 2                            │          │
│  │ "charlie-session" → 3                            │          │
│  └──────────────────────────────────────────────────┘          │
│                                                                 │
│  Next Speaker ID: 4                                            │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

```
USER SPEAKS
    │
    ├─► Microphone Audio
    │       │
    │       ├─► Deepgram API
    │       │       │
    │       │       └─► Transcript with Deepgram Speaker IDs
    │       │           [(text, 0), (text, 1), (text, 0)]
    │       │
    │       ├─► SessionState.enqueue_transcript()
    │       │       │
    │       │       └─► Includes user_speaker_id (e.g., 1)
    │       │
    │       └─► SessionState._gpt_worker()
    │               │
    │               ├─► Maps Deepgram IDs → User Speaker ID
    │               │   [(text, 0), (text, 1)] → [(text, 1), (text, 1)]
    │               │
    │               └─► GPTCall with user-specific speaker IDs
    │                       │
    │                       └─► Creates nodes with correct speaker ID
    │
    └─► Mindmap Node Created
            {
              "id": 42,
              "speaker": 1,  ← Alice's Speaker ID
              "content": "Important point"
            }
```

## Example Scenario

### Setup
```
Room: DEMO01
Users:
- Alice (session: abc-123) → Speaker ID: 1
- Bob   (session: def-456) → Speaker ID: 2
```

### Alice Speaks
```javascript
// Raw Deepgram Output
[("Let's discuss the project", 0), ("We have three main goals", 0)]

// After Speaker ID Mapping
[("Let's discuss the project", 1), ("We have three main goals", 1)]

// Resulting Node
{
  "id": 10,
  "speaker": 1,  // Alice
  "content": "Project Goals",
  "childNodes": [...]
}
```

### Bob Speaks
```javascript
// Raw Deepgram Output
[("I agree with Alice", 0), ("Let's prioritize feature A", 0)]

// After Speaker ID Mapping
[("I agree with Alice", 2), ("Let's prioritize feature A", 2)]

// Resulting Node
{
  "id": 11,
  "speaker": 2,  // Bob
  "content": "Feature Prioritization",
  "childNodes": [...]
}
```

## API Changes

### Backend → Frontend (Socket.IO Events)

#### `room_joined` event (NEW FIELD)
```javascript
{
  "room_code": "ABC123",
  "user_count": 2,
  "mindmap": {...},
  "user_speaker_id": 1,  // ← NEW: User's assigned speaker ID
  "message": "Successfully joined room ABC123 (Speaker ID: 1)"
}
```

#### `node_instruction` event (EXISTING)
```javascript
{
  "action": "add",
  "content": "Important point",
  "speakerID": "1",  // ← Now reflects actual user's speaker ID
  "connectTo": "0",
  "id": "42",
  "room_code": "ABC123"
}
```

## Frontend Implementation Example

```javascript
let myReakerID = null;

socket.on("room_joined", (data) => {
  mySpeakerID = data.user_speaker_id;
  console.log(`My speaker ID is: ${mySpeakerID}`);
  
  // Update UI to show user their speaker ID/color
  updateUserBadge(mySpeakerID);
});

socket.on("node_instruction", (data) => {
  const node = {
    id: data.id,
    content: data.content,
    speakerID: parseInt(data.speakerID),
    parentID: data.connectTo
  };
  
  // Highlight nodes from current user
  const isMyNode = (node.speakerID === mySpeakerID);
  
  // Color-code by speaker
  const nodeColor = getSpeakerColor(node.speakerID);
  
  renderNode(node, nodeColor, isMyNode);
});

// Color palette for speakers
function getSpeakerColor(speakerID) {
  const colors = [
    '#FF6B6B',  // Speaker 1: Red
    '#4ECDC4',  // Speaker 2: Teal
    '#45B7D1',  // Speaker 3: Blue
    '#FFA07A',  // Speaker 4: Orange
    '#98D8C8',  // Speaker 5: Green
    '#F7DC6F',  // Speaker 6: Yellow
    '#BB8FCE',  // Speaker 7: Purple
    '#85C1E2'   // Speaker 8: Light Blue
  ];
  
  if (speakerID === 0) return '#CCCCCC';      // System
  if (speakerID === -41) return '#FFD700';    // Statistics Engine
  return colors[(speakerID - 1) % colors.length];
}
```

## Testing Checklist

- [ ] Single user joins room, receives speaker ID 1
- [ ] Second user joins same room, receives speaker ID 2
- [ ] User 1 speaks, nodes created with speaker ID 1
- [ ] User 2 speaks, nodes created with speaker ID 2
- [ ] User leaves and rejoins, retains same speaker ID
- [ ] Statistics Engine nodes use speaker ID -41
- [ ] Multiple rooms have independent speaker ID spaces
- [ ] Frontend displays speaker IDs correctly
- [ ] Frontend can color-code nodes by speaker
