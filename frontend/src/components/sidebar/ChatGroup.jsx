import StatusDot from "./StatusDot.jsx";

function GroupName({ name, renaming, onRename, onStartRename }) {
  if (!renaming) {
    return (
      <span className="group-name" onDoubleClick={onStartRename}>
        {name}
      </span>
    );
  }

  return (
    <input
      autoFocus
      defaultValue={name}
      onFocus={(e) => e.target.select()}
      onClick={(e) => e.stopPropagation()}
      onBlur={(e) => onRename(e.target.value)}
      onKeyDown={(e) => {
        if (e.key === "Escape") e.target.value = name;
        if (e.key === "Enter" || e.key === "Escape") e.target.blur();
      }}
    />
  );
}

export default function ChatGroup({ name, members, groups, unread, renderRow }) {
  const open = !groups.isCollapsed(name);
  const hasUnread = members.some((c) => unread.has(c.id));

  return (
    <section className="group">
      <div
        className={"group-head" + (groups.isOver(`g:${name}`) ? " over" : "")}
        onClick={() => groups.toggle(name)}
        {...groups.dropTarget(`g:${name}`, { group: name })}
      >
        <span className={"chevron" + (open ? " open" : "")}>›</span>
        <GroupName
          name={name}
          renaming={groups.renaming === name}
          onRename={(to) => groups.rename(name, to)}
          onStartRename={() => groups.startRename(name)}
        />
        {!open && hasUnread ? <StatusDot status="unread" /> : <span className="count">{members.length}</span>}
      </div>
      {open && <div className="thread">{members.map(renderRow)}</div>}
    </section>
  );
}
