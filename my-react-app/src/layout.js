// layout.js
import ELK from 'elkjs/lib/elk.bundled.js';

const elk = new ELK();

export const layoutNodes = async (nodes, edges) => {
  const elkGraph = {
    id: 'root',
    layoutOptions: {
      'elk.algorithm': 'radial', // <- other options: layered, force, tree
    },
    children: nodes.map((node) => ({
      id: node.id,
      width: 150,
      height: 50,
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      sources: [edge.source],
      targets: [edge.target],
    })),
  };

  const layout = await elk.layout(elkGraph);

  const nodeMap = new Map(layout.children.map((n) => [n.id, n]));

  const positionedNodes = nodes.map((node) => ({
    ...node,
    position: {
      x: nodeMap.get(node.id)?.x || 0,
      y: nodeMap.get(node.id)?.y || 0,
    },
  }));

  return positionedNodes;
};
