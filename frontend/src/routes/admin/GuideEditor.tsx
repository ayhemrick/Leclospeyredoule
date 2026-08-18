/** Editing the bilingual guest guide. */

import { useState } from 'react';

import { Markdown } from '@/components/Markdown';
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
import { useAdminSections, useDeleteSection, useSaveSection } from '@/lib/queries';
import type { AdminGuideSection, GuideCategory, Visibility } from '@/lib/types';

const CATEGORIES: GuideCategory[] = ['arrival', 'house', 'practical', 'rules', 'local_tips'];

interface Draft {
  slug: string;
  category: GuideCategory;
  visibility: Visibility;
  position: number;
  is_published: boolean;
  title_fr: string;
  title_en: string;
  body_fr: string;
  body_en: string;
}

const EMPTY: Draft = {
  slug: '',
  category: 'practical',
  visibility: 'guest',
  position: 100,
  is_published: true,
  title_fr: '',
  title_en: '',
  body_fr: '',
  body_en: '',
};

function toDraft(section: AdminGuideSection): Draft {
  return {
    slug: section.slug,
    category: section.category,
    visibility: section.visibility,
    position: section.position,
    is_published: section.is_published,
    title_fr: section.title_fr,
    title_en: section.title_en,
    body_fr: section.body_fr,
    body_en: section.body_en,
  };
}

function SectionForm({
  initial,
  sectionId,
  onDone,
}: {
  initial: Draft;
  sectionId?: string;
  onDone: () => void;
}) {
  const { t } = useLocale();
  const [draft, setDraft] = useState<Draft>(initial);
  const save = useSaveSection();

  const set = <K extends keyof Draft>(key: K, value: Draft[K]) => {
    setDraft((current) => ({ ...current, [key]: value }));
  };

  return (
    <form
      className="space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        // An existing section keeps its slug: changing it would break links.
        const { slug: _slug, ...withoutSlug } = draft;
        const values: Record<string, unknown> = sectionId ? withoutSlug : draft;
        save.mutate({ ...(sectionId ? { id: sectionId } : {}), values }, { onSuccess: onDone });
      }}
    >
      {sectionId ? null : (
        <Field label={t('admin.content.slug')} htmlFor="slug">
          <TextInput
            id="slug"
            required
            pattern="[a-z0-9]+(-[a-z0-9]+)*"
            value={draft.slug}
            onChange={(event) => {
              set('slug', event.target.value);
            }}
          />
        </Field>
      )}

      <div className="grid gap-4 sm:grid-cols-3">
        <Field label={t('admin.content.category')} htmlFor="category">
          <select
            id="category"
            value={draft.category}
            onChange={(event) => {
              set('category', event.target.value as GuideCategory);
            }}
            className="w-full rounded-lg border border-sand bg-white px-3 py-2 text-sm"
          >
            {CATEGORIES.map((category) => (
              <option key={category} value={category}>
                {t(`guide.category.${category}`)}
              </option>
            ))}
          </select>
        </Field>

        <Field label={t('admin.content.visibility')} htmlFor="visibility">
          <select
            id="visibility"
            value={draft.visibility}
            onChange={(event) => {
              set('visibility', event.target.value as Visibility);
            }}
            className="w-full rounded-lg border border-sand bg-white px-3 py-2 text-sm"
          >
            <option value="public">{t('admin.content.visibility.public')}</option>
            <option value="guest">{t('admin.content.visibility.guest')}</option>
          </select>
        </Field>

        <Field label={t('admin.content.position')} htmlFor="position">
          <TextInput
            id="position"
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
        <Field label={t('admin.content.titleFr')} htmlFor="title-fr">
          <TextInput
            id="title-fr"
            required
            value={draft.title_fr}
            onChange={(event) => {
              set('title_fr', event.target.value);
            }}
          />
        </Field>
        <Field label={t('admin.content.titleEn')} htmlFor="title-en">
          <TextInput
            id="title-en"
            required
            value={draft.title_en}
            onChange={(event) => {
              set('title_en', event.target.value);
            }}
          />
        </Field>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Field
          label={t('admin.content.bodyFr')}
          hint={t('admin.content.markdownHint')}
          htmlFor="body-fr"
        >
          <TextArea
            id="body-fr"
            rows={10}
            required
            value={draft.body_fr}
            onChange={(event) => {
              set('body_fr', event.target.value);
            }}
          />
        </Field>
        <Field
          label={t('admin.content.bodyEn')}
          hint={t('admin.content.markdownHint')}
          htmlFor="body-en"
        >
          <TextArea
            id="body-en"
            rows={10}
            required
            value={draft.body_en}
            onChange={(event) => {
              set('body_en', event.target.value);
            }}
          />
        </Field>
      </div>

      <Toggle
        id={`published-${sectionId ?? 'new'}`}
        checked={draft.is_published}
        onChange={(value) => {
          set('is_published', value);
        }}
        label={t('admin.content.published')}
      />

      <div className="flex flex-wrap items-center gap-3">
        <Button type="submit" disabled={save.isPending}>
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

export function AdminGuideEditor() {
  const { locale, t } = useLocale();
  const sections = useAdminSections();
  const remove = useDeleteSection();
  const [editing, setEditing] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);

  if (sections.isPending) return <Loading />;
  if (sections.isError) {
    return (
      <ErrorState
        onRetry={() => {
          void sections.refetch();
        }}
      />
    );
  }

  return (
    <div>
      <div className="mb-6 flex flex-wrap items-center justify-between gap-3">
        <SectionHeading as="h1" title={t('admin.content.title')} />
        <Button
          onClick={() => {
            setCreating((open) => !open);
            setEditing(null);
          }}
        >
          {creating ? t('common.cancel') : t('admin.content.new')}
        </Button>
      </div>

      {creating ? (
        <Card className="mb-6 p-6">
          <SectionForm
            initial={EMPTY}
            onDone={() => {
              setCreating(false);
            }}
          />
        </Card>
      ) : null}

      <div className="space-y-4">
        {sections.data.map((section) => (
          <Card key={section.id} className="p-5">
            <div className="flex flex-wrap items-center gap-3">
              <h2 className="text-lg">{locale === 'fr' ? section.title_fr : section.title_en}</h2>
              <Badge tone={section.visibility === 'public' ? 'neutral' : 'positive'}>
                {t(`admin.content.visibility.${section.visibility}`)}
              </Badge>
              {section.is_published ? null : (
                <Badge tone="warning">{t('admin.content.published')}: ✗</Badge>
              )}
              <code className="text-xs text-muted">{section.slug}</code>

              <div className="ml-auto flex gap-2">
                <Button
                  variant="secondary"
                  onClick={() => {
                    setEditing((current) => (current === section.id ? null : section.id));
                    setCreating(false);
                  }}
                >
                  {editing === section.id ? t('common.close') : t('common.edit')}
                </Button>
                <Button
                  variant="ghost"
                  disabled={remove.isPending}
                  onClick={() => {
                    if (window.confirm(t('admin.content.deleteConfirm'))) remove.mutate(section.id);
                  }}
                >
                  {t('common.delete')}
                </Button>
              </div>
            </div>

            {editing === section.id ? (
              <div className="mt-5 border-t border-sand pt-5">
                <SectionForm
                  initial={toDraft(section)}
                  sectionId={section.id}
                  onDone={() => {
                    setEditing(null);
                  }}
                />
              </div>
            ) : (
              <Markdown
                text={(locale === 'fr' ? section.body_fr : section.body_en).slice(0, 220)}
                className="prose-house mt-2 line-clamp-3 text-muted"
              />
            )}
          </Card>
        ))}
      </div>
    </div>
  );
}
