import { useEffect, useRef, useState } from "react";

import ChatPane from "./components/ChatPane.jsx";
import Sidebar from "./components/sidebar/Sidebar.jsx";
import useChat from "./hooks/useChat.js";
import useShortcut from "./hooks/useShortcut.js";
import useSidebar, { isNarrow } from "./hooks/useSidebar.js";


export default function App() {
  const chat = useChat();
  const [sidebarOpen, setSidebarOpen] = useSidebar();
  const [newChats, setNewChats] = useState(0);
  const inputRef = useRef(null);

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

  useEffect(() => inputRef.current?.focus(), [newChats]);
  useShortcut("mod+shift+o", startNewChat);

  function closeSidebarOnPhone() {
    if (isNarrow()) setSidebarOpen(false);
  }

  function openConversation(id) {
    closeSidebarOnPhone();
    chat.openConversation(id);
  }

  function startNewChat() {
    closeSidebarOnPhone();
    chat.startNewChat();
    setNewChats((n) => n + 1);
  }

  return (
    <div className="h-full bg-[var(--chrome)] text-[var(--ink)] transition-colors duration-200">
      <div className="app">
        <Sidebar
          open={sidebarOpen}
          onOpenChange={setSidebarOpen}
          conversations={chat.conversations}
          listState={chat.listState}
          onRetryList={chat.reloadConversations}
          activeId={chat.activeId}
          pending={chat.pending}
          unread={chat.unread}
          failed={chat.failed}
          onOpen={openConversation}
          onNew={startNewChat}
          onRename={chat.renameConversation}
          onDelete={chat.deleteConversation}
          theme={theme}
          onToggleTheme={toggleTheme}
        />
        {sidebarOpen && (
          <div className="scrim" onClick={() => setSidebarOpen(false)} />
        )}
        <ChatPane
          chat={chat}
          greetingKey={newChats}
          inputRef={inputRef}
          sidebarOpen={sidebarOpen}
          onOpenSidebar={() => setSidebarOpen(true)}
          onRetryLoad={() => chat.openConversation(chat.activeId)}
        />
      </div>
    </div>
  );
}
