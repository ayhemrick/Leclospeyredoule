/** Live visitor sessions, with the ability to end them. */

import { useState } from 'react';

import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Loading,
  SectionHeading,
} from '@/components/ui';
import { useLocale } from '@/i18n';
import { describeDevice, formatDateTime, formatRelative } from '@/lib/format';
import { useGuestSessions, useRevokeAllSessions, useRevokeSession } from '@/lib/queries';

export function AdminSessions({ isOwner }: { isOwner: boolean }) {
  const { locale, t } = useLocale();
  const [includeEnded, setIncludeEnded] = useState(false);
  const sessions = useGuestSessions(includeEnded);
  const revoke = useRevokeSession();
  const revokeAll = useRevokeAllSessions();

  return (
    <div>
      <SectionHeading as="h1" title={t('admin.sessions.title')} />

      <div className="mb-4 flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={includeEnded}
            onChange={(event) => {
              setIncludeEnded(event.target.checked);
            }}
            className="size-4 rounded border-sand accent-moss"
          />
          {t('admin.sessions.includeEnded')}
        </label>

        <Button
          variant="danger"
          className="ml-auto"
          disabled={!isOwner || revokeAll.isPending}
          onClick={() => {
            if (window.confirm(t('admin.sessions.revokeAll'))) revokeAll.mutate();
          }}
        >
          {t('admin.sessions.revokeAll')}
        </Button>
      </div>

      {sessions.isPending ? <Loading /> : null}
      {sessions.isError ? (
        <ErrorState
          onRetry={() => {
            void sessions.refetch();
          }}
        />
      ) : null}
      {sessions.isSuccess && sessions.data.items.length === 0 ? (
        <EmptyState message={t('admin.sessions.empty')} />
      ) : null}

      {sessions.isSuccess && sessions.data.items.length > 0 ? (
        <Card className="overflow-x-auto">
          <table className="w-full min-w-[40rem] text-left text-sm">
            <thead className="border-b border-sand text-xs tracking-wide text-muted uppercase">
              <tr>
                <th scope="col" className="px-4 py-3">
                  {t('admin.sessions.device')}
                </th>
                <th scope="col" className="px-4 py-3">
                  {t('admin.sessions.started')}
                </th>
                <th scope="col" className="px-4 py-3">
                  {t('admin.sessions.expires')}
                </th>
                <th scope="col" className="px-4 py-3">
                  {t('admin.sessions.lastSeen')}
                </th>
                <th scope="col" className="px-4 py-3">
                  <span className="sr-only">{t('admin.sessions.revoke')}</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {sessions.data.items.map((session) => {
                const ended =
                  session.revoked_at !== null || new Date(session.expires_at) < new Date();
                return (
                  <tr key={session.id} className="border-b border-sand/60 last:border-0">
                    <td className="px-4 py-3">
                      {describeDevice(session.user_agent)}{' '}
                      {ended ? <Badge>{t('admin.sessions.ended')}</Badge> : null}
                    </td>
                    <td className="px-4 py-3 text-muted">
                      {formatDateTime(session.created_at, locale)}
                    </td>
                    <td className="px-4 py-3 text-muted">
                      {formatRelative(session.expires_at, locale)}
                    </td>
                    <td className="px-4 py-3 text-muted">
                      {session.last_seen_at ? formatRelative(session.last_seen_at, locale) : '—'}
                    </td>
                    <td className="px-4 py-3 text-right">
                      {ended ? null : (
                        <Button
                          variant="ghost"
                          disabled={revoke.isPending}
                          onClick={() => {
                            revoke.mutate(session.id);
                          }}
                        >
                          {t('admin.sessions.revoke')}
                        </Button>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
      ) : null}
    </div>
  );
}
