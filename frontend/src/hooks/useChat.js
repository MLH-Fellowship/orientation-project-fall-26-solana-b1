import { useEffect, useRef, useState } from "react";

import { createConversation, getConversation, listConversations, sendMessage } from "../api/client.js";

function without(set, item) {
  const next = new Set(set);
  next.delete(item);
  return next;
}

function omit(obj, key) {
  const rest = { ...obj };
  delete rest[key];
  return rest;
}

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
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setPending((s) => new Set(s).add(key));
    try {
      if (key === "new") {
        const convo = await createConversation(text.slice(0, 60));
        setConversations((cs) => [{ ...convo, fresh: true }, ...cs]);
        setPending((s) => without(s, "new").add(convo.id));
        setFailed((f) => (f.new ? { ...omit(f, "new"), [convo.id]: f.new } : f));
        key = convo.id;
        if (activeRef.current === null) {
          activeRef.current = key;
          setActiveId(key);
        }
      }
      const reply = await sendMessage(key, text);
      if (activeRef.current === key) setMessages((prev) => [...prev, reply]);
      else setUnread((s) => new Set(s).add(key));
    } catch {
      if ((activeRef.current ?? "new") === key) setMessages((prev) => prev.slice(0, -1));
      setFailed((f) => ({ ...f, [key]: [...(f[key] ?? []), text] }));
    } finally {
      setPending((s) => without(s, key));
    }
  }

  const key = activeId ?? "new";

  function retry(index) {
    const text = failed[key][index];
    setFailed((f) => {
      const rest = f[key].filter((_, i) => i !== index);
      return rest.length ? { ...f, [key]: rest } : omit(f, key);
    });
    send(text);
  }

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
    failedTexts: failed[key] ?? [],
    openConversation,
    startNewChat,
    send,
    retry,
  };
}
