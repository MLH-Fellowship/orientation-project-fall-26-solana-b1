export default function MessageList({ messages, loading }) {
  return (
    <div className="messages">
      {messages.map((m, i) => (
        <div key={m.id ?? i} className={`message ${m.role}`}>
          {m.content}
        </div>
      ))}
      {loading && <p className="hint">Thinking...</p>}
    </div>
  );
}
