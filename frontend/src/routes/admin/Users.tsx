/** Administrator accounts. Owner only. */

import { useState } from 'react';

import {
  Badge,
  Button,
  Card,
  EmptyState,
  ErrorState,
  Field,
  Loading,
  SectionHeading,
  TextInput,
} from '@/components/ui';
import { useLocale } from '@/i18n';
import { formatDateTime } from '@/lib/format';
import { useAdmins, useCurrentAdmin, useDeleteAdmin, useSaveAdmin } from '@/lib/queries';
import type { AdminRole } from '@/lib/types';

export function AdminUsers({ isOwner }: { isOwner: boolean }) {
  const { locale, t } = useLocale();
  const me = useCurrentAdmin();
  const admins = useAdmins(isOwner);
  const save = useSaveAdmin();
  const remove = useDeleteAdmin();

  const [inviting, setInviting] = useState(false);
  const [email, setEmail] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<AdminRole>('editor');

  if (!isOwner) return <EmptyState message={t('admin.ownerOnly')} />;
  if (admins.isPending) return <Loading />;
  if (admins.isError) {
    return (
      <ErrorState
        onRetry={() => {
          void admins.refetch();
        }}
      />
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <SectionHeading as="h1" title={t('admin.users.title')} />
        <Button
          onClick={() => {
            setInviting((open) => !open);
          }}
        >
          {inviting ? t('common.cancel') : t('admin.users.new')}
        </Button>
      </div>

      {inviting ? (
        <Card className="mb-6 p-6">
          <form
            className="grid gap-4 sm:grid-cols-2"
            onSubmit={(event) => {
              event.preventDefault();
              save.mutate(
                { values: { email, full_name: fullName, password, role } },
                {
                  onSuccess: () => {
                    setInviting(false);
                    setEmail('');
                    setFullName('');
                    setPassword('');
                    setRole('editor');
                  },
                },
              );
            }}
          >
            <Field label={t('admin.users.name')} htmlFor="u-name">
              <TextInput
                id="u-name"
                required
                value={fullName}
                onChange={(event) => {
                  setFullName(event.target.value);
                }}
              />
            </Field>
            <Field label={t('admin.users.email')} htmlFor="u-email">
              <TextInput
                id="u-email"
                type="email"
                required
                value={email}
                onChange={(event) => {
                  setEmail(event.target.value);
                }}
              />
            </Field>
            <Field label={t('admin.users.password')} htmlFor="u-password">
              <TextInput
                id="u-password"
                type="password"
                required
                minLength={12}
                autoComplete="new-password"
                value={password}
                onChange={(event) => {
                  setPassword(event.target.value);
                }}
              />
            </Field>
            <Field label={t('admin.users.role')} hint={t('admin.users.roleHint')} htmlFor="u-role">
              <select
                id="u-role"
                value={role}
                onChange={(event) => {
                  setRole(event.target.value as AdminRole);
                }}
                className="w-full rounded-lg border border-sand bg-white px-3 py-2 text-sm"
              >
                <option value="editor">{t('admin.users.role.editor')}</option>
                <option value="owner">{t('admin.users.role.owner')}</option>
              </select>
            </Field>

            <div className="flex items-center gap-3 sm:col-span-2">
              <Button type="submit" disabled={save.isPending}>
                {save.isPending ? t('common.saving') : t('common.save')}
              </Button>
              {save.isError ? (
                <span className="text-sm text-vine">{save.error.message}</span>
              ) : null}
            </div>
          </form>
        </Card>
      ) : null}

      <Card className="overflow-x-auto">
        <table className="w-full min-w-[42rem] text-left text-sm">
          <thead className="border-b border-sand text-xs tracking-wide text-muted uppercase">
            <tr>
              <th scope="col" className="px-4 py-3">
                {t('admin.users.name')}
              </th>
              <th scope="col" className="px-4 py-3">
                {t('admin.users.role')}
              </th>
              <th scope="col" className="px-4 py-3">
                {t('admin.users.lastLogin')}
              </th>
              <th scope="col" className="px-4 py-3">
                <span className="sr-only">{t('common.edit')}</span>
              </th>
            </tr>
          </thead>
          <tbody>
            {admins.data.map((admin) => {
              const isSelf = me.data?.id === admin.id;
              return (
                <tr key={admin.id} className="border-b border-sand/60 last:border-0">
                  <td className="px-4 py-3">
                    <span className="font-medium">{admin.full_name}</span>
                    <span className="block text-xs text-muted">{admin.email}</span>
                  </td>
                  <td className="px-4 py-3">
                    <Badge tone={admin.role === 'owner' ? 'positive' : 'neutral'}>
                      {t(`admin.users.role.${admin.role}`)}
                    </Badge>
                    {admin.is_active ? null : <Badge tone="warning">✗</Badge>}
                  </td>
                  <td className="px-4 py-3 text-muted">
                    {admin.last_login_at
                      ? formatDateTime(admin.last_login_at, locale)
                      : t('common.never')}
                  </td>
                  <td className="px-4 py-3 text-right whitespace-nowrap">
                    <Button
                      variant="ghost"
                      disabled={save.isPending}
                      onClick={() => {
                        save.mutate({ id: admin.id, values: { is_active: !admin.is_active } });
                      }}
                    >
                      {admin.is_active ? t('admin.users.deactivate') : t('admin.users.activate')}
                    </Button>
                    {isSelf ? null : (
                      <Button
                        variant="ghost"
                        disabled={remove.isPending}
                        onClick={() => {
                          if (window.confirm(t('admin.users.deleteConfirm')))
                            remove.mutate(admin.id);
                        }}
                      >
                        {t('common.delete')}
                      </Button>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {save.isError || remove.isError ? (
        <p role="alert" className="mt-3 text-sm text-vine">
          {(save.error ?? remove.error)?.message}
        </p>
      ) : null}
    </div>
  );
}
