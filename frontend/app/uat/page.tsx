"use client";
import { useState } from "react";

const UAT_PROMPT = "Remove silent parts, add English subtitles, and convert to 9:16";

/** Real UAT workflow: upload -> transcribe -> prompt -> preview/download. */
export default function UatPage() {
  const [assetId, setAssetId] = useState<string | null>(null);
  const [words, setWords] = useState<{ word: string; start: number; end: number }[]>([]);
  const [prompt, setPrompt] = useState(UAT_PROMPT);
  const [result, setResult] = useState<null | {
    jobId: string; ops: string[]; duration: number; width: number; height: number;
    sub_stream: boolean; warnings: string[];
  }>(null);
  const [msg, setMsg] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function parseBody(res: Response) {
    const text = await res.text();
    try { return JSON.parse(text); } catch { return { _raw: text }; }
  }

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0];
    if (!f) return;
    setBusy(true); setMsg(null);
    try {
      const fd = new FormData();
      fd.append("file", f);
      const res = await fetch("/api/proxy/uploads", { method: "POST", body: fd });
      const data = await parseBody(res);
      if (!res.ok) setMsg(`Error ${data.code || res.status}: ${data.detail || "upload failed"}`);
      else { setAssetId(data.assetId); setMsg(`Uploaded ${f.name}: ${data.duration.toFixed(2)}s, ${data.width}x${data.height}`); }
    } catch (err) {
      setMsg(`Error: could not reach API (${err instanceof Error ? err.message : err})`);
    } finally { setBusy(false); }
  }

  async function transcribe() {
    if (!assetId) return;
    setBusy(true); setMsg(null);
    try {
      const res = await fetch("/api/proxy/transcribe", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assetId, model: "tiny" }),
      });
      const data = await parseBody(res);
      if (!res.ok) setMsg(`Error ${data.code || res.status}: ${data.detail || data._raw || "transcribe failed"}`);
      else { setWords(data.words ?? []); setMsg(`Transcribed ${data.n} words`); }
    } catch (err) {
      setMsg(`Error: could not reach API (${err instanceof Error ? err.message : err})`);
    } finally { setBusy(false); }
  }

  async function run() {
    if (!assetId) return;
    setBusy(true); setMsg(null); setResult(null);
    try {
      const res = await fetch("/api/proxy/uat/run", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ assetId, prompt }),
      });
      const data = await parseBody(res);
      if (!res.ok) setMsg(`Error ${data.code || res.status}: ${data.detail || data._raw || "render failed"}`);
      else if (data.status === "clarify") setMsg(`Clarify: ${data.clarify_question}`);
      else { setResult(data); setMsg(`Done: ${data.ops.join(", ")}`); }
    } catch (err) {
      setMsg(`Error: could not reach API (${err instanceof Error ? err.message : err})`);
    } finally { setBusy(false); }
  }

  return (
    <main>
      <h1>UAT: prompt-based edit</h1>
      <label>1. Upload video <input type="file" accept="video/*,audio/*" onChange={upload} disabled={busy} /></label>
      <div><button onClick={transcribe} disabled={!assetId || busy}>2. Transcribe</button>
        <span> {words.length > 0 && `${words.length} words: ${words.slice(0, 8).map((w) => w.word).join(" ")}…`}</span></div>
      <div>
        <label>3. Prompt <input aria-label="UAT prompt" value={prompt} onChange={(e) => setPrompt(e.target.value)} style={{ width: "60%" }} /></label>
        <button onClick={run} disabled={!assetId || busy}>Apply prompt</button>
      </div>
      {msg && <p role="status">{msg}</p>}
      {result && (
        <div>
          <p>Output: {result.duration.toFixed(2)}s, {result.width}x{result.height}, subs(mov_text): {String(result.sub_stream)}</p>
          {result.warnings.map((w) => <p key={w}>Warning: {w}</p>)}
          <video controls src={`/api/proxy/exports/${result.jobId}/download`} style={{ width: 360 }} />
          <p><a href={`/api/proxy/exports/${result.jobId}/download`}>Download MP4</a></p>
        </div>
      )}
    </main>
  );
}
