import { ArrowUp, ChevronDown } from "lucide-react";
import { useLayoutEffect, useState } from "react";

export default function MessageInput({ onSend, disabled, inputRef }) {
  const [text, setText] = useState("");
  const [provider, setProvider] = useState("gemini"); // Default provider is Gemini

  // Grow with the content; CSS max-height caps it, after which the textarea scrolls.
  useLayoutEffect(() => {
    const el = inputRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${el.scrollHeight}px`;
  }, [text, inputRef]);

  function handleSubmit() {
    if (!text.trim() || disabled) return;
    onSend(text, provider);
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
      <div className="flex items-center justify-between gap-3 border-gray-200 dark:border-gray-700 px-1">
        {/* LLM Provider Selector Dropdown */}
        <div className="relative flex items-center">
          <select
            value={provider}
            onChange={(e) => setProvider(e.target.value)}
            disabled={disabled}
            className="text-xs font-medium bg-gray-100 rounded-lg dark:bg-gray-800 text-gray-800 dark:text-gray-200 border border-gray-300 dark:border-gray-600 px-2 py-1.5 pr-6 appearance-none cursor-pointer focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="openai">OpenAI (GPT)</option>
            <option value="gemini">Google (Gemini)</option>
          </select>
          <ChevronDown
            size={12}
            className="absolute right-2 pointer-events-none text-gray-500 dark:text-gray-400"
          />
        </div>

        {/* Send button goes here */}
        <button
          onClick={handleSubmit}
          disabled={disabled || !text.trim()}
          aria-label="Send"
        >
          <ArrowUp size={16} strokeWidth={2.25} />
        </button>
      </div>
    </div>
  );
}
