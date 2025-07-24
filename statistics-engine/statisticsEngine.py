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
   • a “source” URL,
   • a “retrieved_date” (YYYY‑MM‑DD),
   • an optional “confidence” score (0.0–1.0).
   - speaker ID -41.
If you can’t find reliable data, respond with an empty “results” array."""

mindmap_tool = [{
  "type": "function",
  "name": "manage_mindmap",
  "description": "Manages a mindmap by adding, removing, or modifying nodes.",
  "strict": False,
  "parameters": {
    "type": "object",
    "required": [],
    "properties": {
      "action": {
        "type": "string",
        "description": "Type of operation to perform on the mindmap node",
        "enum": [
          "add",
          "remove",
          "modify",
          "set_title"
        ]
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
        "required": [
          "parent_node_id",
          "content",
          "speaker_id"
        ],
        "additionalProperties": False
      },
      "remove": {
        "type": "object",
        "description": "Parameters for removing a node and its children",
        "properties": {
          "node_id": {
            "type": "integer",
            "description": "ID of the node to remove, along with its children"
          }
        },
        "required": [
          "node_id"
        ],
        "additionalProperties": False
      },
      "modify": {
        "type": "object",
        "description": "Parameters for modifying a node",
        "properties": {
          "node_id": {
            "type": "integer",
            "description": "ID of the node to modify"
          },
          "new_content": {
            "type": "string",
            "description": "New content for the node"
          },
          "speaker_id": {
            "type": "string",
            "description": "ID of the speaker associated with the modified node"
          }
        },
        "required": [
          "node_id",
          "new_content",
          "speaker_id"
        ],
        "additionalProperties": False
      },
      "set_title": {
        "type": "object",
        "description": "Set a new title for the mindmap",
        "properties": {
          "new_title": {
            "type": "string",
            "description": "The new title of the mindmap."
          }
        },
        "required": [
          "new_title"
        ],
        "additionalProperties": False
      }

    },
    "additionalProperties": False
  }
}, {"type": "web_search_preview"}]

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
        instruction = json.loads(argumment)
    
    except Exception as e:
        print("Error in GPT call:", e)

    try:
        print("GPT Response:", instruction)

    except json.decoder.JSONDecodeError :
        return None

GPTCall()
