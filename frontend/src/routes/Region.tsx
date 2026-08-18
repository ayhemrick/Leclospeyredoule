/** Everything to see around Blaye, filterable by category. */

import { useState } from 'react';

import { AttractionCard } from '@/components/AttractionCard';
import { EmptyState, ErrorState, Loading, SectionHeading } from '@/components/ui';
import { useLocale } from '@/i18n';
import type { MessageKey } from '@/i18n/messages';
import { useAttractions } from '@/lib/queries';
import type { AttractionCategory } from '@/lib/types';

const FILTERS: { value: AttractionCategory | 'all'; key: MessageKey }[] = [
  { value: 'all', key: 'region.filter.all' },
  { value: 'heritage', key: 'region.filter.heritage' },
  { value: 'wine', key: 'region.filter.wine' },
  { value: 'nature', key: 'region.filter.nature' },
  { value: 'gastronomy', key: 'region.filter.gastronomy' },
  { value: 'family', key: 'region.filter.family' },
];

export function RegionPage() {
  const { t } = useLocale();
  const [filter, setFilter] = useState<AttractionCategory | 'all'>('all');
  const attractions = useAttractions(filter === 'all' ? undefined : filter);

  return (
    <div className="mx-auto max-w-6xl px-4 py-14 sm:px-6">
      <SectionHeading as="h1" title={t('region.title')} subtitle={t('region.subtitle')} />

      <div role="group" aria-label={t('region.title')} className="mb-8 flex flex-wrap gap-2">
        {FILTERS.map((option) => {
          const selected = option.value === filter;
          return (
            <button
              key={option.value}
              type="button"
              aria-pressed={selected}
              onClick={() => {
                setFilter(option.value);
              }}
              className={`rounded-full border px-4 py-1.5 text-sm transition-colors ${
                selected
                  ? 'border-moss bg-moss text-stone'
                  : 'border-sand bg-white text-ink/80 hover:bg-sand'
              }`}
            >
              {t(option.key)}
            </button>
          );
        })}
      </div>

      {attractions.isPending ? <Loading /> : null}
      {attractions.isError ? (
        <ErrorState
          onRetry={() => {
            void attractions.refetch();
          }}
        />
      ) : null}
      {attractions.isSuccess && attractions.data.length === 0 ? (
        <EmptyState message={t('region.empty')} />
      ) : null}

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {(attractions.data ?? []).map((attraction) => (
          <AttractionCard key={attraction.id} attraction={attraction} />
        ))}
      </div>
    </div>
  );
}
