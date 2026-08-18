/** Editing the "what to visit" list. */

import { useState } from 'react';

import {
  Badge,
  Button,
  Card,
  ErrorState,
  Field,
  Loading,
  SectionHeading,
  TextArea,
  TextInput,
  Toggle,
} from '@/components/ui';
import { useLocale } from '@/i18n';
import { useAdminAttractions, useDeleteAttraction, useSaveAttraction } from '@/lib/queries';
import type { AdminAttraction, AttractionCategory } from '@/lib/types';

const CATEGORIES: AttractionCategory[] = ['heritage', 'wine', 'nature', 'gastronomy', 'family'];

interface Draft {
  slug: string;
  category: AttractionCategory;
  position: number;
  is_published: boolean;
  name_fr: string;
  name_en: string;
  summary_fr: string;
  summary_en: string;
  description_fr: string;
  description_en: string;
  distance_km: string;
  travel_time_min: string;
  website_url: string;
  image_path: string;
  image_credit: string;
}

const EMPTY: Draft = {
  slug: '',
  category: 'heritage',
  position: 100,
  is_published: true,
  name_fr: '',
  name_en: '',
  summary_fr: '',
  summary_en: '',
  description_fr: '',
  description_en: '',
  distance_km: '',
  travel_time_min: '',
  website_url: '',
  image_path: '',
  image_credit: '',
};

function toDraft(attraction: AdminAttraction): Draft {
  return {
    slug: attraction.slug,
    category: attraction.category,
    position: attraction.position,
    is_published: attraction.is_published,
    name_fr: attraction.name_fr,
    name_en: attraction.name_en,
    summary_fr: attraction.summary_fr,
    summary_en: attraction.summary_en,
    description_fr: attraction.description_fr,
    description_en: attraction.description_en,
    distance_km: attraction.distance_km ?? '',
    travel_time_min: attraction.travel_time_min?.toString() ?? '',
    website_url: attraction.website_url ?? '',
    image_path: attraction.image_path ?? '',
    image_credit: attraction.image_credit ?? '',
  };
}

/** Optional fields go as `null`, not empty strings, so the API validates them. */
function toPayload(draft: Draft, isUpdate: boolean): Record<string, unknown> {
  const payload: Record<string, unknown> = {
    category: draft.category,
    position: draft.position,
    is_published: draft.is_published,
    name_fr: draft.name_fr,
    name_en: draft.name_en,
    summary_fr: draft.summary_fr,
    summary_en: draft.summary_en,
    description_fr: draft.description_fr,
    description_en: draft.description_en,
    distance_km: draft.distance_km.trim() === '' ? null : draft.distance_km.trim(),
    travel_time_min: draft.travel_time_min.trim() === '' ? null : Number(draft.travel_time_min),
    website_url: draft.website_url.trim() === '' ? null : draft.website_url.trim(),
    image_path: draft.image_path.trim() === '' ? null : draft.image_path.trim(),
    image_credit: draft.image_credit.trim() === '' ? null : draft.image_credit.trim(),
  };
  if (!isUpdate) payload.slug = draft.slug;
  return payload;
}

