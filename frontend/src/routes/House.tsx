/** The publicly readable part of the house guide. */

import { Markdown } from '@/components/Markdown';
import { Card, ErrorState, Loading, SectionHeading } from '@/components/ui';
import { pick, useLocale } from '@/i18n';
import { usePublicGuide } from '@/lib/queries';

export function HousePage() {
  const { locale, t } = useLocale();
  const guide = usePublicGuide();

  return (
    <div className="mx-auto max-w-4xl px-4 py-14 sm:px-6">
      <SectionHeading as="h1" title={t('house.title')} subtitle={t('house.subtitle')} />

      {guide.isPending ? <Loading /> : null}
      {guide.isError ? (
        <ErrorState
          onRetry={() => {
            void guide.refetch();
          }}
        />
      ) : null}

      <div className="space-y-6">
        {(guide.data ?? []).map((section) => (
          <Card key={section.id} className="p-6 sm:p-8">
            <h2 className="text-xl sm:text-2xl">{pick(section.title, locale)}</h2>
            <Markdown text={pick(section.body, locale)} className="prose-house mt-3" />
          </Card>
        ))}
      </div>

      <figure className="mt-12 space-y-2">
        <img
          src="/images/vignoble-blaye.jpg"
          alt={locale === 'fr' ? 'Vignes du Blayais' : 'Vines around Blaye'}
          loading="lazy"
          className="w-full rounded-[var(--radius-card)] object-cover shadow-[var(--shadow-card)]"
        />
        <figcaption className="text-xs text-muted">
          Photo Cobber17, CC BY 3.0, via Wikimedia Commons
        </figcaption>
      </figure>
    </div>
  );
}
