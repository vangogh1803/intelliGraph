import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer
} from "recharts";

const COLORS = {
  hybrid:      "#a78bfa",
  vector_only: "#60a5fa",
  graph_only:  "#4ade80",
  file_exact:  "#67e8f9",
  none:        "#78716c"
};

const RetrievalChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Retrieval Type Breakdown</div>
        <p style={{ color: "#64748b", fontSize: "0.85rem" }}>
          No queries yet
        </p>
      </div>
    );
  }

  const formatted = data.map((d) => ({
    name: d.retrieval_type || "unknown",
    value: d.count
  }));

  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: "#1e2130",
          border: "1px solid #2d3148",
          borderRadius: "8px",
          padding: "0.75rem"
        }}>
          <p style={{ color: "#94a3b8", fontSize: "0.85rem" }}>
            {payload[0].name}
          </p>
          <p style={{ color: "#6366f1", fontWeight: 700 }}>
            {payload[0].value} queries
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-card">
      <div className="chart-title">Retrieval Type Breakdown</div>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={formatted}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={85}
            paddingAngle={3}
            dataKey="value"
          >
            {formatted.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={COLORS[entry.name] || "#6366f1"}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            formatter={(value) => (
              <span style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
                {value}
              </span>
            )}
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
};

export default RetrievalChart;