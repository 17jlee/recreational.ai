def rawWordProcess(rawWords):
    speechList = [(rawWords[0]["word"], int(rawWords[0]["speaker"]))]
    lastSpeaker = int(rawWords[0]["speaker"])

    for x in rawWords[1:] :

                    if lastSpeaker == int(x["speaker"]) : # same speaker
                        currentString = speechList[-1][0]
                        newString = currentString + " " + x["word"]
                        speechList[-1] = (newString, int(x["speaker"]))
                        lastSpeaker = int(x["speaker"])
                    else : #new speaker
                        speechList.append((x["word"], int(x["speaker"])))
                        lastSpeaker = int(x["speaker"])

    return speechList
