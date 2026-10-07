import { PanelLeft, Sun, Moon } from "lucide-react";
import { useEffect } from "react";

import useChatGroups from "../../hooks/useChatGroups.js";
import useChatSearch from "../../hooks/useChatSearch.js";
import useShortcut from "../../hooks/useShortcut.js";
import useTooltip from "../../hooks/useTooltip.js";
import ChatList from "./ChatList.jsx";
import ChatRow from "./ChatRow.jsx";
import SidebarNav from "./SidebarNav.jsx";
import Tooltip from "./Tooltip.jsx";

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
  theme, // <-- Destructure theme
  onToggleTheme,
}) {
  const groups = useChatGroups();
  const tooltip = useTooltip();
  const search = useChatSearch(conversations, {
    onStart: () => onOpenChange(true),
    onPick: onOpen,
  });

  useShortcut("mod+k", search.start);
  const hideTooltip = tooltip.hide;
  useEffect(() => {
    hideTooltip();
  }, [open, hideTooltip]);

  function statusOf(id) {
    if (pending.has(id)) return "pending";
    if (failed[id]) return "failed";
    if (unread.has(id)) return "unread";
    return null;
  }

  function renderRow(c, i) {
    return (
      <ChatRow
        key={c.id}
        conversation={c}
        status={statusOf(c.id)}
        active={c.id === activeId}
        cursor={Boolean(search.query) && i === search.cursor}
        dragging={groups.dragId === c.id}
        over={groups.isOver(c.id)}
        query={search.query}
        dragProps={groups.draggable(c.id, tooltip.hide)}
        onOpen={onOpen}
      />
    );
  }

  return (
    <aside
      className={"sidebar" + (open ? "" : " collapsed")}
      {...tooltip.handlers}
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

      <SidebarNav
        open={open}
        newChatActive={activeId === null}
        onNew={onNew}
        search={search}
      />

      <div className="flex-1 min-h-0 overflow-hidden flex flex-col">
        {open && (
        <nav className={"chats" + (groups.dragId ? " is-dragging" : "")} {...groups.dropTarget("loose", {})}>
          <ChatList
            conversations={conversations}
            listState={listState}
            onRetry={onRetryList}
            search={search}
            groups={groups}
            unread={unread}
            renderRow={renderRow}
          />
        </nav>
      )}
      </div>

      <div className="mt-auto pt-2 border-t border-[var(--line)]">
        <button
          onClick={onToggleTheme}
          className="nav-item flex w-full items-center gap-2.5 rounded-lg px-2.5 py-2 text-xs font-medium transition-colors hover:bg-[var(--hover)] text-[var(--ink-2)]"
        >
          <span className="relative flex h-4 w-4 items-center justify-center">
            <Sun className="h-4 w-4 rotate-0 scale-100 text-amber-500 transition-all duration-500 dark:-rotate-90 dark:scale-0" />
            <Moon className="absolute h-4 w-4 rotate-90 scale-0 text-indigo-400 transition-all duration-500 dark:rotate-0 dark:scale-100" />
          </span>
          <span className="label">
            {theme === "light" ? "Light Mode" : "Dark Mode"}
          </span>
        </button>
      </div>
      
      <Tooltip tip={tooltip.tip} />
    </aside>
  );
}
