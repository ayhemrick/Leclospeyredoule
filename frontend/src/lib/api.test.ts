import { describe, expect, it, vi } from 'vitest';

import { ApiError, api, readCookie } from '@/lib/api';
import { requestedUrl, stubFetch } from '@/test/utils';

describe('api client', () => {
  it('sends cookies with every request', async () => {
    const fetchSpy = stubFetch([{ match: '/api/v1/public/attractions', body: [] }]);
    await api.get('/api/v1/public/attractions');

    const init = fetchSpy.mock.calls[0]?.[1];
    expect(init?.credentials).toBe('include');
  });

  it('mirrors the CSRF cookie into the header on mutations', async () => {
    document.cookie = 'cp_csrf=token-value';
    const fetchSpy = stubFetch([{ match: '/api/v1/auth/logout', method: 'POST', body: {} }]);

    await api.post('/api/v1/auth/logout');

    const init = fetchSpy.mock.calls[0]?.[1];
    const headers = new Headers(init?.headers);
    expect(headers.get('X-CSRF-Token')).toBe('token-value');
  });

  it('does not send a CSRF header on reads', async () => {
    document.cookie = 'cp_csrf=token-value';
    const fetchSpy = stubFetch([{ match: '/api/v1/access/status', body: { granted: false } }]);

    await api.get('/api/v1/access/status');

    const headers = new Headers(fetchSpy.mock.calls[0]?.[1]?.headers);
    expect(headers.get('X-CSRF-Token')).toBeNull();
  });

  it('serialises query parameters and skips undefined ones', async () => {
    const fetchSpy = stubFetch([{ match: '/api/v1/public/attractions', body: [] }]);
    await api.get('/api/v1/public/attractions', { category: 'wine', missing: undefined });

    const url = requestedUrl(fetchSpy.mock.calls[0]?.[0]);
    expect(url).toContain('category=wine');
    expect(url).not.toContain('missing');
  });

  it('turns an error response into an ApiError carrying the detail', async () => {
    stubFetch([
      {
        match: '/api/v1/access/redeem',
        method: 'POST',
        status: 403,
        body: { detail: 'This code is not recognised.' },
      },
    ]);

    await expect(api.post('/api/v1/access/redeem', { code: 'nope' })).rejects.toMatchObject({
      name: 'ApiError',
      status: 403,
      message: 'This code is not recognised.',
    });
  });

  it('classifies 401 and 403 for the caller', () => {
    expect(new ApiError(401, 'x', null).isUnauthenticated).toBe(true);
    expect(new ApiError(403, 'x', null).isAccessDenied).toBe(true);
    expect(new ApiError(500, 'x', null).isAccessDenied).toBe(false);
  });

  it('reads the first validation message out of a 422 body', async () => {
    stubFetch([
      {
        match: '/api/v1/admin/content/attractions',
        method: 'POST',
        status: 422,
        body: { detail: [{ msg: 'image_credit is required when image_path is set' }] },
      },
    ]);

    await expect(api.post('/api/v1/admin/content/attractions', {})).rejects.toThrow(
      'image_credit is required when image_path is set',
    );
  });

  it('survives a non-JSON error body', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => Promise.resolve(new Response('<html>gateway timeout</html>', { status: 504 }))),
    );

    await expect(api.get('/api/v1/public/guide')).rejects.toMatchObject({ status: 504 });
  });
});

describe('readCookie', () => {
  it('returns null when the cookie is absent', () => {
    expect(readCookie('cp_absent')).toBeNull();
  });

  it('decodes a stored value', () => {
    document.cookie = 'cp_test=a%20value';
    expect(readCookie('cp_test')).toBe('a value');
  });
});
