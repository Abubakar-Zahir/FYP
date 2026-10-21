"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useEffect, useState, type ReactNode } from "react";

import { LoadingScreen } from "@/components/ui/states";

const USE_MOCKS = process.env.NEXT_PUBLIC_USE_MOCKS !== "false";
const STALE_TIME_MS = 30_000;

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { staleTime: STALE_TIME_MS, retry: 1, refetchOnWindowFocus: false },
    },
  });
}

/**
 * Starts the MSW worker before any query runs, so the first requests are
 * mocked instead of hitting a backend that does not exist yet.
 */
function useMockWorker(): boolean {
  const [ready, setReady] = useState(!USE_MOCKS);

  useEffect(() => {
    if (!USE_MOCKS) return;
    let cancelled = false;
    import("@/lib/mocks/browser")
      .then(({ worker }) => worker.start({ onUnhandledRequest: "bypass", quiet: true }))
      .then(() => {
        if (!cancelled) setReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  return ready;
}

export function Providers({ children }: { children: ReactNode }) {
  const [queryClient] = useState(createQueryClient);
  const mocksReady = useMockWorker();

  return (
    <QueryClientProvider client={queryClient}>{mocksReady ? children : <LoadingScreen />}</QueryClientProvider>
  );
}
