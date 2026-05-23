import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from "recharts";

const LatencyChart = ({ data }) => {
  if (!data || data.length === 0) {
    return (
      <div className="chart-card">
        <div className="chart-title">Latency Over Time</div>
        <p style={{ color: "#64748b", fontSize: "0.85rem" }}>
          No queries yet
        </p>
      </div>
    );
  }

  const avg = data.reduce((s, d) => s + d.latency_ms, 0) / data.length;

  const formatted = data.map((d, i) => ({
    name: `Q${i + 1}`,
    latency: d.latency_ms,
    type: d.retrieval_type
  }));

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          background: "#1e2130",
          border: "1px solid #2d3148",
          borderRadius: "8px",
          padding: "0.75rem"
        }}>
          <p style={{ color: "#94a3b8", fontSize: "0.8rem" }}>
            {label}
          </p>
          <p style={{ color: "#6366f1", fontWeight: 700 }}>
            {payload[0].value}ms
          </p>
          <p style={{ color: "#64748b", fontSize: "0.75rem" }}>
            {payload[0].payload.type}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="chart-card">
      <div className="chart-title">Latency Over Time (ms)</div>
      <ResponsiveContainer width="100%" height={200}>
        <LineChart data={formatted}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2d3148" />
          <XAxis
            dataKey="name"
            tick={{ fill: "#64748b", fontSize: 11 }}
            axisLine={{ stroke: "#2d3148" }}
          />
          <YAxis
            tick={{ fill: "#64748b", fontSize: 11 }}
            axisLine={{ stroke: "#2d3148" }}
            unit="ms"
          />
          <Tooltip content={<CustomTooltip />} />
          <ReferenceLine
            y={avg}
            stroke="#4f46e5"
            strokeDasharray="4 4"
            label={{
              value: `avg ${Math.round(avg)}ms`,
              fill: "#6366f1",
              fontSize: 11
            }}
          />
          <Line
            type="monotone"
            dataKey="latency"
            stroke="#6366f1"
            strokeWidth={2}
            dot={{ fill: "#6366f1", r: 4 }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default LatencyChart;