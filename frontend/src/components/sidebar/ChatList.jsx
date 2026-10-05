import { MessageSquare, RotateCw } from "lucide-react";

import ChatGroup from "./ChatGroup.jsx";

const SKELETON_WIDTHS = [72, 88, 60, 80, 52];

function Loading() {
  return (
    <div className="skeleton-list" aria-busy="true" aria-label="Loading chats">
      {SKELETON_WIDTHS.map((w, i) => (
        <span key={i} className="skeleton" style={{ width: `${w}%` }} />
      ))}
    </div>
  );
}

function LoadError({ onRetry }) {
  return (
    <div className="side-state">
      <p>Couldn’t load your chats.</p>
      <button className="text-button" onClick={onRetry}>
        <RotateCw size={13} />
        Try again
      </button>
    </div>
  );
}

function NoChats() {
  return (
    <div className="side-state">
      <MessageSquare size={18} strokeWidth={1.5} />
      <p>No chats yet</p>
      <span>Your conversations will show up here.</span>
    </div>
  );
}

function SearchResults({ search, renderRow }) {
  if (search.matches.length === 0) return <p className="empty">No chats match “{search.text.trim()}”.</p>;
  return <div className="loose">{search.matches.map(renderRow)}</div>;
}

export default function ChatList({ conversations, listState, onRetry, search, groups, unread, renderRow }) {
  if (listState === "loading") return <Loading />;
  if (listState === "error") return <LoadError onRetry={onRetry} />;
  if (conversations.length === 0) return <NoChats />;
  if (search.query) return <SearchResults search={search} renderRow={renderRow} />;

  const { grouped, loose } = groups.split(conversations);

  return (
    <>
      <h2 className="section-label">Chats</h2>

      {grouped.map(({ name, members }) => (
        <ChatGroup key={name} name={name} members={members} groups={groups} unread={unread} renderRow={renderRow} />
      ))}

      {loose.length > 0 && <div className="loose">{loose.map(renderRow)}</div>}

      {groups.draggingGrouped && (
        <div className={"drop-zone" + (groups.isOver("loose") ? " over" : "")} {...groups.dropTarget("loose", {})}>
          Drop here to ungroup
        </div>
      )}
    </>
  );
}
