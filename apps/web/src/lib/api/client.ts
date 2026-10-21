import type { ApiError } from "./types";

const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_BASE_URL ?? ""}/api/v1`;

let requestsReady: Promise<unknown> = Promise.resolve();

/** Lets the prototype hold every request until the MSW worker is intercepting. */
export function holdRequestsUntil(ready: Promise<unknown>): void {
  requestsReady = ready;
}

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.name = "ApiRequestError";
    this.status = status;
    this.code = code;
  }
}

function isApiError(body: unknown): body is ApiError {
  return typeof body === "object" && body !== null && "error" in body;
}

async function readError(response: Response): Promise<ApiRequestError> {
  const body: unknown = await response.json().catch(() => null);
  if (isApiError(body)) {
    return new ApiRequestError(response.status, body.error.code, body.error.message);
  }
  return new ApiRequestError(response.status, "unknown_error", response.statusText);
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  await requestsReady;
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    throw await readError(response);
  }
  return (await response.json()) as T;
}

export function apiGet<T>(path: string): Promise<T> {
  return apiRequest<T>(path);
}

export function apiSend<T>(method: "POST" | "PUT" | "DELETE", path: string, body?: unknown): Promise<T> {
  return apiRequest<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) });
}
