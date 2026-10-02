import { Search, SquarePen, X } from "lucide-react";

function NavItem({ icon: Icon, label, kbd, showTip, active, onClick }) {
  return (
    <button
      className={"nav-item" + (active ? " active" : "")}
      onClick={onClick}
      data-tip={showTip ? label : undefined}
      data-kbd={kbd}
      aria-label={label}
    >
      <Icon size={16} />
      <span className="label">{label}</span>
      <kbd>{kbd}</kbd>
    </button>
  );
}

function SearchField({ search }) {
  return (
    <div className="nav-item search">
      <Search size={16} />
      <input
        autoFocus
        value={search.text}
        onChange={(e) => search.change(e.target.value)}
        onKeyDown={search.onKeyDown}
        onBlur={search.onBlur}
        placeholder="Search chats"
        aria-label="Search chats"
      />
      {search.text && (
        <button className="clear" onClick={search.stop} aria-label="Clear search">
          <X size={14} />
        </button>
      )}
    </div>
  );
}

export default function SidebarNav({ open, newChatActive, onNew, search }) {
  return (
    <div className="nav">
      <NavItem icon={SquarePen} label="New chat" kbd="⌘⇧O" showTip={!open} active={newChatActive} onClick={onNew} />
      {search.active && open ? (
        <SearchField search={search} />
      ) : (
        <NavItem icon={Search} label="Search" kbd="⌘K" showTip={!open} onClick={search.start} />
      )}
    </div>
  );
}
