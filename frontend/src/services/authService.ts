import { apiFetch, setTokens, clearTokens } from "@/lib/api";
import type { User, TokenResponse } from "@/types/auth";

export async function login(email: string, password: string): Promise<void> {
  const res = await apiFetch<TokenResponse>("/api/v1/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  setTokens(res.access_token, res.refresh_token);
}

export async function signup(
  email: string,
  password: string,
  fullName: string,
): Promise<void> {
  await apiFetch("/api/v1/auth/signup", {
    method: "POST",
    body: JSON.stringify({ email, password, full_name: fullName }),
  });
  await login(email, password);
}

export async function logout(): Promise<void> {
  try {
    await apiFetch("/api/v1/auth/logout", { method: "POST" });
  } finally {
    clearTokens();
  }
}

export async function getMe(): Promise<User> {
  return apiFetch<User>("/api/v1/users/me");
}
