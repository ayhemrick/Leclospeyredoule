/** Administrator sign-in form. */

import { useState, type SyntheticEvent } from 'react';

import { Button, Card, Field, TextInput } from '@/components/ui';
import { useLocale } from '@/i18n';
import { ApiError } from '@/lib/api';
import { useLogin } from '@/lib/queries';

export function LoginPage() {
  const { t } = useLocale();
  const login = useLogin();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const errorMessage = login.isError
    ? login.error instanceof ApiError && login.error.status === 429
      ? t('admin.login.locked')
      : t('admin.login.failed')
    : undefined;

  function handleSubmit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    login.mutate({ email, password });
  }

  return (
    <div className="grid min-h-dvh place-items-center bg-stone px-4">
      <Card className="w-full max-w-sm p-8">
        <h1 className="font-display text-2xl text-moss">Clos Peyredoule</h1>
        <p className="mt-1 text-sm text-muted">{t('admin.login.title')}</p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4" noValidate>
          <Field label={t('admin.login.email')} htmlFor="email">
            <TextInput
              id="email"
              type="email"
              name="email"
              autoComplete="username"
              required
              value={email}
              onChange={(event) => {
                setEmail(event.target.value);
              }}
            />
          </Field>

          <Field label={t('admin.login.password')} htmlFor="password" error={errorMessage}>
            <TextInput
              id="password"
              type="password"
              name="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(event) => {
                setPassword(event.target.value);
              }}
            />
          </Field>

          <Button type="submit" className="w-full" disabled={login.isPending}>
            {login.isPending ? t('admin.login.working') : t('admin.login.submit')}
          </Button>
        </form>
      </Card>
    </div>
  );
}
