import { describe, expect, it } from 'vitest';

import { messages } from '@/i18n/messages';
import {
  describeDevice,
  formatDistance,
  formatDuration,
  splitInterval,
  toMinutes,
} from '@/lib/format';

const t = ((key: keyof (typeof messages)['fr'], values?: Record<string, string | number>) => {
  const template: string = messages.en[key];
  if (!values) return template;
  return Object.entries(values).reduce(
    (text, [name, value]) => text.replaceAll(`{${name}}`, String(value)),
    template,
  );
}) as Parameters<typeof formatDuration>[1];

describe('formatDuration', () => {
  it('reports days and hours for a long window', () => {
    expect(formatDuration(2 * 86_400 + 3 * 3_600, t)).toBe('2 d 3 h');
  });

  it('drops the smaller unit when it is zero', () => {
    expect(formatDuration(2 * 86_400, t)).toBe('2 d');
  });

  it('reports hours and minutes below a day', () => {
    expect(formatDuration(3 * 3_600 + 30 * 60, t)).toBe('3 h 30 min');
  });

  it('never claims zero minutes remain while time is left', () => {
    expect(formatDuration(30, t)).toBe('1 min');
  });

  it('says expired at or below zero', () => {
    expect(formatDuration(0, t)).toBe('expired');
    expect(formatDuration(-90, t)).toBe('expired');
  });
});

describe('interval conversion', () => {
  it('splits into the largest whole unit', () => {
    expect(splitInterval(10_080)).toEqual({ value: 7, unit: 'days' });
    expect(splitInterval(120)).toEqual({ value: 2, unit: 'hours' });
    expect(splitInterval(45)).toEqual({ value: 45, unit: 'minutes' });
  });

  it('round-trips through toMinutes', () => {
    for (const minutes of [5, 45, 120, 1_440, 10_080]) {
      const { value, unit } = splitInterval(minutes);
      expect(toMinutes(value, unit)).toBe(minutes);
    }
  });
});

describe('formatDistance', () => {
  it('drops a trailing zero decimal', () => {
    expect(formatDistance('3.0')).toBe('3');
  });

  it('keeps a meaningful decimal', () => {
    expect(formatDistance('1.5')).toBe('1.5');
  });

  it('passes through null', () => {
    expect(formatDistance(null)).toBeNull();
  });
});

describe('describeDevice', () => {
  it('summarises a phone user agent', () => {
    const iphone =
      'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1';
    expect(describeDevice(iphone)).toBe('Safari · iOS');
  });

  it('handles a missing user agent', () => {
    expect(describeDevice(null)).toBe('—');
  });
});
