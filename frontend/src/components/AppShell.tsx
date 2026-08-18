/** Header, navigation and footer wrapped around every public page. */

import { Link } from '@tanstack/react-router';
import { useState } from 'react';
import type { ReactNode } from 'react';

import { useLocale } from '@/i18n';
import { useAccessStatus } from '@/lib/queries';

function LanguageSwitch() {
  const { locale, toggleLocale, t } = useLocale();
  return (
    <button
      type="button"
      onClick={toggleLocale}
      aria-label={t('lang.label')}
      className="rounded-full border border-sand px-3 py-1 text-xs font-medium tracking-wide text-ink/80 uppercase transition-colors hover:bg-sand"
    >
      {locale === 'fr' ? 'EN' : 'FR'}
    </button>
  );
}

const NAV = [
  { to: '/', key: 'nav.home' },
  { to: '/la-maison', key: 'nav.house' },
  { to: '/decouvrir', key: 'nav.region' },
  { to: '/guide', key: 'nav.guide' },
] as const;

export function AppShell({ children }: { children: ReactNode }) {
  const { t } = useLocale();
  const [menuOpen, setMenuOpen] = useState(false);
  const { data: access } = useAccessStatus();

  return (
    <div className="flex min-h-dvh flex-col">
      <a href="#main" className="skip-link">
        {t('nav.skip')}
      </a>

      <header className="sticky top-0 z-30 border-b border-sand/80 bg-parchment/90 backdrop-blur no-print">
        <div className="mx-auto flex max-w-6xl items-center gap-4 px-4 py-3 sm:px-6">
          <Link to="/" className="font-display text-lg font-semibold tracking-tight text-moss">
            {t('site.name')}
          </Link>

          <nav aria-label={t('nav.menu')} className="ml-auto hidden items-center gap-1 sm:flex">
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className="rounded-lg px-3 py-1.5 text-sm text-ink/80 transition-colors hover:bg-sand hover:text-ink"
                activeProps={{ className: 'bg-sand text-ink font-medium' }}
                activeOptions={{ exact: item.to === '/' }}
              >
                {t(item.key)}
                {item.key === 'nav.guide' && access?.granted ? (
                  <span
                    aria-hidden="true"
                    className="ml-1.5 inline-block size-1.5 rounded-full bg-moss align-middle"
                  />
                ) : null}
              </Link>
            ))}
          </nav>

          <div className="ml-auto flex items-center gap-2 sm:ml-0">
            <LanguageSwitch />
            <button
              type="button"
              className="rounded-lg border border-sand px-3 py-1.5 text-sm sm:hidden"
              aria-expanded={menuOpen}
              aria-controls="mobile-nav"
              onClick={() => {
                setMenuOpen((open) => !open);
              }}
            >
              {t('nav.menu')}
            </button>
          </div>
        </div>

        {menuOpen ? (
          <nav
            id="mobile-nav"
            aria-label={t('nav.menu')}
            className="border-t border-sand bg-parchment px-4 pb-3 sm:hidden"
          >
            {NAV.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => {
                  setMenuOpen(false);
                }}
                className="block rounded-lg px-3 py-2 text-sm text-ink/80"
                activeProps={{ className: 'bg-sand text-ink font-medium' }}
                activeOptions={{ exact: item.to === '/' }}
              >
                {t(item.key)}
              </Link>
            ))}
          </nav>
        ) : null}
      </header>

      <main id="main" className="flex-1">
        {children}
      </main>

      <footer className="mt-16 border-t border-sand bg-stone no-print">
        <div className="mx-auto grid max-w-6xl gap-6 px-4 py-10 text-sm sm:grid-cols-3 sm:px-6">
          <div>
            <p className="font-display text-base text-moss">{t('site.name')}</p>
            <p className="mt-1 text-muted">{t('site.tagline')}</p>
          </div>
          <nav aria-label={t('nav.menu')} className="space-y-1.5">
            {NAV.map((item) => (
              <Link key={item.to} to={item.to} className="block text-ink/75 hover:text-ink">
                {t(item.key)}
              </Link>
            ))}
            <Link to="/credits" className="block text-ink/75 hover:text-ink">
              {t('nav.credits')}
            </Link>
          </nav>
          <div className="space-y-2 text-muted">
            <p>{t('site.demo')}</p>
            <Link to="/admin" className="inline-block text-ink/70 underline hover:text-ink">
              {t('nav.admin')}
            </Link>
          </div>
        </div>
      </footer>
    </div>
  );
}
