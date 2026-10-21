import { Clapperboard, PenLine } from "lucide-react";

import { ButtonLink } from "@/components/ui/button";

export function QuickActions() {
  return (
    <>
      <ButtonLink href="/editor" variant="secondary">
        <Clapperboard aria-hidden />
        Edit a video
      </ButtonLink>
      <ButtonLink href="/studio">
        <PenLine aria-hidden />
        New script
      </ButtonLink>
    </>
  );
}