function AttractionForm({
  initial,
  attractionId,
  onDone,
}: {
  initial: Draft;
  attractionId?: string;
  onDone: () => void;
}) {
  const { t } = useLocale();
  const [draft, setDraft] = useState<Draft>(initial);
  const save = useSaveAttraction();

  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  const creditMissing = draft.image_path.trim() !== '' && draft.image_credit.trim() === '';

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        if (creditMissing) return;
        save.mutate(
          {
            ...(attractionId ? { id: attractionId } : {}),
            values: toPayload(draft, attractionId !== undefined),
          },
          { onSuccess: onDone },
        );
      }}
    >
      {attractionId ? null : (
        <Field label={t('admin.content.slug')} htmlFor="a-slug">
          <TextInput
            id="a-slug"
            required
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            value={draft.slug}
            onChange={(event) => {
              set('slug', event.target.value);
            }}
          />
        </Field>
      )}

      <div className="grid gap-4 sm:grid-cols-4">
        <Field label={t('admin.content.category')} htmlFor="a-category">
          <select
            id="a-category"
            value={draft.category}
            onChange={(event) => {
              set('category', event.target.value as AttractionCategory);
            }}
            className="w-full rounded-lg border border-sand bg-white px-3 py-2 text-sm"
          >
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {t(`region.filter.${category}`)}
              </option>
            ))}
          </select>
        </Field>
        <Field label={t('admin.attractions.distance')} htmlFor="a-distance">
          <TextInput
            id="a-distance"
            inputMode="decimal"
            value={draft.distance_km}
            onChange={(event) => {
              set('distance_km', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.attractions.duration')} htmlFor="a-duration">
          <TextInput
            id="a-duration"
            inputMode="numeric"
            value={draft.travel_time_min}
            onChange={(event) => {
              set('travel_time_min', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.content.position')} htmlFor="a-position">
          <TextInput
            id="a-position"
            type="number"
            min={0}
            max={999}
            value={draft.position}
            onChange={(event) => {
              set('position', Number(event.target.value));
            }}
          />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Field label={t('admin.attractions.nameFr')} htmlFor="a-name-fr">
          <TextInput
            id="a-name-fr"
            required
            value={draft.name_fr}
            onChange={(event) => {
              set('name_fr', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.attractions.nameEn')} htmlFor="a-name-en">
          <TextInput
            id="a-name-en"
            required
            value={draft.name_en}
            onChange={(event) => {
              set('name_en', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.attractions.summaryFr')} htmlFor="a-summary-fr">
          <TextArea
            id="a-summary-fr"
            rows={3}
            required
            value={draft.summary_fr}
            onChange={(event) => {
              set('summary_fr', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.attractions.summaryEn')} htmlFor="a-summary-en">
          <TextArea
            id="a-summary-en"
            rows={3}
            required
            value={draft.summary_en}
            onChange={(event) => {
              set('summary_en', event.target.value);
            }}
          />
        </Field>
        <Field
          label={t('admin.attractions.descriptionFr')}
          hint={t('admin.content.markdownHint')}
          htmlFor="a-desc-fr"
        >
          <TextArea
            id="a-desc-fr"
            rows={6}
            value={draft.description_fr}
            onChange={(event) => {
              set('description_fr', event.target.value);
            }}
          />
        </Field>
        <Field
          label={t('admin.attractions.descriptionEn')}
          hint={t('admin.content.markdownHint')}
          htmlFor="a-desc-en"
        >
          <TextArea
            id="a-desc-en"
            rows={6}
            value={draft.description_en}
            onChange={(event) => {
              set('description_en', event.target.value);
            }}
          />
        </Field>
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Field label={t('admin.attractions.website')} htmlFor="a-website">
          <TextInput
            id="a-website"
            type="url"
            value={draft.website_url}
            onChange={(event) => {
              set('website_url', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.attractions.image')} htmlFor="a-image">
          <TextInput
            id="a-image"
            value={draft.image_path}
            placeholder="/images/…"
            onChange={(event) => {
              set('image_path', event.target.value);
            }}
          />
        </Field>
        <Field
          label={t('admin.attractions.credit')}
          htmlFor="a-credit"
          {...(creditMissing ? { error: t('admin.attractions.creditRequired') } : {})}
        >
          <TextInput
            id="a-credit"
            value={draft.image_credit}
            onChange={(event) => {
              set('image_credit', event.target.value);
            }}
          />
        </Field>
      </div>

      <Toggle
        id={`a-published-${attractionId ?? 'new'}`}
        checked={draft.is_published}
        onChange={(value) => {
          set('is_published', value);
        }}
        label={t('admin.content.published')}
      />

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={save.isPending || creditMissing}>
          {save.isPending ? t('common.saving') : t('common.save')}
        </Button>
        <Button type="button" variant="ghost" onClick={onDone}>
          {t('common.cancel')}
        </Button>
        {save.isError ? <span className="text-sm text-vine">{save.error.message}</span> : null}
      </div>
    </form>
  );
}

export function AdminAttractionsEditor() {
  const { locale, t } = useLocale();
  const attractions = useAdminAttractions();
  const remove = useDeleteAttraction();
  const [editing, setEditing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  if (attractions.isPending) return <Loading />;
  if (attractions.isError) {
    return (
      <ErrorState
        onRetry={() => {
          void attractions.refetch();
        }}
      />
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <SectionHeading as="h1" title={t('admin.attractions.title')} />
        <Button
          onClick={() => {
            setCreating((open) => !open);
            setEditing(null);
          }}
        >
          {creating ? t('common.cancel') : t('admin.attractions.new')}
        </Button>
      </div>

      {creating ? (
        <Card className="mb-6 p-6">
          <AttractionForm
            initial={EMPTY}
            onDone={() => {
              setCreating(false);
            }}
          />
        </Card>
      ) : null}

      <div className="space-y-4">
        {attractions.data.map((attraction) => (
          <Card key={attraction.id} className="p-5">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg">
                {locale === 'fr' ? attraction.name_fr : attraction.name_en}
              </h2>
              <Badge>{t(`region.filter.${attraction.category}`)}</Badge>
              {attraction.is_published ? null : <Badge tone="warning">✗</Badge>}
              <code className="text-xs text-muted">{attraction.slug}</code>

              <div className="ml-auto flex gap-2">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setEditing((current) => (current === attraction.id ? null : attraction.id));
                    setCreating(false);
                  }}
                >
                  {editing === attraction.id ? t('common.close') : t('common.edit')}
                </Button>
                <Button
                  variant="ghost"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (window.confirm(t('admin.attractions.deleteConfirm'))) {
                      remove.mutate(attraction.id);
                    }
                  }}
                >
                  {t('common.delete')}
                </Button>
              </div>
            </div>

            {editing === attraction.id ? (
              <div className="mt-5 border-t border-sand pt-5">
                <AttractionForm
                  initial={toDraft(attraction)}
                  attractionId={attraction.id}
                  onDone={() => {
                    setEditing(null);
                  }}
                />
              </div>
            ) : (
              <p className="mt-2 text-sm text-muted">
                {locale === 'fr' ? attraction.summary_fr : attraction.summary_en}
              </p>
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
