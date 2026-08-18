/**
 * The printable QR poster and the rules behind it.
 *
 * The QR arrives from the API as SVG markup. It is shown through a data URL in
 * an `<img>` rather than injected into the DOM, so nothing the server sends can
 * execute in the admin's session.
 */

import { useEffect, useState } from 'react';

import {
  Button,
  Card,
  ErrorState,
  Field,
  Loading,
  SectionHeading,
  TextInput,
  Toggle,
} from '@/components/ui';
import { useLocale } from '@/i18n';
import { formatDateTime, splitInterval, toMinutes } from '@/lib/format';
import { useAccessCode, useAccessPolicy, useRotateCode, useUpdatePolicy } from '@/lib/queries';
import type { AccessCode, AccessPolicy } from '@/lib/types';

type Unit = 'minutes' | 'hours' | 'days';

function qrDataUrl(svg: string): string {
  return `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`;
}

function Poster({ code }: { code: AccessCode }) {
  const { locale, t } = useLocale();

  return (
    <Card className="p-6">
      <div className="flex flex-wrap items-start justify-between gap-3 no-print">
        <div>
          <h2 className="text-xl">{t('admin.access.poster')}</h2>
          <p className="mt-1 max-w-md text-sm text-muted">{t('admin.access.posterHint')}</p>
        </div>
        <Button
          variant="secondary"
          onClick={() => {
            window.print();
          }}
        >
          {t('admin.access.print')}
        </Button>
      </div>

      <div className="mt-6 rounded-[var(--radius-card)] border border-sand p-8 text-center">
        <p className="font-display text-2xl text-moss">Clos Peyredoule</p>
        <p className="mt-1 text-sm text-muted">
          {locale === 'fr' ? 'Guide des hôtes — scannez pour ouvrir' : 'Guest guide — scan to open'}
        </p>
        <img
          src={qrDataUrl(code.qr_svg)}
          alt={locale === 'fr' ? 'Code QR d’accès au guide' : 'QR code opening the guest guide'}
          className="mx-auto mt-6 size-56"
        />
        <p className="mt-4 font-mono text-xs break-all text-muted">{code.poster_url}</p>
      </div>

      <dl className="mt-5 grid gap-2 text-sm no-print sm:grid-cols-2">
        <div className="flex gap-2">
          <dt className="text-muted">{t('admin.access.scans', { n: code.scan_count })}</dt>
        </div>
        <div className="sm:text-right">
          <dd className="text-muted">
            {code.expires_at
              ? t('admin.access.expires', { date: formatDateTime(code.expires_at, locale) })
              : t('admin.access.noExpiry')}
          </dd>
        </div>
      </dl>
    </Card>
  );
}

