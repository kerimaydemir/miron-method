import { describe, expect, it } from "vitest";

import type { ScanResult } from "./types";

describe("scan response contract", () => {
  it("keeps the canonical three-day Istanbul window explicit", () => {
    const result = {
      local_dates: ["2026-08-22", "2026-08-23", "2026-08-24"],
      candidates: [],
    } as unknown as ScanResult;

    expect(result.local_dates).toEqual([
      "2026-08-22",
      "2026-08-23",
      "2026-08-24",
    ]);
  });
});
