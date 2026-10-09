import { useEffect, useRef, useState } from "react";

import {
  createConversation,
  deleteConversation as deleteConversationRequest,
  getConversation,
  listConversations,
  renameConversation as renameConversationRequest,
  streamMessage,
} from "../api/client.js";

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

async function loadAllConversations() {
  const pageSize = 100;
  const items = [];
  let offset = 0;
  let total = Infinity;
  while (offset < total) {
    const page = await listConversations({ limit: pageSize, offset });
    items.push(...page.items);
    total = page.total;
    if (page.items.length === 0) break;
    offset += page.items.length;
  }
  return items;
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
    loadAllConversations()
      .then((items) => {
        setConversations(items);
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

  async function renameConversation(id, title) {
    const updated = await renameConversationRequest(id, title);
    setConversations((cs) => cs.map((conversation) => (
      conversation.id === id ? { ...conversation, ...updated } : conversation
    )));
  }

  async function deleteConversation(id) {
    await deleteConversationRequest(id);
    setConversations((cs) => cs.filter((conversation) => conversation.id !== id));
    setPending((s) => without(s, id));
    setUnread((s) => without(s, id));

    if (activeRef.current === id) {
      activeRef.current = null;
      setActiveId(null);
      setMessages([]);
    }
  }

  async function send(text) {
    let key = activeId ?? "new";
    const isNew = key === "new";
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setPending((s) => new Set(s).add(key));
    try {
      if (isNew) {
        const convo = await createConversation();
        setConversations((cs) => [{ ...convo, fresh: true }, ...cs]);
        setPending((s) => without(s, "new").add(convo.id));
        setFailed((f) => (f.new ? { ...omit(f, "new"), [convo.id]: f.new } : f));
        key = convo.id;
        if (activeRef.current === null) {
          activeRef.current = key;
          setActiveId(key);
        }
      }
      if (activeRef.current === key) {
        setMessages((prev) => [...prev, { role: "assistant", content: "", streaming: true }]);
      }
      let reply;
      for await (const event of streamMessage(key, text)) {
        if (event.type === "error") throw new Error(event.message);
        if (event.type === "chunk") {
          setMessages((prev) => {
            const next = [...prev];
            const last = next[next.length - 1];
            if (activeRef.current === key && last?.role === "assistant" && last.streaming) {
              next[next.length - 1] = { ...last, content: last.content + event.text };
            }
            return next;
          });
        }
        if (event.type === "done") reply = event.message;
      }
      if (isNew) {
        try {
          const full = await getConversation(key);
          setConversations((cs) => cs.map((c) => (c.id === key ? { ...c, title: full.title } : c)));
        } catch {
          // The reply is saved. The row keeps "New Conversation" until the next reload.
        }
      }
      if (activeRef.current === key) {
        setMessages((prev) => {
          const next = [...prev];
          if (reply) next[next.length - 1] = reply;
          return next;
        });
      }
      else setUnread((s) => new Set(s).add(key));
    } catch {
      if ((activeRef.current ?? "new") === key) setMessages((prev) => prev.slice(0, -2));
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
    renameConversation,
    deleteConversation,
    send,
    retry,
  };
}
