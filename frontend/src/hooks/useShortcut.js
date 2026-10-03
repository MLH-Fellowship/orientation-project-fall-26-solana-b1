import { useEffect, useRef } from "react";

export default function useShortcut(combo, handler) {
  const handlerRef = useRef(handler);
  handlerRef.current = handler;

  useEffect(() => {
    const parts = combo.toLowerCase().split("+");
    const key = parts.at(-1);
    const shift = parts.includes("shift");

    function onKey(e) {
      if (!(e.metaKey || e.ctrlKey) || e.shiftKey !== shift || e.key.toLowerCase() !== key) return;
      e.preventDefault();
      handlerRef.current(e);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [combo]);
}
