export function secToFrame(t: number, fps: number) { return Math.round(t * fps); }
export function frameToSec(f: number, fps: number) { return f / fps; }
export function snapToFrame(t: number, fps: number) { return secToFrame(t, fps) / fps; }
export function formatTC(f: number, fps: number) {
  const s = Math.floor(f / fps), ff = f % fps;
  const m = Math.floor(s / 60), ss = s % 60;
  return `${String(m).padStart(2, "0")}:${String(ss).padStart(2, "0")}:${String(ff).padStart(2, "0")}`;
}
