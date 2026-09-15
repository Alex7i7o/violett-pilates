import { test, expect } from '@playwright/test';

test.describe('E2E Roles Validation', () => {

  test('Admin Role Flow', async ({ page }) => {
    await page.goto('login?admin=true');
    await page.fill('input[type="email"]', 'admin@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/admin/agenda');
    await expect(page.locator('h2:has-text("Agenda")')).toBeVisible({ timeout: 10000 });

    await page.goto('admin/alumnos');
    await expect(page.locator('text=Directorio de Alumnas')).toBeVisible({ timeout: 10000 });

    await page.goto('admin/profesores');
    await expect(page.locator('text=Staff y Profesores')).toBeVisible({ timeout: 10000 });
    
    await page.goto('admin/planes');
    await expect(page.locator('text=Paquetes de Clases')).toBeVisible({ timeout: 10000 });
  });

  test('Profesor Role Flow', async ({ page }) => {
    await page.goto('login');
    await page.fill('input[type="email"]', 'profesor@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/profesor/dashboard');
    // We just look for the Logout icon or something unique to the professor dashboard
    await expect(page.locator('text=Cerrar Sesión').last()).toBeVisible({ timeout: 10000 });
  });

  test('Alumno Role Flow', async ({ page }) => {
    await page.goto('login');
    await page.fill('input[type="email"]', 'alumno@violett.com');
    await page.fill('input[type="password"]', 'password123');
    await page.click('button[type="submit"]');

    await page.waitForURL('**/');
    // Ensure we are not on login
    await page.click('text=Reservas');
    await expect(page.locator('text=Ver clases a las que asistí')).toBeVisible({ timeout: 10000 });
  });

});