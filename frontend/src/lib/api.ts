/**
 * Lean fetch-based API client with in-memory + localStorage token handling
 * and automatic refresh-on-401. No axios; native fetch only.
 */

const TOKEN_KEY = "rs_access_token";
const REFRESH_KEY = "rs_refresh_token";

export function getAccessToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function setTokens(access: string, refresh: string): void {
  window.localStorage.setItem(TOKEN_KEY, access);
  window.localStorage.setItem(REFRESH_KEY, refresh);
}

export function clearTokens(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(REFRESH_KEY);
}

function getRefreshToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(REFRESH_KEY);
}

export class ApiError extends Error {
  status: number;
  code: string;
  constructor(status: number, message: string, code = "error") {
    super(message);
    this.status = status;
    this.code = code;
  }
}

async function refreshAccessToken(): Promise<boolean> {
  const refresh = getRefreshToken();
  if (!refresh) return false;
  const res = await fetch("/api/v1/auth/refresh", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refresh }),
  });
  if (!res.ok) return false;
  const data = await res.json();
  setTokens(data.access_token, data.refresh_token);
  return true;
}

interface RequestOptions extends RequestInit {
  /** Skip the retry-after-refresh path (used internally). */
  _retry?: boolean;
}

/** Perform an authenticated JSON request, refreshing once on 401. */
export async function apiFetch<T = unknown>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const token = getAccessToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  const res = await fetch(path, { ...options, headers });

  if (res.status === 401 && !options._retry) {
    const refreshed = await refreshAccessToken();
    if (refreshed) {
      return apiFetch<T>(path, { ...options, _retry: true });
    }
    clearTokens();
    throw new ApiError(401, "Session expired", "unauthorized");
  }

  if (!res.ok) {
    let detail = res.statusText;
    let code = "error";
    try {
      const body = await res.json();
      detail = body?.error?.detail ?? body?.detail ?? detail;
      code = body?.error?.code ?? code;
    } catch {
      /* non-JSON error body */
    }
    throw new ApiError(res.status, typeof detail === "string" ? detail : "Request failed", code);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}
