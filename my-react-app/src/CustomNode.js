// CustomNode.js
import React from 'react';
import { Handle, Position } from 'reactflow';

function CustomNode({ data }) {
  return (
    <div style={{ padding: 10, border: '1px solid #777', borderRadius: 5 }}>
      <Handle type="target" position={Position.Top} />
      <div>{data.label}</div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

export default CustomNode;
