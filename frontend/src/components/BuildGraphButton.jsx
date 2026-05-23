import { useState } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const BuildGraphButton = ({ documentId, filename, onDone }) => {
  const [building, setBuilding] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleBuild = async () => {
    setBuilding(true);
    setResult(null);
    setError(null);

    try {
      const res = await axios.post(`${API}/graph/build/${documentId}`);
      setResult(res.data);
      if (onDone) onDone();
    } catch (err) {
      setError(err.response?.data?.detail || "Graph build failed");
    } finally {
      setBuilding(false);
    }
  };

  return (
    <div>
      <button
        className="build-btn"
        onClick={handleBuild}
        disabled={building}
      >
        {building ? "Building..." : "Build Graph"}
      </button>

      {result && (
        <div className="alert alert-success" style={{ marginTop: "0.5rem" }}>
          ✅ {result.entities_extracted} entities,{" "}
          {result.relationships_extracted} relations extracted
        </div>
      )}

      {error && (
        <div className="alert alert-error" style={{ marginTop: "0.5rem" }}>
          ❌ {error}
        </div>
      )}
    </div>
  );
};

export default BuildGraphButton;