// src/FlowDiagram.js
import React, { useCallback, useEffect, useRef } from 'react';
import { layoutNodes } from './layout';

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
    animated: false,
    style: { stroke: 'black' },
  },
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
    const socket = new WebSocket('ws://localhost:1234');

    socket.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      console.log('Received node data:', message);

      if (message.type === 'add_node') {
        const edgeId = `e${message.connectTo}-${message.id}`;

        // Only add node if it's not already in the list
        if (!nodesRef.current.some((n) => n.id === message.id)) {
          const newNode = {
            id: message.id,
            data: { label: message.label },
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
    };

    return () => socket.close();
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
