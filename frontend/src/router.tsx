/**
 * Code-based route tree.
 *
 * Public pages share the site shell; the admin section has its own layout and
 * guards itself on the session query rather than on a router loader, so a
 * lapsed cookie shows the login form instead of a redirect loop.
 */

import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  useRouterState,
} from '@tanstack/react-router';
import { useEffect } from 'react';

import { AppShell } from '@/components/AppShell';
import { useLocale } from '@/i18n';
import { useCurrentAdmin } from '@/lib/queries';
import { CreditsPage, NotFoundPage } from '@/routes/Credits';
import { GuidePage } from '@/routes/Guide';
import { HomePage } from '@/routes/Home';
import { HousePage } from '@/routes/House';
import { RegionPage } from '@/routes/Region';
import { ScanPage } from '@/routes/Scan';
import { AdminAccess } from '@/routes/admin/Access';
import { AdminAudit } from '@/routes/admin/Audit';
import { AdminAttractionsEditor } from '@/routes/admin/AttractionsEditor';
import { AdminDashboard } from '@/routes/admin/Dashboard';
import { AdminGuideEditor } from '@/routes/admin/GuideEditor';
import { AdminLayout } from '@/routes/admin/AdminLayout';
import { AdminSessions } from '@/routes/admin/Sessions';
import { AdminUsers } from '@/routes/admin/Users';

/** Move focus to the top on navigation, so the keyboard follows the page. */
function useScrollReset() {
  const pathname = useRouterState({ select: (state) => state.location.pathname });
  useEffect(() => {
    window.scrollTo({ top: 0 });
  }, [pathname]);
}

function RootLayout() {
  useScrollReset();
  return <Outlet />;
}

const rootRoute = createRootRoute({
  component: RootLayout,
  notFoundComponent: () => (
    <AppShell>
      <NotFoundPage />
    </AppShell>
  ),
});

/** Wraps a public page in the site shell. */
function withShell(Component: () => React.JSX.Element) {
  return function ShelledRoute() {
    return (
      <AppShell>
        <Component />
      </AppShell>
    );
  };
}

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  component: withShell(HomePage),
});

const houseRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/la-maison',
  component: withShell(HousePage),
});

const regionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/decouvrir',
  component: withShell(RegionPage),
});

const guideRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/guide',
  component: withShell(GuidePage),
});

const creditsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/credits',
  component: withShell(CreditsPage),
});

const scanRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/a/$code',
  component: withShell(ScanPage),
});

/** Landing after the code is stripped from the address bar. */
const scanCleanRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/a',
  component: withShell(GuidePage),
});

// ---------------------------------------------------------------------------
// Admin
// ---------------------------------------------------------------------------
const adminRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/admin',
  component: AdminLayout,
});

/** Pages that behave differently for an owner read the role once, here. */
function useIsOwner(): boolean {
  const admin = useCurrentAdmin();
  return admin.data?.role === 'owner';
}

const adminIndexRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/',
  component: AdminDashboard,
});

const adminAccessRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/acces',
  component: function AdminAccessRoute() {
    return <AdminAccess isOwner={useIsOwner()} />;
  },
});

const adminSessionsRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/sessions',
  component: function AdminSessionsRoute() {
    return <AdminSessions isOwner={useIsOwner()} />;
  },
});

const adminGuideRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/guide',
  component: AdminGuideEditor,
});

const adminAttractionsRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/lieux',
  component: AdminAttractionsEditor,
});

const adminUsersRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/comptes',
  component: function AdminUsersRoute() {
    return <AdminUsers isOwner={useIsOwner()} />;
  },
});

const adminAuditRoute = createRoute({
  getParentRoute: () => adminRoute,
  path: '/journal',
  component: AdminAudit,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  houseRoute,
  regionRoute,
  guideRoute,
  creditsRoute,
  scanRoute,
  scanCleanRoute,
  adminRoute.addChildren([
    adminIndexRoute,
    adminAccessRoute,
    adminSessionsRoute,
    adminGuideRoute,
    adminAttractionsRoute,
    adminUsersRoute,
    adminAuditRoute,
  ]),
]);

export const router = createRouter({
  routeTree,
  defaultPreload: 'intent',
  scrollRestoration: true,
});

declare module '@tanstack/react-router' {
  interface Register {
    router: typeof router;
  }
}

/** Keeps the document title in step with the active locale. */
export function DocumentTitle() {
  const { t } = useLocale();
  useEffect(() => {
    document.title = `${t('site.name')} — ${t('site.tagline')}`;
  }, [t]);
  return null;
}
