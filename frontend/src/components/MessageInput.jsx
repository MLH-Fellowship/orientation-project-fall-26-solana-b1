import { ArrowUp } from "lucide-react";
import { useLayoutEffect, useState } from "react";

export default function MessageInput({ onSend, disabled, inputRef }) {
  const [text, setText] = useState("");

  // Grow with the content; CSS max-height caps it, after which the textarea scrolls.
  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text, inputRef]);

  function handleSubmit() {
    if (!text.trim() || disabled) return;
    onSend(text);
    setText("");
  }

  function handleKeyDown(e) {
    // Shift+Enter inserts a newline; skip Enter while an IME is composing (e.g. Japanese input).
    if (e.key === "Enter" && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault();
      handleSubmit();
    }
  }

  return (
    <div className="composer">
      <textarea
        ref={inputRef}
        rows={1}
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
