/** Read-only activity log. */

import { useState } from 'react';

import { Card, EmptyState, ErrorState, Loading, SectionHeading, TextInput } from '@/components/ui';
import { useLocale } from '@/i18n';
import { formatDateTime } from '@/lib/format';
import { useAuditLog } from '@/lib/queries';

function summarise(context: Record<string, unknown>): string {
  const entries = Object.entries(context).filter(([, value]) => value !== null && value !== '');
  if (entries.length === 0) return '—';
  return entries
    .map(([key, value]) => `${key}: ${Array.isArray(value) ? value.join(', ') : String(value)}`)
    .join(' · ');
}

export function AdminAudit() {
  const { locale, t } = useLocale();
  const [filter, setFilter] = useState('');
  const log = useAuditLog(filter);

  return (
    <div>
      <SectionHeading as="h1" title={t('admin.audit.title')} />

      <div className="mb-4 max-w-xs">
        <TextInput
          aria-label={t('admin.audit.filter')}
          placeholder="access. / auth. / content."
          value={filter}
          onChange={(event) => {
            setFilter(event.target.value);
          }}
        />
      </div>

      {log.isPending ? <Loading /> : null}
      {log.isError ? (
        <ErrorState
          onRetry={() => {
            void log.refetch();
          }}
        />
      ) : null}
      {log.isSuccess && log.data.items.length === 0 ? (
        <EmptyState message={t('admin.audit.empty')} />
      ) : null}

      {log.isSuccess && log.data.items.length > 0 ? (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[44rem] text-left text-sm">
            <thead className="border-b border-sand text-xs tracking-wide text-muted uppercase">
              <tr>
                <th scope="col" className="px-4 py-3">
                  {t('admin.audit.when')}
                </th>
                <th scope="col" className="px-4 py-3">
                  {t('admin.audit.who')}
                </th>
                <th scope="col" className="px-4 py-3">
                  {t('admin.audit.what')}
                </th>
                <th scope="col" className="px-4 py-3">
                  {t('admin.audit.details')}
                </th>
              </tr>
            </thead>
            <tbody>
              {log.data.items.map((entry) => (
                <tr key={entry.id} className="border-b border-sand/60 last:border-0">
                  <td className="px-4 py-3 whitespace-nowrap text-muted">
                    {formatDateTime(entry.created_at, locale)}
                  </td>
                  <td className="px-4 py-3">{entry.actor_label}</td>
                  <td className="px-4 py-3">
                    <code className="text-xs">{entry.action}</code>
                  </td>
                  <td className="px-4 py-3 text-xs text-muted">{summarise(entry.context)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}
