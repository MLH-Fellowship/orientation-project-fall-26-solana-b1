import { CloudOff, PanelLeft, RotateCw } from "lucide-react";

import MessageInput from "./MessageInput.jsx";
import MessageList from "./MessageList.jsx";

function LoadError({ onRetry }) {
  return (
    <div className="pane-state" role="alert">
      <CloudOff size={20} strokeWidth={1.5} />
      <p>Couldn’t load this chat</p>
      <span>Check that the server is running, then try again.</span>
      <button className="pill-button" onClick={onRetry}>
        <RotateCw size={14} />
        Try again
      </button>
    </div>
  );
}

export default function ChatPane({ chat, greetingKey, inputRef, sidebarOpen, onOpenSidebar, onRetryLoad }) {
  const empty = chat.messages.length === 0 && !chat.sending && !chat.failedText && !chat.opening;

  return (
    <main className={"chat" + (empty ? " is-empty" : "")}>
      {!sidebarOpen && (
        <button className="icon-button chat-toggle" onClick={onOpenSidebar} aria-label="Open sidebar">
          <PanelLeft size={16} />
        </button>
      )}

      {chat.loadFailed ? (
        <LoadError onRetry={onRetryLoad} />
      ) : empty ? (
        <h1 key={greetingKey} className="greeting">
          What’s on your mind?
        </h1>
      ) : (
        <MessageList
          messages={chat.messages}
          loading={chat.sending}
          opening={chat.opening}
          failedText={chat.failedText}
          onRetry={chat.retry}
        />
      )}

      <MessageInput onSend={chat.send} disabled={chat.sending} inputRef={inputRef} />
    </main>
  );
}
