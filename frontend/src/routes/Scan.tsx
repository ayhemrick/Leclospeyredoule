/**
 * Landing page for the QR code: `/a/<code>`.
 *
 * A phone camera opens this URL directly, so the page redeems the code on
 * arrival and then replaces the history entry with `/guide`. The property code
 * therefore does not survive in the back stack, in browser history, or in a
 * screenshot of the address bar taken by the next guest.
 */

import { Link, useNavigate, useParams } from '@tanstack/react-router';
import { useEffect, useRef } from 'react';

import { Button, Card } from '@/components/ui';
import { useLocale } from '@/i18n';
import { ApiError } from '@/lib/api';
import { useRedeemCode } from '@/lib/queries';

export function ScanPage() {
  const { t } = useLocale();
  const { code } = useParams({ from: '/a/$code' });
  const navigate = useNavigate();
  const redemption = useRedeemCode(code);
  const redirected = useRef(false);

  const granted = redemption.data?.granted === true;

  useEffect(() => {
    if (!granted || redirected.current) return;
    redirected.current = true;
    void navigate({ to: '/guide', replace: true });
  }, [granted, navigate]);

  const failureMessage =
    redemption.error instanceof ApiError ? redemption.error.message : t('common.error');

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
        ) : redemption.isError ? (
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
                  void redemption.refetch();
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
