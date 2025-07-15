class addNodeAction():
    def __init__(self, content, speakerID, parentID):
        self.content = str(content)
        self.speakerID = int(speakerID)
        self.parentID = int(parentID)

class modifyNodeAction():
    def __init__(self, newContent, newSpeakerID, nodeID):
        self.newContent = str(newContent)
        self.newSpeakerID = int(newSpeakerID)
        self.nodeID = int(nodeID)

class deleteNodeAction():
    def __init__(self, nodeID):
        self.nodeID = int(nodeID)

class setTitle():
    def __init__(self, newTitle):
        self.newTitle = str(newTitle)
