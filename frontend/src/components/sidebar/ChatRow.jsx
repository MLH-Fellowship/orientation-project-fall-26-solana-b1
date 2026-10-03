import { useEffect, useRef } from "react";

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

export default function ChatRow({ conversation, status, active, cursor, dragging, over, query, dragProps, onOpen }) {
  const ref = useRef(null);

  useEffect(() => {
    if (cursor) ref.current.scrollIntoView({ block: "nearest" });
  }, [cursor]);

  const classes = ["row"];
  if (active) classes.push("active");
  if (status === "unread") classes.push("unread");
  if (conversation.fresh) classes.push("fresh");
  if (cursor) classes.push("cursor");
  if (dragging) classes.push("dragging");
  else if (over) classes.push("over");

  return (
    <button
      ref={ref}
      className={classes.join(" ")}
      onClick={() => onOpen(conversation.id)}
      data-tip={conversation.title}
      {...dragProps}
    >
      <span className="title">
        <Highlight text={conversation.title} query={query} />
      </span>
      <StatusDot status={status} />
    </button>
  );
}
