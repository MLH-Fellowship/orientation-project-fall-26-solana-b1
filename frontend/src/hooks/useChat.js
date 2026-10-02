import { useEffect, useRef, useState } from "react";

import { createConversation, getConversation, listConversations, sendMessage } from "../api/client.js";
import { omit, without } from "../lib/collections.js";

export default function useChat() {
  const [conversations, setConversations] = useState([]);
  const [listState, setListState] = useState("loading");
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(new Set());
  const [unread, setUnread] = useState(new Set());
  const [failed, setFailed] = useState({});
  const [opening, setOpening] = useState(null);
  const [loadFailed, setLoadFailed] = useState(null);

  const activeRef = useRef(null);
  activeRef.current = activeId;

  function loadConversations() {
    setListState("loading");
    listConversations()
      .then((cs) => {
        setConversations(cs);
        setListState("ready");
      })
      .catch(() => setListState("error"));
  }

  useEffect(loadConversations, []);

  async function openConversation(id) {
    setActiveId(id);
    setUnread((s) => without(s, id));
    setMessages([]);
    setLoadFailed(null);
    setOpening(id);
    try {
      const full = await getConversation(id);
      if (activeRef.current === id) setMessages(full.messages);
    } catch {
      if (activeRef.current === id) setLoadFailed(id);
    } finally {
      setOpening((o) => (o === id ? null : o));
    }
  }

  function startNewChat() {
    setActiveId(null);
    setMessages([]);
    setLoadFailed(null);
    setFailed((f) => omit(f, "new"));
  }

  async function send(text) {
    let key = activeId ?? "new";
    setFailed((f) => omit(f, key));
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
    } catch {
      if ((activeRef.current ?? "new") === key) setMessages((prev) => prev.slice(0, -1));
      setFailed((f) => ({ ...f, [key]: text }));
    } finally {
      setPending((s) => without(s, key));
    }
  }

  const key = activeId ?? "new";

  return {
    conversations,
    listState,
    reloadConversations: loadConversations,
    activeId,
    messages,
    pending,
    unread,
    failed,
    sending: pending.has(key),
    opening: activeId !== null && opening === activeId,
    loadFailed: activeId !== null && loadFailed === activeId,
    failedText: failed[key],
    openConversation,
    startNewChat,
    send,
    retry: () => send(failed[key]),
  };
}
