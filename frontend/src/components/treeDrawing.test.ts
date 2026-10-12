import { describe, expect, it } from "vitest";

import { treeGrowth, treeParts } from "./treeDrawing";

// The server draws the same tree for Stories (backend/tests/test_rewards.py checks the same).
describe("my tree", () => {
  it("grows with the levels and bears apples after the top one", () => {
    expect(treeGrowth(0)).toEqual({ stage: 0, progress: 0, fruits: 0 });
    expect(treeGrowth(300)).toEqual({ stage: 1, progress: 0.5, fruits: 0 });
    expect(treeGrowth(2499).stage).toBe(3);
    expect(treeGrowth(2500)).toEqual({ stage: 4, progress: 1, fruits: 1 });
    expect(treeGrowth(99_999).fruits).toBe(8);
  });

  it("draws more than the ground at every stage", () => {
    for (const points of [0, 50, 100, 500, 1000, 2500]) {
      expect(treeParts(treeGrowth(points)).length).toBeGreaterThan(2);
    }
  });
});
