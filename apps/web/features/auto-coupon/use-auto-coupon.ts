"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import type {
  AutoCouponPerformance,
  AutoCouponReadiness,
  AutoCouponRun,
} from "./types";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function readRun(runId: string): Promise<AutoCouponRun> {
  const response = await fetch(`${API_BASE_URL}/api/v1/auto-coupons/${runId}`);
  if (!response.ok) {
    throw new Error(`AUTO_COUPON_READ_FAILED_${response.status}`);
  }
  return response.json() as Promise<AutoCouponRun>;
}

export function useAutoCoupon(initialRunId?: string) {
  const readiness = useQuery({
    queryKey: ["auto-coupon-readiness"],
    queryFn: async (): Promise<AutoCouponReadiness> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auto-coupons/readiness`,
        {
          cache: "no-store",
        },
      );
      if (!response.ok) {
        throw new Error(`AUTO_COUPON_READINESS_FAILED_${response.status}`);
      }
      return response.json() as Promise<AutoCouponReadiness>;
    },
  });
  const savedRun = useQuery({
    queryKey: ["auto-coupon", initialRunId],
    queryFn: () => readRun(initialRunId ?? ""),
    enabled: Boolean(initialRunId),
  });
  const performance = useQuery({
    queryKey: ["auto-coupon-performance"],
    queryFn: async (): Promise<AutoCouponPerformance> => {
      const response = await fetch(
        `${API_BASE_URL}/api/v1/auto-coupons/performance`,
        { cache: "no-store" },
      );
      if (!response.ok) {
        throw new Error(`AUTO_COUPON_PERFORMANCE_FAILED_${response.status}`);
      }
      return response.json() as Promise<AutoCouponPerformance>;
    },
  });
  const createRun = useMutation({
    mutationFn: async (): Promise<AutoCouponRun> => {
      const response = await fetch(`${API_BASE_URL}/api/v1/auto-coupons`, {
        method: "POST",
        headers: { "Idempotency-Key": crypto.randomUUID() },
      });
      if (!response.ok) {
        const payload = (await response.json().catch(() => null)) as {
          detail?: { code?: string };
        } | null;
        throw new Error(
          payload?.detail?.code ?? `AUTO_COUPON_FAILED_${response.status}`,
        );
      }
      return response.json() as Promise<AutoCouponRun>;
    },
  });

  return {
    data: createRun.data ?? savedRun.data,
    readiness: readiness.data,
    performance: performance.data,
    error: createRun.error ?? savedRun.error,
    isError: createRun.isError || savedRun.isError,
    isPending:
      readiness.isPending ||
      createRun.isPending ||
      (Boolean(initialRunId) && savedRun.isPending),
    mutate: createRun.mutate,
  };
}
