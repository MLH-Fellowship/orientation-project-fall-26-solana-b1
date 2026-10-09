import { useEffect, useState } from "react";

function loadGroups() {
  try {
    return JSON.parse(localStorage.getItem("groups")) || {};
  } catch {
    return {};
  }
}

function nextGroupName(groups) {
  const taken = new Set(Object.values(groups));
  let name = "New group";
  for (let i = 2; taken.has(name); i++) name = `New group ${i}`;
  return name;
}

export default function useChatGroups() {
  const [groups, setGroups] = useState(loadGroups);
  const [collapsed, setCollapsed] = useState(new Set());
  const [renaming, setRenaming] = useState(null);
  const [dragId, setDragId] = useState(null);
  const [overId, setOverId] = useState(null);

  useEffect(() => localStorage.setItem("groups", JSON.stringify(groups)), [groups]);

  function drop({ chat, group }) {
    const id = dragId;
    setDragId(null);
    setOverId(null);
    if (!id || chat === id) return;

    const next = { ...groups };
    let name = group ?? groups[chat];
    if (chat && !name) {
      name = nextGroupName(groups);
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

  function remove(id) {
    setGroups((current) => {
      if (!current[id]) return current;
      const next = { ...current };
      delete next[id];
      return next;
    });
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

  function draggable(id, onStart) {
    return {
      draggable: true,
      onDragStart: (e) => {
        e.dataTransfer.setData("text/plain", id);
        setDragId(id);
        onStart?.();
      },
      onDragEnd: () => {
        setDragId(null);
        setOverId(null);
      },
      ...dropTarget(id, { chat: id }),
    };
  }

  function split(conversations) {
    const names = [...new Set(conversations.map((c) => groups[c.id]).filter(Boolean))];
    return {
      grouped: names.map((name) => ({ name, members: conversations.filter((c) => groups[c.id] === name) })),
      loose: conversations.filter((c) => !groups[c.id]),
    };
  }

  return {
    dragId,
    draggingGrouped: Boolean(dragId && groups[dragId]),
    isOver: (key) => Boolean(dragId) && overId === key,
    isCollapsed: (name) => collapsed.has(name),
    renaming,
    startRename: setRenaming,
    rename,
    remove,
    toggle,
    dropTarget,
    draggable,
    split,
  };
}
