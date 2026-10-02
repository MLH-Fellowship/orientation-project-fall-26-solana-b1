import { useEffect, useState } from "react";

import {
  createConversation,
  getConversation,
  sendMessage,
} from "./api/client.js";
import MessageInput from "./components/MessageInput.jsx";
import MessageList from "./components/MessageList.jsx";

// Barebones single-conversation UI. There's no sidebar, no conversation
// switching, no streaming yet -- those are fellow issues (see ISSUES.md).
export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  // --- Theme State (Persisted in localStorage) ---
  const [theme, setTheme] = useState(() => {
    return document.documentElement.classList.contains("dark")
      ? "dark"
      : "light";
  });

  // Toggle 'dark' class on <html> root element
  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
    } else {
      root.classList.remove("dark");
    }
    localStorage.setItem("theme", theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  };

  useEffect(() => {
    createConversation("New Conversation").then((c) => setConversationId(c.id));
  }, []);

  async function handleSend(text) {
    if (!conversationId) return;
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setLoading(true);
    await sendMessage(conversationId, text);
    const full = await getConversation(conversationId);
    setMessages(full.messages);
    setLoading(false);
  }

  return (
    <div className="min-h-screen bg-white text-gray-900 dark:bg-gray-900 dark:text-gray-100 transition-colors duration-200">
      <div
        style={{
          maxWidth: 700,
          margin: "0 auto",
          padding: 24,
          fontFamily: "sans-serif",
        }}
      >
        <button
          onClick={toggleTheme}
          className="px-3 py-1.5 text-sm font-medium rounded-md border border-gray-300 dark:border-gray-700 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
        >
          {theme === "light" ? "🌙 Dark Mode" : "☀️ Light Mode"}
        </button>
        <h1>MLH LLM Fellowship Project</h1>
        <MessageList messages={messages} loading={loading} />
        <MessageInput onSend={handleSend} disabled={loading} />
      </div>
    </div>
  );
}
