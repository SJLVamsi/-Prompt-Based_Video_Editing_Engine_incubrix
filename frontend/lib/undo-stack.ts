export type Cmd = { id: string; label: string; do(): void; undo(): void };
export class UndoStack {
  past: Cmd[] = []; future: Cmd[] = [];
  push(c: Cmd) { c.do(); this.past.push(c); if (this.past.length > 100) this.past.shift(); this.future = []; }
  undo() { const c = this.past.pop(); if (!c) return false; c.undo(); this.future.push(c); return true; }
  redo() { const c = this.future.pop(); if (!c) return false; c.do(); this.past.push(c); return true; }
}
