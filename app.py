from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import Flask, send_from_directory
from dotenv import load_dotenv
import websocket
import threading
import json
import os
import time
import mindmap
import gptTools
import mindmapMethods
import queue
import threading
import deepgramProcessing
from flask_cors import CORS

# from statisticsEngine import statisticsEngine as statisticsGPTEngine
from session import SessionState
from room_manager import RoomManager

statistics_queue = queue.Queue()
mindmap_lock = threading.Lock()
speech_timeout_timer = None

load_dotenv()  # Load variables from .env

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Configure CORS to allow all origins for debugging
CORS(app, origins="*")

DEEPGRAM_API_KEY = os.getenv("API_KEY")

DG_WS_ENDPOINT = f"wss://api.deepgram.com/v1/listen?punctuate=true&diarize=true&model=nova-3"

# dg_ws = None

sessions = {}         # sid -> SessionState
sessions_lock = threading.Lock()
room_manager = RoomManager()  # Global room manager

# task_queue = queue.Queue()
# currentMindmap = mindmap.MindMap("")

# def statisticsEngine():
#     with mindmap_lock:
#         print("No speech detected for 1 second. Running statisticsEngine...")
#         try:
#             result = statisticsGPTEngine.GPTCall(currentMindmap.to_json())
#             print("Statistics Engine Result:", result.content)
#             if True:
#                 newID = currentMindmap.addNode(result.content, result.speakerID, result.parentID)
#                 print("Socketio emit")

#                 socketio.emit("node_instruction", {
#                     "action": "add",
#                     "content": "statisticsEngine: " + result.content,
#                     "speakerID": str(result.speakerID),
#                     "connectTo": str(result.parentID),
#                     "id": str(newID),  # Temporary ID for frontend
#                 })

#         except Exception as e:
#             print("Statistics Engine Error:", e)

# def statistics_worker():
#     while True:
#         statistics_queue.get()
#         statisticsEngine()
#         statistics_queue.task_done()

def reset_speech_timer():
    global speech_timeout_timer
    if speech_timeout_timer is not None:
        speech_timeout_timer.cancel()
    speech_timeout_timer = threading.Timer(5.0, lambda: statistics_queue.put(True))
    speech_timeout_timer.start()

# def gpt_worker():
#     while True:
#         speechList, transcript, currentMindmap = task_queue.get()
#         currentMindmap.updateTranscript(str(transcript)) # Only here!
#         chatGPTWrapper(speechList, currentMindmap, handle_gpt_response)
#         task_queue.task_done()
      
# threading.Thread(target=gpt_worker, daemon=True).start()
# threading.Thread(target=statistics_worker, daemon=True).start()

def chatGPTWrapper(speechList, mindmap: mindmap.MindMap, callback=None):
    try:
        action = gptTools.GPTCall(speechList, mindmap.currentTranscript, mindmap)

        if action == None :
            print("action error")
        else :
            if callback:
                callback(action, mindmap)  # <- pass both if needed

    except Exception as e:
        print("GPT Error:", e)

# def handle_gpt_response(action, mindmap: mindmap.MindMap):
#     # global currentMindmap
#     """
#     Handle the GPT response after it returns from OpenAI.
#     You can emit to frontend, log, or trigger other backend logic here.
#     """
#     print(mindmap.to_json())


#     if None:
#         print("no action required")
#     elif isinstance(action, mindmapMethods.addNodeAction): #add
#         newID = mindmap.addNode(action.content, action.speakerID, action.parentID)
       
#         socketio.emit("node_instruction", {
#             "action": "add",
#             "content": action.content,
#             "speakerID": str(action.speakerID),
#             "connectTo": str(action.parentID),
#             "id": str(newID),  # Temporary ID for frontend
#         })

#     elif isinstance(action, mindmapMethods.deleteNodeAction):#delete
        
#         mindmap.delete_by_id(action.nodeID)

#         socketio.emit("node_instruction", {
#             "action": "delete",
#             "parentID": action.nodeID
#         })

#     elif isinstance(action, mindmapMethods.modifyNodeAction):#modify
#         mindmap.modify_by_id(action.newContent, action.newSpeakerID, action.nodeID)

#         socketio.emit("node_instruction", {
#             "action": "modify",
#             "newContent": action.newContent,
#             "newSpeakerID": action.newSpeakerID,
#             "nodeID": action.nodeID
#         })
        

#     elif isinstance(action, mindmapMethods.setTitle): #settitle
#         mindmap.title = action.newTitle
#         socketio.emit("node_instruction", {
#             "action": "setTitle",
#             "newTitle": action.newTitle
#         })
       
