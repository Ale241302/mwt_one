import type { ArtifactPolicyState } from '@/components/expediente/ArtifactSection';

export const EXPEDIENTE_LEVEL_ARTIFACTS = new Set(['ART-01', 'ART-02', 'ART-11', 'ART-12']);

export const PROFORMA_ARTIFACT_POLICY: Record<string, Record<string, Record<string, ArtifactPolicyState>>> = {
  marluvas: {
    mode_b: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: ['ART-03'], gate_for_advance: ['ART-01', 'ART-02'] },
      PRODUCCION:   { required: [], optional: [], gate_for_advance: [] },
      PREPARACION:  { required: ['ART-05', 'ART-06', 'ART-07'], optional: ['ART-08'], gate_for_advance: ['ART-05', 'ART-06', 'ART-07'] },
      EN_DESTINO:   { required: ['ART-10'], optional: ['ART-12'], gate_for_advance: ['ART-10'] },
    },
    mode_c: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: ['ART-03'], gate_for_advance: ['ART-01', 'ART-02'] },
      PRODUCCION:   { required: [], optional: [], gate_for_advance: [] },
      PREPARACION:  { required: ['ART-05', 'ART-06', 'ART-07'], optional: ['ART-08'], gate_for_advance: ['ART-05', 'ART-06', 'ART-07'] },
      EN_DESTINO:   { required: ['ART-09'], optional: ['ART-12'], gate_for_advance: ['ART-09'] },
    },
  },
  rana_walk: {
    default: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: [], gate_for_advance: ['ART-01', 'ART-02'] },
      DESPACHO:     { required: ['ART-05', 'ART-06'], optional: [], gate_for_advance: ['ART-05', 'ART-06'] },
      EN_DESTINO:   { required: ['ART-09'], optional: [], gate_for_advance: ['ART-09'] },
    },
  },
  tecmater: {
    default: {
      REGISTRO:     { required: ['ART-01', 'ART-02'], optional: [], gate_for_advance: ['ART-01', 'ART-02'] },
      PREPARACION:  { required: ['ART-05', 'ART-06', 'ART-07'], optional: ['ART-08'], gate_for_advance: ['ART-05', 'ART-06', 'ART-07'] },
      EN_DESTINO:   { required: ['ART-09'], optional: [], gate_for_advance: ['ART-09'] },
    },
  },
};
