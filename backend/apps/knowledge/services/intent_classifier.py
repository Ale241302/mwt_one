"""
S24-10: Clasificador de intención para el Knowledge Pipeline.

Política fail-closed:
  - confidence < 0.7  -> ESCALATE
  - multi-intent       -> ESCALATE
  - parse failure      -> ESCALATE

El clasificador NO accede a DB, NO genera SQL, NO recibe contexto sensible.
Solo recibe el texto de la pregunta del usuario.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import List, Tuple

logger = logging.getLogger(__name__)


class Intent(str, Enum):
    QUERY_PRODUCT    = 'QUERY_PRODUCT'
    QUERY_OPERATIONS = 'QUERY_OPERATIONS'
    QUERY_EXPEDIENTE = 'QUERY_EXPEDIENTE'
    DOWNLOAD_DOC     = 'DOWNLOAD_DOC'
    ASK_CLARIFICATION = 'ASK_CLARIFICATION'
    ESCALATE         = 'ESCALATE'


@dataclass
class IntentResult:
    intent: str
    confidence: float
    raw_scores: dict


# ---------------------------------------------------------------------------
# Patrones por intent (keyword matching heuristico)
# En producción esto puede reemplazarse por llamada a LLM clasificador
# con el mismo contrato de salida (intent + confidence).
# ---------------------------------------------------------------------------
_PATTERNS: List[Tuple[Intent, List[str], float]] = [
    (Intent.DOWNLOAD_DOC, [
        r'\bdescargar?\b', r'\bdownload\b', r'\bpdf\b', r'\bdocumento\b',
        r'\barchivo\b', r'\bfactura\b', r'\bbl\b', r'\bcertificado\b',
        r'\benviar(?:me)?\s+(?:el|la)\b',
    ], 0.85),
    (Intent.QUERY_EXPEDIENTE, [
        r'\bexpediente\b', r'\benvio\b', r'\bcarga\b', r'\bcontent\b',
        r'\bestado\s+de\b', r'\btracking\b', r'\bcontainer\b',
        r'\bpedido\b', r'\borden\b', r'\breference\b', r'\bbl\s*n[uú]mero\b',
        r'\bcuando\s+llega\b', r'\bfecha\s+de\s+llegada\b',
    ], 0.82),
    (Intent.QUERY_PRODUCT, [
        r'\bproducto\b', r'\bzapato\b', r'\bcalzado\b', r'\bprecio\b',
        r'\btalla\b', r'\bcolección\b', r'\bcatalogo\b', r'\bmodelo\b',
        r'\bsku\b', r'\bdisponibilidad\b', r'\bstock\b',
    ], 0.80),
    (Intent.QUERY_OPERATIONS, [
        r'\boperación\b', r'\bproceso\b', r'\bprocedimiento\b', r'\bpolítica\b',
        r'\bpolitica\b', r'\bdocumentación\b', r'\brequisito\b', r'\btransporte\b',
        r'\baduana\b', r'\bflete\b', r'\bseguro\b', r'\bnavilinea\b',
        r'\btiempo\s+de\s+tránsito\b', r'\bincoterm\b',
    ], 0.78),
    (Intent.ASK_CLARIFICATION, [
        r'\bno\s+entend[ií]\b', r'\brepite?\b', r'\bexplica?\b',
        r'\bqué\s+quieres\s+decir\b', r'\bno\s+sé\b', r'\bno\s+tengo\s+claro\b',
        r'^\?+$',  # solo signos de pregunta
    ], 0.75),
]


def _score_question(question: str) -> dict:
    """Retorna score por intent basado en patron matching."""
    q = question.lower()
    scores = {intent.value: 0.0 for intent in Intent}

    for intent, patterns, base_conf in _PATTERNS:
        matches = sum(1 for p in patterns if re.search(p, q))
        if matches > 0:
            # Score escala con cantidad de matches pero no supera base_conf
            score = min(base_conf, base_conf * (0.6 + 0.2 * matches))
            scores[intent.value] = round(score, 4)

    return scores


def classify_intent(question: str) -> IntentResult:
    """
    Clasifica la intención de una pregunta.
    Politica fail-closed: cualquier ambigüedad -> ESCALATE.

    Args:
        question: Texto libre del usuario.

    Returns:
        IntentResult con intent, confidence y raw_scores.
    """
    if not question or not question.strip():
        logger.warning('S24-10 classify_intent: empty question -> ESCALATE')
        return IntentResult(intent=Intent.ESCALATE.value, confidence=0.0, raw_scores={})

    try:
        scores = _score_question(question)
    except Exception as exc:
        logger.error('S24-10 classify_intent parse failure: %s -> ESCALATE', exc)
        return IntentResult(intent=Intent.ESCALATE.value, confidence=0.0, raw_scores={})

    # Ordenar por score descendente
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_intent, top_score = ranked[0]
    second_intent, second_score = ranked[1] if len(ranked) > 1 else ('', 0.0)

    # Fail-closed: confidence baja
    if top_score < 0.7:
        logger.info(
            'S24-10 low confidence %.2f for "%s" -> ESCALATE', top_score, question[:80]
        )
        return IntentResult(
            intent=Intent.ESCALATE.value,
            confidence=top_score,
            raw_scores=scores,
        )

    # Fail-closed: multi-intent (dos intents con score > 0.65)
    if second_score >= 0.65:
        logger.info(
            'S24-10 multi-intent detected (%s=%.2f, %s=%.2f) -> ESCALATE',
            top_intent, top_score, second_intent, second_score
        )
        return IntentResult(
            intent=Intent.ESCALATE.value,
            confidence=top_score,
            raw_scores=scores,
        )

    logger.info(
        'S24-10 classified intent=%s confidence=%.2f question="%s"',
        top_intent, top_score, question[:80]
    )
    return IntentResult(intent=top_intent, confidence=top_score, raw_scores=scores)
