/** The flyer: what the property is, what is nearby, how guests get in. */

import { Link } from '@tanstack/react-router';

import { AttractionCard } from '@/components/AttractionCard';
import { Markdown } from '@/components/Markdown';
import { Button, Card, ErrorState, Loading, SectionHeading } from '@/components/ui';
import { pick, useLocale } from '@/i18n';
import { useAccessStatus, useAttractions, usePublicGuide } from '@/lib/queries';

export function HomePage() {
  const { locale, t } = useLocale();
  const attractions = useAttractions();
  const guide = usePublicGuide();
  const { data: access } = useAccessStatus();

  const story = guide.data?.find((section) => section.slug === 'histoire-du-clos');
  const highlights = (attractions.data ?? []).slice(0, 3);

  return (
    <>
      <section className="relative isolate">
        <img
          src="/images/citadelle-de-blaye.jpg"
          alt=""
          aria-hidden="true"
          className="absolute inset-0 -z-10 size-full object-cover"
        />
        <div className="absolute inset-0 -z-10 bg-gradient-to-b from-ink/75 via-ink/55 to-ink/80" />

        <div className="mx-auto flex max-w-6xl flex-col justify-end px-4 py-24 sm:px-6 sm:py-32">
          <p className="text-xs font-medium tracking-[0.2em] text-stone/80 uppercase">
            {t('home.hero.eyebrow')}
          </p>
          <h1 className="mt-3 max-w-2xl text-4xl text-stone sm:text-5xl">{t('site.name')}</h1>
          <p className="mt-4 max-w-xl text-lg text-stone/90">{t('site.tagline')}</p>

          <div className="mt-8 flex flex-wrap gap-3">
            <Link to="/decouvrir">
              <Button>{t('home.hero.cta')}</Button>
            </Link>
            <Link to="/la-maison">
              <Button variant="secondary">{t('home.hero.secondary')}</Button>
            </Link>
          </div>
        </div>
      </section>

      <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
        <section className="grid gap-10 lg:grid-cols-[minmax(0,3fr)_minmax(0,2fr)]">
          <div>
            <SectionHeading title={t('home.intro.title')} />
            {guide.isPending ? <Loading /> : null}
            {story ? <Markdown text={pick(story.body, locale)} /> : null}
          </div>

          <figure className="space-y-2">
            <img
              src="/images/blaye-remparts.jpg"
              alt={locale === 'fr' ? 'Blaye vue depuis l’estuaire' : 'Blaye seen from the estuary'}
              loading="lazy"
              className="w-full rounded-[var(--radius-card)] object-cover shadow-[var(--shadow-card)]"
            />
            <figcaption className="text-xs text-muted">
              Photo Cobber17, CC BY-SA 3.0, via Wikimedia Commons
            </figcaption>
          </figure>
        </section>

        <section className="mt-20">
          <SectionHeading
            title={t('home.highlights.title')}
            subtitle={t('home.highlights.subtitle')}
          />
          {attractions.isPending ? <Loading /> : null}
          {attractions.isError ? (
            <ErrorState
              onRetry={() => {
                void attractions.refetch();
              }}
            />
          ) : null}
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {highlights.map((attraction) => (
              <AttractionCard key={attraction.id} attraction={attraction} />
            ))}
          </div>
          <div className="mt-8">
            <Link to="/decouvrir">
              <Button variant="secondary">{t('home.hero.cta')} →</Button>
            </Link>
          </div>
        </section>

        <section className="mt-20">
          <Card className="grid gap-6 p-8 sm:grid-cols-[minmax(0,2fr)_minmax(0,1fr)] sm:items-center">
            <div>
              <h2 className="text-2xl">{t('home.guide.title')}</h2>
              <p className="mt-3 max-w-xl text-sm text-ink/80">{t('home.guide.body')}</p>
            </div>
            <div className="sm:justify-self-end">
              <Link to="/guide">
                <Button variant={access?.granted ? 'primary' : 'secondary'}>
                  {access?.granted ? t('nav.guide') : t('home.guide.cta')}
                </Button>
              </Link>
            </div>
          </Card>
        </section>
      </div>
    </>
  );
}
