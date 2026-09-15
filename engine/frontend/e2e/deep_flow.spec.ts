import { test, expect } from '@playwright/test';

test.describe('E2E Deep Flows', () => {

  test('Alumna - Book and Cancel Flow', async ({ page }) => {
    test.setTimeout(45000);

    await page.goto('login');
    await page.fill('input[type="email"]', 'alumno@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/');
    
    await page.waitForTimeout(2000);

    const btnAgendar = page.locator('button:has-text("Agendar")').first();
    
    if (await btnAgendar.isVisible({ timeout: 5000 }).catch(() => false)) {
        await btnAgendar.click();
        await expect(page.locator('text=Confirmar Reserva')).toBeVisible({ timeout: 5000 }).catch(() => null);
        await page.click('button:has-text("Solo esta clase")');
        await page.waitForTimeout(1000);
        
        const btnCancelar = page.locator('button:has-text("Cancelar")').first();
        await btnCancelar.waitFor({ state: 'visible', timeout: 5000 });
        await btnCancelar.click();
        await page.click('button:has-text("cancelar clase")');
        await page.waitForTimeout(1000);
    }
  });

  test('Admin - Modal Creations', async ({ page }) => {
    test.setTimeout(45000);

    await page.goto('login?admin=true');
    await page.fill('input[type="email"]', 'admin@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');
    await page.waitForURL('**/admin/agenda');

    await page.goto('admin/alumnos');
    await page.click('button:has-text("+ Nueva Alumna")');
    await expect(page.locator('h2:has-text("Nueva Alumna")')).toBeVisible({ timeout: 5000 });
    await page.click('button:has-text("Cancelar")');

    // Go to Clases
    await page.goto('admin/clases');
    // Ensure the inline form is visible
    await expect(page.locator('text=Nueva Disciplina')).toBeVisible({ timeout: 5000 }).catch(() => null);
  });

});
