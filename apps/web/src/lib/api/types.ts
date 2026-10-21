/*
 * Planned API shapes from docs/backend.md, used by the prototype and its mocks.
 * Once the FastAPI schemas exist, this file is replaced by types generated with
 * openapi-typescript (rules.md 4.5). Keep field names in snake_case to match.
 */

export type ApiError = {
  error: { code: string; message: string; details: Record<string, unknown> };
};

export type Page<T> = { items: T[]; next_cursor: string | null };

export type JobStatus = "queued" | "running" | "done" | "failed";

export type Job<TResult = unknown> = {
  id: string;
  type: string;
  status: JobStatus;
  progress: number;
  result: TResult | null;
  error: string | null;
};

export type JobAccepted = { job_id: string };

export type Role = "creator" | "brand";
export type Language = "english" | "urdu" | "roman_urdu";
export type ScriptLanguage = "english" | "roman_urdu" | "mixed";

export type Profile = {
  role: Role;
  niche: string;
  language_mix: Language[];
  tone: string;
  goals: string;
};

export type Me = {
  id: string;
  name: string;
  email: string;
  profile: Profile | null;
  instagram: { username: string; account_type: string; trial_reels_eligible: boolean } | null;
};

export type Reel = {
  id: string;
  caption: string;
  posted_at: string;
  hook_type: HookType | null;
  views: number;
  saves: number;
  shares: number;
  avg_watch_time_s: number;
  outlier_score: number;
};

export type TrendPoint = { date: string; views: number };

export type FormatPerformance = { hook_type: HookType; reels: number; median_outlier: number };

export type AnalyticsOverview = {
  period_days: number;
  totals: { views: number; reach: number; saves: number; shares: number; avg_watch_time_s: number };
  change: { views: number; reach: number; saves: number; shares: number; avg_watch_time_s: number };
  trend: TrendPoint[];
  best_formats: FormatPerformance[];
};

export type HookType =
  | "question"
  | "bold_claim"
  | "pattern_interrupt"
  | "story"
  | "list"
  | "other";

export type DnaBeat = { label: string; start_s: number; end_s: number; description: string };

export type DnaOverlay = { at_s: number; text: string };

export type DnaRecord = {
  id: string;
  schema_version: string;
  title: string;
  source: "own" | "reference";
  hook_type: HookType;
  hook_text: string;
  pacing_cuts_per_10s: number;
  length_s: number;
  beats: DnaBeat[];
  overlays: DnaOverlay[];
  cta: string;
  outlier_score: number;
  transcript: string;
  is_template: boolean;
};

export type ScoreFactor = { label: string; impact: number };

export type ScoredHook = { text: string; score: number; top_factors: ScoreFactor[] };

export type ScriptBeat = { beat: string; line: string; shot: string };

export type Script = {
  id: string;
  template_id: string;
  topic: string;
  language: ScriptLanguage;
  hooks: ScoredHook[];
  angles: { title: string; summary: string }[];
  body: ScriptBeat[];
  model_version: string;
};

export type GenerateScriptRequest = {
  template_id: string;
  topic: string;
  language: ScriptLanguage;
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
