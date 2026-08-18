/**
 * Landing page for the QR code: `/a/<code>`.
 *
 * A phone camera opens this URL directly, so the page redeems the code on
 * arrival and then replaces the history entry with `/guide`. The property code
 * therefore does not survive in the back stack, in browser history, or in a
 * screenshot of the address bar taken by the next guest.
 *
 * Success is read from the access-status query rather than from the mutation:
 * the query is the source of truth, and it survives the remount that React's
 * strict mode performs in development.
 */

import { Link, useNavigate, useParams } from '@tanstack/react-router';
import { useEffect, useRef } from 'react';

import { Button, Card } from '@/components/ui';
import { useLocale } from '@/i18n';
import { ApiError } from '@/lib/api';
import { useAccessStatus, useRedeemCode } from '@/lib/queries';

/** Codes already sent during this page session, so a remount does not rescan. */
const attempted = new Set<string>();

export function ScanPage() {
  const { t } = useLocale();
  const { code } = useParams({ from: '/a/$code' });
  const navigate = useNavigate();
  const redeem = useRedeemCode();
  const status = useAccessStatus();

  const { mutate, isError, error, reset } = redeem;
  const granted = status.data?.granted === true;
  const redirected = useRef(false);

  useEffect(() => {
    if (attempted.has(code)) return;
    attempted.add(code);
    mutate(code);
  }, [code, mutate]);

  useEffect(() => {
    if (!granted || redirected.current) return;
    redirected.current = true;
    void navigate({ to: '/guide', replace: true });
  }, [granted, navigate]);

  const failureMessage = error instanceof ApiError ? error.message : t('common.error');

  return (
    <div className="mx-auto flex max-w-2xl flex-col justify-center px-4 py-20 sm:px-6">
      <Card className="p-8 text-center">
        {granted ? (
          <>
            <p className="text-3xl" aria-hidden="true">
              🔓
            </p>
            <h1 className="mt-4 text-2xl">{t('scan.success')}</h1>
            <p className="mt-3 text-sm text-ink/80">{t('scan.successBody')}</p>
            <div className="mt-6">
              <Link to="/guide" replace>
                <Button>{t('scan.continue')}</Button>
              </Link>
            </div>
          </>
        ) : isError ? (
          <>
            <p className="text-3xl" aria-hidden="true">
              ⚠️
            </p>
            <h1 className="mt-4 text-2xl">{t('scan.failed')}</h1>
            <p className="mt-3 text-sm text-ink/80">{failureMessage}</p>
            <div className="mt-6 flex flex-wrap justify-center gap-3">
              <Button
                variant="secondary"
                onClick={() => {
                  reset();
                  attempted.delete(code);
                  mutate(code);
                }}
              >
                {t('scan.retry')}
              </Button>
              <Link to="/">
                <Button variant="ghost">{t('scan.home')}</Button>
              </Link>
            </div>
          </>
        ) : (
          <p role="status" className="text-sm text-muted">
            {t('scan.checking')}
          </p>
        )}
      </Card>
    </div>
  );
}
