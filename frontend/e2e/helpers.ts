/** Shared helpers for the end-to-end suite. */

import type { APIRequestContext } from '@playwright/test';
import { request } from '@playwright/test';

export const API_URL = process.env.E2E_API_URL ?? 'http://localhost:8000';
export const ADMIN_EMAIL = process.env.E2E_ADMIN_EMAIL ?? 'admin@clos-peyredoule.fr';
export const ADMIN_PASSWORD = process.env.E2E_ADMIN_PASSWORD ?? 'Peyredoule!Demo2026';

/** Sign in against the API and return a context carrying the admin session. */
export async function adminApi(): Promise<APIRequestContext> {
  const context = await request.newContext({ baseURL: API_URL });
  const response = await context.post('/api/v1/auth/login', {
    data: { email: ADMIN_EMAIL, password: ADMIN_PASSWORD },
  });
  if (!response.ok()) {
    throw new Error(
      `admin login failed (${String(response.status())}): check E2E_ADMIN_PASSWORD and that the API is running at ${API_URL}`,
    );
  }
  return context;
}

/** The CSRF token the admin context must echo on mutations. */
export async function csrfToken(context: APIRequestContext): Promise<string> {
  const cookies = await context.storageState();
  const token = cookies.cookies.find((cookie) => cookie.name === 'cp_csrf')?.value;
  if (!token) throw new Error('no CSRF cookie on the admin session');
  return token;
}

/** Read the code currently printed on the poster. */
export async function currentCode(context: APIRequestContext): Promise<string> {
  const response = await context.get('/api/v1/admin/access/code');
  const body = (await response.json()) as { code: string };
  return body.code;
}

/** Retire the current code and return the replacement. */
export async function rotateCode(context: APIRequestContext): Promise<string> {
  const response = await context.post('/api/v1/admin/access/code/rotate', {
    headers: { 'X-CSRF-Token': await csrfToken(context) },
  });
  const body = (await response.json()) as { code: string };
  return body.code;
}
