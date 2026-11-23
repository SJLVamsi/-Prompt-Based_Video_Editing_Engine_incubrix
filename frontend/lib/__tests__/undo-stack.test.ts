import { describe, expect, it } from "vitest";
import { UndoStack } from "../undo-stack";

describe("UndoStack", () => {
  it("push/undo/redo round-trips", () => {
    let v = 0;
    const s = new UndoStack();
    s.push({ id: "a", label: "inc", do: () => (v = 1), undo: () => (v = 0) });
    expect(v).toBe(1);
    expect(s.undo()).toBe(true);
    expect(v).toBe(0);
    expect(s.redo()).toBe(true);
    expect(v).toBe(1);
  });
  it("undo on empty returns false", () => {
    expect(new UndoStack().undo()).toBe(false);
  });
  it("push clears redo future", () => {
    let v = 0;
    const s = new UndoStack();
    s.push({ id: "a", label: "a", do: () => (v = 1), undo: () => (v = 0) });
    s.undo();
    s.push({ id: "b", label: "b", do: () => (v = 2), undo: () => (v = 0) });
    expect(s.redo()).toBe(false);
    expect(v).toBe(2);
  });
  it("caps history at 100", () => {
    const s = new UndoStack();
    for (let i = 0; i < 150; i++)
      s.push({ id: `${i}`, label: `${i}`, do: () => {}, undo: () => {} });
    expect(s.past.length).toBe(100);
  });
});
