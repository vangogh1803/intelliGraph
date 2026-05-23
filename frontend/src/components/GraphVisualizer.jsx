import { useEffect, useState, useCallback } from "react";
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import axios from "axios";

const API = "http://localhost:8000";

// Color map per node type
const NODE_COLORS = {
  File:         { bg: "#1e3a5f", border: "#3b82f6", text: "#93c5fd" },
  Function:     { bg: "#14532d", border: "#22c55e", text: "#86efac" },
  Class:        { bg: "#3b0764", border: "#a855f7", text: "#d8b4fe" },
  Module:       { bg: "#713f12", border: "#eab308", text: "#fde047" },
  Endpoint:     { bg: "#7f1d1d", border: "#ef4444", text: "#fca5a5" },
  Table:        { bg: "#164e63", border: "#06b6d4", text: "#67e8f9" },
  Config:       { bg: "#1c1917", border: "#78716c", text: "#d6d3d1" },
  Concept:      { bg: "#1e3a5f", border: "#60a5fa", text: "#bfdbfe" },
  Technology:   { bg: "#064e3b", border: "#10b981", text: "#6ee7b7" },
  default:      { bg: "#1e2130", border: "#4f46e5", text: "#a5b4fc" },
};

const getNodeStyle = (nodeType) => {
  const colors = NODE_COLORS[nodeType] || NODE_COLORS.default;
  return {
    background: colors.bg,
    border: `1px solid ${colors.border}`,
    color: colors.text,
    borderRadius: "8px",
    padding: "8px 12px",
    fontSize: "12px",
    fontWeight: "600",
    minWidth: "100px",
    textAlign: "center",
  };
};

// Layout nodes in a simple grid
const layoutNodes = (nodes) => {
  const cols = Math.ceil(Math.sqrt(nodes.length));
  const spacingX = 220;
  const spacingY = 120;

  return nodes.map((node, i) => ({
    ...node,
    position: {
      x: (i % cols) * spacingX + Math.random() * 40,
      y: Math.floor(i / cols) * spacingY + Math.random() * 40,
    },
    style: getNodeStyle(node.data.nodeType),
  }));
};

