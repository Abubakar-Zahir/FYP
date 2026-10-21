"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "./client";
import type {
  AnalyticsOverview,
  CommentSummary,
  CommentTheme,
  DnaRecord,
  EditOptions,
  Experiment,
  GenerateScriptRequest,
  Job,
  JobAccepted,
  Me,
  Page,
  Profile,
  Reel,
  Script,
  WeeklyReport,
} from "./types";

const JOB_POLL_INTERVAL_MS = 1000;

export const queryKeys = {
  me: ["me"] as const,
  reels: ["reels"] as const,
  overview: ["analytics", "overview"] as const,
  dna: ["dna"] as const,
  dnaRecord: (id: string) => ["dna", id] as const,
  script: (id: string) => ["scripts", id] as const,
  job: (id: string) => ["jobs", id] as const,
  experiment: (id: string) => ["experiments", id] as const,
  commentThemes: ["comments", "themes"] as const,
  commentSummary: ["comments", "summary"] as const,
  weeklyReport: ["reports", "weekly"] as const,
};

export function useMe() {
  return useQuery({ queryKey: queryKeys.me, queryFn: () => apiGet<Me>("/me") });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (profile: Profile) => apiSend<Me>("PUT", "/me/profile", profile),
    onSuccess: (me) => queryClient.setQueryData(queryKeys.me, me),
  });
}

/**
 * The real endpoint starts an OAuth redirect (docs/backend.md). The prototype mock
 * answers with the connected account instead, so the flow can be clicked through.
 */
export function useConnectInstagram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiGet<Me>("/instagram/connect"),
    onSuccess: (me) => queryClient.setQueryData(queryKeys.me, me),
  });
}

export function useReels() {
  return useQuery({ queryKey: queryKeys.reels, queryFn: () => apiGet<Page<Reel>>("/reels?limit=10") });
}

export function useAnalyticsOverview() {
  return useQuery({ queryKey: queryKeys.overview, queryFn: () => apiGet<AnalyticsOverview>("/analytics/overview") });
}

export function useDnaRecords() {
  return useQuery({ queryKey: queryKeys.dna, queryFn: () => apiGet<Page<DnaRecord>>("/dna") });
}

export function useDnaRecord(id: string) {
  return useQuery({ queryKey: queryKeys.dnaRecord(id), queryFn: () => apiGet<DnaRecord>(`/dna/${id}`) });
}

export function useSaveTemplate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => apiSend<DnaRecord>("POST", `/dna/${id}/save-template`),
    onSuccess: (record) => {
      queryClient.setQueryData(queryKeys.dnaRecord(record.id), record);
      return queryClient.invalidateQueries({ queryKey: queryKeys.dna });
    },
  });
}

/** Polls a job until it reaches `done` or `failed` (frontend.md, data rule 3). */
export function useJob<TResult>(jobId: string | null) {
  return useQuery({
    queryKey: queryKeys.job(jobId ?? "none"),
    queryFn: () => apiGet<Job<TResult>>(`/jobs/${jobId}`),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "done" || status === "failed" ? false : JOB_POLL_INTERVAL_MS;
    },
  });
}

export function useStartJob<TInput>(path: string) {
  return useMutation({
    mutationFn: (input: TInput) => apiSend<JobAccepted>("POST", path, input),
  });
}

export function useGenerateScript() {
  return useStartJob<GenerateScriptRequest>("/scripts/generate");
}

export function useStartEdit(videoId: string) {
  return useStartJob<EditOptions>(`/videos/${videoId}/edit`);
}

export function useScript(id: string | null) {
  return useQuery({
    queryKey: queryKeys.script(id ?? "none"),
    queryFn: () => apiGet<Script>(`/scripts/${id}`),
    enabled: id !== null,
  });
}

export function useExperiment(id: string) {
  return useQuery({ queryKey: queryKeys.experiment(id), queryFn: () => apiGet<Experiment>(`/experiments/${id}`) });
}

export function usePublishExperiment(id: string) {
  return useStartJob<void>(`/experiments/${id}/publish`);
}

export function useShareWinner(id: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiSend<Experiment>("POST", `/experiments/${id}/share-winner`),
    onSuccess: (experiment) => queryClient.setQueryData(queryKeys.experiment(id), experiment),
  });
}

export function useCommentThemes() {
  return useQuery({ queryKey: queryKeys.commentThemes, queryFn: () => apiGet<Page<CommentTheme>>("/comments/themes") });
}

export function useCommentSummary() {
  return useQuery({ queryKey: queryKeys.commentSummary, queryFn: () => apiGet<CommentSummary>("/comments/summary") });
}

export function useSyncComments() {
  return useStartJob<void>("/comments/sync");
}

export function useWeeklyReport() {
  return useQuery({ queryKey: queryKeys.weeklyReport, queryFn: () => apiGet<WeeklyReport>("/reports/weekly") });
}
