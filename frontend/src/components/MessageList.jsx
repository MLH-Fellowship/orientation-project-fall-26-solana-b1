export default function MessageList({ messages, loading }) {
  return (
    <div style={{ minHeight: 300, border: "1px solid #ddd", borderRadius: 8, padding: 16, marginBottom: 16 }}>
      {messages.length === 0 && <p style={{ color: "#888" }}>Say hello to start the conversation.</p>}
      {messages.map((m, i) => (
        <div key={i} style={{ marginBottom: 12 }}>
          <strong>{m.role === "user" ? "You" : "Assistant"}:</strong> {m.content}
        </div>
      ))}
      {loading && <p style={{ color: "#888" }}>Thinking...</p>}
    </div>
  );
}
