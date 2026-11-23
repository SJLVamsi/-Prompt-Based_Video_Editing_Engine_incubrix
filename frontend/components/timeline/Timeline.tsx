"use client";
import { useEffect, useRef } from "react";
import { formatTC, secToFrame } from "../../lib/time";
import type { TimelineClip } from "../../lib/contracts";

type Props = {
  clips: TimelineClip[];
  fps: number;
  duration: number;
  currentTime: number;
  pxPerSec: number;
  onSeek: (t: number) => void;
  onSplit: (t: number) => void;
};

/** V1 track: clip blocks + playhead + ruler scrub. Frame-snapped. */
export function Timeline({ clips, fps, duration, currentTime, pxPerSec, onSeek, onSplit }: Props) {
  const rulerRef = useRef<HTMLDivElement>(null);
  const width = Math.ceil(duration * pxPerSec);

  function seekFromClientX(clientX: number) {
    const el = rulerRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const t = Math.min(duration, Math.max(0, (clientX - rect.left) / pxPerSec));
    onSeek(Math.round(t * fps) / fps);
  }

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowLeft") onSeek(Math.max(0, currentTime - 1 / fps));
      if (e.key === "ArrowRight") onSeek(Math.min(duration, currentTime + 1 / fps));
      if (e.key.toLowerCase() === "c") onSplit(currentTime);
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [currentTime, duration, fps, onSeek, onSplit]);

  return (
    <div className="timeline" style={{ width }}>
      <div
        ref={rulerRef}
        className="ruler"
        style={{ width, height: 28, cursor: "crosshair" }}
        onPointerDown={(e) => {
          (e.target as HTMLElement).setPointerCapture(e.pointerId);
          seekFromClientX(e.clientX);
        }}
        onPointerMove={(e) => {
          if (e.buttons & 1) seekFromClientX(e.clientX);
        }}
      />
      <div className="track" style={{ width, position: "relative", height: 56 }}>
        {clips.map((c) => (
          <div
            key={c.id}
            className="clip"
            title={`${c.id} [${c.start}, ${c.end})`}
            style={{
              position: "absolute",
              left: (c.start / fps) * pxPerSec,
              width: Math.max(2, ((c.end - c.start) / fps) * pxPerSec),
              top: 4, bottom: 4,
            }}
          />
        ))}
        <div
          className="playhead"
          style={{ position: "absolute", left: currentTime * pxPerSec, top: 0, bottom: 0 }}
        />
      </div>
      <div className="tc">
        {formatTC(Math.round(currentTime * fps), fps)} / {formatTC(secToFrame(duration, fps), fps)} @ {fps}fps
      </div>
    </div>
  );
}
