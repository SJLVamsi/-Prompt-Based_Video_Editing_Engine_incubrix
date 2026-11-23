"use client";
import { useState } from "react";
import { Timeline } from "../../components/timeline/Timeline";
import { TranscriptView, type WordToken } from "../../components/transcript/TranscriptView";
import { PromptBar } from "../../components/prompt/PromptBar";
import { UndoStack } from "../../lib/undo-stack";
import type { TimelineClip } from "../../lib/contracts";

const FPS = 30;

/** Editor shell: preview + timeline + transcript + prompt + jobs + undo. */
export default function EditorPage({ params }: { params: { projectId: string } }) {
  const [clips, setClips] = useState<TimelineClip[]>([{ id: "c1", start: 0, end: 300 }]);
  const [words] = useState<WordToken[]>([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [busy, setBusy] = useState(false);
  const [stack] = useState(() => new UndoStack());
  const duration = clips.length ? Math.max(...clips.map((c) => c.end)) / FPS : 0;

  function applyCut(t: number) {
    const f = Math.round(t * FPS);
    const before = clips;
    const after: TimelineClip[] = [];
    before.forEach((c) => {
      if (f > c.start && f < c.end) {
        after.push({ ...c, end: f }, { ...c, id: `${c.id}b`, start: f });
      } else after.push(c);
    });
    stack.push({ id: `cut@${f}`, label: `Split at frame ${f}`,
      do: () => setClips(after), undo: () => setClips(before) });
  }

  async function applyPrompt(prompt: string) {
    setBusy(true);
    try {
      const res = await fetch("/api/proxy/v1/plans:generate", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ raw: prompt }),
      });
      void res;
    } finally {
      setBusy(false);
    }
  }

  return (
    <main data-project={params.projectId}>
      <h1>Project {params.projectId}</h1>
      <video controls src="" style={{ width: "100%" }} />
      <Timeline
        clips={clips} fps={FPS} duration={duration} currentTime={currentTime}
        pxPerSec={12} onSeek={setCurrentTime} onSplit={applyCut}
      />
      <div style={{ display: "flex", gap: 8 }}>
        <button onClick={() => stack.undo()}>Undo</button>
        <button onClick={() => stack.redo()}>Redo</button>
      </div>
      <PromptBar onSubmit={applyPrompt} busy={busy} />
      <TranscriptView words={words} currentTime={currentTime} onSeek={setCurrentTime} />
    </main>
  );
}
