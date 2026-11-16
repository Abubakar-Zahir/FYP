import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { LoginPanel } from "./login-panel";

const push = vi.fn();
const auth = {
  signInWithPassword: vi.fn(),
  signInWithOAuth: vi.fn(),
  signUp: vi.fn(),
};

vi.mock("next/navigation", () => ({ useRouter: () => ({ push }) }));
vi.mock("@/lib/auth/supabase", () => ({
  getSupabase: () => ({ auth }),
  authCallbackUrl: () => "http://localhost:3000/auth/callback",
}));

async function fillAndSignIn() {
  await userEvent.type(screen.getByLabelText("Email"), "ayesha@example.com");
  await userEvent.type(screen.getByLabelText("Password"), "password123");
  await userEvent.click(screen.getByRole("button", { name: "Sign in" }));
}

describe("LoginPanel with Supabase", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    render(<LoginPanel />);
  });

  it("signs in and goes to onboarding", async () => {
    auth.signInWithPassword.mockResolvedValue({ data: {}, error: null });

    await fillAndSignIn();

    await waitFor(() => expect(push).toHaveBeenCalledWith("/onboarding"));
    expect(auth.signInWithPassword).toHaveBeenCalledWith({ email: "ayesha@example.com", password: "password123" });
  });

  it("offers to create an account after wrong credentials", async () => {
    auth.signInWithPassword.mockResolvedValue({ data: {}, error: { code: "invalid_credentials" } });
    auth.signUp.mockResolvedValue({ data: { session: null }, error: null });

    await fillAndSignIn();
    await userEvent.click(await screen.findByRole("button", { name: "Create account with this email" }));

    expect(await screen.findByText(/Check your inbox/)).toBeInTheDocument();
    expect(auth.signUp).toHaveBeenCalledWith({
      email: "ayesha@example.com",
      password: "password123",
      options: { emailRedirectTo: "http://localhost:3000/auth/callback" },
    });
    expect(push).not.toHaveBeenCalled();
  });

  it("sends Google sign-in back to the callback page", async () => {
    auth.signInWithOAuth.mockResolvedValue({ data: {}, error: null });

    await userEvent.click(screen.getByRole("button", { name: "Continue with Google" }));

    expect(auth.signInWithOAuth).toHaveBeenCalledWith({
      provider: "google",
      options: { redirectTo: "http://localhost:3000/auth/callback" },
    });
  });
});