#     else :
#         print("unknown action")

    



# Connect to Deepgram with proper error handling and backoff
def connect_to_deepgram(sid: str):
    with sessions_lock:
        state = sessions.get(sid)
        if not state or not state.room:
            return False
        
        # Prevent multiple simultaneous connections and implement backoff
        with state.dg_lock:
            if state.dg_reconnecting:
                print(f"[{sid}] Already reconnecting, skipping...")
                return False
            
            # Simple exponential backoff: wait longer between retries
            current_time = time.time()
            if state.dg_last_attempt > 0:
                time_since_last = current_time - state.dg_last_attempt
                backoff_delay = min(2 ** state.dg_retry_count, 30)  # Max 30 seconds
                if time_since_last < backoff_delay:
                    print(f"[{sid}] Backoff active, waiting {backoff_delay - time_since_last:.1f}s more")
                    return False
            
            state.dg_reconnecting = True
            state.dg_last_attempt = current_time

    try:
        headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

        def on_message(ws, message):
            try:
                data = json.loads(message)
                is_final = data.get("is_final") or data.get("speech_final") or True
                if not is_final:
                    return

                if "channel" in data:
                    alt = data["channel"]["alternatives"][0]
                    punctuatedText = alt.get("transcript", "")
                    rawWords = alt.get("words", [])

                    if punctuatedText:
                        with sessions_lock:
                            state = sessions.get(sid)
                        if not state:
                            return

                        state.reset_speech_timer(timeout_secs=5.0, on_timeout=lambda: None)
                        speech_list = deepgramProcessing.rawWordProcess(rawWords)
                        state.enqueue_transcript(str(speech_list), punctuatedText)
            except Exception as e:
                print(f"[{sid}] Error processing Deepgram message:", e)

        def on_error(ws, error):
            print(f"[{sid}] Deepgram error:", error)

        def on_close(ws, code, msg):
            print(f"[{sid}] Deepgram closed: {msg}")
            with sessions_lock:
                state = sessions.get(sid)
                if state and state.room:
                    with state.dg_lock:
                        # Cancel keepalive timer
                        if state.dg_keepalive_timer:
                            state.dg_keepalive_timer.cancel()
                            state.dg_keepalive_timer = None
                            
                        if "timeout" in str(msg).lower():
                            print(f"[{sid}] Deepgram timeout detected, will reconnect on next audio")
                            state.dg_needs_reconnect = True
                        state.dg_ws = None
                        state.dg_reconnecting = False

        def on_open(ws):
            print(f"[{sid}] Deepgram connected")
            with sessions_lock:
                state = sessions.get(sid)
                if state:
                    with state.dg_lock:
                        state.dg_needs_reconnect = False
                        state.dg_reconnecting = False
                        state.dg_retry_count = 0  # Reset retry count on successful connection
                        
                        # Start keepalive mechanism to prevent timeout
                        def send_keepalive():
                            try:
                                with sessions_lock:
                                    current_state = sessions.get(sid)
                                    if not current_state:
                                        return
                                        
                                with current_state.dg_lock:
                                    if (current_state.dg_ws and hasattr(current_state.dg_ws, 'sock') and 
                                        current_state.dg_ws.sock and getattr(current_state.dg_ws.sock, 'connected', False)):
                                        
                                        # Check if we received audio recently (within last 5 seconds)
                                        current_time = time.time()
                                        if current_time - current_state.dg_last_audio_time > 5:
                                            # Send a simple text message as keepalive (Deepgram accepts any text message)
                                            current_state.dg_ws.send('{"type":"KeepAlive"}')
                                            print(f"[{sid}] Sent Deepgram keepalive")
                                        
                                        # Schedule next keepalive check (every 5 seconds) 
                                        current_state.dg_keepalive_timer = threading.Timer(5.0, send_keepalive)
                                        current_state.dg_keepalive_timer.daemon = True
                                        current_state.dg_keepalive_timer.start()
                            except Exception as e:
                                print(f"[{sid}] Keepalive failed: {e}")
                        
                        # Start the keepalive cycle (every 5 seconds)
                        state.dg_keepalive_timer = threading.Timer(5.0, send_keepalive)
                        state.dg_keepalive_timer.daemon = True
                        state.dg_keepalive_timer.start()

        ws_app = websocket.WebSocketApp(
            DG_WS_ENDPOINT,
            header=headers,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )

        with sessions_lock:
            state = sessions.get(sid)
            if state:
                with state.dg_lock:
                    state.dg_ws = ws_app
                    state.dg_last_audio_time = time.time()  # Initialize audio time
                    threading.Thread(target=ws_app.run_forever, daemon=True).start()
                    return True
    except Exception as e:
        print(f"[{sid}] Failed to create Deepgram connection:", e)
        with sessions_lock:
            state = sessions.get(sid)
            if state:
                with state.dg_lock:
                    state.dg_reconnecting = False
                    state.dg_retry_count += 1  # Increment retry count on failure
        return False
    
    return False

