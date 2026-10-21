import type { Metadata } from "next";

import { CommentSummaryCard } from "@/components/comments/comment-summary-card";
import { CommentThemes } from "@/components/comments/comment-themes";
import { SyncCommentsButton } from "@/components/comments/sync-comments-button";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Comments · Reelmind" };

export default function CommentsPage() {
  return (
    <>
      <PageHeader
        eyebrow="Comment intelligence"
        title="Comments"
        description="English, Urdu and Roman Urdu comments, classified and grouped into themes you can turn into videos."
        actions={<SyncCommentsButton />}
      />
      <div className="grid items-start gap-4 xl:grid-cols-[20rem_1fr]">
        <CommentSummaryCard />
        <CommentThemes />
      </div>
    </>
  );
}
