import { describe, expect, it } from "vitest";
import { EditPlan } from "../contracts";

describe("contracts", () => {
  it("accepts a valid cut plan", () => {
    const p = EditPlan.parse({
      version: "v1",
      ops: [{ op: "cut", start: 0, end: 2 }],
      response: "results",
    });
    expect(p.ops).toHaveLength(1);
  });
  it("rejects unknown op", () => {
    expect(() =>
      EditPlan.parse({ version: "v1", ops: [{ op: "dissolve", start: 0, end: 1 }] })
    ).toThrow();
  });
  it("rejects out-of-range speed factor", () => {
    expect(() =>
      EditPlan.parse({ version: "v1", ops: [{ op: "speed", start: 0, end: 1, factor: 9 }] })
    ).toThrow();
  });
  it("rejects empty caption text", () => {
    expect(() =>
      EditPlan.parse({ version: "v1", ops: [{ op: "caption", start: 0, end: 1, text: "" }] })
    ).toThrow();
  });
});