function PolicyForm({ policy, canEdit }: { policy: AccessPolicy; canEdit: boolean }) {
  const { t } = useLocale();
  const update = useUpdatePolicy();

  const initialRotation = splitInterval(policy.rotation_interval_minutes);
  const initialSession = splitInterval(policy.guest_session_minutes);

  const [autoRotate, setAutoRotate] = useState(policy.auto_rotate);
  const [rotationValue, setRotationValue] = useState(initialRotation.value);
  const [rotationUnit, setRotationUnit] = useState<Unit>(initialRotation.unit);
  const [sessionValue, setSessionValue] = useState(initialSession.value);
  const [sessionUnit, setSessionUnit] = useState<Unit>(initialSession.unit);
  const [revokeOnRotation, setRevokeOnRotation] = useState(policy.revoke_sessions_on_rotation);
  const [maxSessions, setMaxSessions] = useState(policy.max_active_sessions);

  useEffect(() => {
    if (!update.isSuccess) return;
    const timer = window.setTimeout(() => {
      update.reset();
    }, 2500);
    return () => {
      window.clearTimeout(timer);
    };
  }, [update]);

  return (
    <Card className="p-6">
      <h2 className="text-xl">{t('admin.access.settings')}</h2>

      <form
        className="mt-5 space-y-5"
        onSubmit={(event) => {
          event.preventDefault();
          update.mutate({
            auto_rotate: autoRotate,
            rotation_interval_minutes: toMinutes(rotationValue, rotationUnit),
            guest_session_minutes: toMinutes(sessionValue, sessionUnit),
            revoke_sessions_on_rotation: revokeOnRotation,
            max_active_sessions: maxSessions,
          });
        }}
      >
        <Toggle
          id="auto-rotate"
          checked={autoRotate}
          onChange={setAutoRotate}
          label={t('admin.access.autoRotate')}
          hint={t('admin.access.autoRotateHint')}
        />

        <Field label={t('admin.access.interval')} htmlFor="rotation-value">
          <div className="flex gap-2">
            <TextInput
              id="rotation-value"
              type="number"
              min={1}
              max={999}
              value={rotationValue}
              disabled={!autoRotate}
              onChange={(event) => {
                setRotationValue(Number(event.target.value));
              }}
              className="w-28"
            />
            <select
              aria-label={t('admin.access.intervalUnit')}
              value={rotationUnit}
              disabled={!autoRotate}
              onChange={(event) => {
                setRotationUnit(event.target.value as Unit);
              }}
              className="rounded-lg border border-sand bg-white px-3 py-2 text-sm"
            >
              <option value="minutes">{t('admin.access.unit.minutes')}</option>
              <option value="hours">{t('admin.access.unit.hours')}</option>
              <option value="days">{t('admin.access.unit.days')}</option>
            </select>
          </div>
        </Field>

        <Field label={t('admin.access.sessionLength')} htmlFor="session-value">
          <div className="flex gap-2">
            <TextInput
              id="session-value"
              type="number"
              min={1}
              max={999}
              value={sessionValue}
              onChange={(event) => {
                setSessionValue(Number(event.target.value));
              }}
              className="w-28"
            />
            <select
              aria-label={t('admin.access.sessionLengthUnit')}
              value={sessionUnit}
              onChange={(event) => {
                setSessionUnit(event.target.value as Unit);
              }}
              className="rounded-lg border border-sand bg-white px-3 py-2 text-sm"
            >
              <option value="minutes">{t('admin.access.unit.minutes')}</option>
              <option value="hours">{t('admin.access.unit.hours')}</option>
              <option value="days">{t('admin.access.unit.days')}</option>
            </select>
          </div>
        </Field>

        <Toggle
          id="revoke-on-rotation"
          checked={revokeOnRotation}
          onChange={setRevokeOnRotation}
          label={t('admin.access.revokeOnRotation')}
          hint={t('admin.access.revokeOnRotationHint')}
        />

        <Field
          label={t('admin.access.maxSessions')}
          hint={t('admin.access.maxSessionsHint')}
          htmlFor="max-sessions"
        >
          <TextInput
            id="max-sessions"
            type="number"
            min={0}
            max={10_000}
            value={maxSessions}
            onChange={(event) => {
              setMaxSessions(Number(event.target.value));
            }}
            className="w-32"
          />
        </Field>

        <div className="flex items-center gap-3">
          <Button type="submit" disabled={!canEdit || update.isPending}>
            {update.isPending ? t('common.saving') : t('common.save')}
          </Button>
          {update.isSuccess ? <span className="text-sm text-moss">{t('common.saved')}</span> : null}
          {!canEdit ? <span className="text-sm text-muted">{t('admin.ownerOnly')}</span> : null}
          {update.isError ? (
            <span className="text-sm text-vine">{update.error.message}</span>
          ) : null}
        </div>
      </form>
    </Card>
  );
}

export function AdminAccess({ isOwner }: { isOwner: boolean }) {
  const { t } = useLocale();
  const code = useAccessCode();
  const policy = useAccessPolicy();
  const rotate = useRotateCode();

  if (code.isPending || policy.isPending) return <Loading />;
  if (code.isError || policy.isError) {
    return (
      <ErrorState
        onRetry={() => {
          void code.refetch();
          void policy.refetch();
        }}
      />
    );
  }

  return (
    <div className="space-y-6">
      <SectionHeading as="h1" title={t('admin.access.title')} />

      <Poster code={code.data} />

      <Card className="flex flex-wrap items-center gap-4 p-6 no-print">
        <div className="min-w-0 flex-1">
          <h2 className="text-lg">{t('admin.access.rotate')}</h2>
          <p className="mt-1 text-sm text-muted">{t('admin.access.rotateConfirm')}</p>
        </div>
        <Button
          variant="danger"
          disabled={!isOwner || rotate.isPending}
          onClick={() => {
            if (window.confirm(t('admin.access.rotateConfirm'))) rotate.mutate();
          }}
        >
          {t('admin.access.rotate')}
        </Button>
        {rotate.isSuccess ? (
          <span className="text-sm text-moss">{t('admin.access.rotated')}</span>
        ) : null}
        {!isOwner ? <span className="text-sm text-muted">{t('admin.ownerOnly')}</span> : null}
      </Card>

      <div className="no-print">
        <PolicyForm policy={policy.data} canEdit={isOwner} />
      </div>
    </div>
  );
}