@app.route("/")
def index():
    #return send_from_directory(app2.static_folder, 'index.html')
    return render_template("newIndex.html")

@app.route("/api/create-room", methods=["POST"])
def create_room():
    """API endpoint to create a new room"""
    try:
        room_code = room_manager.create_room()
        return jsonify({"success": True, "room_code": room_code})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/room-stats")
def get_room_stats():
    """API endpoint to get room statistics"""
    try:
        stats = room_manager.get_room_stats()
        return jsonify({"success": True, "rooms": stats})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# 
# @socketio.on("connect")
# def handle_connect():
#     sid = request.sid
#     # join_room(sid)  # optional; not needed for this test
#     emit("node_instruction", {
#         "action": "test",
#         "message": "connected",
#         "sid": sid,
#     }, namespace="/")

@socketio.on("connect")
def handle_connect():
    sid = request.sid
    with sessions_lock:
        if sid not in sessions:
            sessions[sid] = SessionState(sid, socketio, room_manager)
    
    # Send connection confirmation but don't join a room yet
    socketio.emit("connection_status", {
        "status": "connected",
        "message": "Connected to server. Please join a room to start collaborating.",
        "sid": sid
    }, to=sid, namespace="/")

    print(f"[{sid}] connected and waiting to join room")

@socketio.on("join_room")
def handle_join_room(data):
    sid = request.sid
    room_code = data.get("room_code", "").strip().upper()
    
    if not room_code:
        socketio.emit("room_error", {
            "error": "Room code is required"
        }, to=sid)
        return
    
    with sessions_lock:
        state = sessions.get(sid)
    
    if not state:
        socketio.emit("room_error", {
            "error": "Session not found"
        }, to=sid)
        return
    
    try:
        # Join the room through the session
        room = state.join_room(room_code)
        
        # Join the socket.io room for real-time updates
        join_room(room_code)
        
        # Connect to Deepgram now that user is in a room
        connect_to_deepgram(sid)
        
        # Send the current mindmap state to the new user
        mindmap_json = room.get_mindmap_json()
        
        socketio.emit("room_joined", {
            "room_code": room_code,
            "user_count": room.get_user_count(),
            "mindmap": json.loads(mindmap_json),
            "message": f"Successfully joined room {room_code}"
        }, to=sid)
        
        # Notify other users in the room
        socketio.emit("user_joined", {
            "user_id": sid,
            "user_count": room.get_user_count(),
            "message": f"A user joined the room"
        }, room=room_code, include_self=False)
        
        # Send welcome node
        socketio.emit("node_instruction", {
            "action": "add",
            "content": f"Welcome to Room {room_code}!",
            "speakerID": "0",
            "connectTo": "0",
            "id": "welcome",
            "room_code": room_code
        }, to=sid, namespace="/")
        
        print(f"[{sid}] joined room {room_code}")
        
    except Exception as e:
        socketio.emit("room_error", {
            "error": f"Failed to join room: {str(e)}"
        }, to=sid)
        
@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"[{sid}] disconnected")
    
    with sessions_lock:
        state = sessions.pop(sid, None)
    
    if state:
        # Get room info before closing
        room = state.room
        room_code = room.room_code if room else None
        
        # Close Deepgram WS and cleanup timers
        try:
            # Cancel keepalive timer
            if state.dg_keepalive_timer:
                state.dg_keepalive_timer.cancel()
                state.dg_keepalive_timer = None
                
            if state.dg_ws and state.dg_ws.sock and state.dg_ws.sock.connected:
                state.dg_ws.close()
        except Exception as e:
            print(f"[{sid}] error closing Deepgram WS:", e)
        
        # Stop worker/timers and leave room
        state.close()
        
        # Notify other users in the room if applicable
        if room_code:
            leave_room(room_code)
            room_after_leave = room_manager.get_room(room_code)
            if room_after_leave:  # Room still exists
                socketio.emit("user_left", {
                    "user_id": sid,
                    "user_count": room_after_leave.get_user_count(),
                    "message": f"A user left the room"
                }, room=room_code)
    
    leave_room(sid)

