from openai import OpenAI
import json
import mindmapMethods
import mindmap

client = OpenAI()

prompt = """Transform live transcription snippets into concise, key points suitable for mindmap nodes, continuously updating the mindmap JSON using the manage_mindmap tool as new partial speech inputs arrive. Inputs will be structured as [(content of speech, speaker ID), (content of speech, speaker ID) ...] depending on how many speakers have been transcribed in the latest sample and you will also receive the current state of the mindmap in JSON format as well as the up-to-date cumulative transcript of the current conversation to that point in time.


For every incoming transcription:
- Review the mindmap JSON thoroughly.
- Carefully read the current cumulative conversation transcript to date.
- Ensure that all key points and topics mentioned in the transcript are represented in the mindmap. Do not omit any relevant information; every significant idea or topic should be preserved as a node.
- Summarize and rephrase speech from the latest transcript sample [(content of speech, speaker ID), ...] to extract concise, relevant key points for addition or modification in the mindmap, considering the full transcript context.
- Maintain conciseness and clarity by merging, modifying, or removing only nodes that are redundant, verbose, or outdated. Do not remove nodes simply because they seem less relevant; preserve all unique information.
- If new topics emerge—even if they seem currently irrelevant to the main discussion—add them as new parent nodes (children of node id 0) rather than deleting or ignoring them.
- If a transcription entry is completely off-topic or not meaningful, take no action.
- Do not produce any direct output; all actions are done exclusively via manage_mindmap tool calls.
- Persist in these actions with each prompt until all mindmap updates are complete before taking further input.


**Output Format:**
No direct textual output is to be generated. All operations are performed solely using the manage_mindmap tool with appropriate parameters.

---

**Example 1**

_Input:_
Transcript so far:
"Let's review our solar panel installation progress and discuss wind farm site selection. Battery storage is also a priority for grid integration."
New Speech: [("Has anyone played the new Nintendo Switch game this weekend?", 2)]
Current Mindmap JSON:
{
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
}

**Reasoning Steps:** 
- Read through the current transcript so far thoroughly.
- Identify that the mention of 'Nintendo Switch' is not a key topic for the mindmap.
- Since the title only describes a meeting about renewable energy, change this to "Renewable Energy & Nintendo Switch Games" by using 'set_title' tool.
- According to the prompt, add this as a new root node (child of node id 0), not delete or ignore.
- No redundant information is detected, so no deletions.

**manage_mindmap Tool Call:**
manage_mindmap({  
  "action": "set_title",  
  "node_id": 1,  
  "new_content": "Renewable Energy & Nintendo Switch Games",
  "speaker_id": 3
})   
manage_mindmap({
  "action": "add",
  "add": {
    "parent_node_id": 0,
    "content": "Nintendo Switch games discussion",
    "speaker_id": 2
  }
})

---

**Example 2**

_Input:_
Transcript so far:
Let’s set clear quarterly goals for the team. We should also define KPIs for each department.
New Speech: [("KPIs should include customer satisfaction and revenue growth targets, not just operational metrics.", 1)]
Current Mindmap JSON:
{
  "title": "Goal Setting Meeting",
  "id": 0,
  "childNodes": [
    {
      "id": 1,
      "speaker": 0,
      "content": "Quarterly goals",
      "childNodes": []
    },
    {
      "id": 2,
      "speaker": 1,
      "content": "Department KPIs",
      "childNodes": []
    },
    {
      "id": 3,
      "speaker": 1,
      "content": "Operational metrics",
      "childNodes": []
    }
  ]
}

**manage_mindmap Tool Call:**
manage_mindmap({
  "action": "modify",
  "node_id": 2,
  "new_content": "KPIs: customer satisfaction, revenue growth, operational metrics",
  "speaker_id": 1
})

manage_mindmap({
  "action": "remove",
  "node_id": 3
})

---

**Example 3**

_Input:_
Transcript so far:
Thanks for joining, everyone. Let’s jump right in. I’ve been reviewing our new marketing strategy proposal, and I think we need to reallocate part of the digital ad budget toward influencer partnerships. I agree. We've seen better engagement with influencers lately. Maybe we shift 20% from paid search into that channel? That could work. But we’ll need to outline new tasks—sourcing influencers, drafting contracts, and creating tailored content briefs. I can start a task tracker for that. Just flag any significant changes in spend by category. I’ll adjust the budget forecast accordingly and send over an updated allocation sheet. Great. So, Lena will handle the influencer workflow, and Raj will revise the digital strategy. We should discuss project deadlines for the new marketing campaign.
New Speech: [("We should discuss project deadlines for the new marketing campaign", 2)]  
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
- Read through the current transcript so far thoroughly. 
- Identify that the mention of 'project deadlines' is a key topic for the mindmap.
- Since it is not currently present, add a concise node: "Project deadlines".
- No redundant information is detected, so no deletions.
- The topic is relevant to the current mindmap.

**manage_mindmap Tool Call:**  
manage_mindmap({  
  "action": "add",  
  "parent_node_id": 0,
  "content": "Project deadlines",
  "speaker_id": 2
})

---

**Reasoning Steps:** 
- Read through the current transcript so far thoroughly.
- The new speech expands on KPIs, specifying customer satisfaction and revenue growth as important metrics.
- "Operational metrics" is now redundant, as KPIs should encompass all relevant metrics.
- Merge "Department KPIs" and "Operational metrics" into a single, more descriptive node.
- Remove the now-redundant "Operational metrics" node.

**Important Reminder:**  
Node 0 (the root node) cannot be removed or directly modified.  
To change the mindmap's title, use the set_title action instead.

**IMPORTANT REMINDER OF PURPOSE AND GOAL**
Important: After every new input, always review and streamline the mindmap structure to maximize conciseness and clarity. All actions must use the manage_mindmap tool exclusively; produce no output text.

**MOST IMPORTANT REMINDER TO KEEP IN MIND: ABOVE ALL ELSE**
MAKE SURE NODES WITH ANY RELATION TO PRE-EXISTING NODES ARE CONNECTED TOGETHER - ALWAYS ADD NEW NODES AS CHILD NODES OF THE HIGHEST ID EXISTING NODES, NEVER AS ROOT NODES.
The depth of a mindmap is the number of child nodes in child nodes, your goal is to have the highest depth possible whilst maintaining a minimum of 4 child nodes for each node, so always add new nodes as children of the highest ID existing nodes if we have exhausted the 4 child nodes of the current node.


**Reminder**: The main objective is to maintain a mindmap that is always current, concise, and relevant by adding, modifying, or deleting nodes exclusively through tool calls, with a thorough review at each update. New topics should be added as root nodes, not deleted, even if they are not immediately relevant."""

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


def GPTCall(speechList, currentTranscript, mindmap : mindmap.MindMap) :
    try :
        response = client.responses.create(
        model="gpt-4.1",
        input=[
            {"role": "developer", "content": prompt},
            {"role": "user", "content": ("Transcript so far:" + "\n" + currentTranscript + "\n" + "New Speech: " + speechList + "\n" + "Current Mindmap JSON:" + "\n" + mindmap.to_json())}
            ],
        tools=mindmap_tool
    )
        argumment = response.output[0].arguments
    
    except Exception as e:
        print("Error in GPT call:", e)

    try:
        instruction = json.loads(argumment)
        print("Transcript so far:" + "\n" + currentTranscript + "\n" + "New Speech: " + speechList + "\n" + "Current Mindmap JSON:" + "\n" + mindmap.to_json())
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

