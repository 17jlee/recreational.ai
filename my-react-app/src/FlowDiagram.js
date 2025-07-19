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
    id: '0',
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

      switch (message.action) {
        case 'add' :
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
          break;

        case 'delete':
          // Remove the node with id = message.parentID
          console.log('Deleting node with ID:', message.parentID);
          const nodeIdToDelete = String(message.parentID);
          const filteredNodes = nodesRef.current.filter(n => n.id !== nodeIdToDelete);
          // Remove edges connected to the deleted node
          const filteredEdges = edgesRef.current.filter(
            e => e.source !== nodeIdToDelete && e.target !== nodeIdToDelete
          );
          setNodes(filteredNodes);
          setEdges(filteredEdges);
          break;

        case 'modify':
          // Update the node with id = message.id
          console.log('Modifying node with ID:', message.nodeID);
          const updatedNode = {
            id: String(message.nodeID),
            data: { label: message.newContent },
            position: { x: 0, y: 0 }, 
          };

          const existingNodeIndex = nodesRef.current.findIndex(n => n.id === String(message.nodeID));
          if (existingNodeIndex !== -1) {
            const updatedNodesList = [...nodesRef.current];
            updatedNodesList[existingNodeIndex] = updatedNode;
            setNodes(updatedNodesList);
          }
          break;

        case 'setTitle':
        // Update the node with id = message.id
          console.log('Setting Title Node', message.nodeID);
          const titleNode = {
            id: '0',
            data: { label: message.newTitle },
            position: { x: 0, y: 0 }, 
          };

          const titleNodeIndex = nodesRef.current.findIndex(n => n.id === '0');
          if (titleNodeIndex !== -1) {
            const newNodesList = [...nodesRef.current];
            newNodesList[titleNodeIndex] = titleNode;
            setNodes(newNodesList);
          }
          break;


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
