// src/FlowDiagram.js
//import CustomNode from './CustomNode';
import React, { useCallback } from 'react';
import { useEffect } from 'react';





//const nodeTypes = { custom: CustomNode };

import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';

import 'reactflow/dist/style.css';

import CustomNode from './CustomNode'; // <== also here if you're using it
const nodeTypes = { custom: CustomNode };

const initialNodes = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Hello Node' },
    position: { x: 100, y: 100 },
  },
  {
    id: '2',
    data: { label: 'Goodbye Node' },
    position: { x: 300, y: 200 },
  },
];

const initialEdges = [
  {
    id: 'e1-2',
    source: '1',
    target: '2',
    animated: false, // optional — default is false
    style: { stroke: 'black' }, // optional: customize color
  },
];

function FlowDiagram() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
  const socket = new WebSocket('ws://localhost:1234');

  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    console.log('Received node data:', message);

    if (message.type === 'add_node') {

      const newNode = {
        id: message.id, // unique id
        type: 'custom',    // or 'input', 'custom', etc. React Flow built-in types are 'input', 'default', 'output'
        data: { label: message.label },
        position: { x: message.x || 100, y: message.y || 100 },
      };


      setNodes((nds) => [...nds, newNode]);
      console.log('Adding node:', newNode);

      if (message.connectTo) {
        const newEdge = {
          id: `e${message.connectTo}-${message.nodeId}`,
          source: message.connectTo,
          target: message.nodeId,
        };

        setEdges((eds) => [...eds, newEdge]);
      }
    }
  };

  return () => socket.close(); // Clean up on unmount
}, [setNodes, setEdges]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (
    <div style={{ width: '100%', height: '100vh' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={nodeTypes}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <MiniMap />
        <Controls />
        <Background color="#aaa" gap={16} />
      </ReactFlow>
    </div>
  );
}




export default FlowDiagram;
