import { CircleAlert, RotateCw } from "lucide-react";

export default function MessageList({ messages, loading, opening, failedTexts, onRetry }) {
  if (opening) {
    return (
      <div className="messages" aria-busy="true" aria-label="Loading chat">
        <span className="skeleton bubble user" />
        <span className="skeleton line" style={{ width: "92%" }} />
        <span className="skeleton line" style={{ width: "78%" }} />
        <span className="skeleton line" style={{ width: "54%" }} />
      </div>
    );
  }

  return (
    <div className="messages">
      {messages.map((m, i) => (
        <div key={m.id ?? i} className={`message ${m.role}`}>
          {m.content}
        </div>
      ))}

      {failedTexts.map((text, i) => (
        <div key={i} className="failed" role="alert">
          <div className="message user">{text}</div>
          <p className="failed-note">
            <CircleAlert size={14} />
            Not sent
            <button className="text-button" onClick={() => onRetry(i)}>
              <RotateCw size={13} />
              Retry
            </button>
          </p>
        </div>
      ))}

      {loading && (
        <div className="typing" role="status" aria-label="Thinking">
          <span />
          <span />
          <span />
        </div>
      )}
    </div>
  );
}
