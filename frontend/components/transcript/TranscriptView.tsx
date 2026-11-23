"use client";
import { useEffect, useRef } from "react";

export type WordToken = { id: string; w: string; start: number; end: number; conf?: number };

/** Bidirectional word <-> playhead linking. Click word seeks; playhead highlights. */
export function TranscriptView({ words, currentTime, onSeek }: {
  words: WordToken[]; currentTime: number; onSeek: (t: number) => void;
}) {
  const activeRef = useRef<HTMLSpanElement>(null);
  const activeIdx = words.findIndex((w) => currentTime >= w.start && currentTime < w.end);

  useEffect(() => {
    activeRef.current?.scrollIntoView({ block: "nearest" });
  }, [activeIdx]);

  return (
    <div className="transcript" style={{ maxHeight: 320, overflowY: "auto" }}>
      {words.map((w, i) => (
        <span
          key={w.id}
          ref={i === activeIdx ? activeRef : undefined}
          data-start={w.start}
          data-end={w.end}
          onClick={() => onSeek(w.start + 0.001)}
          style={{
            cursor: "pointer",
            background: i === activeIdx ? "#FFE45C" : undefined,
            opacity: (w.conf ?? 1) < 0.5 ? 0.55 : 1,
          }}
          title={w.conf != null ? `conf ${w.conf.toFixed(2)}` : undefined}
        >
          {w.w}{" "}
        </span>
      ))}
    </div>
  );
}
