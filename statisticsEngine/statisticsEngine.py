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
If you can’t find reliable data, respond with an empty “results” array."""

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
  "title": "Renewable Energy - Team Meeting",
  "id": 0,
  "childNodes": [
    {
      "id": 1,
      "speaker": 0,
      "content": "Solar Energy",
      "childNodes": [
        {
          "id": 4,
          "speaker": 1,
          "content": "Installation progress",
          "childNodes": [
            {
              "id": 10,
              "speaker": 1,
              "content": "Completed 5 new rooftops",
              "childNodes": []
            }
          ]
        }
      ]
    },
    {
      "id": 2,
      "speaker": 1,
      "content": "Wind Power",
      "childNodes": [
        {
          "id": 5,
          "speaker": 0,
          "content": "Site selection",
          "childNodes": [
            {
              "id": 11,
              "speaker": 0,
              "content": "Review environmental impact",
              "childNodes": []
            }
          ]
        }
      ]
    },
    {
      "id": 3,
      "speaker": 2,
      "content": "Grid Integration",
      "childNodes": [
        {
          "id": 6,
          "speaker": 1,
          "content": "Battery storage",
          "childNodes": [
            {
              "id": 12,
              "speaker": 1,
              "content": "Evaluate new suppliers",
              "childNodes": []
            }
          ]
        }
      ]
    }
  ]
}"""

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
