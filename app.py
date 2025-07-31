import eventlet
eventlet.monkey_patch()
import sys
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
import time

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

activationDict = {}

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

    
def handle_demo(speech):
    if "recreational" in speech.lower() and activationDict.get("recreational") != True:
        activationDict["recreational"] = True
        time.sleep(2)
        print("Demo: Node detected")
        # Here you can add any specific logic for the demo
        # For example, you might want to emit a special event or log it
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "What is Recreational.ai?",
                    "speakerID": str(0),
                    "connectTo": str(0),
                    "type": "topBottom",
                    "x": 1.7,
                    "y": -83,
                    "id": str(1),  # Temporary ID for frontend
                })
    if ("visualizes" in speech.lower() or "visualises" in speech.lower()) and (activationDict.get("visualizes") != True):
        activationDict["visualizes"] = True
        time.sleep(0.5)  # Simulate some processing time
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "A web-app that listens to conversations and automatically visualizes key concepts using nodes and edges.",
                    "type": "topBottom",
                    "speakerID": str(0),
                    "connectTo": str(1),
                    "x": 2,
                    "y": -276,
                    "id": str(2),  # Temporary ID for frontend
                })
        
    if "room" in speech.lower() and activationDict.get("room") != True:
        activationDict["room"] = True
        time.sleep(2)
        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": str(2)
        })
        time.sleep(0.1)
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "A web-app that listens to conversations and automatically visualizes key concepts using nodes and edges.",
                    "type": "topBottom",
                    "speakerID": str(0),
                    "connectTo": str(1),
                    "x": -98,
                    "y": -270,
                    "id": str(3),  # Temporary ID for frontend
                })
        time.sleep(0.1)
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "Designed to run on a main meeting-room screen for all participants.",
                    "type": "topBottom",
                    "speakerID": str(0),
                    "connectTo": str(1),
                    "x": 186,
                    "y": -275,
                    "id": str(4),  # Temporary ID for frontend
                })


    if "summary" in speech.lower() and activationDict.get("summary") != True:
        activationDict["summary"] = True
        print("Demo: University of Liverpool detected")
        time.sleep(2)
        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": str(3)
        })
        time.sleep(0.1)
        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": str(4)
        })
        time.sleep(0.1)
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "A web-app that listens to conversations and automatically visualizes key concepts using nodes and edges.",
                    "type": "topBottom",
                    "speakerID": str(0),
                    "connectTo": str(1),
                    "x": -338,
                    "y": -285,
                    "id": str(5),  # Temporary ID for frontend
                })
        time.sleep(0.3)
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "Designed to run on a main meeting-room screen for all participants.",
                    "type": "topBottom",
                    "speakerID": str(0),
                    "connectTo": str(1),
                    "x": -98,
                    "y": -270,
                    "id": str(6),  # Temporary ID for frontend
                })
        time.sleep(0.4)
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "Core benefit: Provides a real-time summary so you're never lost in a meeting.",
                    "type": "topBottom",
                    "speakerID": str(0),
                    "connectTo": str(1),
                    "x": 186,
                    "y": -275,
                    "id": str(7),  # Temporary ID for frontend
                })
        time.sleep(2)
        socketio.emit("node_instruction", {
                    "action": "add",
                    "content": "Global video conferencing market size: $8.8 billion (2024), projected to reach $19.1 billion by 2029.",
                    "type": "custom",
                    "speakerID": str(1),
                    "connectTo": str(1),
                    "x": 410,
                    "y": -275,
                    "id": str(8),  # Temporary ID for frontend
                })
    if "engine" in speech.lower() and activationDict.get("engine") != True:
        activationDict["engine"] = True
        print("Demo: Engine detected")
        # time.sleep(2)
        socketio.emit("node_instruction", {
            "action": "add",
            "content": "Key Features",
            "type": "leftRight",
            "speakerID": str(1),
            "connectTo": str(0),
            "x": 250,
            "y": 0,
            "id": str(9),  # Temporary ID for frontend
        })
    if "speaker" in speech.lower() and activationDict.get("speaker") != True:
        activationDict["speaker"] = True
        socketio.emit("node_instruction", {
            "action": "add",
            "content": "Statistics Engine: Automatically searches the web for key statistics about the current conversation.",
            "type": "leftRight",
            "speakerID": str(1),
            "connectTo": str(9),
            "x": 500,
            "y": -30,
            "id": str(10),  # Temporary ID for frontend
        })
        time.sleep(1)
        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": str(10)
        })
        socketio.emit("node_instruction", {
            "action": "add",
            "content": "Statistics Engine: Automatically searches the web for key statistics about the current conversation.",
            "type": "leftRight",
            "speakerID": str(1),
            "connectTo": str(9),
            "x": 500,
            "y": -155,
            "id": str(11),  # Temporary ID for frontend
        })
        time.sleep(0.3)
        socketio.emit("node_instruction", {
            "action": "add",
            "content": "Speaker Attribution: Uses speech diarization to identify and credit people for their ideas (e.g., colored nodes).",
            "type": "leftRight",
            "speakerID": str(1),
            "connectTo": str(9),
            "x": 500,
            "y": -30,
            "id": str(12),  # Temporary ID for frontend
        })
        time.sleep(2.4)
        socketio.emit("node_instruction", {
            "action": "add",
            "content": "Unproductive meetings cost U.S. businesses approximately $399 billion each year.",
            "type": "custom",
            "speakerID": str(0),
            "connectTo": str(9),
            "x": 500,
            "y": 100,
            "id": str(13),  # Temporary ID for frontend
        })

    if "zoom" in speech.lower() and activationDict.get("zoom") != True:
        activationDict["zoom"] = True
        print("Demo: Zoom detected")
        time.sleep(3)
        socketio.emit("node_instruction", {
            "action": "add",
            "content": "Market & Vision",
            "type": "topDown",
            "speakerID": str(0),
            "connectTo": str(0),
            "x": 0,
            "y": 100,
            "id": str(14),  # Temporary ID for frontend
        })
        time.sleep(0.3)
        socketio.emit("node_instruction", {
            "content": "Competitors like Zoom are stagnant and others like Otter.ai only help after the meeting.",
            "action": "add",
            "type": "topDown",
            "speakerID": str(0),
            "connectTo": str(14),
            "x": 1.5,
            "y": 260,
            "id": str(15),  # Temporary ID for frontend
        })

    if "disruption" in speech.lower() and activationDict.get("disruption") != True:
        activationDict["disruption"] = True
        print("Demo: Disruption detected")
        time.sleep(3)
        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": str(15)
        })
        time.sleep(0.1)
        socketio.emit("node_instruction", {
            "content": "Competitors like Zoom are stagnant and others like Otter.ai only help after the meeting.",
            "action": "add",
            "type": "topDown",
            "speakerID": str(0),
            "connectTo": str(14),
            "x": -100,
            "y": 260,
            "id": str(16),  # Temporary ID for frontend
        })
        time.sleep(0.1)
        socketio.emit("node_instruction", {
            "content": "Identifies real-time assistance during meetings as a prime target for disruption.",
            "action": "add",
            "type": "topDown",
            "speakerID": str(0),
            "connectTo": str(14),
            "x": 153,
            "y": 260,
            "id": str(17),  # Temporary ID for frontend
        })
        time.sleep(3)
        socketio.emit("node_instruction", {
            "content": "Future Goal: Scale up into a standalone video conferencing software.",
            "action": "add",
            "type": "topDown",
            "speakerID": str(0),
            "connectTo": str(14),
            "x": -348,
            "y": 260,
            "id": str(18),  # Temporary ID for frontend
        })
        time.sleep(0.5)
        socketio.emit("node_instruction", {
            "content": "In 2023, Zoom hosted over 3.3 trillion meeting minutes annually, reflecting its extensive use in virtual communications.",
            "action": "add",
            "type": "custom",
            "speakerID": str(0),
            "connectTo": str(14),
            "x": 375,
            "y": 260,
            "id": str(19),  # Temporary ID for frontend
        })



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
                handle_demo(punctuatedText)


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
