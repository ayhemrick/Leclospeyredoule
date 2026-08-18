import { expect, test } from '@playwright/test';

test.describe('public site', () => {
  test('shows the property and what is nearby', async ({ page }) => {
    await page.goto('/');

    await expect(page.getByRole('heading', { name: 'Clos Peyredoule', level: 1 })).toBeVisible();
    await expect(page.getByRole('heading', { name: /Blaye Citadel|Citadelle de Blaye/ })).toBeVisible();
  });

  test('switches between French and English', async ({ page }) => {
    await page.goto('/');

    const toggle = page.getByRole('button', { name: /Langue|Language/ });
    const before = await toggle.textContent();
    await toggle.click();

    await expect(toggle).not.toHaveText(before ?? '');
    await expect(page.locator('html')).toHaveAttribute('lang', /fr|en/);
  });

  test('filters the places to visit by category', async ({ page }) => {
    await page.goto('/decouvrir');

    const cards = page.locator('article, [class*="rounded"]').filter({ hasText: /km/ });
    await expect(cards.first()).toBeVisible();

    await page.getByRole('button', { name: /^(Vin|Wine)$/ }).click();
    await expect(page.getByRole('button', { name: /^(Vin|Wine)$/ })).toHaveAttribute(
      'aria-pressed',
      'true',
    );
  });

  test('lists photo credits', async ({ page }) => {
    await page.goto('/credits');
    await expect(page.getByRole('link', { name: /CC BY/ }).first()).toBeVisible();
  });

  test('serves a 404 page for an unknown path', async ({ page }) => {
    await page.goto('/pas-de-page-ici');
    await expect(page.getByRole('heading', { name: /introuvable|not found/i })).toBeVisible();
  });
});
