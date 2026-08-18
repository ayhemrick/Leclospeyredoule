/** Shell for the admin section: guard, navigation and sign-out. */

import { Link, Outlet, useNavigate } from '@tanstack/react-router';
import { useEffect } from 'react';

import { Button, Loading } from '@/components/ui';
import { useLocale } from '@/i18n';
import type { MessageKey } from '@/i18n/messages';
import { useCurrentAdmin, useLogout } from '@/lib/queries';

import { LoginPage } from './Login';

const NAV: { to: string; key: MessageKey; ownerOnly?: boolean }[] = [
  { to: '/admin', key: 'admin.nav.dashboard' },
  { to: '/admin/acces', key: 'admin.nav.access' },
  { to: '/admin/sessions', key: 'admin.nav.sessions' },
  { to: '/admin/guide', key: 'admin.nav.guide' },
  { to: '/admin/lieux', key: 'admin.nav.attractions' },
  { to: '/admin/comptes', key: 'admin.nav.users', ownerOnly: true },
  { to: '/admin/journal', key: 'admin.nav.audit' },
];

export function AdminLayout() {
  const { t } = useLocale();
  const navigate = useNavigate();
  const admin = useCurrentAdmin();
  const logout = useLogout();

  useEffect(() => {
    document.title = `${t('admin.title')} · Clos Peyredoule`;
  }, [t]);

  if (admin.isPending) {
    return (
      <div className="grid min-h-dvh place-items-center">
        <Loading />
      </div>
    );
  }

  if (!admin.data) return <LoginPage />;

  const isOwner = admin.data.role === 'owner';

  return (
    <div className="min-h-dvh bg-stone">
      <header className="border-b border-sand bg-white no-print">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3 sm:px-6">
          <Link to="/" className="font-display text-lg text-moss">
            Clos Peyredoule
          </Link>
          <span className="rounded-full bg-sand px-2 py-0.5 text-xs">{t('admin.title')}</span>

          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="hidden text-muted sm:inline">
              {admin.data.full_name} ·{' '}
              {t(isOwner ? 'admin.users.role.owner' : 'admin.users.role.editor')}
            </span>
            <Button
              variant="ghost"
              onClick={() => {
                logout.mutate(undefined, {
                  onSuccess: () => {
                    void navigate({ to: '/admin' });
                  },
                });
              }}
            >
              {t('admin.logout')}
            </Button>
          </div>
        </div>
      </header>

      <div className="mx-auto flex max-w-6xl flex-col gap-6 px-4 py-6 sm:px-6 lg:flex-row">
        <nav aria-label={t('admin.title')} className="lg:w-52 lg:shrink-0 no-print">
          <ul className="flex flex-wrap gap-1 lg:flex-col">
            {NAV.filter((item) => !item.ownerOnly || isOwner).map((item) => (
              <li key={item.to}>
                <Link
                  to={item.to}
                  activeProps={{ className: 'bg-moss text-stone font-medium' }}
                  activeOptions={{ exact: item.to === '/admin' }}
                  className="block rounded-lg px-3 py-2 text-sm text-ink/80 transition-colors hover:bg-sand"
                >
                  {t(item.key)}
                </Link>
              </li>
            ))}
          </ul>
        </nav>

        <main className="min-w-0 flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
