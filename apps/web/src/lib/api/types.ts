/*
 * API types, generated from the FastAPI OpenAPI schema (rules.md 4.5). Do not hand-write
 * shapes here. Change the Pydantic schema, then run from the repo root:
 *   PYTHONPATH=apps/api:. uv run python apps/api/scripts/export_openapi.py apps/web/openapi.json
 *   pnpm --filter @fyp/web gen:api
 */

import type { components } from "./schema";

type Schemas = components["schemas"];

/** The error envelope every endpoint uses (rules.md 3b.3). FastAPI doesn't publish it in OpenAPI. */
export type ApiError = {
  error: { code: string; message: string; details: Record<string, unknown> };
};

/** Matches every generated `Page_*_` schema. */
export type Page<T> = { items: T[]; next_cursor: string | null };

export type JobStatus = Schemas["JobStatus"];
export type Job<TResult = unknown> = Omit<Schemas["JobOut"], "result"> & { result: TResult | null };
export type JobAccepted = Schemas["JobAccepted"];

export type Role = Schemas["Role"];
export type Language = Schemas["Language"];
export type ScriptLanguage = Schemas["ScriptLanguage"];
export type Profile = Schemas["Profile"];
export type Me = Schemas["MeResponse"];
export type InstagramAccount = Schemas["InstagramAccountOut"];
export type InstagramAuthorizeUrl = Schemas["InstagramAuthorizeUrl"];
export type InstagramCallback = Schemas["InstagramCallback"];
export type InstagramConnected = Schemas["InstagramConnected"];

export type Reel = Schemas["ReelOut"];
export type ReelSource = Schemas["ReelSource"];
export type ReferenceUploadRequest = Schemas["ReferenceUploadRequest"];
export type ReferenceUpload = Schemas["ReferenceUpload"];
export type VideoContentType = Schemas["VideoContentType"];

export type HookType = Schemas["HookType"];
export type DnaBeat = Schemas["Beat"];
export type DnaOverlay = Schemas["Overlay"];
export type DnaRecord = Schemas["DnaRecordOut"];
export type AnalyseRequest = Schemas["AnalyseRequest"];

export type ScoreFactor = Schemas["ScoreFactor"];
export type ScoredHook = Schemas["ScoredHook"];
export type ScriptBeat = Schemas["ScriptBeat"];
export type Script = Schemas["ScriptOut"];
export type GenerateScriptRequest = Schemas["GenerateScriptRequest"];

export type DnaCluster = Schemas["DnaClusterOut"];
export type HookScoreRequest = Schemas["HookScoreRequest"];

export type TrendPoint = Schemas["TrendPoint"];
export type FormatPerformance = Schemas["FormatPerformance"];
export type AnalyticsOverview = Schemas["AnalyticsOverview"];

export type CaptionStyle = Schemas["CaptionStyle"];
export type EditOptions = Schemas["EditRequest"];
/** A videos.edit job's `result` (apps/api/app/schemas/videos.py EditResult). Job results aren't in OpenAPI. */
export type EditResult = { output_url: string; duration_s: number; removed_silence_s: number };
export type Video = Schemas["VideoOut"];
export type VideoUpload = Schemas["VideoUpload"];

export type VariantStatus = Schemas["VariantStatus"];
export type VariantInsight = Schemas["VariantInsightOut"];
export type Variant = Schemas["VariantOut"];
export type Experiment = Schemas["ExperimentOut"];
export type ExperimentStatus = Schemas["ExperimentStatus"];
export type CreateExperimentRequest = Schemas["CreateExperimentRequest"];

export type CommentLabel = Schemas["CommentLabel"];
export type CommentTheme = Schemas["CommentThemeOut"];
export type CommentSummary = Schemas["CommentSummaryOut"];

export type WeeklyReport = Schemas["WeeklyReportContent"];
