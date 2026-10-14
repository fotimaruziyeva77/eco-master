import type { ProjectDetail } from "./api/client";
import { parseVideo } from "./videoSource";

/**
 * Where each step starts in the project's video, when the team marked every step of it on a
 * video file (admin panel). Otherwise null: the steps are shown as text only.
 */
export function stepTimes(project: ProjectDetail | undefined, stepCount: number): number[] | null {
  const times = project?.step_times;
  if (!project?.video_url || !times || stepCount === 0 || times.length !== stepCount) return null;
  if (times.some((t) => typeof t !== "number")) return null;
  if (parseVideo(project.video_url).kind !== "file") return null;
  return times as number[];
}

/** Projects whose steps were gone through to the end in this visit: "I did it" opens at once. */
export const stepsWatched = new Set<string>();
