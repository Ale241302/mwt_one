import { test, expect } from '@playwright/test';

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1/';

test.describe('E2E: Expediente [dispatch_mode=client] — flujo cliente', () => {
    let expedienteId: string;

    test.beforeAll(async ({ request }) => {
        const res = await request.post(`${API}expedientes/`, {
            headers: { Authorization: `Bearer ${process.env.TEST_JWT}` },
            data: {
                brand: 'ASICS',
                client_name: 'Test E2E CLIENT',
                mode: 'C',
                dispatch_mode: 'client',
                price_basis: 'FOB',
            },
        });
        expect(res.ok()).toBeTruthy();
        expedienteId = (await res.json()).id;
    });

    test('Toggle costos: Vista Cliente NO muestra margen', async ({ page }) => {
        await page.goto(`${BASE}/expedientes/${expedienteId}`);
        // Activar vista cliente si existe el toggle
        const toggle = page.locator('[data-testid="toggle-client-view"], button:has-text("Vista Cliente")');
        if (await toggle.count()) {
            await toggle.click();
            await expect(page.locator('[data-testid^="margin-"]')).toHaveCount(0);
        }
    });

    test('Expediente bloqueado: botones de pipeline deshabilitados', async ({ page, request }) => {
        // Bloquear expediente
        await request.post(`${API}expedientes/${expedienteId}/block/`, {
            headers: { Authorization: `Bearer ${process.env.TEST_JWT}` },
            data: { reason: 'Test block E2E' },
        });

        await page.goto(`${BASE}/expedientes/${expedienteId}`);
        await expect(page.locator('span:has-text("BLOQUEADO")')).toBeVisible();
        // No debe haber botones de pipeline activos (solo desbloquear)
        const pipelineBtns = page.locator('.acciones-pipeline button:not(:disabled)');
        await expect(pipelineBtns).toHaveCount(0);
    });

    test('Regresión S3-S6: lista carga sin crash', async ({ page }) => {
        await page.goto(`${BASE}/expedientes`);
        await expect(page).not.toHaveURL(/error/);
        await expect(page.locator('table')).toBeVisible();
    });

    test('Regresión S3-S6: detalle carga sin crash', async ({ page }) => {
        await page.goto(`${BASE}/expedientes/${expedienteId}`);
        await expect(page).not.toHaveURL(/error/);
        await expect(page.locator('h1')).toBeVisible();
    });
});
