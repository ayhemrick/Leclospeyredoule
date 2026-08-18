/** Photo credits, kept in the app so attribution travels with the images. */

import { Link } from '@tanstack/react-router';

import { Button, Card, SectionHeading } from '@/components/ui';
import { useLocale } from '@/i18n';
import credits from '@/content/image-credits.json';

interface Credit {
  file: string;
  author: string;
  licence: string;
  licenceUrl: string;
  source: string;
}

const entries = Object.entries(credits as Record<string, Credit>);

export function CreditsPage() {
  const { t } = useLocale();

  return (
    <div className="mx-auto max-w-4xl px-4 py-14 sm:px-6">
      <SectionHeading as="h1" title={t('credits.title')} subtitle={t('credits.intro')} />

      <div className="space-y-4">
        {entries.map(([slug, credit]) => (
          <Card key={slug} className="flex flex-col gap-4 p-4 sm:flex-row sm:items-center">
            <img
              src={`/images/${slug}.jpg`}
              alt={credit.file}
              loading="lazy"
              className="h-24 w-full rounded-lg object-cover sm:w-40"
            />
            <dl className="grid flex-1 gap-x-4 gap-y-1 text-sm sm:grid-cols-[auto_1fr]">
              <dt className="text-muted">{t('credits.author')}</dt>
              <dd>{credit.author}</dd>
              <dt className="text-muted">{t('credits.licence')}</dt>
              <dd>
                <a
                  href={credit.licenceUrl}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-vine underline underline-offset-2"
                >
                  {credit.licence}
                </a>
              </dd>
              <dt className="text-muted">{t('credits.source')}</dt>
              <dd>
                <a
                  href={credit.source}
                  target="_blank"
                  rel="noreferrer noopener"
                  className="text-vine underline underline-offset-2"
                >
                  {credit.file}
                </a>
              </dd>
            </dl>
          </Card>
        ))}
      </div>

      <div className="mt-10">
        <Link to="/">
          <Button variant="secondary">{t('common.back')}</Button>
        </Link>
      </div>
    </div>
  );
}

export function NotFoundPage() {
  const { t } = useLocale();
  return (
    <div className="mx-auto max-w-2xl px-4 py-24 text-center sm:px-6">
      <h1 className="text-3xl">{t('common.notFound')}</h1>
      <p className="mt-3 text-muted">{t('common.notFoundBody')}</p>
      <div className="mt-8">
        <Link to="/">
          <Button>{t('scan.home')}</Button>
        </Link>
      </div>
    </div>
  );
}
