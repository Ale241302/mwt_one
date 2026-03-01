import { test, expect } from '@playwright/test';

test.describe('MWT.ONE Smoke Tests', () => {

    test('should redirect to login when not authenticated', async ({ page }) => {
        // Go to the dashboard
        await page.goto('/');

        // It should redirect to the login page
        await expect(page).toHaveURL(/.*\/login/);

        // Check if the login form is present
        await expect(page.locator('form')).toBeVisible();
        await expect(page.getByPlaceholder('admin')).toBeVisible();
        await expect(page.getByPlaceholder('••••••••')).toBeVisible();
        await expect(page.getByRole('button', { name: 'Ingresar a la plataforma' })).toBeVisible();
    });

    test('login exitoso redirige a dashboard', async ({ page }) => {
        await page.goto('/login');
        await page.getByPlaceholder('admin').fill('admin');
        await page.getByPlaceholder('••••••••').fill('admin');
        await page.getByRole('button', { name: 'Ingresar a la plataforma' }).click();
        await expect(page).toHaveURL(/.*\/dashboard/);
    });

    test('login fallido muestra error', async ({ page }) => {
        await page.goto('/login');
        await page.getByPlaceholder('admin').fill('wrong');
        await page.getByPlaceholder('••••••••').fill('wrong');
        await page.getByRole('button', { name: 'Ingresar a la plataforma' }).click();
        await expect(page.locator('text=Invalid credentials')).toBeVisible();
    });

    test('dashboard muestra 4 stat cards', async ({ page }) => {
        await page.goto('/login');
        await page.getByPlaceholder('admin').fill('admin');
        await page.getByPlaceholder('••••••••').fill('admin');
        await page.getByRole('button', { name: 'Ingresar a la plataforma' }).click();

        await expect(page.locator('.stat-card')).toHaveCount(4);
    });

    test('sidebar navega a lista de expedientes', async ({ page }) => {
        await page.goto('/dashboard');
        await page.getByRole('link', { name: 'Expedientes' }).click();
        await expect(page).toHaveURL(/.*\/expedientes/);
    });

    test('filtro por estado filtra tabla', async ({ page }) => {
        await page.goto('/expedientes');
        // Search for a select or filter button
        await page.locator('select[name="status"]').selectOption('REGISTRO');
        await expect(page).toHaveURL(/.*status=REGISTRO/);
    });

    test('click en fila navega a detalle', async ({ page }) => {
        await page.goto('/expedientes');
        await page.locator('table tbody tr').first().click();
        await expect(page).toHaveURL(/.*\/expedientes\/[0-9a-f-]+/);
    });

    test('detalle muestra acciones habilitadas', async ({ page }) => {
        await page.goto('/expedientes');
        await page.locator('table tbody tr').first().click();
        await expect(page.locator('.action-button')).toBeVisible();
    });

    test('Block con reason → bloqueado → Unblock funcional', async ({ page }) => {
        await page.goto('/expedientes');
        await page.locator('table tbody tr').first().click();

        // Block
        await page.getByRole('button', { name: 'Bloquear' }).click();
        await page.locator('textarea[name="reason"]').fill('Test block reason');
        await page.getByRole('button', { name: 'Confirmar Bloqueo' }).click();

        await expect(page.locator('text=BLOQUEADO')).toBeVisible();

        // Unblock
        await page.getByRole('button', { name: 'Desbloquear' }).click();
        await expect(page.locator('text=BLOQUEADO')).not.toBeVisible();
    });

    test('back button preserva filtros en URL', async ({ page }) => {
        await page.goto('/expedientes?status=REGISTRO');
        await page.locator('table tbody tr').first().click();
        await page.goBack();
        await expect(page).toHaveURL(/.*status=REGISTRO/);
    });

    test('logout redirige a /login', async ({ page }) => {
        await page.goto('/dashboard');
        await page.getByRole('button', { name: 'Cerrar Sesión' }).click();
        await expect(page).toHaveURL(/.*\/login/);
    });

});
