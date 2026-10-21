"use client";

import { useEffect, useRef, useState } from "react";

export const MAX_DURATION_S = 90;
const MAX_SIZE_BYTES = 500 * 1024 * 1024;
const UPLOAD_TICK_MS = 120;
const UPLOAD_STEP = 0.06;

export type UploadState =
  | { status: "idle" }
  | { status: "uploading"; fileName: string; progress: number; previewUrl: string | null }
  | { status: "uploaded"; fileName: string; previewUrl: string | null; durationS: number }
  | { status: "invalid"; message: string };

function readVideoMetadata(url: string): Promise<{ durationS: number; vertical: boolean }> {
  return new Promise((resolve, reject) => {
    const video = document.createElement("video");
    video.preload = "metadata";
    video.onloadedmetadata = () =>
      resolve({ durationS: video.duration, vertical: video.videoHeight >= video.videoWidth });
    video.onerror = () => reject(new Error("This file could not be read as a video."));
    video.src = url;
  });
}

/**
 * Validates the file locally (rules.md 6.3: type, size, duration) and fakes the
 * presigned R2 upload with a progress timer. P1 swaps the timer for a real PUT.
 */
export function useMockUpload() {
  const [state, setState] = useState<UploadState>({ status: "idle" });
  const timerRef = useRef<number | null>(null);
  const urlRef = useRef<string | null>(null);

  useEffect(
    () => () => {
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
      if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    },
    [],
  );

  function simulateUpload(fileName: string, previewUrl: string | null, durationS: number) {
    let progress = 0;
    setState({ status: "uploading", fileName, progress, previewUrl });
    timerRef.current = window.setInterval(() => {
      progress = Math.min(1, progress + UPLOAD_STEP);
      if (progress < 1) {
        setState({ status: "uploading", fileName, progress, previewUrl });
        return;
      }
      if (timerRef.current !== null) window.clearInterval(timerRef.current);
      setState({ status: "uploaded", fileName, previewUrl, durationS });
    }, UPLOAD_TICK_MS);
  }

  async function uploadFile(file: File) {
    if (!file.type.startsWith("video/")) {
      setState({ status: "invalid", message: "Upload an MP4 or MOV video." });
      return;
    }
    if (file.size > MAX_SIZE_BYTES) {
      setState({ status: "invalid", message: "This file is over 500 MB." });
      return;
    }
    if (urlRef.current) URL.revokeObjectURL(urlRef.current);
    const url = URL.createObjectURL(file);
    urlRef.current = url;
    try {
      const { durationS, vertical } = await readVideoMetadata(url);
      if (durationS > MAX_DURATION_S) {
        setState({ status: "invalid", message: `Clips can be up to ${MAX_DURATION_S} s. This one is ${Math.round(durationS)} s.` });
        return;
      }
      if (!vertical) {
        setState({ status: "invalid", message: "Use vertical (9:16) footage." });
        return;
      }
      simulateUpload(file.name, url, durationS);
    } catch (error) {
      setState({ status: "invalid", message: error instanceof Error ? error.message : "Could not read this video." });
    }
  }

  function loadSampleClip() {
    simulateUpload("sample-samosa-chaat.mp4", null, 34);
  }

  function reset() {
    if (timerRef.current !== null) window.clearInterval(timerRef.current);
    setState({ status: "idle" });
  }

  return { state, uploadFile, loadSampleClip, reset };
}
