import ChatGroup from "./ChatGroup.jsx";

function SearchResults({ search, renderRow }) {
  if (search.matches.length === 0) return <p className="empty">No chats match “{search.text.trim()}”.</p>;
  return <div className="loose">{search.matches.map(renderRow)}</div>;
}

export default function ChatList({ conversations, search, groups, unread, renderRow }) {
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
