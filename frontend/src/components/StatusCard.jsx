const StatusCard = ({ label, status }) => {
  const isOk = status === "ok";

  return (
    <div className="status-card">
      <span className="status-label">{label}</span>
      <span className={`status-badge ${isOk ? "badge-ok" : "badge-error"}`}>
        {isOk ? "● Online" : "● Offline"}
      </span>
    </div>
  );
};

export default StatusCard;