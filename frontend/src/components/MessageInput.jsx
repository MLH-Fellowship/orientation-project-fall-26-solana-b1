import { ArrowUp } from "lucide-react";
import { useState } from "react";

export default function MessageInput({ onSend, disabled, inputRef }) {
  const [text, setText] = useState("");

  function handleSubmit() {
    if (!text.trim() || disabled) return;
    onSend(text);
    setText("");
  }

  return (
    <div className="composer">
      <input
        ref={inputRef}
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
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