const GraphVisualizer = ({ projectId }) => {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState(null);
  const [selectedNode, setSelectedNode] = useState(null);
  const [filter, setFilter] = useState("all");
  const [allNodes, setAllNodes] = useState([]);
  const [allEdges, setAllEdges] = useState([]);

  const fetchGraph = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const res = await axios.get(`${API}/graph/visualize/${projectId}`);
      const laid = layoutNodes(res.data.nodes);
      setAllNodes(laid);
      setAllEdges(res.data.edges);
      setNodes(laid);
      setEdges(res.data.edges);
      setStats(res.data.stats);
    } catch (err) {
      console.error("Graph fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchGraph();
  }, [projectId]);

  // Filter by node type
  useEffect(() => {
    if (filter === "all") {
      setNodes(allNodes);
      setEdges(allEdges);
      return;
    }

    const filtered = allNodes.filter(
      (n) => n.data.nodeType === filter
    );
    const filteredIds = new Set(filtered.map((n) => n.id));
    const filteredEdges = allEdges.filter(
      (e) => filteredIds.has(e.source) && filteredIds.has(e.target)
    );

    setNodes(filtered);
    setEdges(filteredEdges);
  }, [filter]);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const nodeTypes = [
    "all", "File", "Function", "Class",
    "Module", "Endpoint", "Table", "Concept", "Technology"
  ];

  if (!projectId) {
    return (
      <div className="graph-placeholder">
        <p>Select a project to view its graph</p>
      </div>
    );
  }

  return (
    <div className="section">
      <h2>Graph Explorer</h2>

      {/* Stats Row */}
      {stats && (
        <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
          {[
            { label: "Nodes",    value: stats.total_nodes },
            { label: "Edges",    value: stats.total_edges },
            { label: "Files",    value: stats.files },
            { label: "Entities", value: stats.entities },
          ].map((s) => (
            <div key={s.label} style={{
              background: "#1e2130",
              border: "1px solid #2d3148",
              borderRadius: "8px",
              padding: "0.5rem 1rem",
              textAlign: "center"
            }}>
              <div style={{ color: "#6366f1", fontWeight: 700, fontSize: "1.2rem" }}>
                {s.value}
              </div>
              <div style={{ color: "#64748b", fontSize: "0.75rem" }}>
                {s.label}
              </div>
            </div>
          ))}
          <button className="btn" onClick={fetchGraph} style={{ margin: 0 }}>
            ↺ Refresh
          </button>
        </div>
      )}

      {/* Filter Row */}
      <div className="tab-row" style={{ marginBottom: "1rem", flexWrap: "wrap" }}>
        {nodeTypes.map((t) => (
          <button
            key={t}
            className={`tab ${filter === t ? "active" : ""}`}
            onClick={() => setFilter(t)}
            style={{ fontSize: "0.75rem", padding: "0.3rem 0.7rem" }}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Graph + Detail Panel */}
      <div style={{ display: "flex", gap: "1rem" }}>

        {/* React Flow Canvas */}
        <div style={{
          width: "100%",
          height: "520px",
          background: "#0f1117",
          border: "1px solid #2d3148",
          borderRadius: "12px",
          overflow: "hidden"
        }}>
          {loading ? (
            <div style={{
              display: "flex", alignItems: "center",
              justifyContent: "center", height: "100%",
              color: "#64748b"
            }}>
              Loading graph...
            </div>
          ) : (
            <ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onNodeClick={onNodeClick}
  fitView
  fitViewOptions={{ padding: 0.2 }}
  minZoom={0.1}
  maxZoom={2}
  defaultEdgeOptions={{
    style: { stroke: "#4f46e5", strokeWidth: 1.5 },
    labelStyle: { fill: "#94a3b8", fontSize: 10 },
    labelBgStyle: { fill: "#0f1117" },
    animated: false,
  }}
>
              <Controls />
              <MiniMap
                style={{ background: "#1e2130" }}
                nodeColor={(n) => {
                  const c = NODE_COLORS[n.data?.nodeType] || NODE_COLORS.default;
                  return c.border;
                }}
              />
              <Background color="#2d3148" gap={20} />
            </ReactFlow>
          )}
        </div>

        {/* Detail Panel */}
        {selectedNode && (
          <div style={{
            minWidth: "220px",
            background: "#1e2130",
            border: "1px solid #2d3148",
            borderRadius: "12px",
            padding: "1rem",
          }}>
            <div style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              marginBottom: "1rem"
            }}>
              <h3 style={{ color: "#e2e8f0", fontSize: "0.9rem" }}>
                Node Details
              </h3>
              <button
                onClick={() => setSelectedNode(null)}
                style={{
                  background: "none", border: "none",
                  color: "#64748b", cursor: "pointer", fontSize: "1rem"
                }}
              >
                ✕
              </button>
            </div>

            <div style={{ marginBottom: "0.75rem" }}>
              <div style={{ color: "#64748b", fontSize: "0.75rem", marginBottom: "0.25rem" }}>
                NAME
              </div>
              <div style={{ color: "#e2e8f0", fontWeight: 600, wordBreak: "break-all" }}>
                {selectedNode.data.label}
              </div>
            </div>

            <div style={{ marginBottom: "0.75rem" }}>
              <div style={{ color: "#64748b", fontSize: "0.75rem", marginBottom: "0.25rem" }}>
                TYPE
              </div>
              <span style={{
                background: (NODE_COLORS[selectedNode.data.nodeType] || NODE_COLORS.default).bg,
                color: (NODE_COLORS[selectedNode.data.nodeType] || NODE_COLORS.default).text,
                border: `1px solid ${(NODE_COLORS[selectedNode.data.nodeType] || NODE_COLORS.default).border}`,
                padding: "0.2rem 0.6rem",
                borderRadius: "999px",
                fontSize: "0.75rem",
                fontWeight: 600
              }}>
                {selectedNode.data.nodeType}
              </span>
            </div>

            {selectedNode.data.fullPath && (
              <div style={{ marginBottom: "0.75rem" }}>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginBottom: "0.25rem" }}>
                  PATH
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.8rem", wordBreak: "break-all" }}>
                  {selectedNode.data.fullPath}
                </div>
              </div>
            )}

            {selectedNode.data.extension && (
              <div>
                <div style={{ color: "#64748b", fontSize: "0.75rem", marginBottom: "0.25rem" }}>
                  EXTENSION
                </div>
                <div style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
                  {selectedNode.data.extension}
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div style={{
        display: "flex", flexWrap: "wrap",
        gap: "0.5rem", marginTop: "1rem"
      }}>
        {Object.entries(NODE_COLORS).filter(([k]) => k !== "default").map(([type, colors]) => (
          <div key={type} style={{
            display: "flex", alignItems: "center",
            gap: "0.4rem", fontSize: "0.75rem"
          }}>
            <div style={{
              width: "10px", height: "10px",
              borderRadius: "50%",
              background: colors.border
            }} />
            <span style={{ color: "#94a3b8" }}>{type}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GraphVisualizer;