"use client";
import { useCallback, useEffect, useRef, useState } from "react";
function useCopyFeedback(duration = 1900) {
  const [state, setState] = useState("idle");
  const [activeKey, setActiveKey] = useState(null);
  const timeout = useRef(null);
  const reset = useCallback(() => {
    if (timeout.current) clearTimeout(timeout.current);
    timeout.current = null;
    setState("idle");
    setActiveKey(null);
  }, []);
  useEffect(() => () => {
    if (timeout.current) clearTimeout(timeout.current);
  }, []);
  const copy = useCallback(async (value, key = "default") => {
    if (timeout.current) clearTimeout(timeout.current);
    setActiveKey(key);
    try {
      await navigator.clipboard.writeText(value);
      setState("copied");
      timeout.current = setTimeout(reset, duration);
      return true;
    } catch {
      setState("error");
      timeout.current = setTimeout(reset, duration);
      return false;
    }
  }, [duration, reset]);
  return { state, activeKey, copy, reset };
}
export {
  useCopyFeedback
};
