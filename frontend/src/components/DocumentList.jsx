import BuildGraphButton from "./BuildGraphButton";

const DocumentList = ({ documents, onGraphBuilt }) => {
  if (!documents || documents.length === 0) {
    return (
      <div className="section">
        <h2>Documents</h2>
        <p style={{ color: "#64748b" }}>No documents uploaded yet.</p>
      </div>
    );
  }

  return (
    <div className="section">
      <h2>Documents</h2>
      <table className="doc-table">
        <thead>
          <tr>
            <th>Filename</th>
            <th>Chunks</th>
            <th>Uploaded</th>
            <th>Graph</th>
          </tr>
        </thead>
        <tbody>
          {documents.map((doc) => (
            <tr key={doc.id}>
              <td>{doc.filename}</td>
              <td>
                <span className="chunk-badge">
                  {doc.chunk_count} chunks
                </span>
              </td>
              <td>
                {new Date(doc.created_at).toLocaleDateString()}
              </td>
              <td>
                <BuildGraphButton
                  documentId={doc.id}
                  filename={doc.filename}
                  onDone={onGraphBuilt}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DocumentList;