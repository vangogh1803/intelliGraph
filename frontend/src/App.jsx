import { useEffect, useState } from "react";
import axios from "axios";
import StatusCard from "./components/StatusCard";
import ProjectImport from "./components/ProjectImport";
import ProjectList from "./components/ProjectList";
import GraphStats from "./components/GraphStats";
import GraphVisualizer from "./components/GraphVisualizer";
import ProjectSelector from "./components/ProjectSelector";
import ChatPanel from "./components/ChatPanel";
import ObservabilityDashboard from "./components/ObservabilityDashboard";
import "./index.css";

const API = "http://localhost:8000";

function App() {
  const [health, setHealth] = useState(null);
  const [healthLoading, setHealthLoading] = useState(true);
  const [projects, setProjects] = useState([]);
  const [graphKey, setGraphKey] = useState(0);
  const [selectedProjectId, setSelectedProjectId] = useState(null);
  const [activeTab, setActiveTab] = useState("chat");

  const fetchHealth = () => {
    axios.get(`${API}/health`)
      .then((res) => setHealth(res.data))
      .catch(() => setHealth(null))
      .finally(() => setHealthLoading(false));
  };

  const fetchProjects = () => {
    axios.get(`${API}/projects`)
      .then((res) => {
        const p = res.data.projects;
        setProjects(p);
        if (!selectedProjectId && p.length > 0) {
          const ready = p.find((x) => x.status === "ready");
          if (ready) setSelectedProjectId(ready.id);
        }
      })
      .catch(() => setProjects([]));
  };

  useEffect(() => {
    fetchHealth();
    fetchProjects();
  }, []);

  const selectedProject = projects.find((p) => p.id === selectedProjectId);

  return (
    <div>
      {/* Header */}
<div className="header">
  <div className="header-row">
    <span style={{ fontSize: "1.6rem" }}>🧠</span>
    <h1>Project Intelligence Graph</h1>
  </div>
  <p>
    Upload any codebase → auto-build knowledge graph →
    ask questions → explore visually
  </p>
</div>

      {/* System Status */}
      <div className="section">
        <h2>System Status</h2>
        {healthLoading && <p className="loading">Checking services...</p>}
        {!healthLoading && health && (
          <div className="status-grid">
            <StatusCard label="API"        status={health.app} />
            <StatusCard label="PostgreSQL" status={health.postgres} />
            <StatusCard label="Neo4j"      status={health.neo4j} />
            <StatusCard label="Ollama"     status={health.ollama} />
          </div>
        )}
      </div>

      {/* Graph Stats */}
      <GraphStats key={graphKey} />

      {/* Project Selector */}
      <ProjectSelector
        projects={projects}
        selectedId={selectedProjectId}
        onSelect={(id) => {
          setSelectedProjectId(id);
          setActiveTab("chat");
        }}
      />

      {/* Tab Navigation */}
      {selectedProjectId && (
        <div className="tab-row" style={{ marginBottom: "0.5rem" }}>
          {[
            { key: "chat",    label: "💬 Ask" },
            { key: "graph",   label: "🕸 Graph" },
            { key: "metrics", label: "📊 Observability" },
          ].map((tab) => (
            <button
              key={tab.key}
              className={`tab ${activeTab === tab.key ? "active" : ""}`}
              onClick={() => setActiveTab(tab.key)}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Tab Content */}
      {activeTab === "chat" && (
        <ChatPanel
          projectId={selectedProjectId}
          projectName={selectedProject?.name}
        />
      )}

      {activeTab === "graph" && (
        <GraphVisualizer projectId={selectedProjectId} />
      )}

      {activeTab === "metrics" && (
        <ObservabilityDashboard projectId={selectedProjectId} />
      )}

      {/* Import + Projects always visible */}
      <ProjectImport onImportSuccess={fetchProjects} />

      <ProjectList
        projects={projects}
        onGraphBuilt={() => {
          setGraphKey((k) => k + 1);
          fetchProjects();
        }}
      />
    </div>
  );
}

export default App;