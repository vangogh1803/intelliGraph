const MetricCard = ({ label, value, unit, colorClass }) => {
  return (
    <div className="metric-card">
      <div className={`metric-value ${colorClass || ""}`}>
        {value}
        {unit && (
          <span style={{ fontSize: "0.85rem", marginLeft: "2px" }}>
            {unit}
          </span>
        )}
      </div>
      <div className="metric-label">{label}</div>
    </div>
  );
};

export default MetricCard;