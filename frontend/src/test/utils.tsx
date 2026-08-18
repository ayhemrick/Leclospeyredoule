/** Rendering helpers: providers, a router harness and a scripted fetch. */

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  RouterProvider,
} from '@tanstack/react-router';
import { render, type RenderResult } from '@testing-library/react';
import type { ReactNode } from 'react';
import { vi } from 'vitest';

import { LocaleProvider } from '@/i18n';

/** A query client that fails fast, so tests never wait on retries. */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, staleTime: 0 },
      mutations: { retry: false },
    },
  });
}

export function renderWithProviders(ui: ReactNode): RenderResult {
  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <LocaleProvider>{ui}</LocaleProvider>
    </QueryClientProvider>,
  );
}

/**
 * Render a component inside a real router at `initialPath`.
 *
 * Components that read route params or render `<Link>` need a router in the
 * tree; a memory history keeps the test out of the jsdom URL bar.
 */
export function renderAtRoute(
  path: string,
  Component: () => ReactNode,
  initialPath: string,
): RenderResult {
  const rootRoute = createRootRoute();
  const route = createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: () => <>{Component()}</>,
  });
  const catchAll = createRoute({
    getParentRoute: () => rootRoute,
    path: '/$',
    component: () => <div data-testid="elsewhere" />,
  });
  const router = createRouter({
    routeTree: rootRoute.addChildren([route, catchAll]),
    history: createMemoryHistory({ initialEntries: [initialPath] }),
  });

  return render(
    <QueryClientProvider client={createTestQueryClient()}>
      <LocaleProvider>
        {/* eslint-disable-next-line @typescript-eslint/no-explicit-any -- the test router is intentionally untyped */}
        <RouterProvider router={router as any} />
      </LocaleProvider>
    </QueryClientProvider>,
  );
}

/** The URL of a recorded fetch call, whatever form the caller used. */
export function requestedUrl(input: unknown): string {
  if (typeof input === 'string') return input;
  if (input instanceof URL) return input.href;
  if (input instanceof Request) return input.url;
  return '';
}

export interface FetchRoute {
  /** Substring matched against the request URL. */
  match: string;
  status?: number;
  body?: unknown;
  /** Optional method filter, when one URL answers differently per verb. */
  method?: string;
}

/**
 * Install a fetch stub that answers from a list of routes.
 *
 * Returns the spy so a test can assert on headers, credentials or call order.
 */
export function stubFetch(routes: FetchRoute[]) {
  const spy = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url;
    const method = init?.method ?? 'GET';
    const route = routes.find(
      (candidate) =>
        url.includes(candidate.match) && (!candidate.method || candidate.method === method),
    );
    if (!route) {
      return Promise.resolve(
        new Response(JSON.stringify({ detail: `no stub for ${method} ${url}` }), { status: 404 }),
      );
    }
    return Promise.resolve(
      new Response(JSON.stringify(route.body ?? {}), {
        status: route.status ?? 200,
        headers: { 'Content-Type': 'application/json' },
      }),
    );
  });
  vi.stubGlobal('fetch', spy);
  return spy;
}
