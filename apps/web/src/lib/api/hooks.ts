"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiSend } from "./client";
import type {
  AnalyticsOverview,
  CommentSummary,
  CommentTheme,
  DnaRecord,
  EditOptions,
  CreateExperimentRequest,
  Experiment,
  GenerateScriptRequest,
  InstagramAuthorizeUrl,
  InstagramCallback,
  InstagramConnected,
  Job,
  JobAccepted,
  Me,
  Page,
  Profile,
  Reel,
  ReferenceUpload,
  Script,
  VideoContentType,
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
  experiments: ["experiments"] as const,
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

/** Gets Instagram's sign-in URL. The caller sends the browser there. */
export function useStartInstagramConnect() {
  return useMutation({ mutationFn: () => apiGet<InstagramAuthorizeUrl>("/instagram/connect") });
}

/** Finishes the OAuth flow from the callback page. It also starts the reel import job. */
export function useFinishInstagramConnect() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (callback: InstagramCallback) => apiSend<InstagramConnected>("POST", "/instagram/callback", callback),
    onSuccess: (connected) => {
      queryClient.setQueryData<Me>(queryKeys.me, (me) => (me ? { ...me, instagram: connected.instagram } : me));
      return queryClient.invalidateQueries({ queryKey: queryKeys.reels });
    },
  });
}

export function useDisconnectInstagram() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiSend<void>("DELETE", "/instagram/account"),
    onSuccess: () => {
      queryClient.setQueryData<Me>(queryKeys.me, (me) => (me ? { ...me, instagram: null } : me));
      return queryClient.invalidateQueries({ queryKey: queryKeys.reels });
    },
  });
}

export function useDeleteAccount() {
  return useMutation({ mutationFn: () => apiSend<void>("DELETE", "/me") });
}

const ACCEPTED_VIDEO_TYPES: readonly VideoContentType[] = ["video/mp4", "video/quicktime"];

export function isAcceptedVideo(file: File): file is File & { type: VideoContentType } {
  return ACCEPTED_VIDEO_TYPES.some((type) => type === file.type);
}

/**
 * Uploads a reference reel straight to storage, then starts its DNA analysis. The video never
 * passes through the API (apps/api/README.md, Reference reel upload).
 */
export function useUploadReference() {
  return useMutation({
    mutationFn: async (file: File & { type: VideoContentType }) => {
      const upload = await apiSend<ReferenceUpload>("POST", "/reels/reference", {
        filename: file.name,
        content_type: file.type,
        size_bytes: file.size,
      });
      const stored = await fetch(upload.upload_url, { method: "PUT", headers: upload.upload_headers, body: file });
      if (!stored.ok) {
        throw new Error("The upload did not finish. Check your connection and try again.");
      }
      return apiSend<JobAccepted>("POST", "/dna/analyse", { reel_id: upload.reel.id });
    },
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

/** The video id comes from the upload, so it is passed when the edit starts. */
export function useStartEdit() {
  return useMutation({
    mutationFn: ({ videoId, options }: { videoId: string; options: EditOptions }) =>
      apiSend<JobAccepted>("POST", `/videos/${videoId}/edit`, options),
  });
}

export function useCreateExperiment() {
  return useStartJob<CreateExperimentRequest>("/experiments");
}

export function useExperiments() {
  return useQuery({ queryKey: queryKeys.experiments, queryFn: () => apiGet<Page<Experiment>>("/experiments?limit=10") });
}

export function useAnalyseReel() {
  return useMutation({
    mutationFn: (reelId: string) => apiSend<JobAccepted>("POST", "/dna/analyse", { reel_id: reelId }),
  });
}

export function useBuildWeeklyReport() {
  return useStartJob<void>("/reports/weekly");
}

export function useScript(id: string | null) {
  return useQuery({
    queryKey: queryKeys.script(id ?? "none"),
    queryFn: () => apiGet<Script>(`/scripts/${id}`),
    enabled: id !== null,
  });
}

export function useExperiment(id: string | null) {
  return useQuery({
    queryKey: queryKeys.experiment(id ?? "none"),
    queryFn: () => apiGet<Experiment>(`/experiments/${id}`),
    enabled: id !== null,
  });
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
