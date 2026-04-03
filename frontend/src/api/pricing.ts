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

/**
 * S22-13: Llama a GET /api/pricing/resolve/ y retorna el dict de precio resuelto.
 * Para usuarios de portal, el backend ya filtra y solo devuelve price + grade_moq.
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
