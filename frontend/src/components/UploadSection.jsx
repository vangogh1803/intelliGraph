import { useState, useRef } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const UploadSection = ({ onUploadSuccess }) => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const fileRef = useRef();

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    console.log("File selected:", selected); // debug
    if (selected) {
      setFile(selected);
      setResult(null);
      setError(null);
    }
  };

  const handleUpload = async () => {
    console.log("Upload clicked, file:", file); // debug
    if (!file) return;

    setUploading(true);
    setResult(null);
    setError(null);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post(`${API}/upload`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      setResult(res.data);
      onUploadSuccess();
    } catch (err) {
      setError(
        err.response?.data?.detail || "Upload failed. Check backend."
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="upload-section">
      <h2>Upload Document</h2>

      {/* File Input - separate from the box click */}
      <input
        ref={fileRef}
        type="file"
        accept=".pdf,.txt"
        onChange={handleFileChange}
        style={{ display: "block", marginBottom: "1rem", color: "#cbd5e1" }}
      />

      {/* Show selected file name */}
      {file && (
        <p style={{ color: "#94a3b8", marginBottom: "1rem", fontSize: "0.875rem" }}>
          Selected: {file.name} ({(file.size / 1024).toFixed(1)} KB)
        </p>
      )}

      {/* Upload Button */}
      <button
        className="btn"
        onClick={handleUpload}
        disabled={!file || uploading}
        style={{
          opacity: !file || uploading ? 0.5 : 1,
          cursor: !file || uploading ? "not-allowed" : "pointer"
        }}
      >
        {uploading ? "Processing..." : "Upload & Process"}
      </button>

      {/* Debug info */}
      <p style={{ color: "#64748b", fontSize: "0.75rem", marginTop: "0.5rem" }}>
        {file ? `Ready to upload: ${file.name}` : "No file selected"}
      </p>

      {result && (
        <div className="alert alert-success">
          ✅ {result.filename} → {result.chunks_created} chunks in {result.processing_time_ms}ms
        </div>
      )}

      {error && (
        <div className="alert alert-error">
          ❌ {error}
        </div>
      )}
    </div>
  );
};

export default UploadSection;