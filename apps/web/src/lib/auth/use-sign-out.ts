"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useCallback } from "react";

import { getSupabase } from "./supabase";

export function useSignOut(): () => Promise<void> {
  const router = useRouter();
  const queryClient = useQueryClient();
  return useCallback(async () => {
    await getSupabase()?.auth.signOut();
    queryClient.clear();
    router.replace("/login");
  }, [queryClient, router]);
}
