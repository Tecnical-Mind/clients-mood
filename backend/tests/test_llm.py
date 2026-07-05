from types import SimpleNamespace
from unittest.mock import patch

from app.services.llm import analyze_email


def _tool_use_response(mood_label="negativo", mood_score=-0.8, requires_attention=True):
    block = SimpleNamespace(
        type="tool_use",
        name="record_mood_analysis",
        input={
            "mood_label": mood_label,
            "mood_score": mood_score,
            "summary": "Cliente insatisfecho con el producto.",
            "requires_attention": requires_attention,
        },
    )
    return SimpleNamespace(content=[block])


def test_analyze_email_happy_path():
    with patch("app.services.llm._call_claude", return_value=_tool_use_response()):
        result = analyze_email("angry@example.com", "Broken!", "This is terrible.")

    assert result.mood_label == "negativo"
    assert result.mood_score == -0.8
    assert result.requires_attention is True
    assert result.failed is False


def test_analyze_email_falls_back_gracefully_on_persistent_failure():
    with patch("app.services.llm._call_claude", side_effect=RuntimeError("API unreachable")):
        result = analyze_email("someone@example.com", "Hi", "Just checking in.")

    assert result.failed is True
    assert result.mood_label == "neutral"


def test_analyze_email_handles_missing_tool_use_block():
    empty_response = SimpleNamespace(content=[SimpleNamespace(type="text", text="oops")])
    with patch("app.services.llm._call_claude", return_value=empty_response):
        result = analyze_email("someone@example.com", "Hi", "body")

    assert result.failed is True
