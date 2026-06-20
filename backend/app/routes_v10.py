"""Routes v10 Business — devis, intervention detail, settings, users."""
from __future__ import annotations

import base64
import csv
import io
import re
import shutil
from datetime import datetime
from io import BytesIO
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import get_admin_or_redirect, get_user_or_redirect, hash_password, log_activity
from .database import get_session
from .helpers import generate_ai_summary, quote_html, try_pdf_response
from .models import ActivityLog, Client, Intervention, InterventionPart, InterventionPhoto, Invoice, Part, Quote, Ticket, User

router = APIRouter()


def init_v10_routes(templates: Jinja2Templates, storage_dir: Path, report_dir: Path, sanitize_filename, intervention_dir_fn, resolve_storage_path):
    """Injecte les dépendances depuis main."""

    PHOTOS_DIR = storage_dir / "photos"
    SIGNATURES_DIR = storage_dir / "signatures"
    PHOTOS_DIR.mkdir(parents=True, exist_ok=True)
    SIGNATURES_DIR.mkdir(parents=True, exist_ok=True)

    @router.get("/quotes", response_class=HTMLResponse)
    def quotes_list(request: Request, session: Session = Depends(get_session)):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        quotes = session.scalars(select(Quote).order_by(Quote.created_at.desc())).all()
        interventions = session.scalars(select(Intervention).order_by(Intervention.created_at.desc())).all()
        return templates.TemplateResponse("quotes.html", {
            "request": request, "quotes": quotes, "interventions": interventions, "user": user,
        })

    @router.post("/quotes")
    def create_quote(
        request: Request,
        intervention_id: int = Form(...),
        amount: float = Form(...),
        tax: float = Form(0.0),
        description: str = Form(""),
        status: str = Form("draft"),
        valid_until: str = Form(""),
        session: Session = Depends(get_session),
    ):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention introuvable")
        total = amount + tax
        quote_number = f"DEV-{datetime.utcnow().strftime('%Y%m%d')}-{intervention_id:04d}"
        quote = Quote(
            intervention_id=intervention_id,
            client_id=intervention.client_id,
            quote_number=quote_number,
            description=description or None,
            amount=amount,
            tax=tax,
            total=total,
            status=status,
            valid_until=datetime.strptime(valid_until, "%Y-%m-%d") if valid_until else None,
        )
        session.add(quote)
        log_activity(session, user, "quote.create", quote_number)
        session.commit()
        return RedirectResponse("/quotes", status_code=303)

    @router.post("/delete/quote/{quote_id}")
    def delete_quote(quote_id: int, request: Request, session: Session = Depends(get_session)):
        user, redirect = get_admin_or_redirect(request, session)
        if redirect:
            return redirect
        quote = session.scalars(select(Quote).where(Quote.id == quote_id)).first()
        if quote:
            session.delete(quote)
            log_activity(session, user, "quote.delete", str(quote_id))
            session.commit()
        return RedirectResponse("/quotes", status_code=303)

    @router.get("/quote/{quote_id}/pdf")
    def quote_pdf(quote_id: int, request: Request, session: Session = Depends(get_session)):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        quote = session.scalars(select(Quote).where(Quote.id == quote_id)).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Devis introuvable")
        return try_pdf_response(quote_html(quote), f"{quote.quote_number}.pdf")

    @router.post("/quote/{quote_id}/convert")
    def convert_quote_to_invoice(quote_id: int, request: Request, session: Session = Depends(get_session)):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        quote = session.scalars(select(Quote).where(Quote.id == quote_id)).first()
        if not quote:
            raise HTTPException(status_code=404, detail="Devis introuvable")
        existing = session.scalars(select(Invoice).where(Invoice.quote_id == quote_id)).first()
        if existing:
            return RedirectResponse(f"/invoice/{existing.id}/pdf", status_code=303)
        invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{quote.intervention_id or quote_id:04d}"
        invoice = Invoice(
            intervention_id=quote.intervention_id,
            client_id=quote.client_id,
            quote_id=quote.id,
            invoice_number=invoice_number,
            amount=quote.amount,
            tax=quote.tax,
            total=quote.total,
            status="draft",
            notes=quote.description,
        )
        quote.status = "accepted"
        session.add(invoice)
        log_activity(session, user, "quote.convert", f"{quote.quote_number} -> {invoice_number}")
        session.commit()
        return RedirectResponse("/invoices", status_code=303)

    @router.post("/invoice/{invoice_id}/pay")
    def mark_invoice_paid(
        invoice_id: int,
        request: Request,
        payment_method: str = Form("cash"),
        session: Session = Depends(get_session),
    ):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        invoice = session.scalars(select(Invoice).where(Invoice.id == invoice_id)).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Facture introuvable")
        invoice.status = "paid"
        invoice.paid_at = datetime.utcnow()
        invoice.payment_method = payment_method
        log_activity(session, user, "invoice.pay", invoice.invoice_number)
        session.commit()
        return RedirectResponse("/invoices", status_code=303)

    @router.get("/intervention/{intervention_id}", response_class=HTMLResponse)
    def intervention_detail(intervention_id: int, request: Request, session: Session = Depends(get_session)):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention introuvable")
        parts = session.scalars(select(Part).order_by(Part.part_type)).all()
        tickets = session.scalars(select(Ticket).where(Ticket.intervention_id == intervention_id)).all()
        folder = intervention_dir_fn(intervention)
        if folder and not intervention.ai_summary:
            intervention.ai_summary = generate_ai_summary(intervention, folder)
            session.commit()
        return templates.TemplateResponse("intervention_detail.html", {
            "request": request,
            "intervention": intervention,
            "parts": parts,
            "tickets": tickets,
            "user": user,
            "atelier_statuses": ["nouvelle", "en_attente", "en_cours", "termine", "livre", "facture"],
        })

    @router.post("/intervention/{intervention_id}/photo")
    async def upload_intervention_photo(
        intervention_id: int,
        request: Request,
        phase: str = Form("during"),
        file: UploadFile = File(...),
        session: Session = Depends(get_session),
    ):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention introuvable")
        if phase not in {"before", "during", "after"}:
            phase = "during"
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Image requise")
        safe = sanitize_filename(file.filename or "photo.jpg")
        rel = f"photos/int_{intervention_id}_{phase}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{safe}"
        target = storage_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        photo = InterventionPhoto(intervention_id=intervention_id, phase=phase, file_path=rel)
        session.add(photo)
        log_activity(session, user, "intervention.photo", f"#{intervention_id} {phase}")
        session.commit()
        return RedirectResponse(f"/intervention/{intervention_id}", status_code=303)

    @router.post("/intervention/{intervention_id}/signature")
    async def save_intervention_signature(
        intervention_id: int,
        request: Request,
        signature_data: str = Form(...),
        session: Session = Depends(get_session),
    ):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention introuvable")
        match = re.match(r"data:image/(png|jpeg|jpg);base64,(.+)", signature_data, re.I)
        if not match:
            raise HTTPException(status_code=400, detail="Signature invalide")
        ext = "png" if match.group(1).lower() == "png" else "jpg"
        raw = base64.b64decode(match.group(2))
        rel = f"signatures/int_{intervention_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{ext}"
        target = storage_dir / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        intervention.signature_path = rel
        log_activity(session, user, "intervention.signature", f"#{intervention_id}")
        session.commit()
        return RedirectResponse(f"/intervention/{intervention_id}", status_code=303)

    @router.post("/intervention/{intervention_id}/labor")
    def update_intervention_labor(
        intervention_id: int,
        request: Request,
        labor_minutes: int = Form(0),
        labor_rate: float = Form(0.0),
        session: Session = Depends(get_session),
    ):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
        if not intervention:
            raise HTTPException(status_code=404, detail="Intervention introuvable")
        intervention.labor_minutes = max(labor_minutes, 0)
        intervention.labor_rate = max(labor_rate, 0.0)
        log_activity(session, user, "intervention.labor", f"#{intervention_id} {labor_minutes}min")
        session.commit()
        return RedirectResponse(f"/intervention/{intervention_id}", status_code=303)

    @router.post("/intervention/{intervention_id}/parts")
    def add_intervention_part(
        intervention_id: int,
        request: Request,
        part_id: int = Form(...),
        quantity: int = Form(1),
        notes: str = Form(""),
        session: Session = Depends(get_session),
    ):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
        part = session.scalars(select(Part).where(Part.id == part_id)).first()
        if not intervention or not part:
            raise HTTPException(status_code=404, detail="Intervention ou pièce introuvable")
        qty = max(quantity, 1)
        if part.quantity < qty:
            raise HTTPException(status_code=400, detail="Stock insuffisant")
        part.quantity -= qty
        session.add(InterventionPart(
            intervention_id=intervention_id, part_id=part_id, quantity=qty, notes=notes or None,
        ))
        log_activity(session, user, "intervention.part", f"#{intervention_id} part#{part_id} x{qty}")
        session.commit()
        return RedirectResponse(f"/intervention/{intervention_id}", status_code=303)

    @router.get("/settings", response_class=HTMLResponse)
    def settings_page(request: Request, session: Session = Depends(get_session)):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        return templates.TemplateResponse("settings.html", {"request": request, "user": user, "message": None, "error": None})

    @router.post("/settings/password")
    def change_password(
        request: Request,
        current_password: str = Form(...),
        new_password: str = Form(...),
        confirm_password: str = Form(...),
        session: Session = Depends(get_session),
    ):
        from .auth import verify_password
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        if new_password != confirm_password:
            return templates.TemplateResponse("settings.html", {
                "request": request, "user": user, "message": None, "error": "Les mots de passe ne correspondent pas.",
            })
        if len(new_password) < 8:
            return templates.TemplateResponse("settings.html", {
                "request": request, "user": user, "message": None, "error": "Minimum 8 caractères.",
            })
        if not verify_password(current_password, user.hashed_password):
            return templates.TemplateResponse("settings.html", {
                "request": request, "user": user, "message": None, "error": "Mot de passe actuel incorrect.",
            })
        user.hashed_password = hash_password(new_password)
        log_activity(session, user, "settings.password", user.username)
        session.commit()
        return templates.TemplateResponse("settings.html", {
            "request": request, "user": user, "message": "Mot de passe mis à jour.", "error": None,
        })

    @router.get("/users", response_class=HTMLResponse)
    def users_page(request: Request, session: Session = Depends(get_session)):
        user, redirect = get_admin_or_redirect(request, session)
        if redirect:
            return redirect
        users = session.scalars(select(User).order_by(User.created_at.desc())).all()
        return templates.TemplateResponse("users.html", {"request": request, "users": users, "user": user, "error": None})

    @router.post("/users")
    def create_user(
        request: Request,
        username: str = Form(...),
        password: str = Form(...),
        full_name: str = Form(""),
        role: str = Form("technicien"),
        session: Session = Depends(get_session),
    ):
        admin, redirect = get_admin_or_redirect(request, session)
        if redirect:
            return redirect
        if session.scalars(select(User).where(User.username == username)).first():
            users = session.scalars(select(User).order_by(User.created_at.desc())).all()
            return templates.TemplateResponse("users.html", {
                "request": request, "users": users, "user": admin, "error": "Identifiant déjà utilisé.",
            })
        if role not in {"admin", "technicien"}:
            role = "technicien"
        session.add(User(
            username=username.strip(),
            hashed_password=hash_password(password),
            full_name=full_name or None,
            role=role,
        ))
        log_activity(session, admin, "user.create", username)
        session.commit()
        return RedirectResponse("/users", status_code=303)

    @router.post("/delete/user/{user_id}")
    def delete_user(user_id: int, request: Request, session: Session = Depends(get_session)):
        admin, redirect = get_admin_or_redirect(request, session)
        if redirect:
            return redirect
        target = session.scalars(select(User).where(User.id == user_id)).first()
        if target and target.id != admin.id:
            session.delete(target)
            log_activity(session, admin, "user.delete", target.username)
            session.commit()
        return RedirectResponse("/users", status_code=303)

    @router.get("/activity", response_class=HTMLResponse)
    def activitylog_activity_page(request: Request, session: Session = Depends(get_session)):
        user, redirect = get_admin_or_redirect(request, session)
        if redirect:
            return redirect
        logs = session.scalars(select(ActivityLog).order_by(ActivityLog.created_at.desc()).limit(200)).all()
        return templates.TemplateResponse("activity.html", {"request": request, "logs": logs, "user": user})

    @router.get("/export/interventions.csv")
    def export_interventions_csv(request: Request, session: Session = Depends(get_session)):
        user, redirect = get_user_or_redirect(request, session)
        if redirect:
            return redirect
        interventions = session.scalars(select(Intervention).order_by(Intervention.created_at.desc())).all()
        stream = io.StringIO()
        writer = csv.writer(stream)
        writer.writerow(["ID", "Date", "Client", "Machine", "Score", "Disque", "Statut"])
        for item in interventions:
            writer.writerow([
                item.id,
                item.created_at.strftime("%Y-%m-%d %H:%M"),
                item.client.name if item.client else "",
                item.machine_name or "",
                item.health_score or "",
                item.disk_risk or "",
                item.status,
            ])
        return StreamingResponse(
            iter([stream.getvalue().encode("utf-8-sig")]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=interventions.csv"},
        )

    return router
