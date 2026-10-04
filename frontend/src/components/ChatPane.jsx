import { PanelLeft } from "lucide-react";

import MessageInput from "./MessageInput.jsx";
import MessageList from "./MessageList.jsx";

export default function ChatPane({ chat, greetingKey, inputRef, sidebarOpen, onOpenSidebar }) {
  const empty = chat.messages.length === 0 && !chat.sending;

  return (
    <main className={"chat" + (empty ? " is-empty" : "")}>
      {!sidebarOpen && (
        <button className="icon-button chat-toggle" onClick={onOpenSidebar} aria-label="Open sidebar">
          <PanelLeft size={16} />
        </button>
      )}

      {empty ? (
        <h1 key={greetingKey} className="greeting">
          What’s on your mind?
        </h1>
      ) : (
        <MessageList messages={chat.messages} loading={chat.sending} />
      )}

      <MessageInput onSend={chat.send} disabled={chat.sending} inputRef={inputRef} />
    </main>
  );
}
