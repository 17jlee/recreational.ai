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
};

document.getElementById("stopBtn").onclick = () => {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
  }
};

// 👇 Listen for GPT results and transcripts from backend
socket.on("node_instruction", (data) => {
  const messagesDiv = document.getElementById("messages");

  const msgEl = document.createElement("div");
  msgEl.classList.add("message");

  msgEl.innerHTML = `
    <div class="transcript"><strong>Transcript:</strong> ${data.transcript}</div>
    <div class="gpt"><strong>GPT:</strong> ${data.gpt_response}</div>
  `;

  messagesDiv.appendChild(msgEl);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
});
