/** Locale-aware formatting helpers. */

import type { Translate } from '@/i18n';
import type { Locale } from '@/lib/types';

const LOCALE_TAGS: Record<Locale, string> = { fr: 'fr-FR', en: 'en-GB' };

export function formatDate(iso: string | null | undefined, locale: Locale): string {
  if (!iso) return '—';
  return new Intl.DateTimeFormat(LOCALE_TAGS[locale], {
    dateStyle: 'long',
  }).format(new Date(iso));
}

export function formatDateTime(iso: string | null | undefined, locale: Locale): string {
  if (!iso) return '—';
  return new Intl.DateTimeFormat(LOCALE_TAGS[locale], {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(new Date(iso));
}

export function formatRelative(iso: string | null | undefined, locale: Locale): string {
  if (!iso) return '—';
  const deltaSeconds = Math.round((new Date(iso).getTime() - Date.now()) / 1000);
  const formatter = new Intl.RelativeTimeFormat(LOCALE_TAGS[locale], { numeric: 'auto' });
  const steps: [Intl.RelativeTimeFormatUnit, number][] = [
    ['day', 86_400],
    ['hour', 3_600],
    ['minute', 60],
  ];
  for (const [unit, size] of steps) {
    if (Math.abs(deltaSeconds) >= size) {
      return formatter.format(Math.round(deltaSeconds / size), unit);
    }
  }
  return formatter.format(deltaSeconds, 'second');
}

/**
 * A countdown in the coarsest two units that still say something useful:
 * "2 j 3 h" rather than "2 j 3 h 14 min 9 s".
 */
export function formatDuration(totalSeconds: number, t: Translate): string {
  if (totalSeconds <= 0) return t('duration.expired');

  const days = Math.floor(totalSeconds / 86_400);
  const hours = Math.floor((totalSeconds % 86_400) / 3_600);
  const minutes = Math.floor((totalSeconds % 3_600) / 60);

  if (days > 0) {
    return hours > 0
      ? `${t('duration.days', { n: days })} ${t('duration.hours', { n: hours })}`
      : t('duration.days', { n: days });
  }
  if (hours > 0) {
    return minutes > 0
      ? `${t('duration.hours', { n: hours })} ${t('duration.minutes', { n: minutes })}`
      : t('duration.hours', { n: hours });
  }
  return t('duration.minutes', { n: Math.max(minutes, 1) });
}

/** Split a minute count into the largest whole unit, for the policy form. */
export function splitInterval(minutes: number): {
  value: number;
  unit: 'minutes' | 'hours' | 'days';
} {
  if (minutes % 1_440 === 0) return { value: minutes / 1_440, unit: 'days' };
  if (minutes % 60 === 0) return { value: minutes / 60, unit: 'hours' };
  return { value: minutes, unit: 'minutes' };
}

export function toMinutes(value: number, unit: 'minutes' | 'hours' | 'days'): number {
  if (unit === 'days') return value * 1_440;
  if (unit === 'hours') return value * 60;
  return value;
}

/** Distances arrive as decimal strings; drop a trailing ".0". */
export function formatDistance(value: string | null): string | null {
  if (value === null) return null;
  const numeric = Number(value);
  if (Number.isNaN(numeric)) return value;
  return numeric % 1 === 0 ? String(numeric) : numeric.toFixed(1);
}

/** A short, human label for a device, derived from its user agent. */
export function describeDevice(userAgent: string | null): string {
  if (!userAgent) return '—';
  const platform = /iPhone|iPad|iPod/.test(userAgent)
    ? 'iOS'
    : userAgent.includes('Android')
      ? 'Android'
      : userAgent.includes('Macintosh')
        ? 'macOS'
        : userAgent.includes('Windows')
          ? 'Windows'
          : userAgent.includes('Linux')
            ? 'Linux'
            : null;
  const browser = userAgent.includes('Edg/')
    ? 'Edge'
    : userAgent.includes('Chrome/')
      ? 'Chrome'
      : userAgent.includes('Safari/')
        ? 'Safari'
        : userAgent.includes('Firefox/')
          ? 'Firefox'
          : null;
  if (platform && browser) return `${browser} · ${platform}`;
  return platform ?? browser ?? userAgent.slice(0, 40);
}
