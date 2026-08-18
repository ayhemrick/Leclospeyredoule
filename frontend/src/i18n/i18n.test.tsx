import { screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { pick, useLocale } from '@/i18n';
import { messages } from '@/i18n/messages';
import { renderWithProviders } from '@/test/utils';

function Probe() {
  const { locale, toggleLocale, t } = useLocale();
  return (
    <div>
      <p data-testid="locale">{locale}</p>
      <p data-testid="translated">{t('guide.title')}</p>
      <p data-testid="interpolated">{t('region.distance', { distance: '1.5' })}</p>
      <button type="button" onClick={toggleLocale}>
        switch
      </button>
    </div>
  );
}

/** jsdom reports an English browser; override it to test the other branch. */
function setBrowserLanguage(language: string): void {
  vi.spyOn(window.navigator, 'language', 'get').mockReturnValue(language);
}

describe('locale detection', () => {
  it('follows a French browser', () => {
    setBrowserLanguage('fr-FR');
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('locale')).toHaveTextContent('fr');
    expect(screen.getByTestId('translated')).toHaveTextContent('Guide des hôtes');
  });

  it('follows an English browser', () => {
    setBrowserLanguage('en-GB');
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('locale')).toHaveTextContent('en');
    expect(screen.getByTestId('translated')).toHaveTextContent('Guest guide');
  });

  it('falls back to French for any other language', () => {
    setBrowserLanguage('de-DE');
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('locale')).toHaveTextContent('fr');
  });

  it('prefers a stored choice over the browser', () => {
    setBrowserLanguage('en-GB');
    window.localStorage.setItem('cp-locale', 'fr');
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('locale')).toHaveTextContent('fr');
  });

  it('ignores a corrupted stored value', () => {
    setBrowserLanguage('fr-FR');
    window.localStorage.setItem('cp-locale', 'klingon');
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('locale')).toHaveTextContent('fr');
  });
});

describe('locale switching', () => {
  beforeEach(() => {
    setBrowserLanguage('fr-FR');
  });

  it('switches language and remembers the choice', async () => {
    const user = userEvent.setup();
    const { unmount } = renderWithProviders(<Probe />);

    await user.click(screen.getByRole('button', { name: 'switch' }));
    expect(screen.getByTestId('translated')).toHaveTextContent('Guest guide');
    expect(window.localStorage.getItem('cp-locale')).toBe('en');

    unmount();
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('locale')).toHaveTextContent('en');
  });

  it('interpolates placeholders', () => {
    renderWithProviders(<Probe />);
    expect(screen.getByTestId('interpolated')).toHaveTextContent('à 1.5 km');
  });

  it('sets the document language for screen readers', async () => {
    const user = userEvent.setup();
    renderWithProviders(<Probe />);
    expect(document.documentElement.lang).toBe('fr');

    await user.click(screen.getByRole('button', { name: 'switch' }));
    expect(document.documentElement.lang).toBe('en');
  });
});

describe('message catalogue', () => {
  it('defines every key in both languages', () => {
    expect(Object.keys(messages.en).sort()).toEqual(Object.keys(messages.fr).sort());
  });

  it('has no empty strings', () => {
    for (const [locale, catalogue] of Object.entries(messages)) {
      for (const [key, value] of Object.entries(catalogue)) {
        expect(value, `${locale}.${key}`).not.toBe('');
      }
    }
  });

  it('keeps the same placeholders in both languages', () => {
    const placeholders = (text: string) => (text.match(/\{[a-z]+\}/g) ?? []).sort();
    for (const key of Object.keys(messages.fr) as (keyof typeof messages.fr)[]) {
      expect(placeholders(messages.en[key]), key).toEqual(placeholders(messages.fr[key]));
    }
  });
});

describe('pick', () => {
  it('reads the requested language out of a bilingual field', () => {
    const value = { fr: 'La citadelle', en: 'The citadel' };
    expect(pick(value, 'fr')).toBe('La citadelle');
    expect(pick(value, 'en')).toBe('The citadel');
  });
});
