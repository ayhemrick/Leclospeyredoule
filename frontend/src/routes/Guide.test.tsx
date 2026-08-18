/** The gate is the product: these tests hold it in place. */

import { screen, waitFor } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { GuidePage } from '@/routes/Guide';
import { renderAtRoute, requestedUrl, stubFetch } from '@/test/utils';

const GUEST_SECTION = {
  id: '00000000-0000-0000-0000-000000000001',
  slug: 'wifi-et-connexion',
  category: 'practical',
  visibility: 'guest',
  position: 10,
  icon: null,
  title: { fr: 'Wi-Fi et connexion', en: 'Wi-Fi and connectivity' },
  body: { fr: 'Réseau : `ClosPeyredoule`', en: 'Network: `ClosPeyredoule`' },
  updated_at: '2026-08-01T10:00:00Z',
};

function renderGuide() {
  return renderAtRoute('/guide', GuidePage, '/guide');
}

describe('GuidePage', () => {
  it('tells a visitor without access to scan the code', async () => {
    stubFetch([
      {
        match: '/api/v1/access/status',
        body: { granted: false, expires_at: null, seconds_remaining: null },
      },
    ]);

    renderGuide();

    expect(await screen.findByText('Guests only')).toBeInTheDocument();
    expect(screen.queryByText('Wi-Fi and connectivity')).not.toBeInTheDocument();
  });

  it('never requests the gated content without access', async () => {
    const fetchSpy = stubFetch([
      {
        match: '/api/v1/access/status',
        body: { granted: false, expires_at: null, seconds_remaining: null },
      },
    ]);

    renderGuide();
    await screen.findByText('Guests only');

    const requested = fetchSpy.mock.calls.map((call) => requestedUrl(call[0]));
    expect(requested.some((url) => url.includes('/guide/guest'))).toBe(false);
  });

  it('shows the guide and the remaining window once access is granted', async () => {
    stubFetch([
      {
        match: '/api/v1/access/status',
        body: {
          granted: true,
          expires_at: new Date(Date.now() + 3 * 3_600 * 1000).toISOString(),
          seconds_remaining: 3 * 3_600,
        },
      },
      { match: '/api/v1/public/guide/guest', body: [GUEST_SECTION] },
    ]);

    renderGuide();

    expect(await screen.findByText('Wi-Fi and connectivity')).toBeInTheDocument();
    await waitFor(() => {
      expect(screen.getByText(/Access open for another/)).toBeInTheDocument();
    });
    expect(screen.getByText(/3 h/)).toBeInTheDocument();
  });

  it('groups sections under their category heading', async () => {
    stubFetch([
      {
        match: '/api/v1/access/status',
        body: {
          granted: true,
          expires_at: new Date(Date.now() + 3_600_000).toISOString(),
          seconds_remaining: 3_600,
        },
      },
      {
        match: '/api/v1/public/guide/guest',
        body: [GUEST_SECTION, { ...GUEST_SECTION, id: 'b', slug: 'arrivee', category: 'arrival' }],
      },
    ]);

    renderGuide();

    expect(await screen.findByRole('heading', { name: 'Practical' })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Arrival' })).toBeInTheDocument();
  });

  it('surfaces a server refusal instead of hanging', async () => {
    stubFetch([
      {
        match: '/api/v1/access/status',
        body: {
          granted: true,
          expires_at: new Date(Date.now() + 3_600_000).toISOString(),
          seconds_remaining: 3_600,
        },
      },
      { match: '/api/v1/public/guide/guest', status: 403, body: { detail: 'Scan the code' } },
    ]);

    renderGuide();

    expect(await screen.findByRole('alert')).toBeInTheDocument();
  });
});
