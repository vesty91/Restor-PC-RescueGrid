"""Utilitaires v10 : documents, analyse IA, filtres."""
from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from fastapi.responses import FileResponse, HTMLResponse

from .models import Intervention, Invoice, Quote


def document_html(
    doc_type: str,
    number: str,
    client_name: str,
    created: str,
    due: str,
    description: str,
    amount: float,
    tax: float,
    total: float,
    status: str,
    extra: str = "",
) -> str:
    title = "Devis" if doc_type == "quote" else "Facture"
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><title>{title} {number}</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:#f5f7fb;color:#172033;margin:40px}}
.page{{max-width:900px;margin:auto;background:white;border-radius:18px;padding:36px;box-shadow:0 20px 50px #0001}}
h1{{color:#0f766e;margin:0 0 8px}} .meta{{color:#667085;margin-bottom:24px}}
table{{width:100%;border-collapse:collapse;margin-top:24px}} th,td{{border-bottom:1px solid #e5e7eb;padding:10px;text-align:left}}
.total{{font-size:28px;font-weight:800;color:#0f766e;margin-top:20px}}
.print-hint{{margin-top:24px;color:#667085;font-size:13px}}
@media print{{body{{background:white;margin:0}}.page{{box-shadow:none;border-radius:0}}.no-print{{display:none}}}}
</style></head><body>
<button class="no-print" onclick="window.print()">Imprimer / PDF</button>
<main class="page">
<h1>{title} {number}</h1>
<p class="meta"><strong>Client :</strong> {client_name}</p>
<p class="meta"><strong>Date :</strong> {created} &nbsp; <strong>{"Validité" if doc_type == "quote" else "Échéance"} :</strong> {due or "-"}</p>
<table><tr><th>Désignation</th><th>Montant HT</th><th>TVA</th><th>Total TTC</th></tr>
<tr><td>{description}</td><td>{amount:.2f} €</td><td>{tax:.2f} €</td><td>{total:.2f} €</td></tr></table>
<p class="total">Total {"estimé" if doc_type == "quote" else "à payer"} : {total:.2f} €</p>
<p><strong>Statut :</strong> {status}</p>
{extra}
<p class="print-hint">Document généré par Restor-PC RescueGrid v10.</p>
</main></body></html>"""


def quote_html(quote: Quote) -> str:
    client = quote.client
    intervention = quote.intervention
    desc = quote.description or (intervention.title if intervention else "Intervention Restor-PC RescueGrid")
    valid = quote.valid_until.strftime("%d/%m/%Y") if quote.valid_until else ""
    return document_html(
        "quote",
        quote.quote_number,
        client.name if client else "Client",
        quote.created_at.strftime("%d/%m/%Y"),
        valid,
        desc,
        quote.amount,
        quote.tax,
        quote.total,
        quote.status,
    )


def invoice_html(invoice: Invoice) -> str:
    client = invoice.client
    intervention = invoice.intervention
    desc = invoice.notes or (intervention.title if intervention else "Intervention Restor-PC RescueGrid")
    due = invoice.due_date.strftime("%d/%m/%Y") if invoice.due_date else ""
    paid = f"<p><strong>Payé le :</strong> {invoice.paid_at.strftime('%d/%m/%Y')}</p>" if invoice.paid_at else ""
    method = f"<p><strong>Mode de paiement :</strong> {invoice.payment_method}</p>" if invoice.payment_method else ""
    return document_html(
        "invoice",
        invoice.invoice_number,
        client.name if client else "Client",
        invoice.created_at.strftime("%d/%m/%Y"),
        due,
        desc,
        invoice.amount,
        invoice.tax,
        invoice.total,
        invoice.status,
        extra=paid + method,
    )


def try_pdf_response(html_content: str, filename: str) -> FileResponse | HTMLResponse:
    """Génère un PDF via wkhtmltopdf si disponible, sinon HTML imprimable."""
    wkhtml = None
    for cmd in ("wkhtmltopdf", r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"):
        try:
            subprocess.run([cmd, "--version"], capture_output=True, check=True, timeout=5)
            wkhtml = cmd
            break
        except (FileNotFoundError, subprocess.SubprocessError, OSError):
            continue
    if not wkhtml:
        return HTMLResponse(html_content)
    with tempfile.TemporaryDirectory() as tmp:
        html_path = Path(tmp) / "doc.html"
        pdf_path = Path(tmp) / filename
        html_path.write_text(html_content, encoding="utf-8")
        try:
            subprocess.run(
                [wkhtml, "--enable-local-file-access", "--quiet", str(html_path), str(pdf_path)],
                check=True,
                timeout=30,
                capture_output=True,
            )
            if pdf_path.is_file():
                return FileResponse(pdf_path, filename=filename, media_type="application/pdf")
        except (subprocess.SubprocessError, OSError):
            pass
    return HTMLResponse(html_content)


def generate_ai_summary(intervention: Intervention, folder: Path | None) -> str:
    """Analyse heuristique locale (SMART, Windows, score) — sans API externe."""
    lines = ["=== Analyse Restor-PC RescueGrid ===", ""]
    score = intervention.health_score
    if score is not None:
        if score >= 90:
            lines.append(f"Score santé {score}/100 : machine globalement saine.")
        elif score >= 70:
            lines.append(f"Score santé {score}/100 : surveillance recommandée.")
        else:
            lines.append(f"Score santé {score}/100 : intervention prioritaire.")

    disk = (intervention.disk_risk or "").lower()
    if disk in ("healthy", "ok", "faible"):
        lines.append("Disque : SMART matériel OK — pas de panne hardware détectée.")
    elif disk in ("attention", "warning", "suspect"):
        lines.append("Disque : état suspect — image disque recommandée avant réparation.")
    elif disk:
        lines.append(f"Disque : risque {intervention.disk_risk} — ddrescue avant toute action destructive.")

    if intervention.data_loss_risk:
        lines.append(f"Risque perte données : {intervention.data_loss_risk}.")

    if folder and (folder / "inventory.json").is_file():
        try:
            inv = json.loads((folder / "inventory.json").read_text(encoding="utf-8-sig"))
            health = inv.get("health") or {}
            for key in ("windows_issues", "critical_events", "bsod_count"):
                if health.get(key):
                    lines.append(f"Windows — {key} : {health[key]}")
            disk_risk = inv.get("disk_risk") or {}
            if isinstance(disk_risk, dict) and disk_risk.get("recommendation"):
                lines.append(f"Recommandation : {disk_risk['recommendation']}")
        except (json.JSONDecodeError, OSError):
            pass

    lines.extend([
        "",
        "Cause probable : dégradation progressive ou anomalies système cumulées.",
        "Action : sauvegarde, puis réparation ciblée selon rapport HTML.",
    ])
    return "\n".join(lines)


def apply_intervention_filters(query, status: str | None, sort: str | None):
    from .models import Intervention

    if status:
        query = query.where(Intervention.status == status)
    if sort == "score":
        return query.order_by(Intervention.health_score.desc().nulls_last())
    if sort == "date_asc":
        return query.order_by(Intervention.created_at.asc())
    return query.order_by(Intervention.created_at.desc())
