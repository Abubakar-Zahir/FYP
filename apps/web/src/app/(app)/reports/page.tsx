import type { Metadata } from "next";

import { WeeklyReportView } from "@/components/reports/weekly-report-view";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Weekly report · Reelmind" };

export default function ReportsPage() {
  return (
    <>
      <PageHeader eyebrow="Every Monday" title="Weekly report" description="Wins, losses, what your comments asked for, and 5 ideas for next week." />
      <WeeklyReportView />
    </>
  );
}
