import eventlet
eventlet.monkey_patch()

import random

from flask import Flask, render_template
from flask_socketio import SocketIO, emit
from flask import Flask, send_from_directory
import websocket
import threading
import json
import os
import mindmap
import gptTools
import mindmapMethods

app2 = Flask(__name__, static_folder='my-react-app/build')

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

DEEPGRAM_API_KEY = "6e85a7a5f06a649ea729ebc388767458a737d45a"
DG_WS_ENDPOINT = f"wss://api.deepgram.com/v1/listen?punctuate=true&diarize=true&model=nova-3"

dg_ws = None

currentMindmap = mindmap.MindMap("")

# def chatGPTWrapper(content, personID) :


def chatGPTWrapper(speechList, punctuatedSpeech, mindmap: mindmap.MindMap, callback=None):
    try:
        action = gptTools.GPTCall(speechList, punctuatedSpeech, mindmap)

        if action == None :
            print("action error")
        else :
            if callback:
                callback(action)  # <- pass both if needed

    except Exception as e:
        print("GPT Error:", e)

def handle_gpt_response(action):
    global currentMindmap
    """
    Handle the GPT response after it returns from OpenAI.
    You can emit to frontend, log, or trigger other backend logic here.
    """
    print(currentMindmap.to_json())


    if None:
        print("no action required")
    elif isinstance(action, mindmapMethods.addNodeAction): #add
        newID = currentMindmap.addNode(action.content, action.speakerID, action.parentID)
       
        socketio.emit("node_instruction", {
            "action": "add",
            "content": action.content,
            "speakerID": str(action.speakerID),
            "connectTo": str(action.parentID),
            "id": str(newID),  # Temporary ID for frontend
        })

    elif isinstance(action, mindmapMethods.deleteNodeAction):#delete
        
        currentMindmap.delete_by_id(action.nodeID)

        socketio.emit("node_instruction", {
            "action": "delete",
            "parentID": action.nodeID
        })

    elif isinstance(action, mindmapMethods.modifyNodeAction):#modify
        currentMindmap.modify_by_id(action.newContent, action.newSpeakerID, action.nodeID)

        socketio.emit("node_instruction", {
            "action": "modify",
            "newContent": action.newContent,
            "newSpeakerID": action.newSpeakerID,
            "nodeID": action.nodeID
        })
        

    elif isinstance(action, mindmapMethods.setTitle): #settitle
        currentMindmap.title = action.newTitle
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

    headers = {
        "Authorization": f"Token {DEEPGRAM_API_KEY}"
    }

    def on_message(ws, message):
        data = json.loads(message)
        if "channel" in data:
            transcript = data["channel"]["alternatives"][0]["transcript"]
            wordContent = data["channel"]["alternatives"][0]["words"]

            
            if transcript:
                speechList = [(wordContent[0]["word"], int(wordContent[0]["speaker"]))]
                lastSpeaker = int(wordContent[0]["speaker"])

                for x in wordContent[1:] :

                    if lastSpeaker == int(x["speaker"]) : # same speaker
                        currentString = speechList[-1][0]
                        newString = currentString + " " + x["word"]
                        speechList[-1] = (newString, int(x["speaker"]))
                        lastSpeaker = int(x["speaker"])
                    else : #new speaker
                        speechList.append((x["word"], int(x["speaker"])))
                        lastSpeaker = int(x["speaker"])
                print("-------------------------")
                # print(data)
                print(transcript)
                print(speechList)
                print("-------------------------")

                threading.Thread(
                target=chatGPTWrapper,
                args=(str(speechList), "", currentMindmap, handle_gpt_response),
                daemon=True
                ).start()


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
