import { useState } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const StatusBadge = ({ status }) => {
  const cls =
    status === "ready"      ? "status-badge-ready" :
    status === "processing" ? "status-badge-processing" :
    status === "failed"     ? "status-badge-failed" :
    "status-badge-processing";

  const label =
    status === "ready"      ? "✓ Ready" :
    status === "processing" ? "⟳ Processing" :
    status === "failed"     ? "✗ Failed" : status;

  return <span className={cls}>{label}</span>;
};

const ProjectList = ({ projects, onGraphBuilt }) => {
  const [building, setBuilding] = useState(null);
  const [results, setResults] = useState({});

  const handleBuildGraph = async (projectId) => {
    setBuilding(projectId);
    try {
      const res = await axios.post(`${API}/graph/build-project/${projectId}`);
      setResults((prev) => ({ ...prev, [projectId]: res.data }));
      if (onGraphBuilt) onGraphBuilt();
    } catch (err) {
      setResults((prev) => ({
        ...prev,
        [projectId]: {
          error: err.response?.data?.detail || "Graph build failed"
        }
      }));
    } finally {
      setBuilding(null);
    }
  };

  if (!projects || projects.length === 0) {
    return (
      <div className="section">
        <h2>Projects</h2>
        <p style={{ color: "#64748b" }}>
          No projects yet. Import one above.
        </p>
      </div>
    );
  }

  return (
    <div className="section">
      <h2>Projects</h2>
      <table className="projects-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Source</th>
            <th>Files</th>
            <th>Chunks</th>
            <th>Status</th>
            <th>Graph</th>
          </tr>
        </thead>
        <tbody>
          {projects.map((p) => (
            <tr key={p.id}>
              <td>{p.name}</td>
              <td>
                <span className="source-badge">
                  {p.source === "github" ? "🐙 GitHub" : "📦 ZIP"}
                </span>
              </td>
              <td>{p.file_count}</td>
              <td>{p.chunk_count}</td>
              <td><StatusBadge status={p.status} /></td>
              <td>
                <button
                  className="build-btn"
                  onClick={() => handleBuildGraph(p.id)}
                  disabled={building === p.id || p.status !== "ready"}
                >
                  {building === p.id ? "Building..." : "Build Graph"}
                </button>
                {results[p.id] && !results[p.id].error && (
                  <div style={{ color: "#4ade80", fontSize: "0.75rem", marginTop: "0.25rem" }}>
                    ✅ {results[p.id].entities_extracted} entities
                  </div>
                )}
                {results[p.id]?.error && (
                  <div style={{ color: "#f87171", fontSize: "0.75rem", marginTop: "0.25rem" }}>
                    ❌ {results[p.id].error}
                  </div>
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default ProjectList;