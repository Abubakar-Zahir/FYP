import type { BadgeTone } from "@/components/ui/badge";
import type { CommentLabel, HookType } from "@/lib/api/types";

export const HOOK_TYPE_LABEL: Record<HookType, string> = {
  question: "Question",
  bold_claim: "Bold claim",
  pattern_interrupt: "Pattern interrupt",
  story: "Story",
  list: "List",
  other: "Other",
};

export const COMMENT_LABEL: Record<CommentLabel, { label: string; tone: BadgeTone }> = {
  question: { label: "Question", tone: "accent" },
  request: { label: "Request", tone: "accent" },
  praise: { label: "Praise", tone: "success" },
  objection: { label: "Objection", tone: "warning" },
  complaint: { label: "Complaint", tone: "danger" },
  spam: { label: "Spam", tone: "neutral" },
};

/** Outlier score is views relative to the account median (FR-2.4). 1.0 means a typical reel. */
export function outlierTone(score: number): BadgeTone {
  if (score >= 2) return "success";
  if (score >= 1) return "accent";
  return "neutral";
}
