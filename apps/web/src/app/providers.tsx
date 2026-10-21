"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, type ReactNode } from "react";

import { holdRequestsUntil } from "@/lib/api/client";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const STALE_TIME_MS = 30_000;

/*
 * Pages render right away (Next validates every segment for instant navigation),
 * and only the API requests wait for the MSW worker. Started at module load, once,
 * because Strict Mode runs effects twice and a second worker.start() throws.
 */
if (USE_MOCKS && typeof window !== "undefined") {
  holdRequestsUntil(
    import("@/lib/mocks/browser").then(({ worker }) => worker.start({ onUnhandledRequest: "bypass", quiet: true })),
  );
}

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: STALE_TIME_MS, retry: 1, refetchOnWindowFocus: false },
    },
  });
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>;
}
