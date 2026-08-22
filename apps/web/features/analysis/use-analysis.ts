"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { AnalysisEvidenceDossier, AnalysisRun } from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function useStartAnalysis() {
  return useMutation({
    mutationFn: async (fixtureId: string): Promise<AnalysisRun> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/analysis-runs`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": crypto.randomUUID(),
        },
        body: JSON.stringify({ fixture_id: fixtureId }),
      });
      if (!response.ok)
        throw new Error(`ANALYSIS_START_FAILED_${response.status}`);
      return response.json() as Promise<AnalysisRun>;
    },
  });
}

export function useAnalysisRun(runId: string) {
  return useQuery({
    queryKey: ["analysis-run", runId],
    queryFn: async (): Promise<AnalysisRun> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/analysis-runs/${runId}`,
      );
      if (!response.ok)
        throw new Error(`ANALYSIS_LOAD_FAILED_${response.status}`);
      return response.json() as Promise<AnalysisRun>;
    },
  });
}

export function useAnalysisEvidence(runId: string) {
  return useQuery({
    queryKey: ["analysis-evidence", runId],
    queryFn: async (): Promise<AnalysisEvidenceDossier> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/analysis-runs/${runId}/evidence`,
      );
      if (!response.ok)
        throw new Error(`ANALYSIS_EVIDENCE_LOAD_FAILED_${response.status}`);
      return response.json() as Promise<AnalysisEvidenceDossier>;
    },
  });
}

export function useLockAnalysis(runId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<AnalysisRun> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/analysis-runs/${runId}/lock`,
        { method: "POST" },
      );
      if (!response.ok) throw new Error(`LOCK_FAILED_${response.status}`);
      return response.json() as Promise<AnalysisRun>;
    },
    onSuccess: (data) =>
      queryClient.setQueryData(["analysis-run", runId], data),
  });
}
