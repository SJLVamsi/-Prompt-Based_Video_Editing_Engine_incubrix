import { TimelineClip } from "../lib/contracts";
export function frameToSec(f: number, fps: number) { return f / fps; }
export function secToFrame(t: number, fps: number) { return Math.round(t * fps); }
export function Timeline({ clips, fps, currentTime }: { clips: TimelineClip[]; fps: number; currentTime: number }) {
  return null as unknown as JSX.Element; // canvas/DOM tracks implemented in Phase 5.4 full
}
