import { describe, expect, it } from "vitest";

import { formatTime, parseTime } from "./stepTimes";

describe("step times in the admin panel", () => {
  it("reads minutes and seconds, or plain seconds", () => {
    expect(parseTime("0:12")).toBe(12);
    expect(parseTime("1:05.5")).toBe(65.5);
    expect(parseTime("7,5")).toBe(7.5);
    expect(parseTime("  ")).toBeNull();
    expect(parseTime("abc")).toBeNull();
  });

  it("writes them back the same way", () => {
    expect(formatTime(12)).toBe("0:12");
    expect(formatTime(65.5)).toBe("1:05.5");
    expect(parseTime(formatTime(131.6))).toBe(131.6);
  });
});
