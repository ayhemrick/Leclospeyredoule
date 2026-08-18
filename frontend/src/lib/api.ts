/**
 * The one place that talks to the API.
 *
 * Sessions live in `HttpOnly` cookies, so every request is sent with
 * credentials and no token is ever held in JavaScript. Mutations mirror the
 * readable CSRF cookie into a header, which a cross-site page cannot do.
 */

const CSRF_COOKIE = 'cp_csrf';
const CSRF_HEADER = 'X-CSRF-Token';

const BASE_URL: string = (import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000').replace(
  /\/$/,
  '',
);

/** An unsuccessful API response, carrying enough detail to show the user. */
export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(status: number, message: string, detail: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.detail = detail;
  }

  /** The visitor has no valid guest session (or it has just lapsed). */
  get isAccessDenied(): boolean {
    return this.status === 403;
  }

  /** Nobody is signed in as an administrator. */
  get isUnauthenticated(): boolean {
    return this.status === 401;
  }
}

export function readCookie(name: string): string | null {
  const match = new RegExp(`(?:^|; )${name}=([^;]*)`).exec(document.cookie);
  return match?.[1] ? decodeURIComponent(match[1]) : null;
}

interface RequestOptions {
  method?: 'GET' | 'POST' | 'PATCH' | 'DELETE';
  body?: unknown;
  query?: Record<string, string | number | boolean | undefined> | undefined;
  signal?: AbortSignal | undefined;
}

function buildUrl(path: string, query?: RequestOptions['query']): string {
  const url = new URL(`${BASE_URL}${path}`);
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value !== undefined) url.searchParams.set(key, String(value));
  }
  return url.toString();
}

async function readError(response: Response): Promise<ApiError> {
  let detail: unknown = null;
  let message = `Request failed with status ${response.status}`;
  try {
    const payload: unknown = await response.json();
    if (payload && typeof payload === 'object' && 'detail' in payload) {
      detail = payload.detail;
      if (typeof detail === 'string') message = detail;
      else if (Array.isArray(detail) && detail.length > 0) {
        const first: unknown = detail[0];
        if (first && typeof first === 'object' && 'msg' in first) {
          message = String(first.msg);
        }
      }
    }
  } catch {
    // A non-JSON error body (a proxy timeout page, say) keeps the default text.
  }
  return new ApiError(response.status, message, detail);
}

/** Perform a request and decode the JSON body. */
export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', body, query, signal } = options;
  const headers = new Headers();
  if (body !== undefined) headers.set('Content-Type', 'application/json');
  if (method !== 'GET') {
    const csrf = readCookie(CSRF_COOKIE);
    if (csrf) headers.set(CSRF_HEADER, csrf);
  }

  const init: RequestInit = {
    method,
    headers,
    credentials: 'include',
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
    ...(signal ? { signal } : {}),
  };

  const response = await fetch(buildUrl(path, query), init);
  if (!response.ok) throw await readError(response);
  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}

export const api = {
  get: <T>(path: string, query?: RequestOptions['query'], signal?: AbortSignal) =>
    request<T>(path, { query, ...(signal ? { signal } : {}) }),
  post: <T>(path: string, body?: unknown) => request<T>(path, { method: 'POST', body }),
  patch: <T>(path: string, body?: unknown) => request<T>(path, { method: 'PATCH', body }),
  delete: <T>(path: string) => request<T>(path, { method: 'DELETE' }),
};

export const apiBaseUrl = BASE_URL;
