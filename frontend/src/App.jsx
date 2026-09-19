import { useEffect, useState } from "react";

import { createConversation, getConversation, sendMessage } from "./api/client.js";
import MessageInput from "./components/MessageInput.jsx";
import MessageList from "./components/MessageList.jsx";

// Barebones single-conversation UI. There's no sidebar, no conversation
// switching, no streaming yet -- those are fellow issues (see ISSUES.md).
export default function App() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

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
    <div style={{ maxWidth: 700, margin: "0 auto", padding: 24, fontFamily: "sans-serif" }}>
      <h1>MLH LLM Fellowship Project</h1>
      <MessageList messages={messages} loading={loading} />
      <MessageInput onSend={handleSend} disabled={loading} />
    </div>
  );
}
