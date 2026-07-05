import smtplib
from collections import Counter
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.config import settings
from app.models.email_analysis import EmailAnalysis

_TEMPLATES_DIR = Path(__file__).parent / "mailer_templates"
_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATES_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
)

_MOOD_COLORS = {
    "positivo": ("#dcfce7", "#166534"),
    "neutral": ("#f3f4f6", "#374151"),
    "negativo": ("#fee2e2", "#991b1b"),
    "urgente-enojado": ("#fee2e2", "#7f1d1d"),
}


def _send(to_address: str, subject: str, html_body: str) -> None:
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.smtp_from_address
    msg["To"] = to_address
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=15) as server:
        if settings.smtp_use_tls:
            server.starttls()
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.sendmail(settings.smtp_from_address, [to_address], msg.as_string())


def send_magic_link_email(to_address: str, link: str) -> None:
    template = _env.get_template("magic_link.html.j2")
    html = template.render(
        title="Tu enlace de acceso",
        link=link,
        ttl_minutes=settings.magic_link_ttl_minutes,
    )
    _send(to_address, "Tu enlace de acceso a Client's Mood", html)


def send_immediate_report(to_address: str, analysis: EmailAnalysis) -> None:
    template = _env.get_template("immediate_report.html.j2")
    badge_bg, badge_fg = _MOOD_COLORS.get(analysis.mood_label, ("#f3f4f6", "#374151"))
    html = template.render(
        title="Nuevo correo analizado",
        analysis=analysis,
        badge_bg=badge_bg,
        badge_fg=badge_fg,
    )
    _send(to_address, f"Análisis de ánimo: {analysis.subject or '(sin asunto)'}", html)


def send_digest_report(
    to_address: str,
    analyses: list[EmailAnalysis],
    period_start: datetime,
    period_end: datetime,
) -> None:
    template = _env.get_template("digest_report.html.j2")
    counts = Counter(a.mood_label for a in analyses)
    urgent = [a for a in analyses if a.requires_attention]
    html = template.render(
        title="Resumen de estado de ánimo",
        counts=dict(counts),
        urgent=urgent,
        analyses=analyses,
        period_start=period_start,
        period_end=period_end,
    )
    subject = (
        f"Resumen de ánimo — {period_start.strftime('%d/%m')} a {period_end.strftime('%d/%m')}"
    )
    _send(to_address, subject, html)
