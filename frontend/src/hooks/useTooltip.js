import { useCallback, useRef, useState } from "react";

const DELAY = 400;
const WARM = 300;

export default function useTooltip() {
  const [tip, setTip] = useState(null);
  const anchor = useRef(null);
  const timer = useRef(null);
  const shown = useRef(false);
  const warmUntil = useRef(0);

  const hide = useCallback(() => {
    clearTimeout(timer.current);
    if (shown.current) warmUntil.current = Date.now() + WARM;
    shown.current = false;
    anchor.current = null;
    setTip(null);
  }, []);

  function onPointerOver(e) {
    const el = e.target.closest("[data-tip]");
    if (el === anchor.current) return;
    hide();
    anchor.current = el;
    if (!el) return;
    const title = el.querySelector(".title");
    if (title && title.scrollWidth <= title.clientWidth) return;

    const show = () => {
      const r = el.getBoundingClientRect();
      shown.current = true;
      setTip({ text: el.dataset.tip, kbd: el.dataset.kbd, x: r.right + 8, y: r.top + r.height / 2 });
    };
    if (Date.now() < warmUntil.current) show();
    else timer.current = setTimeout(show, DELAY);
  }

  return { tip, hide, handlers: { onPointerOver, onPointerLeave: hide, onPointerDown: hide } };
}
