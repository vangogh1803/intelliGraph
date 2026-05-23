const ProjectSelector = ({ projects, selectedId, onSelect }) => {
  if (!projects || projects.length === 0) return null;

  return (
    <div className="section">
      <h2>Active Project</h2>
      <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
        {projects.map((p) => (
          <button
            key={p.id}
            onClick={() => onSelect(p.id)}
            style={{
              background: selectedId === p.id ? "#4f46e5" : "#1e2130",
              border: `1px solid ${selectedId === p.id ? "#6366f1" : "#2d3148"}`,
              color: selectedId === p.id ? "#fff" : "#94a3b8",
              padding: "0.5rem 1.25rem",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "0.875rem",
              fontWeight: selectedId === p.id ? 700 : 400,
              transition: "all 0.2s"
            }}
          >
            {p.source === "github" ? "🐙" : "📦"} {p.name}
            {p.status === "ready" && (
              <span style={{ color: "#4ade80", marginLeft: "0.5rem", fontSize: "0.75rem" }}>
                ✓
              </span>
            )}
          </button>
        ))}
      </div>
    </div>
  );
};

export default ProjectSelector;