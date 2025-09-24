# session.py
import queue
import threading
import mindmap
import gptTools
import mindmapMethods  # needed for action types

class SessionState:
    def __init__(self, sid, socketio):
        self.sid = sid
        self.socketio = socketio
        self.mindmap = mindmap.MindMap("")
        self.task_queue = queue.Queue(maxsize=100)
        self._stop = threading.Event()
        self.gpt_thread = socketio.start_background_task(self._gpt_worker)

        # Optional per-session resources managed by app.py:
        self.dg_ws = None
        self.speech_timer = None

    def enqueue_transcript(self, speech_list, transcript):
        try:
            self.task_queue.put_nowait((speech_list, transcript))
        except queue.Full:
            print(f"[{self.sid}] task queue full; dropping oldest")
            try:
                self.task_queue.get_nowait()
            except queue.Empty:
                pass
            self.task_queue.put_nowait((speech_list, transcript))

    def _gpt_worker(self):
        while not self._stop.is_set():
            try:
                item = self.task_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            try:
                speech_list, transcript = item
                # Append transcript here (single place => no races)
                self.mindmap.updateTranscript(str(transcript))
                action = gptTools.GPTCall(
                    speech_list,
                    self.mindmap.currentTranscript,
                    self.mindmap
                )
                if action:
                    self._handle_gpt_response(action)
            except Exception as e:
                print(f"[{self.sid}] GPT worker error:", e)
            finally:
                self.task_queue.task_done()

    def _handle_gpt_response(self, action):
        
        if isinstance(action, mindmapMethods.addNodeAction):
            newID = self.mindmap.addNode(action.content, action.speakerID, action.parentID)
            print("hit", self.sid)
            self.socketio.emit("node_instruction", {
                "action": "add",
                "content": action.content,
                "speakerID": str(action.speakerID),
                "connectTo": str(action.parentID),
                "id": str(newID),
            "sid": self.sid
            }, to=self.sid, namespace="/")

        elif isinstance(action, mindmapMethods.deleteNodeAction):
            self.mindmap.delete_by_id(action.nodeID)
            self.socketio.emit("node_instruction", {
                "action": "delete",
                "parentID": action.nodeID
            }, room=self.sid)

        elif isinstance(action, mindmapMethods.modifyNodeAction):
            self.mindmap.modify_by_id(action.newContent, action.newSpeakerID, action.nodeID)
            self.socketio.emit("node_instruction", {
                "action": "modify",
                "newContent": action.newContent,
                "newSpeakerID": action.newSpeakerID,
                "nodeID": action.nodeID
            }, room=self.sid)

        elif isinstance(action, mindmapMethods.setTitle):
            self.mindmap.title = action.newTitle
            self.socketio.emit("node_instruction", {
                "action": "setTitle",
                "newTitle": action.newTitle
            }, room=self.sid)

        else:
            print(f"[{self.sid}] unknown action type: {type(action)}")

    def reset_speech_timer(self, timeout_secs=5.0, on_timeout=None):
        if self.speech_timer is not None:
            self.speech_timer.cancel()
        if on_timeout:
            self.speech_timer = threading.Timer(timeout_secs, on_timeout)
            self.speech_timer.start()

    def close(self):
        self._stop.set()
        if self.speech_timer:
            try:
                self.speech_timer.cancel()
            except Exception:
                pass
        # Deepgram WS is closed by app.py
