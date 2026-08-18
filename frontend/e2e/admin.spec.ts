/** The admin section: sign-in, the poster, and changing the rules. */

import { expect, test, type Page } from '@playwright/test';

import { ADMIN_EMAIL, ADMIN_PASSWORD } from './helpers';

async function signIn(page: Page): Promise<void> {
  await page.goto('/admin');
  await page.getByLabel(/E-mail/).fill(ADMIN_EMAIL);
  await page.getByLabel(/Password|Mot de passe/).fill(ADMIN_PASSWORD);
  await page.getByRole('button', { name: /Sign in|Se connecter/ }).click();
  await expect(page.getByRole('heading', { name: /Dashboard|Tableau de bord/ })).toBeVisible();
}

test.describe('admin', () => {
  test('refuses the wrong password', async ({ page }) => {
    await page.goto('/admin');
    await page.getByLabel(/E-mail/).fill(ADMIN_EMAIL);
    await page.getByLabel(/Password|Mot de passe/).fill('not-the-password');
    await page.getByRole('button', { name: /Sign in|Se connecter/ }).click();

    await expect(page.getByRole('alert')).toBeVisible();
    await expect(page.getByRole('heading', { name: /Dashboard|Tableau de bord/ })).toHaveCount(0);
  });

  test('signs in and reports access statistics', async ({ page }) => {
    await signIn(page);
    await expect(page.getByText(/Active sessions|Sessions actives/)).toBeVisible();
    await expect(page.getByText(/rotation/i).first()).toBeVisible();
  });

  test('shows a printable QR poster carrying the scan URL', async ({ page }) => {
    await signIn(page);
    await page.getByRole('link', { name: /Access & QR|Accès & QR/ }).click();

    const qr = page.getByRole('img', { name: /QR/ });
    await expect(qr).toBeVisible();
    await expect(qr).toHaveAttribute('src', /^data:image\/svg\+xml/);
    await expect(page.getByText(/\/a\//)).toBeVisible();
  });

  test('rotates the code on demand', async ({ page }) => {
    await signIn(page);
    await page.getByRole('link', { name: /Access & QR|Accès & QR/ }).click();

    const posterUrl = page.getByText(/\/a\//);
    const before = await posterUrl.textContent();

    page.once('dialog', (dialog) => void dialog.accept());
    await page.getByRole('button', { name: /Change the code now|Changer le code/ }).click();

    await expect(posterUrl).not.toHaveText(before ?? '');
  });

  test('saves a change to the access policy', async ({ page }) => {
    await signIn(page);
    await page.getByRole('link', { name: /Access & QR|Accès & QR/ }).click();

    const sessionLength = page.getByLabel(/Access granted per scan|Durée d’accès/);
    await sessionLength.fill('12');
    await page.getByRole('button', { name: /^(Save|Enregistrer)$/ }).click();

    await expect(page.getByText(/^(Saved|Enregistré)$/)).toBeVisible();
  });

  test('lists the guest guide for editing', async ({ page }) => {
    await signIn(page);
    await page.getByRole('link', { name: /^(Guide)$/ }).click();
    await expect(page.getByText('wifi-et-connexion')).toBeVisible();
  });

  test('records actions in the audit log', async ({ page }) => {
    await signIn(page);
    await page.getByRole('link', { name: /Audit log|Journal/ }).click();
    await expect(page.getByText('auth.login_succeeded').first()).toBeVisible();
  });

  test('signs out', async ({ page }) => {
    await signIn(page);
    await page.getByRole('button', { name: /Sign out|Se déconnecter/ }).click();
    await expect(page.getByRole('button', { name: /Sign in|Se connecter/ })).toBeVisible();
  });
});
