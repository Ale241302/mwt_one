import { test, expect } from '@playwright/test';

const BASE = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1/';

test.describe('E2E: Expediente REGISTRO → CERRADO [dispatch_mode=mwt]', () => {
    let expedienteId: string;

    test.beforeAll(async ({ request }) => {
        // Crear expediente vía API directa para el test
        const res = await request.post(`${API}expedientes/`, {
            headers: { Authorization: `Bearer ${process.env.TEST_JWT}` },
            data: {
                brand: 'SKECHERS',
                client_name: 'Test E2E MWT',
                mode: 'B',
                dispatch_mode: 'mwt',
                price_basis: 'CIF',
            },
        });
        expect(res.ok()).toBeTruthy();
        const data = await res.json();
        expedienteId = data.id;
    });

    test('Carga la lista de expedientes', async ({ page }) => {
        await page.goto(`${BASE}/expedientes`);
        await expect(page.locator('h1')).toContainText('Expedientes');
        await expect(page.locator('table tbody tr')).not.toHaveCount(0);
    });

    test('Detalle: muestra el expediente creado en REGISTRO', async ({ page }) => {
        await page.goto(`${BASE}/expedientes/${expedienteId}`);
        await expect(page.locator('h1')).toContainText('EXP-');
        await expect(page.locator('span:has-text("REGISTRO")')).toBeVisible();
    });

    test('Detalle: tiene al menos 1 artefacto (ART-01 Orden de Compra)', async ({ page, request }) => {
        // Registrar OC vía API
        await request.post(`${API}expedientes/${expedienteId}/register-oc/`, {
            headers: { Authorization: `Bearer ${process.env.TEST_JWT}` },
            data: { po_number: 'PO-E2E-001', po_date: '2026-03-01', amount: 5000 },
        });

        await page.goto(`${BASE}/expedientes/${expedienteId}`);
        await expect(page.locator('td:has-text("Orden de Compra")')).toBeVisible();
    });

    test('RegisterPaymentDrawer: abre y registra pago', async ({ page, request }) => {
        // Emitir factura primero
        await request.post(`${API}expedientes/${expedienteId}/emit-invoice/`, {
            headers: { Authorization: `Bearer ${process.env.TEST_JWT}` },
            data: { amount: 5000, currency: 'USD' },
        });

        await page.goto(`${BASE}/expedientes/${expedienteId}`);
        await page.click('button:has-text("Registrar Pago")');
        await expect(page.locator('h2:has-text("Registrar Pago")')).toBeVisible();

        await page.fill('input[name="amount"]', '5000');
        await page.selectOption('select[name="method"]', 'TRANSFERENCIA');
        await page.click('button[type="submit"]:has-text("Registrar Pago")');

        await expect(page.locator('text=Pago registrado')).toBeVisible({ timeout: 5000 });
    });
});
