import { AutoCouponDashboard } from "@/features/auto-coupon/auto-coupon-dashboard";

type AutoCouponResultPageProps = {
  params: Promise<{ runId: string }>;
};

export default async function AutoCouponResultPage({
  params,
}: AutoCouponResultPageProps) {
  const { runId } = await params;
  return <AutoCouponDashboard initialRunId={runId} />;
}
