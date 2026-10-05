import { PanelLeft } from "lucide-react";
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
}) {
  const groups = useChatGroups();
  const tooltip = useTooltip();
  const search = useChatSearch(conversations, { onStart: () => onOpenChange(true), onPick: onOpen });

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
    <aside className={"sidebar" + (open ? "" : " collapsed")} {...tooltip.handlers}>
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

      <SidebarNav open={open} newChatActive={activeId === null} onNew={onNew} search={search} />

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

      <Tooltip tip={tooltip.tip} />
    </aside>
  );
}
