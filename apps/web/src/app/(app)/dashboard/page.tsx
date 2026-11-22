import type { Metadata } from "next";

import { BestFormats } from "@/components/dashboard/best-formats";
import { OverviewStats } from "@/components/dashboard/overview-stats";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentReels } from "@/components/dashboard/recent-reels";
import { ViewsTrend } from "@/components/dashboard/views-trend";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Dashboard · Reelmind" };

export default function DashboardPage() {
  return (
    <>
      <PageHeader eyebrow="Last 30 days" title="Dashboard" description="How your reels are doing and what to make next." actions={<QuickActions />} />
      <div className="space-y-4">
        <OverviewStats />
        <div className="grid gap-4 xl:grid-cols-3">
          <ViewsTrend className="xl:col-span-2" />
          <BestFormats />
        </div>
        <RecentReels />
      </div>
    </>
  );
}
