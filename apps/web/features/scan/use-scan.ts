"use client";

import { useMutation } from "@tanstack/react-query";
import type { ScanResult } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function useScan() {
  return useMutation({
    mutationFn: async (): Promise<ScanResult> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/scans`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({
          timezone: "Europe/Istanbul",
          ui_config_version: "dashboard.v1",
        }),
      });
      if (!response.ok) throw new Error(`SCAN_FAILED_${response.status}`);
      return response.json() as Promise<ScanResult>;
    },
  });
}
