import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type { Job } from "@/lib/api/types";

import { JobProgress } from "./job-progress";

function job(overrides: Partial<Job>): Job {
  return { id: "job_1", type: "test", status: "running", progress: 0.42, result: null, error: null, ...overrides };
}

describe("JobProgress", () => {
  it("shows queued before the job data arrives", () => {
    render(<JobProgress label="Rendering" job={undefined} onRetry={vi.fn()} />);

    expect(screen.getByText("Queued")).toBeInTheDocument();
  });

  it("shows running progress", () => {
    render(<JobProgress label="Rendering" job={job({})} onRetry={vi.fn()} />);

    expect(screen.getByText(/Running · 42%/)).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "42");
  });

  it("offers no retry while the job is healthy", () => {
    render(<JobProgress label="Rendering" job={job({})} onRetry={vi.fn()} />);

    expect(screen.queryByRole("button", { name: "Retry" })).not.toBeInTheDocument();
  });

  it("shows the job error and retries on click", async () => {
    const onRetry = vi.fn();
    render(<JobProgress label="Rendering" job={job({ status: "failed", error: "FFmpeg crashed" })} onRetry={onRetry} />);

    expect(screen.getByText("FFmpeg crashed")).toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Retry" }));

    expect(onRetry).toHaveBeenCalledOnce();
  });

  it("treats a failed status request as a failure", () => {
    render(<JobProgress label="Rendering" job={job({})} requestError={new Error("Network down")} onRetry={vi.fn()} />);

    expect(screen.getByText("Failed")).toBeInTheDocument();
    expect(screen.getByText("Network down")).toBeInTheDocument();
  });
});
