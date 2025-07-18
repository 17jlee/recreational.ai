// src/FlowDiagram.js
import React, { useCallback, useEffect, useRef } from 'react';
import { layoutNodes } from './layout';
import MicButton from './MicButton';
import { io } from "socket.io-client";


import ReactFlow, {
  addEdge,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
} from 'reactflow';

import 'reactflow/dist/style.css';

import CustomNode from './CustomNode';
const nodeTypes = { custom: CustomNode };

const initialNodes = [
  {
    id: '1',
    type: 'input',
    data: { label: 'Initial Node' },
    position: { x: 100, y: 100 },
  },
];

const initialEdges = [
  // {
  //   id: 'e1-2',
  //   source: '1',
  //   target: '2',
  //   animated: false,
  //   style: { stroke: 'black' },
  // },
];

function FlowDiagram() {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  // Refs to track current state (avoid stale closures)
  const nodesRef = useRef(nodes);
  const edgesRef = useRef(edges);

  useEffect(() => {
    nodesRef.current = nodes;
    edgesRef.current = edges;
  }, [nodes, edges]);

  useEffect(() => {
    const socket = io("http://localhost:2500"); // Use http, not ws

    socket.on("node_instruction", async (message) => {
      console.log('Received node data:', message);

      if (message.action === 'add') {
        const edgeId = `e${message.connectTo}-${message.id}`;

        // Only add node if it's not already in the list
        if (!nodesRef.current.some((n) => n.id === message.id)) {
          console.log('Received node message:', message.content);
          const newNode = {
            id: message.id,
            data: { label: message.content },
            position: { x: 0, y: 0 }, 
          };

          const updatedNodes = [...nodesRef.current, newNode];
          let updatedEdges = [...edgesRef.current];

          if (message.connectTo && !edgesRef.current.some(e => e.id === edgeId)) {
            updatedEdges.push({
              id: edgeId,
              source: message.connectTo,
              target: message.id,
              style: { stroke: 'black' },
            });
          }

          const laidOut = await layoutNodes(updatedNodes, updatedEdges);

          setEdges(updatedEdges);
          setNodes(laidOut);
        }
      }




    });

  return () => socket.disconnect();
}, [setNodes, setEdges]);

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  return (

    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
        <MicButton onClick={() => console.log('Microphone button clicked')} />

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
