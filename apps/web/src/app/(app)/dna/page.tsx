import type { Metadata } from "next";

import { DnaLibrary } from "@/components/dna/dna-library";
import { UploadReferenceButton } from "@/components/dna/upload-reference-button";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "DNA library · Reelmind" };

export default function DnaLibraryPage() {
  return (
    <>
      <PageHeader
        eyebrow="Format DNA"
        title="DNA library"
        description="Every analysed reel broken into hook, pacing, beats and CTA. Save the ones you want to reuse as templates."
        actions={<UploadReferenceButton />}
      />
      <DnaLibrary />
    </>
  );
}
