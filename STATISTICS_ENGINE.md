# Statistics Engine - Enabled

## Overview
The Statistics Engine has been enabled for all users and is configured to run automatically every 10 seconds for each active room.

## What It Does
The Statistics Engine:
- Automatically searches the web for relevant statistics about the current conversation
- Analyzes the mindmap content to find contextually relevant data
- Adds statistical information as new nodes to the mindmap
- Runs continuously every 10 seconds while users are in a room

## Configuration

### Interval
- **Default**: 10 seconds
- **Location**: `room_manager.py` - `reset_statistics_timer()` function
- **Auto-restart**: Yes - the timer automatically restarts after each run

### How It Works

1. **When a user joins a room**: The statistics timer starts automatically if it's not already running
2. **Every 10 seconds**: 
   - The Statistics Engine analyzes the room's mindmap
   - Uses OpenAI's GPT model with web search to find relevant statistics
   - Adds findings as new nodes with speaker ID `-41`
3. **All users in the room**: Receive the statistics updates in real-time via WebSocket

### Modified Files

#### 1. `app.py`
- Uncommented the `statisticsEngine` import
- Added logic to start the statistics timer when first user joins a room

#### 2. `room_manager.py`
- Imported `statisticsEngine` module
- Enabled the statistics engine in `reset_statistics_timer()`
- Changed default timeout from 5 seconds to 10 seconds
- Added auto-restart logic to keep the engine running continuously
- Added error handling to restart timer even if statistics engine fails

#### 3. `session.py`
- Updated statistics timer call to use 10-second interval
- Timer resets on each GPT interaction to keep it active

### Statistics Node Format

Nodes created by the Statistics Engine have:
- **Speaker ID**: `-41` (identifies it as a statistics node)
- **Content**: Prefixed with "StatisticsEngine: " followed by the statistic
- **Parent**: Automatically determined based on relevance to existing nodes
- **Format**: Brief statistic (number + units) with one-sentence description

## Configuration Options

### To Change the Interval

Edit `room_manager.py`, line ~63:
```python
def reset_statistics_timer(self, socketio, timeout_secs=10.0):  # Change 10.0 to desired seconds
```

Also update in `session.py`, line ~74:
```python
self.room.reset_statistics_timer(self.socketio, timeout_secs=10.0)  # Change to match
```

### To Disable the Statistics Engine

Comment out the statistics timer start in `app.py` around line 335:
```python
# if room.statistics_timer is None or not room.statistics_timer.is_alive():
#     print(f"[{sid}] Starting statistics timer for room {room_code}")
#     room.reset_statistics_timer(socketio, timeout_secs=10.0)
```

## Dependencies

The Statistics Engine requires:
- OpenAI API key (set in `.env` file as `OPENAI_API_KEY`)
- `statisticsEngine/statisticsEngine.py` module
- OpenAI Python SDK

## Error Handling

- If the statistics engine fails, it logs the error and automatically restarts
- Timer continues running even if individual calls fail
- No impact on core mindmapping functionality

## Performance Considerations

- The engine runs in separate threads per room
- Does not block user interactions
- Network calls to OpenAI may introduce latency
- Consider increasing interval if rate limits are hit

## Future Enhancements

- Configurable interval per room
- User-controlled enable/disable toggle
- Different speaker IDs for different types of statistics
- Throttling based on conversation activity
