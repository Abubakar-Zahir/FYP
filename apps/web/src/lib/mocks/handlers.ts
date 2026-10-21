import { delay, http, HttpResponse, type JsonBodyType } from "msw";

import type {
  ApiError,
  EditResult,
  Experiment,
  GenerateScriptRequest,
  Job,
  Me,
  Page,
  Profile,
  Script,
} from "@/lib/api/types";

import {
  buildScript,
  commentSummaryFixture,
  commentThemesFixture,
  connectedInstagram,
  dnaFixture,
  experimentFixture,
  experimentInsights,
  meFixture,
  overviewFixture,
  reelsFixture,
  weeklyReportFixture,
} from "./fixtures";
import { readMockScenario } from "./scenario";

const API = "*/api/v1";
const NETWORK_DELAY_MS = 450;
const SLOW_DELAY_MS = 4000;

const JOB_DURATION_MS = {
  script: 3500,
  edit: 6000,
  publish: 5000,
  commentSync: 3000,
} as const;

type MockJob = {
  type: string;
  startedAt: number;
  durationMs: number;
  result: unknown;
  onDone?: () => void;
};

const jobs = new Map<string, MockJob>();
const scripts = new Map<string, Script>();
let me: Me = structuredClone(meFixture);
let experiment: Experiment = structuredClone(experimentFixture);
const dnaRecords = structuredClone(dnaFixture);

let idCounter = 0;
function nextId(prefix: string): string {
  idCounter += 1;
  return `${prefix}_${Date.now().toString(36)}${idCounter}`;
}

function errorBody(code: string, message: string): ApiError {
  return { error: { code, message, details: {} } };
}

async function networkDelay(): Promise<void> {
  await delay(readMockScenario() === "slow" ? SLOW_DELAY_MS : NETWORK_DELAY_MS);
}

/** Applies the reviewer's chosen scenario, then answers with `body`. */
async function respond(body: JsonBodyType, init?: { status?: number }) {
  await networkDelay();
  if (readMockScenario() === "error") {
    return HttpResponse.json(errorBody("upstream_unavailable", "The service did not respond. Try again."), {
      status: 503,
    });
  }
  return HttpResponse.json(body, init);
}

function pageOf<T>(items: T[]): Page<T> {
  return { items: readMockScenario() === "empty" ? [] : items, next_cursor: null };
}

function startJob(type: string, durationMs: number, result: unknown, onDone?: () => void) {
  const id = nextId("job");
  jobs.set(id, { type, startedAt: Date.now(), durationMs, result, onDone });
  return respond({ job_id: id }, { status: 202 });
}

function jobSnapshot(id: string, job: MockJob): Job {
  const progress = Math.min(1, (Date.now() - job.startedAt) / job.durationMs);
  if (progress < 1) {
    return { id, type: job.type, status: progress < 0.1 ? "queued" : "running", progress, result: null, error: null };
  }
  job.onDone?.();
  job.onDone = undefined;
  return { id, type: job.type, status: "done", progress: 1, result: job.result, error: null };
}

function publishVariants(): void {
  experiment = {
    ...experiment,
    winner_variant_id: "var_c",
    variants: experiment.variants.map((variant) => ({
      ...variant,
      status: "live",
      insights: experimentInsights[variant.id] ?? [],
    })),
  };
}

export const handlers = [
  http.get(`${API}/me`, () => respond(me)),

  http.put(`${API}/me/profile`, async ({ request }) => {
    const profile = (await request.json()) as Profile;
    me = { ...me, profile };
    return respond(me);
  }),

  http.get(`${API}/instagram/connect`, () => {
    me = { ...me, instagram: connectedInstagram };
    return respond(me);
  }),

  http.get(`${API}/reels`, () => respond(pageOf(reelsFixture))),

  http.get(`${API}/analytics/overview`, () => {
    const empty = readMockScenario() === "empty";
    const zero = { views: 0, reach: 0, saves: 0, shares: 0, avg_watch_time_s: 0 };
    return respond(empty ? { ...overviewFixture, totals: zero, change: zero, trend: [], best_formats: [] } : overviewFixture);
  }),

  http.get(`${API}/dna`, () => respond(pageOf(dnaRecords))),

  http.get(`${API}/dna/:id`, ({ params }) => {
    const record = dnaRecords.find((item) => item.id === params.id);
    if (!record) {
      return HttpResponse.json(errorBody("not_found", "This DNA record does not exist."), { status: 404 });
    }
    return respond(record);
  }),

  http.post(`${API}/dna/:id/save-template`, ({ params }) => {
    const record = dnaRecords.find((item) => item.id === params.id);
    if (!record) {
      return HttpResponse.json(errorBody("not_found", "This DNA record does not exist."), { status: 404 });
    }
    record.is_template = true;
    return respond(record);
  }),

  http.post(`${API}/scripts/generate`, async ({ request }) => {
    const input = (await request.json()) as GenerateScriptRequest;
    const scriptId = nextId("scr");
    scripts.set(scriptId, buildScript(scriptId, input.template_id, input.topic, input.language));
    return startJob("scripts.generate", JOB_DURATION_MS.script, { script_id: scriptId });
  }),

  http.get(`${API}/scripts/:id`, ({ params }) => {
    const script = scripts.get(String(params.id));
    if (!script) {
      return HttpResponse.json(errorBody("not_found", "Script not found."), { status: 404 });
    }
    return respond(script);
  }),

  http.post(`${API}/videos/:id/edit`, () => {
    const result: EditResult = { output_url: "mock://edited.mp4", duration_s: 27, removed_silence_s: 6.4 };
    return startJob("videos.edit", JOB_DURATION_MS.edit, result);
  }),

  http.get(`${API}/experiments/:id`, () => respond(experiment)),

  http.post(`${API}/experiments/:id/publish`, () => {
    experiment = {
      ...experiment,
      variants: experiment.variants.map((variant) => ({ ...variant, status: "publishing" })),
    };
    return startJob("experiments.publish", JOB_DURATION_MS.publish, { experiment_id: experiment.id }, publishVariants);
  }),

  http.post(`${API}/experiments/:id/share-winner`, () => respond(experiment)),

  http.get(`${API}/comments/themes`, () => respond(pageOf(commentThemesFixture))),

  http.get(`${API}/comments/summary`, () => {
    const empty = readMockScenario() === "empty";
    return respond(empty ? { ...commentSummaryFixture, total: 0, by_label: [] } : commentSummaryFixture);
  }),

  http.post(`${API}/comments/sync`, () => startJob("comments.sync", JOB_DURATION_MS.commentSync, { synced: 48 })),

  http.get(`${API}/reports/weekly`, () => {
    const empty = readMockScenario() === "empty";
    return respond(empty ? { ...weeklyReportFixture, wins: [], losses: [], themes: [], ideas: [] } : weeklyReportFixture);
  }),

  http.get(`${API}/jobs/:id`, ({ params }) => {
    const id = String(params.id);
    const job = jobs.get(id);
    if (!job) {
      return HttpResponse.json(errorBody("not_found", "Job not found."), { status: 404 });
    }
    return respond(jobSnapshot(id, job));
  }),
];
