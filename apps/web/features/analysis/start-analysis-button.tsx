"use client";

import { useRouter } from "next/navigation";
import { useStartAnalysis } from "./use-analysis";

export function StartAnalysisButton({
  fixtureId,
  children = "ANALİZİ BAŞLAT",
}: {
  fixtureId: string;
  children?: string;
}) {
  const router = useRouter();
  const start = useStartAnalysis();
  return (
    <button
      type="button"
      disabled={start.isPending}
      onClick={() =>
        start.mutate(fixtureId, {
          onSuccess: (run) => router.push(`/runs/${run.run_id}`),
        })
      }
    >
      {start.isPending ? "HAZIRLANIYOR…" : children}
    </button>
  );
}
