from openai import OpenAI
import json
import mindmapMethods
import mindmap

client = OpenAI()

prompt = """
Transform live transcription snippets into concise, key points suitable for mindmap nodes, continuously updating the mindmap JSON using the manage_mindmap tool as new partial speech inputs arrive. Inputs will be structured as [content of speech, speaker ID], and you will also receive the current state of the mindmap in JSON format. 

For every incoming transcription:
- Review the mindmap JSON thoroughly.
- Summarize and rephrase speech to extract only concise, relevant key points for potential addition to or modification of the mindmap.
- Remove or merge any redundant, verbose, or irrelevant nodes, ensuring the mindmap remains as concise and organized as possible. 
- If new topics emerge, create new parent nodes as necessary using the tool.
- If a transcription entry is irrelevant to the central discussion, take no action.
- Prioritize deletion or modification of existing nodes to maximize conciseness and relevance after each update.
- Do not produce any direct output; all actions are done exclusively via manage_mindmap tool calls.
- Persist in these actions with each prompt until all mindmap updates are complete before taking further input.

**Output Format:**
No direct textual output is to be generated. All operations are performed solely using the manage_mindmap tool with appropriate parameters.

---

**Example 1**

_Input:_
Speech: ["We should discuss project deadlines for the new marketing campaign", 2]  
Current Mindmap JSON:  
{
  "title": "Marketing Discussion",
  "id": 0,
  "childNodes": [
    {
        "id": 1,
        "speaker": 0,
        "content": "Project tasks",
        "childNodes": []
    },
    {
        "id": 2,
        "speaker": 1, 
        "content": "Budget allocation",
        "childNodes": []
    }
  ]
}

**Reasoning Steps:**  
- Identify that the mention of 'project deadlines' is a key topic for the mindmap.
- Since it is not currently present, add a concise node: "Project deadlines".
- No redundant information is detected, so no deletions.
- The topic is relevant to the current mindmap.

**manage_mindmap Tool Call:**  
manage_mindmap({  
  "action": "add_node",  
  "node": {"content": "Project deadlines"}  
})

---

**Example 2**

_Input:_
Speech: ["We already talked about the timeline and budget constraints", 1]  
Current Mindmap JSON:  
{
  "title": "Marketing Discussion",
  "id": 0,
  "childNodes": [
    {
        "id": 1,
        "speaker": 0,
        "content": "Project deadlines",
        "childNodes": []
    },
    {
        "id": 2, 
        "speaker": 2,
        "content": "Budget allocation",
        "childNodes": []
    },
    {
        "id": 3, 
        "speaker": 1,
        "content": "Timeline",
        "childNodes": []
        }
  ]
}

**Reasoning Steps:**  
- Detects 'timeline' and 'budget' are both referenced and redundantly represented as "Project deadlines" and "Timeline".
- Merge or condense these to form a single, clearer node: "Project deadlines & budget".
- Delete or reword the other nodes for conciseness.

**manage_mindmap Tool Calls:**  
manage_mindmap({  
  "action": "modify",  
  "node_id": 1,  
  "new_content": "Project deadlines & budget",
  "speaker_id": 3
})  
manage_mindmap({  
  "action": "remove",  
  "node_id": 3  
})

---

Important: After every new input, always review and streamline the mindmap structure to maximize conciseness and clarity. All actions must use the manage_mindmap tool exclusively; produce no output text.

**Reminder**: The main objective is to maintain a mindmap that is always current, concise, and relevant by adding, modifying, or deleting nodes exclusively through tool calls, with a thorough review at each update."""

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
}]


def GPTCall(speechList, punctuatedSpeech, mindmap : mindmap.MindMap) :
    try :
        response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "developer", "content": prompt},
            {"role": "user", "content": ("Speech: " + speechList + "\n" + "Current Mindmap JSON:" + "\n" + mindmap.to_json())}
            ],
        tools=mindmap_tool
    )
        argumment = response.output[0].arguments
    
    except Exception as e:
        print("Error in GPT call:", e)

    try:
        instruction = json.loads(argumment)
        print(instruction)

        instructionAction = instruction["action"]

        if instructionAction == "set_title" :
            return (mindmapMethods.setTitle(instruction["set_title"]["new_title"]))
        elif instructionAction == "add" :
            return (mindmapMethods.addNodeAction(instruction["add"]["content"], instruction["add"]["speaker_id"], instruction["add"]["parent_node_id"]))
        elif instructionAction == "modify" :
            try:
                return (mindmapMethods.modifyNodeAction(instruction["modify"]["new_content"], instruction["modify"]["speaker_id"],  instruction["modify"]["node_id"]))
            except:
                print("modification error")
        elif instructionAction == "remove" :
            try:
                return (mindmapMethods.deleteNodeAction(instruction["remove"]["node_id"]))
            except:
                print("deletion error")

    except json.decoder.JSONDecodeError :
        return None



#mindmap = MindMap("")

# while True :
#     newSpeech = str(input("New Data:"))
#     currentJSON = mindmap.to_json()
#     # print(mindmap_tool[0].type)

#     response = client.responses.create(
#         model="gpt-4.1",
#         input=[
#             {"role": "developer", "content": prompt},
#             {"role": "user", "content": ("Speech: " + newSpeech + "\n" + "Current Mindmap JSON:" + "\n" + currentJSON)}
#             ],
#         tools=mindmap_tool
#     )

#     argumment = response.output[0].arguments

#     try:
#         instruction = json.loads(argumment)
#         print(instruction)

#         instructionAction = instruction["action"]

#         if instructionAction == "set_title" :
#             mindmap.title = instruction["set_title"]["new_title"]
#         elif instructionAction == "add" :
#             mindmap.addNode(instruction["add"]["content"], instruction["add"]["speaker_id"], instruction["add"]["parent_node_id"])
#         elif instructionAction == "modify" :
#             try:
#                 mindmap.modify_by_id(instruction["modify"]["new_content"], instruction["modify"]["speaker_id"], instruction["modify"]["node_id"])
#             except:
#                 print("modification error")
#         elif instructionAction == "remove" :
#             try:
#                 mindmap.delete_by_id(instruction["remove"]["node_id"])
#             except:
#                 print("deletion error")

#     except json.decoder.JSONDecodeError :
#         print("none found")

#     print(mindmap.to_json())


    
    
    

# ['this recording is from the british council', 0]
