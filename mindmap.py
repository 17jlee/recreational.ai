import json

class Node:
    def __init__(self, content, id, speaker) :
        self.content = str(content)
        self.id = int(id)
        self.speaker = int(speaker)
        self.childNodes = []
    
    def modify(self, content, speaker) :
        self.content = str(content)
        self.speaker = int(speaker)
    
    def addChild(self, childNode) :
        self.childNodes.append(childNode)    
    
    def delChild(self, id) :
        newChildNodes = []
        
        for node in self.childNodes :
            if (node.id) != int(id) :
                newChildNodes.append(node)
        
        self.childNodes = newChildNodes

    def display(self, level=0):
        indent = "  " * level
        print(f"{indent}Node ID: {self.id} | Speaker: {self.speaker}\n{indent}{self.content}")
        for child in self.childNodes:
            child.display(level + 1)
    
    def to_dict(self):
        return {
            "id": self.id,
            "speaker": self.speaker,
            "content": self.content,
            "childNodes": [child.to_dict() for child in self.childNodes]
        }
    
    def find_by_id(self, id):
        if self.id == id:
            return self
        for child in self.childNodes:
            result = child.find_by_id(id)
            if result:
                return result
        return None


class MindMap :
    def __init__(self, title) :
        self.title = str(title)
        self.childNodes = []
        self.id = 0
        self.currentID = 1

    def addChild(self, childNode) :
        self.childNodes.append(childNode)

    def display(self):
        print("MindMap Title:", self.title)
        for child in self.childNodes:
            child.display()

    def find_by_id(self, id):
        for child in self.childNodes:
            result = child.find_by_id(id)
            if result:
                return result
        return None
    
    def to_dict(self):
        return {
            "title": self.title,
            "id": self.id,
            "childNodes": [child.to_dict() for child in self.childNodes]
        }

    def to_json(self):
        return json.dumps(self.to_dict(), indent=2)
    
    def add_child_to_id(self, parent_id, new_node):
        parent_node = self.find_by_id(parent_id)
        if parent_node:
            parent_node.addChild(new_node)
        else:
            raise NameError("Parent node ID not found.")
    
    def delete_by_id(self, id):
        id = int(id)

        if id == 0 :
            raise ValueError("This is the title node. Use the set_title tool instead.")

        for i, child in enumerate(self.childNodes):
            if child.id == id:
                del self.childNodes[i]
                return True
            if self._delete_from_node(child, id):
                return True
        raise NameError("Node ID for deletion not found.")

    def _delete_from_node(self, node, id):
        for i, child in enumerate(node.childNodes):
            if child.id == id:
                del node.childNodes[i]
                return True
            if self._delete_from_node(child, id):
                return True
        return False
    
    def modify_by_id(self, new_content, new_speaker, id):
        if id == 0:
            self.title = new_content
        else :
            node = self.find_by_id(int(id))
            if node:
                node.modify(new_content, new_speaker)
            else:
                raise NameError("Node ID for modification not found.") 
        
    def addNode(self, content, speaker, parentID) :
        newNode = Node(content, self.currentID, speaker)
        
        if parentID == 0 :
            self.addChild(newNode)
        else :
            self.add_child_to_id(parentID, newNode)
        self.currentID+=1
        


# mindmap = MindMap("British Council Recording")
# json_output = mindmap.to_json()
# print(json_output)



# while True :
#     a = str(input("content: "))
#     b = int(input("speaker: "))
#     c = int(input("parentID: "))
#     try :
#         mindmap.addNode(a,b,c)
#     except NameError as error :
#         print(error)
#     except ValueError as error :
#         print(error)
#     else :
#         print("success")
#         json_output = mindmap.to_json()
#         print(json_output)

    








