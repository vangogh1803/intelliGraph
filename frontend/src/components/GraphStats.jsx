import { useEffect, useState } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const GraphStats = () => {
  const [stats, setStats] = useState(null);

  const fetchStats = () => {
    axios
      .get(`${API}/graph/stats`)
      .then((res) => setStats(res.data))
      .catch(() => setStats(null));
  };

  useEffect(() => {
    fetchStats();
    // Refresh every 10 seconds
    const interval = setInterval(fetchStats, 10000);
    return () => clearInterval(interval);
  }, []);

  if (!stats) return null;

  return (
    <div className="section">
      <h2>Knowledge Graph</h2>
      <div className="graph-stats-grid">
        <div className="stat-card">
          <div className="stat-number">{stats.docs ?? 0}</div>
          <div className="stat-label">Documents</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.chunks ?? 0}</div>
          <div className="stat-label">Chunks</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.entities ?? 0}</div>
          <div className="stat-label">Entities</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{stats.rels ?? 0}</div>
          <div className="stat-label">Relations</div>
        </div>
      </div>
    </div>
  );
};

export default GraphStats;