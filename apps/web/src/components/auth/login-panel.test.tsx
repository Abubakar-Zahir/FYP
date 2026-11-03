import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPanel } from "./login-panel";

const push = vi.fn();

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));

async function submit(email: string, password: string) {
  if (email) await userEvent.type(screen.getByLabelText("Email"), email);
  if (password) await userEvent.type(screen.getByLabelText("Password"), password);
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

describe("LoginPanel", () => {
  beforeEach(() => {
    push.mockClear();
    render(<LoginPanel />);
  });

  it("rejects an invalid email", async () => {
    await submit("not-an-email", "password123");

    expect(await screen.findByText("Enter a valid email address")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("rejects a short password", async () => {
    await submit("ayesha@example.com", "short");

    expect(await screen.findByText("Use at least 8 characters")).toBeInTheDocument();
    expect(push).not.toHaveBeenCalled();
  });

  it("continues with valid details", async () => {
    await submit("ayesha@example.com", "password123");

    await waitFor(() => expect(push).toHaveBeenCalledWith("/onboarding"));
  });

  it("continues with Google without the form", async () => {
    await userEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

    expect(push).toHaveBeenCalledWith("/onboarding");
  });

  it("can never put the password in the URL", () => {
    expect(screen.getByLabelText("Email").closest("form")).toHaveAttribute("method", "post");
  });
});
