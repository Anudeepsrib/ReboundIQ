export const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export class ApiError extends Error {
  status: number;
  payload: unknown;

  constructor(status: number, message: string, payload: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

export function getStoredToken() {
  if (typeof window === 'undefined') return null;
  return window.sessionStorage.getItem('token');
}

function getStoredRefreshToken() {
  if (typeof window === 'undefined') return null;
  return window.sessionStorage.getItem('refresh_token');
}

export function setStoredTokens(accessToken: string, refreshToken?: string | null) {
  if (typeof window === 'undefined') return;
  window.sessionStorage.setItem('token', accessToken);
  if (refreshToken) window.sessionStorage.setItem('refresh_token', refreshToken);
}

export function clearStoredTokens() {
  if (typeof window === 'undefined') return;
  window.sessionStorage.removeItem('token');
  window.sessionStorage.removeItem('refresh_token');
}

async function parsePayload(response: Response) {
  const contentType = response.headers.get('content-type') || '';
  return contentType.includes('application/json') ? response.json() : response.text();
}

async function refreshAccessToken() {
  const refreshToken = getStoredRefreshToken();
  if (!refreshToken) return false;
  try {
    const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    const payload = await parsePayload(response);
    if (!response.ok || typeof payload !== 'object' || !payload || !('access_token' in payload)) {
      clearStoredTokens();
      return false;
    }
    const tokens = payload as { access_token: string; refresh_token?: string | null };
    setStoredTokens(tokens.access_token, tokens.refresh_token);
    return true;
  } catch {
    clearStoredTokens();
    return false;
  }
}

function buildHeaders(init: RequestInit) {
  const token = getStoredToken();
  const headers = new Headers(init.headers);
  const body = init.body;

  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (body && !(body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  return headers;
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  async function request() {
    return fetch(`${API_BASE}${path}`, {
      ...init,
      headers: buildHeaders(init),
      credentials: 'include',
    });
  }

  let response = await request();
  let payload = await parsePayload(response);
  if (response.status === 401 && (await refreshAccessToken())) {
    response = await request();
    payload = await parsePayload(response);
  }
  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed with ${response.status}`;
    throw new ApiError(response.status, detail, payload);
  }
  return payload as T;
}
