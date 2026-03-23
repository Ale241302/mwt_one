export const STATE_LABELS = {
    DRAFT: 'Borrador',
    UNDER_REVIEW: 'En Revisión',
    APPROVED: 'Aprobado',
    REJECTED: 'Rechazado',
    CANCELLED: 'Cancelado',
    IN_PROGRESS: 'En Progreso',
    COMPLETED: 'Completado',
    ON_HOLD: 'En Pausa',
    COMPLIANCE_HOLD: 'Bloqueo Compliance',
    PENDING_PAYMENT: 'Pendiente de Pago',
    DISPATCHED: 'Despachado',
    DELIVERED: 'Entregado'
} as const;

export type StateKey = keyof typeof STATE_LABELS;

export const TIMELINE_STEPS = [
    'REGISTRO',
    'UNDER_REVIEW',
    'APPROVED',
    'PENDING_PAYMENT',
    'IN_PROGRESS',
    'DISPATCHED',
    'DELIVERED'
] as const;

export const STATE_BADGE_CLASSES: Record<string, string> = {
    DRAFT: 'badge-neutral',
    UNDER_REVIEW: 'badge-warning',
    APPROVED: 'badge-success',
    REJECTED: 'badge-critical',
    CANCELLED: 'badge-neutral',
    IN_PROGRESS: 'badge-info',
    COMPLETED: 'badge-success',
    ON_HOLD: 'badge-warning',
    COMPLIANCE_HOLD: 'badge-critical',
    PENDING_PAYMENT: 'badge-warning',
    DISPATCHED: 'badge-info',
    DELIVERED: 'badge-success',
    REGISTRO: 'badge-info'
};
