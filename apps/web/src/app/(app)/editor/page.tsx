import type { Metadata } from "next";

import { VideoEditor } from "@/components/editor/video-editor";
import { PageHeader } from "@/components/ui/page-header";

export const metadata: Metadata = { title: "Editor · Reelmind" };

export default function EditorPage() {
  return (
    <>
      <PageHeader
        eyebrow="Auto-edit"
        title="Editor"
        description="Upload raw vertical footage. We add word-level captions, cut silences and render a preview."
      />
      <VideoEditor />
    </>
  );
}
