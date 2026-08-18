/** One place to visit, as shown on the public site. */

import { useState } from 'react';

import { pick, useLocale } from '@/i18n';
import { formatDistance } from '@/lib/format';
import type { Attraction } from '@/lib/types';

import { Markdown } from './Markdown';
import { Badge, Card } from './ui';

const CATEGORY_KEY = {
  heritage: 'region.filter.heritage',
  wine: 'region.filter.wine',
  nature: 'region.filter.nature',
  gastronomy: 'region.filter.gastronomy',
  family: 'region.filter.family',
} as const;

export function AttractionCard({ attraction }: { attraction: Attraction }) {
  const { locale, t } = useLocale();
  const [expanded, setExpanded] = useState(false);

  const name = pick(attraction.name, locale);
  const description = pick(attraction.description, locale);
  const distance = formatDistance(attraction.distance_km);

  return (
    <Card className="flex h-full flex-col overflow-hidden">
      {attraction.image_path ? (
        <figure className="relative">
          <img
            src={attraction.image_path}
            alt={name}
            loading="lazy"
            decoding="async"
            className="h-44 w-full object-cover"
          />
          {attraction.image_credit ? (
            <figcaption className="absolute right-0 bottom-0 bg-ink/60 px-2 py-0.5 text-[0.65rem] text-stone">
              {attraction.image_credit}
            </figcaption>
          ) : null}
        </figure>
      ) : null}

      <div className="flex flex-1 flex-col p-5">
        <div className="mb-2 flex flex-wrap items-center gap-2">
          <Badge>{t(CATEGORY_KEY[attraction.category])}</Badge>
          {distance ? (
            <span className="text-xs text-muted">{t('region.distance', { distance })}</span>
          ) : null}
          {attraction.travel_time_min ? (
            <span className="text-xs text-muted">
              · {t('region.duration', { minutes: attraction.travel_time_min })}
            </span>
          ) : null}
        </div>

        <h3 className="text-lg leading-snug">{name}</h3>
        <p className="mt-2 text-sm text-ink/80">{pick(attraction.summary, locale)}</p>

        {description ? (
          <>
            {expanded ? <Markdown text={description} className="prose-house mt-3" /> : null}
            <button
              type="button"
              onClick={() => {
                setExpanded((open) => !open);
              }}
              aria-expanded={expanded}
              className="mt-3 self-start text-sm font-medium text-vine underline underline-offset-2"
            >
              {expanded ? t('common.readLess') : t('common.readMore')}
            </button>
          </>
        ) : null}

        {attraction.website_url ? (
          <a
            href={attraction.website_url}
            target="_blank"
            rel="noreferrer noopener"
            className="mt-auto pt-3 text-sm text-vine underline underline-offset-2"
          >
            {t('region.website')} ↗
          </a>
        ) : null}
      </div>
    </Card>
  );
}
