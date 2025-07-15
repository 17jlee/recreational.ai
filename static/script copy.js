let socket = io.connect(location.origin);
let mediaRecorder;

document.getElementById("startBtn").onclick = async () => {
  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  mediaRecorder = new MediaRecorder(stream, { mimeType: "audio/webm" });

  mediaRecorder.ondataavailable = (event) => {
    if (event.data.size > 0) {
      event.data.arrayBuffer().then(buffer => {
        socket.emit("audio_chunk", buffer);
      });
    }
  };

  mediaRecorder.start(250); // Capture every 250ms
 // mediaRecorder.start(5000);
};

document.getElementById("stopBtn").onclick = () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
};
