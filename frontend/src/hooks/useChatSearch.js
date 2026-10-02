import { useState } from "react";

export default function useChatSearch(conversations, { onStart, onPick }) {
  const [active, setActive] = useState(false);
  const [text, setText] = useState("");
  const [cursor, setCursor] = useState(0);

  const query = text.trim().toLowerCase();
  const matches = query ? conversations.filter((c) => c.title.toLowerCase().includes(query)) : [];

  function start() {
    onStart();
    setActive(true);
  }

  function stop() {
    setActive(false);
    setText("");
  }

  function change(value) {
    setText(value);
    setCursor(0);
  }

  function onKeyDown(e) {
    if (e.key === "Escape") stop();
    else if (e.key === "ArrowDown") {
      e.preventDefault();
      setCursor((c) => Math.min(c + 1, matches.length - 1));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setCursor((c) => Math.max(c - 1, 0));
    } else if (e.key === "Enter" && matches[cursor]) {
      onPick(matches[cursor].id);
      stop();
    }
  }

  function onBlur() {
    if (!text) setActive(false);
  }

  return { active, text, query, matches, cursor, start, stop, change, onKeyDown, onBlur };
}
