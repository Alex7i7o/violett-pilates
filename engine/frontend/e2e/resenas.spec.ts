import { test, expect } from '@playwright/test';

test.describe('Plugin Reseñas', () => {

  test('Alumna can see and submit a review', async ({ page }) => {
    test.setTimeout(30000);

    await page.goto('login');
    await page.fill('input[type="email"]', 'alumno@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
    
    // Check if widget is present
    await expect(page.locator('text=¿Qué te pareció tu última clase?')).toBeVisible({ timeout: 10000 });
    
    // Click 5th star
    const stars = page.locator('button:has-text("★")');
    await expect(stars).toHaveCount(5);
    await stars.nth(4).click(); // Click 5th star
    
    // Fill text
    await page.fill('textarea', '¡Me encantó la clase de hoy! Excelente profe.');
    
    // Submit
    await page.click('button:has-text("Enviar Opinión")');
    
    // Wait for success
    await expect(page.locator('text=¡Gracias por dejarnos tu opinión!')).toBeVisible({ timeout: 5000 });
  });

  test('Admin can see reviews', async ({ page }) => {
    test.setTimeout(30000);

    await page.goto('login?admin=true');
    await page.fill('input[type="email"]', 'admin@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin/agenda');

    await page.goto('admin/resenas');
    await expect(page.locator('h1:has-text("Reseñas de Alumnas")')).toBeVisible({ timeout: 5000 });
    
    // We should see the review we just submitted
    await expect(page.locator('text=¡Me encantó la clase de hoy! Excelente profe.').first()).toBeVisible({ timeout: 5000 });
  });

});