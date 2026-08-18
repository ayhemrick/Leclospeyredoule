/**
 * Locale state and translation.
 *
 * Both languages are always in memory, so switching is instant and does not
 * refetch content: the API already returns every field in French and English.
 */

import { createContext, use, useCallback, useEffect, useMemo, useState } from 'react';
import type { ReactNode } from 'react';

import type { LocalizedString, Locale } from '@/lib/types';

import { messages, type MessageKey } from './messages';

const STORAGE_KEY = 'cp-locale';
const LOCALES: readonly Locale[] = ['fr', 'en'];

export type Translate = (key: MessageKey, values?: Record<string, string | number>) => string;

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => void;
  toggleLocale: () => void;
  t: Translate;
}

const LocaleContext = createContext<LocaleContextValue | null>(null);

function isLocale(value: string | null): value is Locale {
  return value !== null && (LOCALES as readonly string[]).includes(value);
}

/** French by default; a stored choice or the browser's preference wins. */
function detectLocale(): Locale {
  if (typeof window === 'undefined') return 'fr';
  const stored = window.localStorage.getItem(STORAGE_KEY);
  if (isLocale(stored)) return stored;
  return window.navigator.language.toLowerCase().startsWith('en') ? 'en' : 'fr';
}

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(detectLocale);

  useEffect(() => {
    window.localStorage.setItem(STORAGE_KEY, locale);
    document.documentElement.lang = locale;
  }, [locale]);

  const setLocale = useCallback((next: Locale) => {
    setLocaleState(next);
  }, []);

  const toggleLocale = useCallback(() => {
    setLocaleState((current) => (current === 'fr' ? 'en' : 'fr'));
  }, []);

  const t = useCallback<Translate>(
    (key, values) => {
      const template: string = messages[locale][key];
      if (!values) return template;
      return Object.entries(values).reduce<string>(
        (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
        template,
      );
    },
    [locale],
  );

  const value = useMemo<LocaleContextValue>(
    () => ({ locale, setLocale, toggleLocale, t }),
    [locale, setLocale, toggleLocale, t],
  );

  return <LocaleContext value={value}>{children}</LocaleContext>;
}

export function useLocale(): LocaleContextValue {
  const context = use(LocaleContext);
  if (!context) throw new Error('useLocale must be used inside a LocaleProvider');
  return context;
}

/** Read the current language out of a bilingual field from the API. */
export function pick(value: LocalizedString, locale: Locale): string {
  return value[locale];
}
