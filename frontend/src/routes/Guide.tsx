/**
 * The guest guide, behind the scanned code.
 *
 * The gate is enforced by the API; this page mirrors it so the visitor sees an
 * explanation rather than an error, and shows how long their access lasts.
 */

import { Link } from '@tanstack/react-router';
import { useEffect, useMemo, useState } from 'react';

import { Markdown } from '@/components/Markdown';
import { Button, Card, ErrorState, Loading, SectionHeading } from '@/components/ui';
import { pick, useLocale } from '@/i18n';
import type { MessageKey } from '@/i18n/messages';
import { formatDuration } from '@/lib/format';
import { useAccessStatus, useGuestGuide, useLeaveAccess } from '@/lib/queries';
import type { GuideCategory, GuideSection } from '@/lib/types';

const CATEGORY_ORDER: GuideCategory[] = ['arrival', 'house', 'practical', 'rules', 'local_tips'];
const CATEGORY_KEY: Record<GuideCategory, MessageKey> = {
  arrival: 'guide.category.arrival',
  house: 'guide.category.house',
  practical: 'guide.category.practical',
  rules: 'guide.category.rules',
  local_tips: 'guide.category.local_tips',
};

/** Seconds left on the visitor's window, recomputed every 30 seconds. */
function useCountdown(expiresAt: string | null | undefined): number | null {
  const target = useMemo(() => (expiresAt ? new Date(expiresAt).getTime() : null), [expiresAt]);
  const [now, setNow] = useState(() => Date.now());

  useEffect(() => {
    if (target === null) return;
    const timer = window.setInterval(() => {
      setNow(Date.now());
    }, 30_000);
    return () => {
      window.clearInterval(timer);
    };
  }, [target]);

  if (target === null) return null;
  return Math.max(0, Math.round((target - now) / 1000));
}

function LockedNotice() {
  const { t } = useLocale();
  return (
    <Card className="mx-auto max-w-2xl p-8 text-center">
      <p className="text-3xl" aria-hidden="true">
        🔒
      </p>
      <h1 className="mt-4 text-2xl">{t('guide.locked.title')}</h1>
      <p className="mt-3 text-sm text-ink/80">{t('guide.locked.body')}</p>
      <div className="mt-6">
        <Link to="/">
          <Button variant="secondary">{t('scan.home')}</Button>
        </Link>
      </div>
    </Card>
  );
}

function GuideGroup({ category, sections }: { category: GuideCategory; sections: GuideSection[] }) {
  const { locale, t } = useLocale();
  return (
    <section aria-labelledby={`group-${category}`} className="space-y-4">
      <h2
        id={`group-${category}`}
        className="text-sm font-semibold tracking-wide text-muted uppercase"
      >
        {t(CATEGORY_KEY[category])}
      </h2>
      {sections.map((section) => (
        <Card key={section.id} className="p-6">
          <h3 className="text-lg">{pick(section.title, locale)}</h3>
          <Markdown text={pick(section.body, locale)} className="prose-house mt-2" />
        </Card>
      ))}
    </section>
  );
}

export function GuidePage() {
  const { t } = useLocale();
  const status = useAccessStatus();
  const granted = status.data?.granted === true;
  const guide = useGuestGuide(granted);
  const leave = useLeaveAccess();
  const secondsLeft = useCountdown(status.data?.expires_at);

  const grouped = useMemo(() => {
    const sections = guide.data ?? [];
    return CATEGORY_ORDER.map((category) => ({
      category,
      sections: sections.filter((section) => section.category === category),
    })).filter((group) => group.sections.length > 0);
  }, [guide.data]);

  if (status.isPending) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <Loading />
      </div>
    );
  }

  if (!granted) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-16 sm:px-6">
        <LockedNotice />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-4xl px-4 py-14 sm:px-6">
      <SectionHeading as="h1" title={t('guide.title')} subtitle={t('guide.subtitle')} />

      <div className="mb-8 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-card)] bg-moss/8 px-4 py-3">
        <p className="text-sm text-moss">
          {secondsLeft === null
            ? null
            : t('guide.remaining', { duration: formatDuration(secondsLeft, t) })}
        </p>
        <Button
          variant="ghost"
          onClick={() => {
            leave.mutate();
          }}
          disabled={leave.isPending}
        >
          {t('guide.leave')}
        </Button>
      </div>

      {guide.isPending ? <Loading /> : null}
      {guide.isError ? (
        <ErrorState
          onRetry={() => {
            void guide.refetch();
          }}
        />
      ) : null}

      <div className="space-y-10">
        {grouped.map((group) => (
          <GuideGroup key={group.category} category={group.category} sections={group.sections} />
        ))}
      </div>
    </div>
  );
}
