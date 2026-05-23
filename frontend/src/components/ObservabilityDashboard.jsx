import { useEffect, useState } from "react";
import axios from "axios";
import MetricCard from "./MetricCard";
import LatencyChart from "./LatencyChart";
import RetrievalChart from "./RetrievalChart";
import TracesTable from "./TracesTable";

const API = "http://localhost:8000";

const ObservabilityDashboard = ({ projectId }) => {
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);

  const fetchMetrics = async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const url = `${API}/metrics/${projectId}`;
      const res = await axios.get(url);
      setMetrics(res.data);
    } catch (err) {
      console.error("Metrics fetch failed:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    // Auto refresh every 30 seconds
    const interval = setInterval(fetchMetrics, 30000);
    return () => clearInterval(interval);
  }, [projectId]);

  if (!projectId) return null;

  if (loading && !metrics) {
    return (
      <div className="section">
        <h2>Observability</h2>
        <p className="loading">Loading metrics...</p>
      </div>
    );
  }

  if (!metrics) return null;

  const avgLatencySec = (metrics.avg_latency_ms / 1000).toFixed(1);
  const latencyColor =
    metrics.avg_latency_ms < 5000  ? "green"  :
    metrics.avg_latency_ms < 15000 ? "yellow" : "red";

  return (
    <div className="section">
      <div style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        marginBottom: "1.25rem",
        maxWidth: "700px"
      }}>
        <h2 style={{ margin: 0 }}>Observability</h2>
        <button
          className="btn"
          onClick={fetchMetrics}
          style={{ margin: 0, fontSize: "0.8rem", padding: "0.4rem 0.9rem" }}
        >
          ↺ Refresh
        </button>
      </div>

      {/* Metric Cards */}
      <div className="dashboard-grid">
        <MetricCard
          label="Total Queries"
          value={metrics.total_queries}
          colorClass="blue"
        />
        <MetricCard
          label="Avg Latency"
          value={avgLatencySec}
          unit="s"
          colorClass={latencyColor}
        />
        <MetricCard
          label="Avg Chunks"
          value={metrics.avg_chunks_retrieved}
          colorClass="blue"
        />
        <MetricCard
          label="Success Rate"
          value={`${metrics.success_rate}%`}
          colorClass={metrics.success_rate > 80 ? "green" : "yellow"}
        />
      </div>

      {/* Secondary Metrics */}
      <div className="dashboard-grid" style={{ marginBottom: "1.5rem" }}>
        <MetricCard
          label="Min Latency"
          value={(metrics.min_latency_ms / 1000).toFixed(1)}
          unit="s"
          colorClass="green"
        />
        <MetricCard
          label="Max Latency"
          value={(metrics.max_latency_ms / 1000).toFixed(1)}
          unit="s"
          colorClass="red"
        />
        <MetricCard
          label="Avg Entities"
          value={metrics.avg_entities_matched}
          colorClass="blue"
        />
        <MetricCard
          label="Query Types"
          value={metrics.retrieval_breakdown.length}
          colorClass="blue"
        />
      </div>

      {/* Charts Row */}
      <div style={{ display: "flex", gap: "1rem", maxWidth: "700px" }}>
        <div style={{ flex: 2 }}>
          <LatencyChart data={metrics.latency_over_time} />
        </div>
        <div style={{ flex: 1 }}>
          <RetrievalChart data={metrics.retrieval_breakdown} />
        </div>
      </div>

      {/* Slowest Queries */}
      {metrics.slowest_queries.length > 0 && (
        <div className="chart-card" style={{ maxWidth: "700px" }}>
          <div className="chart-title">Slowest Queries</div>
          {metrics.slowest_queries.map((q, i) => (
            <div key={i} style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "0.5rem 0",
              borderTop: i > 0 ? "1px solid #2d3148" : "none"
            }}>
              <span style={{
                color: "#94a3b8",
                fontSize: "0.82rem",
                flex: 1,
                marginRight: "1rem",
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap"
              }}>
                {q.question}
              </span>
              <span style={{
                color: "#f87171",
                fontSize: "0.8rem",
                fontWeight: 600,
                whiteSpace: "nowrap"
              }}>
                {(q.latency_ms / 1000).toFixed(1)}s
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Traces Table */}
      <TracesTable traces={metrics.recent_traces} />
    </div>
  );
};

export default ObservabilityDashboard;