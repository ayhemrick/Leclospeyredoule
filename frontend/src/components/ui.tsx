/** Small presentational primitives shared by the public site and the admin. */

import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from 'react';

import { useLocale } from '@/i18n';

type ButtonVariant = 'primary' | 'secondary' | 'ghost' | 'danger';

const BUTTON_STYLES: Record<ButtonVariant, string> = {
  primary: 'bg-moss text-stone hover:bg-moss-soft disabled:bg-moss/50',
  secondary: 'bg-sand text-ink hover:bg-sand/70 disabled:opacity-60',
  ghost: 'bg-transparent text-ink hover:bg-sand/60 disabled:opacity-50',
  danger: 'bg-vine text-stone hover:bg-vine/85 disabled:opacity-60',
};

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

export function Button({ variant = 'primary', className = '', ...props }: ButtonProps) {
  return (
    <button
      {...props}
      className={`inline-flex items-center justify-center gap-2 rounded-lg px-4 py-2 text-sm font-medium transition-colors disabled:cursor-not-allowed ${BUTTON_STYLES[variant]} ${className}`}
    />
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return (
    <div
      className={`rounded-[var(--radius-card)] border border-sand bg-white shadow-[var(--shadow-card)] ${className}`}
    >
      {children}
    </div>
  );
}

export function SectionHeading({
  title,
  subtitle,
  as: Tag = 'h2',
}: {
  title: string;
  subtitle?: string | undefined;
  as?: 'h1' | 'h2';
}) {
  return (
    <header className="mb-6">
      <Tag className={Tag === 'h1' ? 'text-3xl sm:text-4xl' : 'text-2xl sm:text-3xl'}>{title}</Tag>
      {subtitle ? <p className="mt-2 max-w-2xl text-muted">{subtitle}</p> : null}
    </header>
  );
}

export function Field({
  label,
  hint,
  error,
  children,
  htmlFor,
}: {
  label: string;
  hint?: string | undefined;
  error?: string | undefined;
  children: ReactNode;
  htmlFor?: string | undefined;
}) {
  return (
    <div className="space-y-1.5">
      <label htmlFor={htmlFor} className="block text-sm font-medium text-ink">
        {label}
      </label>
      {children}
      {hint ? <p className="text-xs text-muted">{hint}</p> : null}
      {error ? (
        <p role="alert" className="text-xs font-medium text-vine">
          {error}
        </p>
      ) : null}
    </div>
  );
}

export function TextInput(props: InputHTMLAttributes<HTMLInputElement>) {
  const { className = '', ...rest } = props;
  return (
    <input
      {...rest}
      className={`w-full rounded-lg border border-sand bg-white px-3 py-2 text-sm text-ink placeholder:text-muted/70 focus:border-moss ${className}`}
    />
  );
}

export function TextArea({
  className = '',
  ...rest
}: InputHTMLAttributes<HTMLTextAreaElement> & { rows?: number }) {
  return (
    <textarea
      {...rest}
      className={`w-full rounded-lg border border-sand bg-white px-3 py-2 font-mono text-[0.8rem] leading-relaxed text-ink focus:border-moss ${className}`}
    />
  );
}

export function Toggle({
  checked,
  onChange,
  label,
  hint,
  id,
}: {
  checked: boolean;
  onChange: (value: boolean) => void;
  label: string;
  hint?: string;
  id: string;
}) {
  return (
    <div className="flex items-start gap-3">
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={(event) => {
          onChange(event.target.checked);
        }}
        className="mt-1 size-4 rounded border-sand accent-moss"
      />
      <div>
        <label htmlFor={id} className="text-sm font-medium text-ink">
          {label}
        </label>
        {hint ? <p className="text-xs text-muted">{hint}</p> : null}
      </div>
    </div>
  );
}

export function Badge({
  children,
  tone = 'neutral',
}: {
  children: ReactNode;
  tone?: 'neutral' | 'positive' | 'warning';
}) {
  const tones = {
    neutral: 'bg-sand text-ink/80',
    positive: 'bg-moss/10 text-moss',
    warning: 'bg-clay/15 text-clay',
  } as const;
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${tones[tone]}`}>
      {children}
    </span>
  );
}

export function Loading({ label }: { label?: string }) {
  const { t } = useLocale();
  return (
    <p role="status" className="py-8 text-center text-sm text-muted">
      {label ?? t('common.loading')}
    </p>
  );
}

export function ErrorState({ message, onRetry }: { message?: string; onRetry?: () => void }) {
  const { t } = useLocale();
  return (
    <div role="alert" className="space-y-3 py-8 text-center">
      <p className="text-sm text-vine">{message ?? t('common.error')}</p>
      {onRetry ? (
        <Button variant="secondary" onClick={onRetry}>
          {t('common.retry')}
        </Button>
      ) : null}
    </div>
  );
}

export function EmptyState({ message }: { message: string }) {
  return <p className="py-10 text-center text-sm text-muted">{message}</p>;
}
