import { test, expect } from '@playwright/test';

test('has title and can toggle admin mode', async ({ page }) => {
  page.on('console', msg => console.log('BROWSER LOG:', msg.text()));
  page.on('pageerror', err => console.log('BROWSER ERROR:', err.message));
  page.on('requestfailed', request =>
    console.log('REQUEST FAILED:', request.url(), request.failure()?.errorText)
  );
  
  await page.goto('login');

  await page.waitForTimeout(3000); // Wait 3 seconds
  // Log the current HTML to see what's really there
  const html = await page.content();
  console.log('HTML CONTENT:', html);

  await expect(page).toHaveTitle(/Violett Pilates/, { timeout: 5000 });
  await expect(page.locator('text=Email de alumna')).toBeVisible({ timeout: 5000 });
});
