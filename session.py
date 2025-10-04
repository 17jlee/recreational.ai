# session.py
import queue
import threading
import gptTools
import mindmapMethods  # needed for action types

class SessionState:
    def __init__(self, sid, socketio, room_manager):
        self.sid = sid
        self.socketio = socketio
        self.room_manager = room_manager
        self.room = None  # Will be set when user joins a room
        self.user_speaker_id = None  # Will be set when user joins a room
        self.task_queue = queue.Queue(maxsize=100)
        self._stop = threading.Event()
        self.gpt_thread = socketio.start_background_task(self._gpt_worker)

        # Optional per-session resources managed by app.py:
        self.dg_ws = None
        self.speech_timer = None
        self.dg_needs_reconnect = False  # Flag to indicate if Deepgram needs reconnection
        self.dg_reconnecting = False  # Flag to prevent multiple simultaneous reconnections
        self.dg_lock = threading.Lock()  # Lock for Deepgram operations
        self.dg_retry_count = 0  # Track retry attempts
        self.dg_last_attempt = 0  # Track last connection attempt time
        self.dg_keepalive_timer = None  # Timer for sending keepalive messages
        self.dg_last_audio_time = 0  # Track last audio data sent

    def enqueue_transcript(self, speech_list, transcript):
        try:
            # Include user's speaker ID with the transcript
            self.task_queue.put_nowait((speech_list, transcript, self.user_speaker_id))
        except queue.Full:
            print(f"[{self.sid}] task queue full; dropping oldest")
            try:
                self.task_queue.get_nowait()
            except queue.Empty:
                pass
            self.task_queue.put_nowait((speech_list, transcript, self.user_speaker_id))

    def join_room(self, room_code: str):
        """Join this session to a room"""
        self.room = self.room_manager.join_room(self.sid, room_code)
        # Get the user's speaker ID for this room
        self.user_speaker_id = self.room.get_user_speaker_id(self.sid)
        return self.room

    def _gpt_worker(self):
        while not self._stop.is_set():
            try:
                item = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                speech_list, transcript, user_speaker_id = item
                
                # Only process if user is in a room
                if not self.room:
                    continue
                    
                # Map Deepgram speaker IDs to the user's speaker ID
                # Convert speech_list from [(text, deepgram_speaker_id), ...] to [(text, user_speaker_id), ...]
                mapped_speech_list = [(text, user_speaker_id) for text, _ in speech_list]
                
                # Append transcript to the room's shared mindmap (thread-safe)
                self.room.update_transcript(str(transcript))
                
                # Get the current transcript and mindmap state (thread-safe)
                current_transcript = self.room.mindmap.currentTranscript
                mindmap_json = self.room.get_mindmap_json()
                
                action = gptTools.GPTCall(
                    mapped_speech_list,
                    current_transcript,
                    self.room.mindmap  # Pass the room's shared mindmap
                )
                if action:
                    self._handle_gpt_response(action)
                    
                # Reset statistics timer for the room (runs every 10 seconds)
                self.room.reset_statistics_timer(self.socketio, timeout_secs=10.0)
                    
            except Exception as e:
                print(f"[{self.sid}] GPT worker error:", e)
            finally:
                self.task_queue.task_done()

    def _handle_gpt_response(self, action):
        if not self.room:
            return
            
        room_code = self.room.room_code
        
        if isinstance(action, mindmapMethods.addNodeAction):
            # Use thread-safe method to add node to shared mindmap
            newID = self.room.add_node_safe(action.content, action.speakerID, action.parentID)
            print(f"[{self.sid}] Added node {newID} to room {room_code}")
            
            # Emit to all users in the room
            self.socketio.emit("node_instruction", {
                "action": "add",
                "content": action.content,
                "speakerID": str(action.speakerID),
                "connectTo": str(action.parentID),
                "id": str(newID),
                "room_code": room_code,
                "from_user": self.sid
            }, room=room_code, namespace="/")

        elif isinstance(action, mindmapMethods.deleteNodeAction):
            # Use thread-safe method to delete node from shared mindmap
            self.room.delete_node_safe(action.nodeID)
            
            # Emit to all users in the room
            self.socketio.emit("node_instruction", {
                "action": "delete",
                "parentID": action.nodeID,
                "room_code": room_code,
                "from_user": self.sid
            }, room=room_code)

        elif isinstance(action, mindmapMethods.modifyNodeAction):
            # Use thread-safe method to modify node in shared mindmap
            self.room.modify_node_safe(action.newContent, action.newSpeakerID, action.nodeID)
            
            # Emit to all users in the room
            self.socketio.emit("node_instruction", {
                "action": "modify",
                "newContent": action.newContent,
                "newSpeakerID": action.newSpeakerID,
                "nodeID": action.nodeID,
                "room_code": room_code,
                "from_user": self.sid
            }, room=room_code)

        elif isinstance(action, mindmapMethods.setTitle):
            # Use thread-safe method to set title in shared mindmap
            self.room.set_title_safe(action.newTitle)
            
            # Emit to all users in the room
            self.socketio.emit("node_instruction", {
                "action": "setTitle",
                "newTitle": action.newTitle,
                "room_code": room_code,
                "from_user": self.sid
            }, room=room_code)

        else:
            print(f"[{self.sid}] unknown action type: {type(action)}")

    def reset_speech_timer(self, timeout_secs=5.0, on_timeout=None):
        if self.speech_timer is not None:
            self.speech_timer.cancel()
        if on_timeout:
            self.speech_timer = threading.Timer(timeout_secs, on_timeout)
            self.speech_timer.start()

    def close(self):
        self._stop.set()
        if self.speech_timer:
            try:
                self.speech_timer.cancel()
            except Exception:
                pass
        # Cancel keepalive timer
        if self.dg_keepalive_timer:
            try:
                self.dg_keepalive_timer.cancel()
            except Exception:
                pass
        # Leave room when session closes
        if self.room_manager:
            self.room_manager.leave_room(self.sid)
        # Deepgram WS is closed by app.py
