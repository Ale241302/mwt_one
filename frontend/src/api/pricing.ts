// S22-13 — Hook/función resolveClientPrice
import api from '@/lib/api';

export interface ResolveClientPriceParams {
  brand_sku_id: number;
  client_subsidiary_id: number;
  payment_days?: number;
  skip_cache?: boolean;
}

export interface ResolvedPrice {
  price: string | null;
  source: string | null;
  pricelist_version: number | null;
  discount_applied: string | null;
  base_price: string | null;
  grade_moq: number | null;
  size_multipliers: Record<string, number> | null;
  grade_pricelist_version: number | null;
}

export interface PriceListVersion {
  id: number;
  version_label: string;
  is_active: boolean;
  created_at: string;
  activated_at: string | null;
  notes: string;
  items_count: number;
  uploaded_by_name: string;
}

export interface EarlyPaymentTier {
  id: number;
  payment_days: number;
  discount_pct: string;
}

export interface EarlyPaymentPolicy {
  id: number;
  client_subsidiary: number;
  client_subsidiary_name: string;
  base_payment_days: number;
  base_commission_pct: string;
  is_active: boolean;
  tiers: EarlyPaymentTier[];
}

export interface ClientProductAssignment {
  id: number;
  client_subsidiary: number;
  client_subsidiary_name: string;
  brand_sku: number;
  brand_sku_code: string;
  brand_sku_description: string;
  cached_client_price: string;
  cached_base_price: string;
  cached_at: string;
  is_active: boolean;
  is_stale: boolean;
}

/**
 * S22-13: Llama a GET /api/pricing/resolve/ y retorna el dict de precio resuelto.
 */
export async function resolveClientPrice(
  params: ResolveClientPriceParams,
): Promise<ResolvedPrice | null> {
  try {
    const query = new URLSearchParams({
      brand_sku_id: String(params.brand_sku_id),
      client_subsidiary_id: String(params.client_subsidiary_id),
      ...(params.payment_days != null ? { payment_days: String(params.payment_days) } : {}),
      ...(params.skip_cache ? { skip_cache: 'true' } : {}),
    });
    const res = await api.get<ResolvedPrice>(`pricing/resolve/?${query.toString()}`);
    return res.data;
  } catch {
    return null;
  }
}

// S22-01: Listar versiones por marca
export async function getPriceListVersions(brandId: number): Promise<PriceListVersion[]> {
  const res = await api.get<PriceListVersion[]>(`pricing/pricelists/?brand_id=${brandId}`);
  return res.data;
}

// S22-06: Activar versión
export async function activatePriceList(versionId: number, force = false): Promise<any> {
  const res = await api.post(`pricing/pricelists/${versionId}/activate/`, { force });
  return res.data;
}

// S22-03: Early Payment Policies
export async function getEarlyPaymentPolicies(brandId: number): Promise<EarlyPaymentPolicy[]> {
  const res = await api.get<EarlyPaymentPolicy[]>(`pricing/early-payment-policies/?brand_id=${brandId}`);
  return res.data;
}

export async function updateEarlyPaymentPolicy(id: number, data: Partial<EarlyPaymentPolicy>): Promise<EarlyPaymentPolicy> {
  const res = await api.patch<EarlyPaymentPolicy>(`pricing/early-payment-policies/${id}/`, data);
  return res.data;
}

// S22-02: Client Assignments
export async function getClientAssignments(brandId: number): Promise<ClientProductAssignment[]> {
  const res = await api.get<ClientProductAssignment[]>(`pricing/client-assignments/?brand_id=${brandId}`);
  return res.data;
}

export async function bulkAssignProducts(data: { product_key: string; client_subsidiary_ids: number[] }): Promise<any> {
  const res = await api.post(`pricing/client-assignments/bulk/`, data);
  return res.data;
}
