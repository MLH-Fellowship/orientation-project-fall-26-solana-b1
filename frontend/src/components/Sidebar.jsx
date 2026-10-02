import { MessageSquare, PanelLeft, RotateCw, Search, SquarePen, X } from "lucide-react";
import { useEffect, useRef, useState } from "react";

function loadGroups() {
  try {
    return JSON.parse(localStorage.getItem("groups")) || {};
  } catch {
    return {};
  }
}

const STATUS_LABELS = { pending: "Replying", failed: "Message not sent", unread: "New reply" };

const TOOLTIP_DELAY = 400;
const TOOLTIP_WARM = 300;

export default function Sidebar({
  open,
  onOpenChange,
  conversations,
  listState,
  onRetryList,
  activeId,
  pending,
  unread,
  failed,
  onOpen,
  onNew,
}) {
  const [groups, setGroups] = useState(loadGroups);
  const [collapsed, setCollapsed] = useState(new Set());
  const [renaming, setRenaming] = useState(null);
  const [dragId, setDragId] = useState(null);
  const [overId, setOverId] = useState(null);
  const [searching, setSearching] = useState(false);
  const [query, setQuery] = useState("");
  const [cursor, setCursor] = useState(0);
  const [tip, setTip] = useState(null);
  const searchRef = useRef(null);
  const listRef = useRef(null);
  const tipEl = useRef(null);
  const tipTimer = useRef(null);
  const tipShown = useRef(false);
  const tipWarmUntil = useRef(0);

  useEffect(() => localStorage.setItem("groups", JSON.stringify(groups)), [groups]);

  useEffect(() => {
    if (searching && open) searchRef.current?.focus();
  }, [searching, open]);

  useEffect(() => {
    function onKey(e) {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        onOpenChange(true);
        setSearching(true);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onOpenChange]);

  useEffect(() => {
    listRef.current?.querySelector(".row.cursor")?.scrollIntoView({ block: "nearest" });
  }, [cursor]);

  useEffect(hideTip, [open]);

  const q = query.trim().toLowerCase();
  const matches = q ? conversations.filter((c) => c.title.toLowerCase().includes(q)) : [];

  function startSearch() {
    onOpenChange(true);
    setSearching(true);
  }

  function stopSearch() {
    setSearching(false);
    setQuery("");
  }

  function onSearchKey(e) {
    if (e.key === "Escape") stopSearch();
    else if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter" && matches[cursor]) {
      onOpen(matches[cursor].id);
      stopSearch();
    }
  }

  function onTipOver(e) {
    const el = e.target.closest("[data-tip]");
    if (el === tipEl.current) return;
    hideTip();
    tipEl.current = el;
    if (!el || dragId) return;
    const title = el.querySelector(".title");
    if (title && title.scrollWidth <= title.clientWidth) return;

    const show = () => {
      const r = el.getBoundingClientRect();
      tipShown.current = true;
      setTip({ text: el.dataset.tip, kbd: el.dataset.kbd, x: r.right + 8, y: r.top + r.height / 2 });
    };
    if (Date.now() < tipWarmUntil.current) show();
    else tipTimer.current = setTimeout(show, TOOLTIP_DELAY);
  }

  function hideTip() {
    clearTimeout(tipTimer.current);
    if (tipShown.current) tipWarmUntil.current = Date.now() + TOOLTIP_WARM;
    tipShown.current = false;
    tipEl.current = null;
    setTip(null);
  }

  function drop({ chat, group }) {
    const id = dragId;
    setDragId(null);
    setOverId(null);
    if (!id || chat === id) return;

    const next = { ...groups };
    let name = group ?? groups[chat];
    if (chat && !name) {
      name = "New group";
      for (let i = 2; Object.values(groups).includes(name); i++) name = `New group ${i}`;
      next[chat] = name;
      setRenaming(name);
    }
    if (name) next[id] = name;
    else delete next[id];
    setGroups(next);
  }

  function rename(from, to) {
    setRenaming(null);
    to = to.trim();
    if (!to || to === from) return;
    setGroups((g) => Object.fromEntries(Object.entries(g).map(([k, v]) => [k, v === from ? to : v])));
  }

  function toggle(name) {
    setCollapsed((s) => {
      const next = new Set(s);
      next.has(name) ? next.delete(name) : next.add(name);
      return next;
    });
  }

  function dropTarget(key, target) {
    return {
      onDragOver: (e) => {
        e.preventDefault();
        e.stopPropagation();
        setOverId(key);
      },
      onDrop: (e) => {
        e.preventDefault();
        e.stopPropagation();
        drop(target);
      },
    };
  }

  function highlight(title) {
    const i = q ? title.toLowerCase().indexOf(q) : -1;
    if (i < 0) return title;
    return (
      <>
        {title.slice(0, i)}
        <mark>{title.slice(i, i + q.length)}</mark>
        {title.slice(i + q.length)}
      </>
    );
  }

  function row(c, i) {
    const status = pending.has(c.id) ? "pending" : failed[c.id] ? "failed" : unread.has(c.id) ? "unread" : null;
    const classes = ["row"];
    if (c.id === activeId) classes.push("active");
    if (status === "unread") classes.push("unread");
    if (c.fresh) classes.push("fresh");
    if (q && i === cursor) classes.push("cursor");
    if (c.id === dragId) classes.push("dragging");
    else if (dragId && overId === c.id) classes.push("over");

    return (
      <button
        key={c.id}
        className={classes.join(" ")}
        onClick={() => onOpen(c.id)}
        data-tip={c.title}
        draggable
        onDragStart={(e) => {
          e.dataTransfer.setData("text/plain", c.id);
          setDragId(c.id);
          hideTip();
        }}
        onDragEnd={() => {
          setDragId(null);
          setOverId(null);
        }}
        {...dropTarget(c.id, { chat: c.id })}
      >
        <span className="title">{highlight(c.title)}</span>
        {status && <span className={`status ${status}`} role="img" aria-label={STATUS_LABELS[status]} />}
      </button>
    );
  }

  function chatList() {
    if (listState === "loading") {
      return (
        <div className="skeleton-list" aria-busy="true" aria-label="Loading chats">
          {[72, 88, 60, 80, 52].map((w, i) => (
            <span key={i} className="skeleton" style={{ width: `${w}%` }} />
          ))}
        </div>
      );
    }

    if (listState === "error") {
      return (
        <div className="side-state">
          <p>Couldn’t load your chats.</p>
          <button className="text-button" onClick={onRetryList}>
            <RotateCw size={13} />
            Try again
          </button>
        </div>
      );
    }

    if (conversations.length === 0) {
      return (
        <div className="side-state">
          <MessageSquare size={18} strokeWidth={1.5} />
          <p>No chats yet</p>
          <span>Your conversations will show up here.</span>
        </div>
      );
    }

    if (q) {
      if (matches.length === 0) return <p className="empty">No chats match “{query.trim()}”.</p>;
      return <div className="loose">{matches.map(row)}</div>;
    }

    const names = [...new Set(conversations.map((c) => groups[c.id]).filter(Boolean))];
    const loose = conversations.filter((c) => !groups[c.id]);

    return (
      <>
        {names.map((name) => {
          const members = conversations.filter((c) => groups[c.id] === name);
          const isOpen = !collapsed.has(name);
          const hasUnread = members.some((c) => unread.has(c.id));
          return (
            <section key={name} className="group">
              <div
                className={"group-head" + (dragId && overId === `g:${name}` ? " over" : "")}
                onClick={() => toggle(name)}
                {...dropTarget(`g:${name}`, { group: name })}
              >
                <span className={"chevron" + (isOpen ? " open" : "")}>›</span>
                {renaming === name ? (
                  <input
                    autoFocus
                    defaultValue={name}
                    onFocus={(e) => e.target.select()}
                    onClick={(e) => e.stopPropagation()}
                    onBlur={(e) => rename(name, e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === "Escape") e.target.value = name;
                      if (e.key === "Enter" || e.key === "Escape") e.target.blur();
                    }}
                  />
                ) : (
                  <span className="group-name" onDoubleClick={() => setRenaming(name)}>
                    {name}
                  </span>
                )}
                {!isOpen && hasUnread ? (
                  <span className="status unread" role="img" aria-label={STATUS_LABELS.unread} />
                ) : (
                  <span className="count">{members.length}</span>
                )}
              </div>
              {isOpen && <div className="thread">{members.map(row)}</div>}
            </section>
          );
        })}

        {loose.length > 0 && <div className="loose">{loose.map(row)}</div>}

        {dragId && groups[dragId] && (
          <div className={"drop-zone" + (overId === "loose" ? " over" : "")} {...dropTarget("loose", {})}>
            Drop here to ungroup
          </div>
        )}
      </>
    );
  }

  return (
    <aside
      className={"sidebar" + (open ? "" : " collapsed")}
      onPointerOver={onTipOver}
      onPointerLeave={hideTip}
      onPointerDown={hideTip}
    >
      <header className="sidebar-top">
        <button
          className="icon-button"
          onClick={() => onOpenChange(!open)}
          data-tip={open ? "Close sidebar" : "Open sidebar"}
          data-kbd="⌘B"
          aria-label={open ? "Close sidebar" : "Open sidebar"}
          aria-expanded={open}
        >
          <PanelLeft size={16} />
        </button>
      </header>

      <div className="nav">
        <button
          className={"nav-item" + (activeId === null ? " active" : "")}
          onClick={onNew}
          data-tip={open ? undefined : "New chat"}
          data-kbd="⌘⇧O"
          aria-label="New chat"
        >
          <SquarePen size={16} />
          <span className="label">New chat</span>
          <kbd>⌘⇧O</kbd>
        </button>

        {searching && open ? (
          <div className="nav-item search">
            <Search size={16} />
            <input
              ref={searchRef}
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setCursor(0);
              }}
              onKeyDown={onSearchKey}
              onBlur={() => !query && setSearching(false)}
              placeholder="Search chats"
              aria-label="Search chats"
            />
            {query && (
              <button className="clear" onClick={stopSearch} aria-label="Clear search">
                <X size={14} />
              </button>
            )}
          </div>
        ) : (
          <button
            className="nav-item"
            onClick={startSearch}
            data-tip={open ? undefined : "Search"}
            data-kbd="⌘K"
            aria-label="Search chats"
          >
            <Search size={16} />
            <span className="label">Search</span>
            <kbd>⌘K</kbd>
          </button>
        )}
      </div>

      {open && (
        <nav ref={listRef} className={"chats" + (dragId ? " is-dragging" : "")} {...dropTarget("loose", {})}>
          {listState === "ready" && conversations.length > 0 && !q && <h2 className="section-label">Chats</h2>}
          {chatList()}
        </nav>
      )}

      {tip && (
        <div className="tooltip" role="tooltip" style={{ left: tip.x, top: tip.y }}>
          {tip.text}
          {tip.kbd && <kbd>{tip.kbd}</kbd>}
        </div>
      )}
    </aside>
  );
}
