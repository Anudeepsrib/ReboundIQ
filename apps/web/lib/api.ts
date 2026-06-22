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
  return window.localStorage.getItem('token');
}

export function setStoredTokens(accessToken: string, refreshToken?: string | null) {
  if (typeof window === 'undefined') return;
  window.localStorage.setItem('token', accessToken);
  if (refreshToken) window.localStorage.setItem('refresh_token', refreshToken);
}

export function clearStoredTokens() {
  if (typeof window === 'undefined') return;
  window.localStorage.removeItem('token');
  window.localStorage.removeItem('refresh_token');
}

export async function apiFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getStoredToken();
  const headers = new Headers(init.headers);
  const body = init.body;

  if (token) headers.set('Authorization', `Bearer ${token}`);
  if (body && !(body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
  });
  const contentType = response.headers.get('content-type') || '';
  const payload = contentType.includes('application/json') ? await response.json() : await response.text();
  if (!response.ok) {
    const detail =
      typeof payload === 'object' && payload && 'detail' in payload
        ? String((payload as { detail: unknown }).detail)
        : `Request failed with ${response.status}`;
    throw new ApiError(response.status, detail, payload);
  }
  return payload as T;
}
