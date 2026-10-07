import { ArrowUp } from "lucide-react";
import { useState } from "react";

export default function MessageInput({ onSend, disabled, inputRef }) {
  const [text, setText] = useState("");

  function handleSubmit() {
    if (!text.trim() || disabled) return;
    onSend(text);
    setText("");
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="composer">
      <textarea
        ref={inputRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder="Ask anything"
        disabled={disabled}
        autoFocus
      />
      <button onClick={handleSubmit} disabled={disabled || !text.trim()} aria-label="Send">
        <ArrowUp size={16} strokeWidth={2.25} />
      </button>
    </div>
  );
}
