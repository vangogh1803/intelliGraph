import { useState, useRef } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const ProjectImport = ({ onImportSuccess }) => {
  const [tab, setTab] = useState("zip");
  const [githubUrl, setGithubUrl] = useState("");
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef();

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setResult(null);
    setError(null);
  };

  const handleZipUpload = async () => {
    if (!file) return;
    setLoading(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(
        `${API}/projects/upload-zip`,
        formData,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      setResult(res.data);
      onImportSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setLoading(false);
    }
  };

  const handleGithubImport = async () => {
    if (!githubUrl.trim()) return;
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await axios.post(`${API}/projects/import-github`, {
        url: githubUrl.trim()
      });
      setResult(res.data);
      onImportSuccess();
    } catch (err) {
      setError(err.response?.data?.detail || "Import failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="section">
      <h2>Import Project</h2>
      <div className="import-box">

        {/* Tabs */}
        <div className="tab-row">
          <button
            className={`tab ${tab === "zip" ? "active" : ""}`}
            onClick={() => { setTab("zip"); setResult(null); setError(null); }}
          >
            📦 Upload ZIP
          </button>
          <button
            className={`tab ${tab === "github" ? "active" : ""}`}
            onClick={() => { setTab("github"); setResult(null); setError(null); }}
          >
            🐙 GitHub URL
          </button>
        </div>

        {/* ZIP Tab */}
        {tab === "zip" && (
          <div>
            <input
              ref={fileRef}
              type="file"
              accept=".zip"
              onChange={handleFileChange}
              style={{ display: "block", color: "#cbd5e1", marginBottom: "1rem" }}
            />
            {file && (
              <p style={{ color: "#94a3b8", fontSize: "0.875rem", marginBottom: "1rem" }}>
                Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
              </p>
            )}
            <button
              className="btn"
              onClick={handleZipUpload}
              disabled={!file || loading}
            >
              {loading ? "Processing..." : "Upload & Process"}
            </button>
          </div>
        )}

        {/* GitHub Tab */}
        {tab === "github" && (
          <div>
            <div className="input-row">
              <input
                className="text-input"
                type="text"
                placeholder="https://github.com/username/repo"
                value={githubUrl}
                onChange={(e) => setGithubUrl(e.target.value)}
              />
              <button
                className="btn"
                onClick={handleGithubImport}
                disabled={!githubUrl.trim() || loading}
                style={{ margin: 0 }}
              >
                {loading ? "Cloning..." : "Import"}
              </button>
            </div>
            <p style={{ color: "#64748b", fontSize: "0.8rem" }}>
              Public repositories only
            </p>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="alert alert-success" style={{ marginTop: "1rem" }}>
            ✅ {result.project_name} → {result.files_processed} files,{" "}
            {result.chunks_created} chunks created
          </div>
        )}

        {/* Error */}
        {error && (
          <div className="alert alert-error" style={{ marginTop: "1rem" }}>
            ❌ {error}
          </div>
        )}
      </div>
    </div>
  );
};

export default ProjectImport;