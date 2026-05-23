const getLatencyClass = (ms) => {
  if (ms < 5000)  return "latency-fast";
  if (ms < 15000) return "latency-medium";
  return "latency-slow";
};

const getRetrievalClass = (type) => {
  if (!type) return "rt-none";
  if (type.includes("hybrid"))     return "rt-hybrid";
  if (type.includes("vector"))     return "rt-vector";
  if (type.includes("graph"))      return "rt-graph";
  if (type.includes("file"))       return "rt-file";
  return "rt-none";
};

const TracesTable = ({ traces }) => {
  if (!traces || traces.length === 0) {
    return (
      <div className="section">
        <h2>Recent Queries</h2>
        <p style={{ color: "#64748b", fontSize: "0.85rem" }}>
          No queries yet
        </p>
      </div>
    );
  }

  return (
    <div className="section">
      <h2>Recent Queries</h2>
      <table className="traces-table">
        <thead>
          <tr>
            <th>Question</th>
            <th>Latency</th>
            <th>Retrieval</th>
            <th>Chunks</th>
            <th>Entities</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {traces.map((t) => (
            <tr key={t.id}>
              <td>
                <div className="question-cell" title={t.question}>
                  {t.question}
                </div>
              </td>
              <td>
                <span className={`latency-pill ${getLatencyClass(t.latency_ms)}`}>
                  {t.latency_ms >= 1000
                    ? `${(t.latency_ms / 1000).toFixed(1)}s`
                    : `${t.latency_ms}ms`
                  }
                </span>
              </td>
              <td>
                <span className={`retrieval-pill ${getRetrievalClass(t.retrieval_type)}`}>
                  {t.retrieval_type || "none"}
                </span>
              </td>
              <td style={{ color: "#60a5fa" }}>
                {t.chunks_retrieved}
              </td>
              <td style={{ color: "#4ade80" }}>
                {t.entities_matched}
              </td>
              <td style={{ color: "#64748b", fontSize: "0.72rem" }}>
                {new Date(t.created_at).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default TracesTable;