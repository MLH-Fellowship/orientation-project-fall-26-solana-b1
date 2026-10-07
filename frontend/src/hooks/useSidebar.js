import { useEffect, useState } from "react";

import useShortcut from "./useShortcut.js";

export const isNarrow = () => window.matchMedia("(max-width: 640px)").matches;

function loadOpen() {
  if (isNarrow()) return false;
  try {
    return localStorage.getItem("sidebar") !== "closed";
  } catch {
    return true;
  }
}

export default function useSidebar() {
  const [open, setOpen] = useState(loadOpen);

  useEffect(() => {
    if (isNarrow()) return;
    try {
      localStorage.setItem("sidebar", open ? "open" : "closed");
    } catch {
      // Keep the sidebar usable when browser storage is unavailable.
    }
  }, [open]);

  useShortcut("mod+b", () => setOpen((o) => !o));

  return [open, setOpen];
}
