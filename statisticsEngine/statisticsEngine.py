from openai import OpenAI
import json
client = OpenAI()

prompt = """SYSTEM:
You are “StatBot,” an expert research assistant with real‑time web search access. 
Your task is to find and return the most relevant, up‑to‑date statistics or key facts on various topics.
You will be given a mindmap in JSON format, which contains a discussion topic and its subtopics.
Find reliable, high‑confidence statistics or key facts related to the topic and its subtopics in the mindmap.
Whenever asked about a topic, you will:
1. Formulate concise search queries.
2. Execute them via the GPT Search API.
3. Extract 1–3 up‑to‑date, high‑confidence statistics or key facts.
4. Return results using the manage_mindmap tool with add, each with:
   • a short “statistic” (number + units),
   • a one‑sentence “description”,
   - speaker ID -41.
If you can’t find reliable data, respond with an empty “results” array. Give me a statistic about zoom meetings"""

mindmap_tool = [{
  "type": "function",
  "name": "manage_mindmap",
  "description": "Manages a mindmap by adding, removing, or modifying nodes.",
  "parameters": {
    "type": "object",
    "properties": {
      "action": {
        "type": "string",
        "description": "Type of operation to perform on the mindmap node",
        "enum": ["add"]
      },
      "add": {
        "type": "object",
        "description": "Parameters for adding a node",
        "properties": {
          "parent_node_id": {
            "type": "integer",
            "description": "ID of the parent node to which the new node will be added"
          },
          "content": {
            "type": "string",
            "description": "Content of the new node"
          },
          "speaker_id": {
            "type": "integer",
            "description": "ID of the speaker associated with the new node"
          }
        },
        "required": ["parent_node_id", "content", "speaker_id"],
        "additionalProperties": False
      }
    },
    "required": ["action", "add"],
    "additionalProperties": False
  }
}
 , {"type": "web_search_preview"}]

sampleMap = """{
  "title": "Recreational.ai Pitch to YC",
  "id": 0,
  "childNodes": [
    {
      "id": 1,
      "speaker": 1,
      "content": "What is Recreational.ai?",
      "childNodes": [
        {
          "id": 2,
          "speaker": 1,
          "content": "A web-app that listens to conversations and automatically visualizes key concepts using nodes and edges.",
          "childNodes": []
        },
        {
          "id": 3,
          "speaker": 1,
          "content": "Designed to run on a main meeting-room screen for all participants.",
          "childNodes": []
        },
        {
          "id": 4,
          "speaker": 1,
          "content": "Core benefit: Provides a real-time summary so you're never lost in a meeting.",
          "childNodes": []
        }
      ]
    },
    {
      "id": 5,
      "speaker": 1,
      "content": "Key Features",
      "childNodes": [
        {
          "id": 6,
          "speaker": 1,
          "content": "Statistics Engine: Automatically searches the web for key statistics about the current conversation.",
          "childNodes": []
        },
        {
          "id": 7,
          "speaker": 1,
          "content": "Speaker Attribution: Uses speech diarization to identify and credit people for their ideas (e.g., colored nodes).",
          "childNodes": []
        }
      ]
    },
    {
      "id": 8,
      "speaker": 1,
      "content": "Market & Vision",
      "childNodes": [
        {
          "id": 9,
          "speaker": 1,
          "content": "Competitors like Zoom are stagnant and others like Otter.ai only help after the meeting.",
          "childNodes": []
        },
        {
          "id": 10,
          "speaker": 1,
          "content": "Identifies real-time assistance during meetings as a prime target for disruption.",
          "childNodes": []
        },
        {
          "id": 11,
          "speaker": 1,
          "content": "Future Goal: Scale up into a standalone video conferencing software.",
          "childNodes": []
        }
      ]
    }
  ]"""

class addNodeAction():
    def __init__(self, content, speakerID, parentID):
        self.content = str(content)
        self.speakerID = int(speakerID)
        self.parentID = int(parentID)

def GPTCall(mindmapJSON) :
    try :
        response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "developer", "content": prompt},
            {"role": "user", "content": mindmapJSON},
            ],
        tools=mindmap_tool
    )
        print("GPT Response:", response)
        argumment = response.output[0].arguments
        
    
    except Exception as e:
        print("Error in GPT call:", e)

    try:
        instruction = json.loads(argumment)
        print("GPT Response:", instruction)
        instruction = json.loads(argumment)
        if "action" not in instruction or instruction["action"] != "add":
            print("Invalid action in GPT response")
            return None
        else :
            if instruction["action"] == "add" :
             return (addNodeAction(instruction["add"]["content"], instruction["add"]["speaker_id"], instruction["add"]["parent_node_id"]))

    except json.decoder.JSONDecodeError :
        return None

# GPTCall(sampleMap)
