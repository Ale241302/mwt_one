import { PROFORMA_ARTIFACT_POLICY } from '@/constants/proforma-artifact-policy';
import type { ArtifactPolicyState } from '@/components/expediente/ArtifactSection';

export function resolveProformaPolicy(
  brandSlug: string,
  mode: string,
  state: string
): ArtifactPolicyState {
  return PROFORMA_ARTIFACT_POLICY[brandSlug]?.[mode]?.[state] ?? {
    required: [], optional: [], gate_for_advance: []
  };
}
