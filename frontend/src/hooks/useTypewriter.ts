import { useEffect, useRef, useState } from "react";

/**
 * Reveals `text` progressively with requestAnimationFrame for a smooth
 * "streaming" feel. When `enabled` is false the full text is shown instantly
 * (used for messages replayed from history).
 */
export function useTypewriter(
  text: string,
  enabled: boolean,
  speed = 220,
): { displayed: string; done: boolean } {
  const [displayed, setDisplayed] = useState(() => (enabled ? "" : text));
  const [done, setDone] = useState(!enabled);
  const frame = useRef<number | null>(null);

  useEffect(() => {
    if (!enabled) {
      setDisplayed(text);
      setDone(true);
      return;
    }

    // Restart cleanly on every (re)run — this also survives React 19
    // StrictMode mounting effects twice in development.
    let index = 0;
    setDone(false);
    setDisplayed("");

    const step = () => {
      // Reveal a chunk proportional to length so long answers stay ~constant.
      const stride = Math.max(1, Math.round(text.length / speed));
      index = Math.min(text.length, index + stride);
      setDisplayed(text.slice(0, index));
      if (index < text.length) {
        frame.current = requestAnimationFrame(step);
      } else {
        setDone(true);
      }
    };

    frame.current = requestAnimationFrame(step);
    return () => {
      if (frame.current !== null) cancelAnimationFrame(frame.current);
    };
  }, [text, enabled, speed]);

  return { displayed, done };
}
