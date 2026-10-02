import { CloudOff, PanelLeft, RotateCw } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import { createConversation, getConversation, listConversations, sendMessage } from "./api/client.js";
import MessageInput from "./components/MessageInput.jsx";
import MessageList from "./components/MessageList.jsx";
import Sidebar from "./components/Sidebar.jsx";

function without(set, item) {
  const next = new Set(set);
  next.delete(item);
  return next;
}

function omit(obj, key) {
  const { [key]: _, ...rest } = obj;
  return rest;
}

const isNarrow = () => window.matchMedia("(max-width: 640px)").matches;

function loadSidebarOpen() {
  if (isNarrow()) return false;
  try {
    return localStorage.getItem("sidebar") !== "closed";
  } catch {
    return true;
  }
}

export default function App() {
  const [conversations, setConversations] = useState([]);
  const [listState, setListState] = useState("loading");
  const [activeId, setActiveId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [pending, setPending] = useState(new Set());
  const [unread, setUnread] = useState(new Set());
  const [failed, setFailed] = useState({});
  const [opening, setOpening] = useState(null);
  const [loadFailed, setLoadFailed] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(loadSidebarOpen);
  const [newChats, setNewChats] = useState(0);
  const inputRef = useRef(null);

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

  useEffect(() => {
    if (isNarrow()) return;
    try {
      localStorage.setItem("sidebar", sidebarOpen ? "open" : "closed");
    } catch {}
  }, [sidebarOpen]);

  useEffect(() => {
    inputRef.current?.focus();
  }, [newChats]);

  useEffect(() => {
    function onKey(e) {
      if (!(e.metaKey || e.ctrlKey)) return;
      const key = e.key.toLowerCase();
      if (key === "b") {
        e.preventDefault();
        setSidebarOpen((o) => !o);
      } else if (key === "o" && e.shiftKey) {
        e.preventDefault();
        startNewChat();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, []);

  async function openConversation(id) {
    if (isNarrow()) setSidebarOpen(false);
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
    setNewChats((n) => n + 1);
    if (isNarrow()) setSidebarOpen(false);
  }

  async function handleSend(text) {
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

  function retrySend() {
    handleSend(failed[activeId ?? "new"]);
  }

  const key = activeId ?? "new";
  const loading = pending.has(key);
  const isOpening = activeId !== null && opening === activeId;
  const empty = messages.length === 0 && !loading && !failed[key] && !isOpening;

  return (
    <div className="app">
      <Sidebar
        open={sidebarOpen}
        onOpenChange={setSidebarOpen}
        conversations={conversations}
        listState={listState}
        onRetryList={loadConversations}
        activeId={activeId}
        pending={pending}
        unread={unread}
        failed={failed}
        onOpen={openConversation}
        onNew={startNewChat}
      />
      {sidebarOpen && <div className="scrim" onClick={() => setSidebarOpen(false)} />}
      <main className={"chat" + (empty ? " is-empty" : "")}>
        {!sidebarOpen && (
          <button className="icon-button chat-toggle" onClick={() => setSidebarOpen(true)} aria-label="Open sidebar">
            <PanelLeft size={16} />
          </button>
        )}
        {activeId !== null && loadFailed === activeId ? (
          <div className="pane-state" role="alert">
            <CloudOff size={20} strokeWidth={1.5} />
            <p>Couldn’t load this chat</p>
            <span>Check that the server is running, then try again.</span>
            <button className="pill-button" onClick={() => openConversation(activeId)}>
              <RotateCw size={14} />
              Try again
            </button>
          </div>
        ) : empty ? (
          <h1 key={newChats} className="greeting">
            What’s on your mind?
          </h1>
        ) : (
          <MessageList
            messages={messages}
            loading={loading}
            opening={isOpening}
            failedText={failed[key]}
            onRetry={retrySend}
          />
        )}
        <MessageInput onSend={handleSend} disabled={loading} inputRef={inputRef} />
      </main>
    </div>
  );
}
