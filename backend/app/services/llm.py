import logging
from dataclasses import dataclass

import anthropic
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)

_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

_MOOD_LABELS = ("positivo", "neutral", "negativo", "urgente-enojado")

_TOOL_SCHEMA = {
    "name": "record_mood_analysis",
    "description": "Registra el resultado del analisis de animo de un correo.",
    "input_schema": {
        "type": "object",
        "properties": {
            "mood_label": {"type": "string", "enum": list(_MOOD_LABELS)},
            "mood_score": {
                "type": "number",
                "description": "-1.0 (muy negativo) a 1.0 (muy positivo)",
            },
            "summary": {"type": "string", "description": "Resumen de 1-2 lineas"},
            "requires_attention": {"type": "boolean"},
        },
        "required": ["mood_label", "mood_score", "summary", "requires_attention"],
    },
}

_SYSTEM_PROMPT = (
    "Sos un analista de sentimiento de correos de clientes. Vas a recibir el "
    "remitente, asunto y cuerpo de un email. Evalua el estado de animo del "
    "remitente y registralo usando la herramienta record_mood_analysis. "
    "Identifica senales de enojo o urgencia: lenguaje agresivo, quejas, "
    "amenazas, mayusculas excesivas, signos de exclamacion multiples, "
    "decepcion severa."
)


@dataclass
class AnalysisResult:
    mood_label: str
    mood_score: float
    summary: str
    requires_attention: bool
    failed: bool = False


class LLMAnalysisError(Exception):
    pass


@retry(
    reraise=True,
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    retry=retry_if_exception_type((anthropic.RateLimitError, anthropic.APIStatusError)),
)
def _call_claude(sender: str, subject: str, body: str):
    return _client.messages.create(
        model=settings.claude_model,
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        tools=[_TOOL_SCHEMA],
        tool_choice={"type": "tool", "name": "record_mood_analysis"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Remitente: {sender}\nAsunto: {subject}\nCuerpo:\n{body}"
                ),
            }
        ],
    )


def analyze_email(sender: str, subject: str, body: str) -> AnalysisResult:
    try:
        response = _call_claude(sender, subject, body)
        for block in response.content:
            if block.type == "tool_use" and block.name == "record_mood_analysis":
                data = block.input
                return AnalysisResult(
                    mood_label=data["mood_label"],
                    mood_score=float(data["mood_score"]),
                    summary=data["summary"],
                    requires_attention=bool(data["requires_attention"]),
                )
        raise LLMAnalysisError("No tool_use block in Claude response")
    except Exception:
        logger.exception("Mood analysis failed for email from %s", sender)
        return AnalysisResult(
            mood_label="neutral",
            mood_score=0.0,
            summary="No se pudo analizar este correo automaticamente.",
            requires_attention=False,
            failed=True,
        )
