/*
 * Shapes for screens whose endpoints don't exist yet (Phase 2 and 3: analytics, editing,
 * variants, comments, weekly report). Only the prototype mocks use them. When an endpoint
 * ships, delete its type here and alias the generated one in types.ts (rules.md 4.5).
 */

import type { HookType } from "./types";

export type TrendPoint = { date: string; views: number };

export type FormatPerformance = { hook_type: HookType; reels: number; median_outlier: number };

export type AnalyticsOverview = {
  period_days: number;
  totals: { views: number; reach: number; saves: number; shares: number; avg_watch_time_s: number };
  change: { views: number; reach: number; saves: number; shares: number; avg_watch_time_s: number };
  trend: TrendPoint[];
  best_formats: FormatPerformance[];
};

export type CaptionStyle = "bold_pop" | "karaoke" | "minimal" | "boxed";

export type EditOptions = {
  caption_style: CaptionStyle;
  cut_silences: boolean;
  progress_bar: boolean;
  hook_overlay: boolean;
};

export type EditResult = { output_url: string; duration_s: number; removed_silence_s: number };

export type VariantStatus = "draft" | "publishing" | "live" | "failed";

export type VariantInsight = { window: "24h" | "72h"; views: number; reach: number; saves: number; shares: number };

export type Variant = {
  id: string;
  label: string;
  hook_line: string;
  opener: string;
  caption: string;
  is_trial: boolean;
  status: VariantStatus;
  insights: VariantInsight[];
};

export type Experiment = {
  id: string;
  video_title: string;
  strategy: "thompson_sampling";
  winner_variant_id: string | null;
  variants: Variant[];
};

export type CommentLabel = "question" | "request" | "praise" | "objection" | "complaint" | "spam";

export type CommentTheme = {
  id: string;
  theme: string;
  size: number;
  dominant_label: CommentLabel;
  examples: string[];
  idea: string;
};

export type CommentSummary = {
  total: number;
  period_days: number;
  by_label: { label: CommentLabel; count: number }[];
};

export type WeeklyReport = {
  week_start: string;
  headline: string;
  wins: { title: string; detail: string }[];
  losses: { title: string; detail: string }[];
  themes: string[];
  ideas: { title: string; why: string }[];
};
