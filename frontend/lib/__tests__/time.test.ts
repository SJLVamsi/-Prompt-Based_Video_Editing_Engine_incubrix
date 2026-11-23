import { describe, expect, it } from "vitest";
import { formatTC, frameToSec, secToFrame, snapToFrame } from "../time";

describe("time", () => {
  it("round-trips frames at 30fps", () => {
    expect(secToFrame(3, 30)).toBe(90);
    expect(frameToSec(90, 30)).toBe(3);
  });
  it("snaps to frame boundary", () => {
    expect(snapToFrame(1.017, 30)).toBeCloseTo(1.0333, 3); // 31/30
  });
  it("formats timecode", () => {
    expect(formatTC(90, 30)).toBe("00:03:00");
    expect(formatTC(0, 30)).toBe("00:00:00");
  });
  it("23976: 144 frames is exactly 6.006s", () => {
    expect(frameToSec(144, 24000 / 1001)).toBeCloseTo(6.006, 6);
  });
});
