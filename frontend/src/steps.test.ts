import { describe, expect, it } from "vitest";

import type { ProjectDetail } from "./api/client";
import { stepTimes } from "./steps";

const project = (values: Partial<ProjectDetail>) => ({ video_url: "/media/v/abc.mp4", ...values }) as ProjectDetail;

describe("step clips", () => {
  it("are used when every step has a time on a video file", () => {
    expect(stepTimes(project({ step_times: [0, 4.5, 9] }), 3)).toEqual([0, 4.5, 9]);
  });

  it("are not used when steps and times do not match or a step is not marked", () => {
    expect(stepTimes(project({ step_times: [0, 4.5] }), 3)).toBeNull();
    expect(stepTimes(project({ step_times: [0, null, 9] }), 3)).toBeNull();
    expect(stepTimes(project({ step_times: null }), 3)).toBeNull();
    expect(stepTimes(project({ step_times: [0, 4.5], video_url: "https://youtu.be/abcdefgh" }), 2)).toBeNull();
  });
});
