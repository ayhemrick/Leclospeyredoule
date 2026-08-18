/** Headline access numbers. */

import { Link } from '@tanstack/react-router';

import { Badge, Card, ErrorState, Loading, SectionHeading } from '@/components/ui';
import { useLocale } from '@/i18n';
import { formatRelative } from '@/lib/format';
import { useAccessStats } from '@/lib/queries';

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <Card className="p-5">
      <p className="text-sm text-muted">{label}</p>
      <p className="mt-1 font-display text-3xl text-moss">{value}</p>
    </Card>
  );
}

export function AdminDashboard() {
  const { locale, t } = useLocale();
  const stats = useAccessStats();

  if (stats.isPending) return <Loading />;
  if (stats.isError) {
    return (
      <ErrorState
        onRetry={() => {
          void stats.refetch();
        }}
      />
    );
  }

  return (
    <div>
      <SectionHeading as="h1" title={t('admin.dashboard.title')} />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <Stat label={t('admin.dashboard.activeSessions')} value={stats.data.active_sessions} />
        <Stat label={t('admin.dashboard.sessions24h')} value={stats.data.sessions_last_24h} />
        <Stat label={t('admin.dashboard.currentScans')} value={stats.data.scans_current_code} />
        <Stat label={t('admin.dashboard.totalScans')} value={stats.data.total_scans} />
      </div>

      <Card className="mt-6 flex flex-wrap items-center gap-3 p-5">
        <Badge tone={stats.data.auto_rotate ? 'positive' : 'warning'}>
          {stats.data.auto_rotate
            ? t('admin.dashboard.rotationOn')
            : t('admin.dashboard.rotationOff')}
        </Badge>
        {stats.data.auto_rotate && stats.data.code_expires_at ? (
          <span className="text-sm text-muted">
            {t('admin.dashboard.nextRotation', {
              when: formatRelative(stats.data.code_expires_at, locale),
            })}
          </span>
        ) : null}
        <Link to="/admin/acces" className="ml-auto text-sm text-vine underline underline-offset-2">
          {t('admin.access.title')} →
        </Link>
      </Card>
    </div>
  );
}
