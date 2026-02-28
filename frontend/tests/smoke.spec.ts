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

});
