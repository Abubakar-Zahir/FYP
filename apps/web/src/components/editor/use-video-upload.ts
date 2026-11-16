"use client";

import { useEffect, useRef, useState } from "react";

import { apiSend } from "@/lib/api/client";
import { isAcceptedVideo } from "@/lib/api/hooks";
import type { VideoUpload } from "@/lib/api/types";
import { USE_MOCKS } from "@/lib/config";

const SAMPLE_VIDEO_ID = "vid_sample";

export const MAX_DURATION_S = 90;
// rules.md 6.3. The API checks the size again, and the worker checks the length.
const MAX_SIZE_BYTES = 200 * 1024 * 1024;

export type UploadState =
  | { status: "idle" }
  | { status: "uploading"; fileName: string; progress: number; previewUrl: string | null }
  | { status: "uploaded"; fileName: string; previewUrl: string | null; durationS: number; videoId: string }
  | { status: "invalid"; message: string };

function readVideoMetadata(url: string): Promise<{ durationS: number; vertical: boolean }> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () => resolve({ durationS: video.duration, vertical: video.videoHeight >= video.videoWidth });
    video.onerror = () => reject(new Error("This file could not be read as a video."));
    video.src = url;
  });
}

/** XHR rather than fetch, because only XHR reports upload progress. */
function putWithProgress(upload: VideoUpload, file: File, onProgress: (fraction: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    request.open("PUT", upload.upload_url);
    Object.entries(upload.upload_headers).forEach(([name, value]) => request.setRequestHeader(name, value));
    request.upload.onprogress = (event) => event.lengthComputable && onProgress(event.loaded / event.total);
    request.onload = () => (request.status < 300 ? resolve() : reject(new Error("The upload did not finish. Try again.")));
    request.onerror = () => reject(new Error("The upload did not finish. Check your connection and try again."));
    request.send(file);
  });
}

/**
 * Checks the file in the browser first (type, size, 90 s, vertical), then uploads it straight
 * to storage with a presigned URL. The video never passes through the API.
 */
export function useVideoUpload() {
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const urlRef = useRef<string | null>(null);

  useEffect(() => () => {
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
  }, []);

  async function uploadFile(file: File) {
    if (!isAcceptedVideo(file)) return setState({ status: "invalid", message: "Upload an MP4 or MOV video." });
    if (file.size > MAX_SIZE_BYTES) return setState({ status: "invalid", message: "This file is over 200 MB." });
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    const previewUrl = URL.createObjectURL(file);
    urlRef.current = previewUrl;
    try {
      const { durationS, vertical } = await readVideoMetadata(previewUrl);
      if (durationS > MAX_DURATION_S) {
        return setState({ status: "invalid", message: `Clips can be up to ${MAX_DURATION_S} s. This one is ${Math.round(durationS)} s.` });
      }
      if (!vertical) return setState({ status: "invalid", message: "Use vertical (9:16) footage." });
      setState({ status: "uploading", fileName: file.name, progress: 0, previewUrl });
      const upload = await apiSend<VideoUpload>("POST", "/videos/upload-url", {
        filename: file.name,
        content_type: file.type,
        size_bytes: file.size,
      });
      await putWithProgress(upload, file, (progress) =>
        setState({ status: "uploading", fileName: file.name, progress, previewUrl }),
      );
      setState({ status: "uploaded", fileName: file.name, previewUrl, durationS, videoId: upload.video.id });
    } catch (error) {
      setState({ status: "invalid", message: error instanceof Error ? error.message : "Could not upload this video." });
    }
  }

  function reset() {
    setState({ status: "idle" });
  }

  /** Prototype only: the mock API accepts this id without a real file. */
  function loadSampleClip() {
    setState({ status: "uploaded", fileName: "sample-samosa-chaat.mp4", previewUrl: null, durationS: 34, videoId: SAMPLE_VIDEO_ID });
  }

  return { state, uploadFile, reset, loadSampleClip: USE_MOCKS ? loadSampleClip : undefined };
}
