/** The QR access journey, end to end against the real API. */

import { expect, test } from '@playwright/test';

import { adminApi, currentCode, rotateCode } from './helpers';

test.describe('guest access', () => {
  test('the guide is closed until the code is scanned', async ({ page }) => {
    await page.goto('/guide');
    await expect(page.getByRole('heading', { name: /Guests only|Accès réservé/ })).toBeVisible();
    await expect(page.getByText(/Wi-Fi/)).toHaveCount(0);
  });

  test('scanning the poster opens the guide and hides the code', async ({ page }) => {
    const api = await adminApi();
    const code = await currentCode(api);

    await page.goto(`/a/${code}`);

    await expect(page.getByRole('heading', { name: /Guest guide|Guide des hôtes/ })).toBeVisible();
    await expect(page.getByText(/Wi-Fi/)).toBeVisible();
    // The code is replaced in history, so it cannot be read off the address bar.
    await expect(page).toHaveURL(/\/guide$/);

    await api.dispose();
  });

  test('an unknown code is refused with an explanation', async ({ page }) => {
    await page.goto('/a/definitely-not-a-real-code');

    await expect(page.getByRole('heading', { name: /not valid|non valable/i })).toBeVisible();
    await expect(page.getByText(/not recognised|pas reconnu|non valable/i).first()).toBeVisible();
  });

  test('a retired code stops working after rotation', async ({ page }) => {
    const api = await adminApi();
    const stale = await currentCode(api);
    await rotateCode(api);

    await page.goto(`/a/${stale}`);
    await expect(page.getByRole('heading', { name: /not valid|non valable/i })).toBeVisible();

    await api.dispose();
  });

  test('ending access closes the guide again', async ({ page }) => {
    const api = await adminApi();
    const code = await currentCode(api);

    await page.goto(`/a/${code}`);
    await expect(page.getByRole('heading', { name: /Guest guide|Guide des hôtes/ })).toBeVisible();

    await page.getByRole('button', { name: /End access|Terminer/ }).click();
    await expect(page.getByRole('heading', { name: /Guests only|Accès réservé/ })).toBeVisible();

    await api.dispose();
  });

  test('access survives a reload', async ({ page }) => {
    const api = await adminApi();
    const code = await currentCode(api);

    await page.goto(`/a/${code}`);
    await expect(page.getByText(/Wi-Fi/)).toBeVisible();

    await page.reload();
    await expect(page.getByText(/Wi-Fi/)).toBeVisible();

    await api.dispose();
  });
});
