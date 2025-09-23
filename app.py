import eventlet
eventlet.monkey_patch()
from flask import Flask, render_template
from flask_socketio import SocketIO, emit
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

statistics_queue = queue.Queue()
mindmap_lock = threading.Lock()
speech_timeout_timer = None

load_dotenv()  # Load variables from .env

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DEEPGRAM_API_KEY = os.getenv("API_KEY")

DG_WS_ENDPOINT = f"wss://api.deepgram.com/v1/listen?punctuate=true&diarize=true&model=nova-3"

dg_ws = None

task_queue = queue.Queue()
currentMindmap = mindmap.MindMap("")

def statisticsEngine():
    with mindmap_lock:
        print("No speech detected for 1 second. Running statisticsEngine...")
        try:
            result = statisticsGPTEngine.GPTCall(currentMindmap.to_json())
            print("Statistics Engine Result:", result.content)
            if True:
                newID = currentMindmap.addNode(result.content, result.speakerID, result.parentID)
                print("Socketio emit")

                socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "statisticsEngine: " + result.content,
                    "speakerID": str(result.speakerID),
                    "connectTo": str(result.parentID),
                    "id": str(newID),  # Temporary ID for frontend
                })

        except Exception as e:
            print("Statistics Engine Error:", e)

def statistics_worker():
    while True:
        statistics_queue.get()
        statisticsEngine()
        statistics_queue.task_done()

def reset_speech_timer():
    global speech_timeout_timer
    if speech_timeout_timer is not None:
        speech_timeout_timer.cancel()
    speech_timeout_timer = threading.Timer(5.0, lambda: statistics_queue.put(True))
    speech_timeout_timer.start()

def gpt_worker():
    while True:
        speechList, transcript, currentMindmap = task_queue.get()
        currentMindmap.updateTranscript(str(transcript)) # Only here!
        chatGPTWrapper(speechList, currentMindmap, handle_gpt_response)
        task_queue.task_done()
      
threading.Thread(target=gpt_worker, daemon=True).start()
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

def handle_gpt_response(action, mindmap: mindmap.MindMap):
    # global currentMindmap
    """
    Handle the GPT response after it returns from OpenAI.
    You can emit to frontend, log, or trigger other backend logic here.
    """
    print(mindmap.to_json())


    if None:
        print("no action required")
    elif isinstance(action, mindmapMethods.addNodeAction): #add
        newID = mindmap.addNode(action.content, action.speakerID, action.parentID)
       
        socketio.emit("node_instruction", {
            "action": "add",
            "content": action.content,
            "speakerID": str(action.speakerID),
            "connectTo": str(action.parentID),
            "id": str(newID),  # Temporary ID for frontend
        })

    elif isinstance(action, mindmapMethods.deleteNodeAction):#delete
        
        mindmap.delete_by_id(action.nodeID)

        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": action.nodeID
        })

    elif isinstance(action, mindmapMethods.modifyNodeAction):#modify
        mindmap.modify_by_id(action.newContent, action.newSpeakerID, action.nodeID)

        socketio.emit("node_instruction", {
            "action": "modify",
            "newContent": action.newContent,
            "newSpeakerID": action.newSpeakerID,
            "nodeID": action.nodeID
        })
        

    elif isinstance(action, mindmapMethods.setTitle): #settitle
        mindmap.title = action.newTitle
        socketio.emit("node_instruction", {
            "action": "setTitle",
            "newTitle": action.newTitle
        })
       
    else :
        print("unknown action")

    



# Connect to Deepgram once
def connect_to_deepgram():
    global dg_ws
    global currentMindmap
    #global currentTranscript

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }

    def on_message(ws, message):

        data = json.loads(message)
        if "channel" in data:
            punctuatedText = data["channel"]["alternatives"][0]["transcript"]
            rawWords = data["channel"]["alternatives"][0]["words"]

            if punctuatedText:
                reset_speech_timer()
                rawSpeechList = deepgramProcessing.rawWordProcess(rawWords)
                print("-------------------------")
                print(punctuatedText)
                print(rawSpeechList)
                print("-------------------------")
                task_queue.put((str(rawSpeechList), punctuatedText, currentMindmap))


                # Optionally send to client:
                #socketio.emit("transcript", transcript)

    def on_error(ws, error):
        print("WebSocket Error:", error)

    def on_close(ws, close_status_code, close_msg):
        print("Deepgram WebSocket closed:", close_msg)

    def on_open(ws):
        print("Connected to Deepgram")

    dg_ws = websocket.WebSocketApp(
        DG_WS_ENDPOINT,
        header=headers,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )

    threading.Thread(target=dg_ws.run_forever, daemon=True).start()

connect_to_deepgram()


@app.route("/")
def index():
    #return send_from_directory(app2.static_folder, 'index.html')
    return render_template("newIndex.html")

@socketio.on("audio_chunk")
def handle_audio_chunk(data):
    print(f"Received {len(data)} bytes of audio")  # Placeholder
    if dg_ws and dg_ws.sock and dg_ws.sock.connected:
        try:
            dg_ws.send(data, opcode=websocket.ABNF.OPCODE_BINARY)
        except Exception as e:
            print("Error sending to Deepgram:", e)
    else:
        print("Deepgram WebSocket not ready")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=2500)
