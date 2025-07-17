// src/components/MicrophoneButton.js
import React, { useRef } from 'react';
import { io } from 'socket.io-client';

//const socket = io.connect(window.location.origin);
const socket = io('http://localhost:2500');

function MicButton() {
  const mediaRecorderRef = useRef(null);

  const handleStart = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          event.data.arrayBuffer().then((buffer) => {
            socket.emit('audio_chunk', buffer);
          });
        }
      };

      mediaRecorder.start(250); // capture every 250ms
      mediaRecorderRef.current = mediaRecorder;
    } catch (err) {
      console.error('Microphone access denied or error:', err);
    }
  };

  return (
    <button
      onClick={handleStart}
      style={{
        position: 'absolute',
        top: '20px',
        right: '20px',
        zIndex: 10,
        padding: '12px 16px',
        borderRadius: '999px',
        backgroundColor: '#f87171',
        color: '#fff',
        border: 'none',
        fontSize: '16px',
        cursor: 'pointer',
        boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
      }}
    >
      🎤 Start Mic
    </button>
  );
}

export default MicButton;
