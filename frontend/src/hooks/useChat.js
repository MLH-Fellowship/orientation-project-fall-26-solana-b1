import { useEffect, useRef, useState } from "react";

import { createConversation, getConversation, listConversations, sendMessage } from "../api/client.js";
import { without } from "../lib/collections.js";

export default function useChat() {
  const [conversations, setConversations] = useState([]);
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(new Set());
  const [unread, setUnread] = useState(new Set());

  const activeRef = useRef(null);
  activeRef.current = activeId;

  useEffect(() => {
    listConversations().then(setConversations);
  }, []);

  async function openConversation(id) {
    setActiveId(id);
    setUnread((s) => without(s, id));
    setMessages([]);
    const full = await getConversation(id);
    if (activeRef.current === id) setMessages(full.messages);
  }

  function startNewChat() {
    setActiveId(null);
    setMessages([]);
  }

  async function send(text) {
    let key = activeId ?? "new";
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setPending((s) => new Set(s).add(key));
    try {
      if (key === "new") {
        const convo = await createConversation(text.slice(0, 60));
        setConversations((cs) => [{ ...convo, fresh: true }, ...cs]);
        setPending((s) => without(s, "new").add(convo.id));
        key = activeRef.current = convo.id;
        setActiveId(key);
      }
      const reply = await sendMessage(key, text);
      if (activeRef.current === key) setMessages((prev) => [...prev, reply]);
      else setUnread((s) => new Set(s).add(key));
    } finally {
      setPending((s) => without(s, key));
    }
  }

  return {
    conversations,
    activeId,
    messages,
    pending,
    unread,
    sending: pending.has(activeId ?? "new"),
    openConversation,
    startNewChat,
    send,
  };
}
