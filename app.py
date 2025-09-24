import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import Flask, send_from_directory
from dotenv import load_dotenv
import websocket
import threading
import json
import os
import mindmap
import gptTools
import mindmapMethods
import queue
import threading
import deepgramProcessing

from statisticsEngine import statisticsEngine as statisticsGPTEngine
from session import SessionState

statistics_queue = queue.Queue()
mindmap_lock = threading.Lock()
speech_timeout_timer = None

load_dotenv()  # Load variables from .env

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DEEPGRAM_API_KEY = os.getenv("API_KEY")

DG_WS_ENDPOINT = f"wss://api.deepgram.com/v1/listen?punctuate=true&diarize=true&model=nova-3"

# dg_ws = None

sessions = {}         # sid -> SessionState
sessions_lock = threading.Lock()

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

    



# Connect to Deepgram once
def connect_to_deepgram(sid: str):
    headers = {"Authorization": f"Token {DEEPGRAM_API_KEY}"}

    def on_message(ws, message):
        data = json.loads(message)

        # Only process "final" results to avoid duplicate partials; adjust if your schema differs.
        is_final = data.get("is_final") or data.get("speech_final") or True  # fallback to True if Deepgram doesn't flag
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

                # Optional: on-silence hook via per-session timer
                state.reset_speech_timer(timeout_secs=5.0, on_timeout=lambda: None)

                speech_list = deepgramProcessing.rawWordProcess(rawWords)
                # Enqueue for this session; worker will update transcript + call GPT + emit
                state.enqueue_transcript(str(speech_list), punctuatedText)

    def on_error(ws, error):
        print(f"[{sid}] Deepgram error:", error)

    def on_close(ws, code, msg):
        print(f"[{sid}] Deepgram closed: {msg}")

    def on_open(ws):
        print(f"[{sid}] Deepgram connected")

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
        state.dg_ws = ws_app
        threading.Thread(target=ws_app.run_forever, daemon=True).start()

@app.route("/")
def index():
    #return send_from_directory(app2.static_folder, 'index.html')
    return render_template("newIndex.html")

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
    join_room(sid)
    with sessions_lock:
        if sid not in sessions:
            sessions[sid] = SessionState(sid, socketio)
    # Test emit to verify wiring
    print(sid, "sid")
    socketio.emit("node_instruction", {
            "action": "add",
            "content": "Welcome to MindMap!",
            "speakerID": "0",
            "connectTo": "0",
            "id": "1",
        "sid": sid
    }, to=sid, namespace="/")

    connect_to_deepgram(sid)
    print(f"[{sid}] connected")

@socketio.on("disconnect")
def handle_disconnect():
    sid = request.sid
    print(f"[{sid}] disconnected")
    with sessions_lock:
        state = sessions.pop(sid, None)
    if state:
        # Close Deepgram WS
        try:
            if state.dg_ws and state.dg_ws.sock and state.dg_ws.sock.connected:
                state.dg_ws.close()
        except Exception as e:
            print(f"[{sid}] error closing Deepgram WS:", e)
        # Stop worker/timers
        state.close()
    leave_room(sid)

@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    sid = request.sid
    with sessions_lock:
        state = sessions.get(sid)
    if not state or not state.dg_ws or not state.dg_ws.sock or not state.dg_ws.sock.connected:
        print(f"[{sid}] Deepgram WebSocket not ready")
        return
    try:
        state.dg_ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
    except Exception as e:
        print(f"[{sid}] Error sending to Deepgram:", e)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=2500)
