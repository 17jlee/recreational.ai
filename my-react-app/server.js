// server.js
const WebSocket = require('ws');

const wss = new WebSocket.Server({ port: 1234 });

wss.on('connection', (ws) => {
  console.log('Client connected');

  // Send a test message every 3 seconds
  let count = 1;
  const interval = setInterval(() => {
    const message = {
      type: 'add_node',
      id: `node-${count}`,
      label: `Node ${count}`,
      x: 100 + count * 30,
      y: 100 + count * 20,
      connectTo: '1',
    };
    ws.send(JSON.stringify(message));
    count++;
  }, 3000);

  ws.on('close', () => {
    console.log('Client disconnected');
    clearInterval(interval);
  });
});

