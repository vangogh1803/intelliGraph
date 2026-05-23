import { useState, useRef, useEffect } from "react";
import axios from "axios";

const API = "http://localhost:8000";

const ChatPanel = ({ projectId, projectName }) => {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEnd = useRef(null);

  const scrollToBottom = () => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  // Clear chat when project changes
  useEffect(() => {
    setMessages([]);
  }, [projectId]);

  const handleSend = async () => {
    if (!input.trim() || !projectId || loading) return;

    const question = input.trim();
    setInput("");

    // Add user message
    setMessages((prev) => [
      ...prev,
      { role: "user", content: question }
    ]);

    setLoading(true);

    try {
      const res = await axios.post(`${API}/query`, {
        question: question,
        project_id: projectId
      });

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: res.data.answer,
          sources: res.data.sources,
          trace: res.data.trace
        }
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          content: "Sorry, something went wrong. " +
            (err.response?.data?.detail || "Check if backend is running."),
          sources: [],
          trace: null
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!projectId) {
    return (
      <div className="section">
        <h2>Ask Questions</h2>
        <div className="graph-placeholder">
          <p>Select a project first to start asking questions</p>
        </div>
      </div>
    );
  }

  return (
    <div className="section">
      <h2>
        Ask about{" "}
        <span style={{ color: "#6366f1" }}>{projectName || "project"}</span>
      </h2>

      <div className="chat-container">
        {/* Messages */}
        <div className="messages">
        {messages.length === 0 && (
  <div style={{
    color: "#374151",
    padding: "2rem 0",
    fontSize: "0.875rem"
  }}>
    <p style={{ marginBottom: "1rem", color: "#4b5563" }}>
      Try asking:
    </p>
    {[
      "What functions does this project use?",
      "Explain the project structure",
      "How does the chunking work?",
      "What does App.js do?",
      "What technologies are used?"
    ].map((q) => (
      <div
        key={q}
        onClick={() => setInput(q)}
        style={{
          padding: "0.5rem 0.85rem",
          marginBottom: "0.4rem",
          background: "#111827",
          border: "1px solid #1e2130",
          borderRadius: "8px",
          cursor: "pointer",
          color: "#6366f1",
          fontSize: "0.82rem",
          maxWidth: "400px",
          transition: "border-color 0.15s"
        }}
      >
        {q}
      </div>
    ))}
  </div>
)}

          {messages.map((msg, i) => (
            <div key={i}>
              {msg.role === "user" ? (
                <div className="message-user">{msg.content}</div>
              ) : (
                <div>
                  <div className="message-bot">
                    <pre style={{
                      whiteSpace: "pre-wrap",
                      wordBreak: "break-word",
                      background: "none",
                      border: "none",
                      padding: 0,
                      margin: 0,
                      fontFamily: "inherit",
                      fontSize: "inherit"
                    }}>
                      {msg.content}
                    </pre>

                    {/* Sources */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="sources-panel">
                        <div className="sources-title">Sources Used</div>
                        {msg.sources.map((s, j) => (
                          <div key={j} className="source-item">
                            <span className={`source-type-badge ${
                              s.source_type === "vector"
                                ? "source-vector"
                                : "source-graph"
                            }`}>
                              {s.source_type}
                            </span>
                            <span>📄 {s.file_path}</span>
                            {s.via_entity && (
                              <span style={{ color: "#4ade80", fontSize: "0.7rem" }}>
                                via: {s.via_entity}
                              </span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Trace */}
                    {msg.trace && (
                      <div className="trace-bar">
                        <span className="trace-item">
                          ⏱ {msg.trace.latency_ms}ms
                        </span>
                        <span className="trace-item">
                          📦 {msg.trace.chunks_retrieved} chunks
                        </span>
                        <span className="trace-item">
                          🕸 {msg.trace.graph_hops} hops
                        </span>
                        <span className="trace-item">
                          🎯 {msg.trace.entities_matched} entities
                        </span>
                        <span className="trace-item">
                          🔀 {msg.trace.retrieval_type}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}

          {/* Loading */}
          {loading && (
            <div className="message-bot">
              <div className="loading-dots">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}

          <div ref={messagesEnd} />
        </div>

        {/* Input */}
        <div className="chat-input-row" style={{ marginTop: "1rem" }}>
          <input
            className="chat-input"
            type="text"
            placeholder="Ask about your project..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
          />
          <button
            className="send-btn"
            onClick={handleSend}
            disabled={!input.trim() || loading}
          >
            {loading ? "Thinking..." : "Ask →"}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatPanel;