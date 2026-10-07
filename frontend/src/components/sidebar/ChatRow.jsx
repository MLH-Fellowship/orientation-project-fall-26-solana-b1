import { Pencil, Trash2 } from "lucide-react";
import { useEffect, useRef, useState } from "react";

import StatusDot from "./StatusDot.jsx";

function Highlight({ text, query }) {
  const i = query ? text.toLowerCase().indexOf(query) : -1;
  if (i < 0) return text;
  return (
    <>
      {text.slice(0, i)}
      <mark>{text.slice(i, i + query.length)}</mark>
      {text.slice(i + query.length)}
    </>
  );
}

export default function ChatRow({
  conversation,
  status,
  active,
  cursor,
  dragging,
  over,
  query,
  dragProps,
  onOpen,
  onRename,
  onDelete,
}) {
  const ref = useRef(null);
  const skipBlur = useRef(false);
  const saving = useRef(false);
  const [editing, setEditing] = useState(false);
  const [title, setTitle] = useState(conversation.title);
  const [busy, setBusy] = useState(false);
  const [renameError, setRenameError] = useState("");

  useEffect(() => {
    if (cursor) ref.current.scrollIntoView({ block: "nearest" });
  }, [cursor]);

  useEffect(() => {
    if (!editing) setTitle(conversation.title);
  }, [conversation.title, editing]);

  function startRename() {
    skipBlur.current = false;
    setTitle(conversation.title);
    setRenameError("");
    setEditing(true);
  }

  function cancelRename() {
    skipBlur.current = true;
    setTitle(conversation.title);
    setRenameError("");
    setEditing(false);
  }

  async function commitRename() {
    if (skipBlur.current || saving.current) return;

    const nextTitle = title.trim();
    if (!nextTitle) {
      cancelRename();
      return;
    }
    if (nextTitle === conversation.title) {
      setEditing(false);
      return;
    }

    saving.current = true;
    setBusy(true);
    try {
      await onRename(conversation.id, nextTitle);
      setRenameError("");
      setEditing(false);
    } catch {
      setRenameError("Couldn’t rename conversation. Try again.");
    } finally {
      saving.current = false;
      setBusy(false);
    }
  }

  async function confirmDelete() {
    const confirmed = window.confirm(`Delete “${conversation.title}”? This cannot be undone.`);
    if (!confirmed) return;

    setBusy(true);
    try {
      await onDelete(conversation.id);
    } catch {
      window.alert("Couldn’t delete this conversation. Please try again.");
    } finally {
      setBusy(false);
    }
  }

  const classes = ["row"];
  if (active) classes.push("active");
  if (status === "unread") classes.push("unread");
  if (conversation.fresh) classes.push("fresh");
  if (cursor) classes.push("cursor");
  if (dragging) classes.push("dragging");
  else if (over) classes.push("over");

  return (
    <div
      ref={ref}
      className={classes.join(" ")}
      data-tip={editing ? undefined : conversation.title}
      {...dragProps}
      draggable={!editing && !busy}
    >
      {editing ? (
        <form
          className="rename-form"
          onSubmit={(e) => {
            e.preventDefault();
            commitRename();
          }}
        >
          <input
            autoFocus
            aria-label={`Rename ${conversation.title}`}
            value={title}
            maxLength={200}
            disabled={busy}
            aria-invalid={Boolean(renameError)}
            title={renameError || undefined}
            onChange={(e) => {
              setTitle(e.target.value);
              setRenameError("");
            }}
            onFocus={(e) => e.target.select()}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === "Escape") cancelRename();
            }}
          />
        </form>
      ) : (
        <>
          <button
            className="row-open"
            onClick={() => onOpen(conversation.id)}
            disabled={busy}
            aria-current={active ? "page" : undefined}
          >
            <span className="title">
              <Highlight text={conversation.title} query={query} />
            </span>
            <StatusDot status={status} />
          </button>
          <span className="row-actions">
            <button
              className="row-action"
              type="button"
              onClick={startRename}
              disabled={busy || status === "pending"}
              data-tip="Rename"
              aria-label={`Rename ${conversation.title}`}
            >
              <Pencil size={13} />
            </button>
            <button
              className="row-action danger"
              type="button"
              onClick={confirmDelete}
              disabled={busy || status === "pending"}
              data-tip="Delete"
              aria-label={`Delete ${conversation.title}`}
            >
              <Trash2 size={13} />
            </button>
          </span>
        </>
      )}
    </div>
  );
}
