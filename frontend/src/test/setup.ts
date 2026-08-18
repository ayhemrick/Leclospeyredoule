import '@testing-library/jest-dom/vitest';

import { cleanup } from '@testing-library/react';
import { afterEach, beforeEach, vi } from 'vitest';

/**
 * jsdom 30 under Vitest does not expose a working `localStorage`, and the
 * locale provider stores the language choice there. A tiny in-memory stand-in
 * keeps the tests honest without pulling in a polyfill package.
 */
function installLocalStorage(): void {
  // Typed as always-present by the DOM lib, but genuinely missing here.
  const existing = window.localStorage as Storage | undefined;
  if (existing !== undefined && typeof existing.getItem === 'function') return;

  const store = new Map<string, string>();
  const storage: Storage = {
    get length() {
      return store.size;
    },
    clear: () => {
      store.clear();
    },
    getItem: (key: string) => store.get(key) ?? null,
    key: (index: number) => [...store.keys()][index] ?? null,
    removeItem: (key: string) => {
      store.delete(key);
    },
    setItem: (key: string, value: string) => {
      store.set(key, value);
    },
  };
  Object.defineProperty(window, 'localStorage', { value: storage, configurable: true });
}

// jsdom has no matchMedia either, and layout-aware components can touch it.
function installMatchMedia(): void {
  vi.stubGlobal(
    'matchMedia',
    vi.fn().mockImplementation((query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    })),
  );
}

beforeEach(() => {
  installLocalStorage();
  installMatchMedia();
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
  window.localStorage.clear();
  // Cookies persist across tests in jsdom; clear the ones the app sets.
  for (const cookie of document.cookie.split(';')) {
    const name = cookie.split('=')[0]?.trim();
    if (name) document.cookie = `${name}=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/`;
  }
});
