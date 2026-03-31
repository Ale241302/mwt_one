/**
 * S20B-01: Verificador de expedientes Legacy
 * Devuelve true si un expediente antiguo no tiene proformas creadas pero
 * ya pasó la fase de REGISTRO, por lo tanto su artifact_policy dinámico 
 * solo muestra 'REGISTRO' (cayó en fallback porque no se definió mode).
 */
export function isLegacyExpediente(expediente: any): boolean {
  if (!expediente) return false;

  const policy = expediente.artifact_policy || {};
  const hasOnlyRegistro = Object.keys(policy).length === 1 && !!policy['REGISTRO'];
  
  const status = expediente.status || 'REGISTRO';
  const isPastRegistro = status !== 'REGISTRO';

  const artifacts = expediente.artifacts || [];
  const proformasCount = artifacts.filter((a: any) => a.artifact_type === 'ART-02').length;

  // 3 Condiciones AND:
  // 1. policy solo REGISTRO
  // 2. status > REGISTRO
  // 3. 0 proformas
  return hasOnlyRegistro && isPastRegistro && proformasCount === 0;
}