@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    sid = request.sid
    with sessions_lock:
        state = sessions.get(sid)
    
    # Only process audio if user is in a room
    if not state or not state.room:
        print(f"[{sid}] User not in a room, ignoring audio")
        return
    
    # Check connection status with proper locking
    with state.dg_lock:
        needs_connection = (
            state.dg_needs_reconnect or 
            not state.dg_ws or 
            not hasattr(state.dg_ws, 'sock') or 
            not state.dg_ws.sock or
            not getattr(state.dg_ws.sock, 'connected', False)
        )
        
        # Only attempt reconnection if not already in progress
        if needs_connection and not state.dg_reconnecting:
            print(f"[{sid}] Connecting to Deepgram...")
            
            # Notify frontend about reconnection
            socketio.emit("audio_status", {
                "status": "reconnecting",
                "message": "Connecting to speech service..."
            }, to=sid)
            
            # Try to connect
            if connect_to_deepgram(sid):
                # Give connection time to establish
                time.sleep(0.3)
                
                # Check if connection is now ready
                if (state.dg_ws and hasattr(state.dg_ws, 'sock') and 
                    state.dg_ws.sock and getattr(state.dg_ws.sock, 'connected', False)):
                    socketio.emit("audio_status", {
                        "status": "connected",
                        "message": "Speech service connected"
                    }, to=sid)
                else:
                    print(f"[{sid}] Connection still not ready after attempt")
                    return
            else:
                print(f"[{sid}] Failed to connect to Deepgram")
                socketio.emit("audio_status", {
                    "status": "error",
                    "message": "Failed to connect to speech service"
                }, to=sid)
                return
        elif state.dg_reconnecting:
            # Already reconnecting, skip this audio chunk
            return
    
    # Send audio data with proper error handling
    with state.dg_lock:
        if (state.dg_ws and hasattr(state.dg_ws, 'sock') and 
            state.dg_ws.sock and getattr(state.dg_ws.sock, 'connected', False)):
            try:
                state.dg_ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
                state.dg_last_audio_time = time.time()  # Track when audio was sent
            except Exception as e:
                print(f"[{sid}] Error sending audio to Deepgram: {e}")
                # Mark for reconnection but don't immediately reconnect
                state.dg_needs_reconnect = True
                state.dg_ws = None

@socketio.on("get_room_info")
def handle_get_room_info():
    sid = request.sid
    with sessions_lock:
        state = sessions.get(sid)
    
    if not state or not state.room:
        socketio.emit("room_info", {
            "error": "Not in a room"
        }, to=sid)
        return
    
    room = state.room
    socketio.emit("room_info", {
        "room_code": room.room_code,
        "user_count": room.get_user_count(),
        "mindmap": json.loads(room.get_mindmap_json())
    }, to=sid)

@socketio.on("leave_room")
def handle_leave_room():
    sid = request.sid
    with sessions_lock:
        state = sessions.get(sid)
    
    if not state or not state.room:
        socketio.emit("room_error", {
            "error": "Not in a room"
        }, to=sid)
        return
    
    room_code = state.room.room_code
    
    # Leave the socket.io room
    leave_room(room_code)
    
    # Remove from room manager
    room_manager.leave_room(sid)
    state.room = None
    
    # Close Deepgram connection
    try:
        if state.dg_ws and state.dg_ws.sock and state.dg_ws.sock.connected:
            state.dg_ws.close()
            state.dg_ws = None
    except Exception as e:
        print(f"[{sid}] error closing Deepgram WS:", e)
    
    socketio.emit("room_left", {
        "message": f"Left room {room_code}"
    }, to=sid)
    
    # Notify other users
    room_after_leave = room_manager.get_room(room_code)
    if room_after_leave:  # Room still exists
        socketio.emit("user_left", {
            "user_id": sid,
            "user_count": room_after_leave.get_user_count(),
            "message": f"A user left the room"
        }, room=room_code)
    
    print(f"[{sid}] left room {room_code}")

@socketio.on("reconnect_audio")
def handle_reconnect_audio():
    """Manual audio reconnection endpoint"""
    sid = request.sid
    with sessions_lock:
        state = sessions.get(sid)
    
    if not state or not state.room:
        socketio.emit("audio_status", {
            "status": "error",
            "message": "Not in a room"
        }, to=sid)
        return
    
    print(f"[{sid}] Manual audio reconnection requested")
    
    try:
        # Close existing connection
        if state.dg_ws and state.dg_ws.sock:
            state.dg_ws.close()
    except:
        pass
    
    # Reconnect
    connect_to_deepgram(sid)
    
    socketio.emit("audio_status", {
        "status": "reconnecting",
        "message": "Reconnecting to speech service..."
    }, to=sid)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=2500)
