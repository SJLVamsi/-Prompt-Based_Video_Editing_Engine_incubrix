"use client";
import { useState } from "react";

export function PromptBar({ onSubmit, busy }: { onSubmit: (prompt: string) => void; busy?: boolean }) {
  const [value, setValue] = useState("");
  return (
    <form
      className="promptbar"
      onSubmit={(e) => {
        e.preventDefault();
        if (value.trim() && !busy) onSubmit(value.trim());
      }}
    >
      <input
        aria-label="Edit prompt"
        placeholder='e.g. "cut silences, keep the demo, 30s short with captions"'
        value={value}
        onChange={(e) => setValue(e.target.value)}
      />
      <button type="submit" disabled={busy || !value.trim()}>
        {busy ? "Planning…" : "Apply prompt"}
      </button>
    </form>
  );
}
