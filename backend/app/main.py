import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import get_session, init_db, SessionLocal
from .helpers import apply_intervention_filters, generate_ai_summary, invoice_html, try_pdf_response
from .models import Client, Intervention, Invoice, Machine, Part, Quote, Ticket, User
from .routes_v10 import init_v10_routes


BASE_DIR = Path(__file__).resolve().parents[1]
STORAGE_DIR = Path(os.getenv("STORAGE_PATH", str(BASE_DIR / "storage"))).resolve()
UPLOAD_DIR = STORAGE_DIR / "uploads"
REPORT_DIR = STORAGE_DIR / "reports"
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(2 * 1024 * 1024 * 1024)))
MAX_ZIP_FILES = int(os.getenv("MAX_ZIP_FILES", "10000"))
MAX_ZIP_UNCOMPRESSED_BYTES = int(os.getenv("MAX_ZIP_UNCOMPRESSED_BYTES", str(4 * 1024 * 1024 * 1024)))
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_filename(value: str) -> str:
    cleaned = "".join(c if c.isalnum() or c in "-_." else "_" for c in value)
    return cleaned[:180] or "upload"

def safe_extract_zip(archive_path: Path, destination: Path) -> None:
    destination = destination.resolve()
    total_size = 0
    with ZipFile(archive_path) as archive:
        members = archive.infolist()
        if len(members) > MAX_ZIP_FILES:
            raise HTTPException(status_code=413, detail=f"Archive trop volumineuse: {len(members)} fichiers")
        for member in members:
            total_size += max(member.file_size, 0)
            if total_size > MAX_ZIP_UNCOMPRESSED_BYTES:
                raise HTTPException(status_code=413, detail="Archive ZIP trop volumineuse apres extraction")
            target_path = (destination / member.filename).resolve()
            if not str(target_path).startswith(str(destination)):
                raise HTTPException(status_code=400, detail="Archive ZIP invalide: chemin dangereux detecte")
        archive.extractall(destination)


def get_logo_path() -> str | None:
    """Logo affiché dans le dashboard. Utilise le logo Restor-PC embarqué par défaut."""
    config_path = BASE_DIR / "logo_config.json"
    if config_path.exists():
        try:
            configured = json.loads(config_path.read_text(encoding="utf-8")).get("logo_path")
            if configured:
                return configured
        except Exception:
            pass
    default_logo = BASE_DIR / "static" / "restorpc_logo.png"
    if default_logo.exists():
        return "/static/restorpc_logo.png"
    return None


def risk_badge(level: str | None) -> dict:
    value = (level or "").lower()
    if any(word in value for word in ["critical", "critique", "noir", "urgent"]):
        return {"label": "Critique", "emoji": "⚫", "class": "risk-critical"}
    if any(word in value for word in ["high", "haut", "rouge", "danger"]):
        return {"label": "Élevé", "emoji": "🔴", "class": "risk-high"}
    if any(word in value for word in ["warning", "warn", "suspect", "orange", "moyen"]):
        return {"label": "Surveillance", "emoji": "🟠", "class": "risk-warning"}
    if value:
        return {"label": level, "emoji": "🟢", "class": "risk-ok"}
    return {"label": "Non évalué", "emoji": "⚪", "class": "risk-none"}



def _gb(value) -> str:
    try:
        return f"{float(value) / (1024 ** 3):.0f} Go"
    except Exception:
        return "-"


def _tb(value) -> str:
    try:
        tb = float(value) / (1024 ** 4)
        return f"{tb:.2f} To"
    except Exception:
        return "-"


def _as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return [value]
    return []

def _first_dict(*values):
    for value in values:
        if isinstance(value, dict) and value:
            return value
        if isinstance(value, list):
            for item in value:
                if isinstance(item, dict) and item:
                    return item
    return {}

def _pick(d, *keys):
    if not isinstance(d, dict):
        return None
    lowered = {str(k).lower(): v for k, v in d.items()}
    for key in keys:
        if key in d and d.get(key) not in (None, ""):
            return d.get(key)
        lk = str(key).lower()
        if lk in lowered and lowered[lk] not in (None, ""):
            return lowered[lk]
    return None

def _hardware_from_inventory(inv: dict) -> dict:
    """Extraction robuste CPU/RAM/GPU/Windows/stockage depuis inventory.json."""
    machine = _first_dict(
        inv.get("machine"), inv.get("system"), inv.get("computer_system"),
        inv.get("computerSystem"), inv.get("os"), inv.get("operating_system")
    )
    osinfo = _first_dict(inv.get("os"), inv.get("operating_system"), inv.get("windows"), inv.get("machine"))
    cpu = _first_dict(inv.get("processors"), inv.get("processor"), inv.get("cpu"), inv.get("cpus"))
    gpu = _first_dict(inv.get("video_controllers"), inv.get("video"), inv.get("gpu"), inv.get("gpus"), inv.get("graphics"))
    disks = _as_list(inv.get("disks") or inv.get("physical_disks") or inv.get("drives") or inv.get("storage"))

    cpu_name = _pick(cpu, "Name", "name", "ProcessorName", "Model") or "-"
    cores = _pick(cpu, "NumberOfCores", "Cores", "cores")
    threads = _pick(cpu, "NumberOfLogicalProcessors", "LogicalProcessors", "threads")
    cpu_sub = f"{cores or '-'} cœurs / {threads or '-'} threads" if cores or threads else ""

    ram_bytes = _pick(machine, "CsTotalPhysicalMemory", "TotalPhysicalMemory", "total_physical_memory", "MemoryBytes")
    ram = _gb(ram_bytes) if ram_bytes else (_pick(machine, "RAM", "ram", "Memory") or "-")

    gpu_name = _pick(gpu, "Name", "name", "Caption", "Model") or "-"
    gpu_ram = _pick(gpu, "AdapterRAM", "Memory", "RAM")
    gpu_sub = _gb(gpu_ram) if gpu_ram else ""

    windows_name = (
        _pick(osinfo, "WindowsProductName", "Caption", "ProductName", "Name", "windows")
        or _pick(machine, "WindowsProductName", "Caption", "ProductName", "Name")
        or "-"
    )
    windows_version = _pick(osinfo, "WindowsVersion", "Version", "BuildNumber", "OSVersion") or _pick(machine, "WindowsVersion", "Version") or ""

    total = 0
    nvme_count = usb_count = ssd_count = hdd_count = 0
    for d in disks:
        if not isinstance(d, dict):
            continue
        size = _pick(d, "Size", "size", "TotalSize", "Bytes")
        try:
            total += int(float(size or 0))
        except Exception:
            pass
        bus = str(_pick(d, "BusType", "bus", "InterfaceType", "Interface") or "").lower()
        media = str(_pick(d, "MediaType", "type", "Model", "FriendlyName") or "").lower()
        if "nvme" in bus or "nvme" in media:
            nvme_count += 1
        if "usb" in bus:
            usb_count += 1
        if "ssd" in media or "nvme" in bus:
            ssd_count += 1
        if "hdd" in media:
            hdd_count += 1

    parts = []
    if nvme_count:
        parts.append(f"{nvme_count} NVMe")
    if ssd_count and not nvme_count:
        parts.append(f"{ssd_count} SSD")
    if hdd_count:
        parts.append(f"{hdd_count} HDD")
    if usb_count:
        parts.append(f"{usb_count} USB")

    return {
        "cpu": cpu_name,
        "cpu_sub": cpu_sub,
        "ram": ram,
        "ram_sub": "Mémoire installée" if ram and ram != "-" else "",
        "gpu": gpu_name,
        "gpu_sub": gpu_sub,
        "windows": str(windows_name).replace("Microsoft ", "") if windows_name else "-",
        "windows_sub": str(windows_version or ""),
        "storage": _tb(total) if total else "-",
        "storage_sub": " + ".join(parts),
    }


def _clean_html_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", value or "")
    value = value.replace("&nbsp;", " ").replace("&eacute;", "é").replace("&egrave;", "è").replace("&agrave;", "à")
    value = value.replace("&ocirc;", "ô").replace("&rsquo;", "'").replace("&mdash;", "—")
    return re.sub(r"\s+", " ", value).strip()


def _extract_table_value_from_report(html_text: str, label: str) -> str | None:
    """Lit une valeur simple depuis les tables du rapport HTML généré par l'agent."""
    pattern = rf"<tr>\s*<th>\s*{re.escape(label)}\s*</th>\s*<td>(.*?)</td>\s*</tr>"
    match = re.search(pattern, html_text, flags=re.I | re.S)
    if match:
        value = _clean_html_text(match.group(1))
        return value if value and value != "-" else None
    return None


def _hardware_from_report_html(report_path: Path | None) -> dict:
    """Fallback lorsque inventory.json n'est plus accessible mais que rapport.html existe."""
    if not report_path or not report_path.exists():
        return {}
    try:
        html_text = report_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return {}

    cpu = _extract_table_value_from_report(html_text, "Processeur(s)")
    ram = _extract_table_value_from_report(html_text, "RAM")
    gpu = _extract_table_value_from_report(html_text, "Carte graphique")
    windows = _extract_table_value_from_report(html_text, "Windows")

    # Additionne les tailles disque visibles dans le tableau "Disques" du rapport.
    total_gb = 0.0
    try:
        disk_section = re.search(r"<h2>Disques</h2>(.*?)(?:<h2>|</main>)", html_text, flags=re.I | re.S)
        if disk_section:
            for size_txt in re.findall(r">([0-9]+(?:[.,][0-9]+)?)\s*GB<", disk_section.group(1), flags=re.I):
                total_gb += float(size_txt.replace(",", "."))
    except Exception:
        total_gb = 0.0

    hardware = {}
    if cpu:
        hardware["cpu"] = cpu
        m = re.search(r"\(([^)]*(?:coeurs|cœurs|logiques)[^)]*)\)", cpu, flags=re.I)
        hardware["cpu_sub"] = m.group(1) if m else ""
    if ram:
        hardware["ram"] = ram
        hardware["ram_sub"] = "Mémoire installée"
    if gpu:
        hardware["gpu"] = gpu
        m = re.search(r"RAM:\s*([^/)]*)", gpu, flags=re.I)
        hardware["gpu_sub"] = m.group(1).strip() if m else ""
    if windows:
        hardware["windows"] = windows.replace("Microsoft ", "")
        hardware["windows_sub"] = ""
    if total_gb:
        hardware["storage"] = f"{total_gb/1024:.2f} To" if total_gb >= 1024 else f"{total_gb:.0f} Go"
        hardware["storage_sub"] = "Stockage détecté"
    return hardware


def _hardware_for_intervention(intervention: Intervention | None) -> dict:
    specs = {
        "machine": "-",
        "cpu": "-",
        "cpu_sub": "",
        "ram": "-",
        "ram_sub": "",
        "gpu": "-",
        "gpu_sub": "",
        "windows": "-",
        "windows_sub": "",
        "storage": "-",
        "storage_sub": "",
    }
    if not intervention:
        return specs

    specs["machine"] = intervention.machine_name or (intervention.machine.machine_name if intervention.machine else "-")

    folder = intervention_dir(intervention)
    candidates: list[Path] = []
    if folder:
        candidates.append(folder / "inventory.json")
    # Fallback : recherche par nom de dossier/titre, utile après déplacement de projet.
    try:
        title_token = sanitize_filename(intervention.title or "")
        for p in REPORT_DIR.glob(f"*{title_token}*/inventory.json"):
            candidates.append(p)
        if intervention.machine_name:
            for p in REPORT_DIR.glob(f"*{sanitize_filename(intervention.machine_name)}*/inventory.json"):
                candidates.append(p)
    except Exception:
        pass

    for inv_path in candidates:
        if inv_path and inv_path.exists():
            try:
                inv = json.loads(inv_path.read_text(encoding="utf-8-sig", errors="replace"))
                specs.update({k: v for k, v in _hardware_from_inventory(inv).items() if v not in (None, "", "-")})
                break
            except Exception:
                pass

    # Fallback rapport HTML.
    report_candidates: list[Path] = []
    if folder:
        report_candidates.append(folder / "rapport.html")
        report_candidates.append(folder / "report.html")
    if intervention.report_path:
        try:
            report_candidates.append(resolve_storage_path(intervention.report_path))
        except Exception:
            pass
    try:
        if intervention.machine_name:
            for p in REPORT_DIR.glob(f"*{sanitize_filename(intervention.machine_name)}*/rapport.html"):
                report_candidates.append(p)
            for p in REPORT_DIR.glob(f"*{sanitize_filename(intervention.machine_name)}*/report.html"):
                report_candidates.append(p)
    except Exception:
        pass
    if specs.get("cpu") in (None, "", "-") or specs.get("ram") in (None, "", "-") or specs.get("gpu") in (None, "", "-") or specs.get("storage") in (None, "", "-"):
        for report_path in report_candidates:
            fallback = _hardware_from_report_html(report_path)
            if fallback:
                for key, value in fallback.items():
                    if specs.get(key) in (None, "", "-") and value not in (None, "", "-"):
                        specs[key] = value
                break

    return specs


def dashboard_machine_specs(intervention: Intervention | None) -> dict:
    """Résumé matériel pour le tableau de bord premium."""
    return _hardware_for_intervention(intervention)

def default_billing_amount(intervention: Intervention | None) -> float:
    if not intervention:
        return 60.0
    minutes = int(getattr(intervention, "labor_minutes", 0) or 0)
    rate = float(getattr(intervention, "labor_rate", 0) or 60.0)
    if minutes > 0:
        return round((minutes / 60.0) * rate, 2)
    return 60.0


def today_date() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def build_dashboard_context(
    request: Request,
    session: Session,
    user: User,
    q: str | None = None,
    status: str | None = None,
    sort: str | None = None,
) -> dict:
    if q:
        query = f"%{q}%"
        clients = session.scalars(select(Client).where(Client.name.ilike(query)).order_by(Client.created_at.desc())).all()
        machines = session.scalars(select(Machine).where(
            (Machine.machine_name.ilike(query)) | (Machine.bios_serial.ilike(query)) |
            (Machine.manufacturer.ilike(query)) | (Machine.model.ilike(query))
        ).order_by(Machine.last_intervention.desc().nulls_last())).all()
        interventions = session.scalars(select(Intervention).where(
            (Intervention.title.ilike(query)) | (Intervention.machine_name.ilike(query)) |
            (Intervention.bios_serial.ilike(query)) | (Intervention.status.ilike(query))
        ).order_by(Intervention.created_at.desc())).all()
        parts = session.scalars(select(Part).where(
            (Part.brand.ilike(query)) | (Part.model.ilike(query)) |
            (Part.serial_number.ilike(query)) | (Part.part_type.ilike(query))
        ).order_by(Part.created_at.desc())).all()
        invoices = session.scalars(select(Invoice).where(Invoice.invoice_number.ilike(query)).order_by(Invoice.created_at.desc())).all()
        quotes = session.scalars(select(Quote).where(Quote.quote_number.ilike(query)).order_by(Quote.created_at.desc())).all()
        tickets = session.scalars(select(Ticket).where(
            (Ticket.title.ilike(query)) | (Ticket.description.ilike(query)) |
            (Ticket.priority.ilike(query)) | (Ticket.status.ilike(query))
        ).order_by(Ticket.created_at.desc())).all()
    else:
        clients = session.scalars(select(Client).order_by(Client.created_at.desc())).all()
        iq = apply_intervention_filters(select(Intervention), status, sort)
        interventions = session.scalars(iq).all()
        machines = session.scalars(select(Machine).order_by(Machine.last_intervention.desc().nulls_last())).all()
        parts = session.scalars(select(Part).order_by(Part.created_at.desc())).all()
        invoices = session.scalars(select(Invoice).order_by(Invoice.created_at.desc())).all()
        quotes = session.scalars(select(Quote).order_by(Quote.created_at.desc())).all()
        tickets = session.scalars(select(Ticket).order_by(Ticket.created_at.desc())).all()

    critical_words = ("critical", "critique", "rouge", "noir", "urgent", "danger", "high")
    warning_words = ("warning", "suspect", "orange", "moyen", "surveillance")
    disk_critical = [i for i in interventions if any(w in ((i.disk_risk or "") + " " + (i.data_loss_risk or "")).lower() for w in critical_words)]
    disk_warning = [i for i in interventions if any(w in ((i.disk_risk or "") + " " + (i.data_loss_risk or "")).lower() for w in warning_words)]
    open_tickets = [t for t in tickets if (t.status or "").lower() in {"open", "in_progress", "nouveau", "ouvert"}]
    now = datetime.utcnow()
    month_invoices = [i for i in invoices if i.created_at.year == now.year and i.created_at.month == now.month and (i.status or "").lower() in {"paid", "payee", "payée"}]
    monthly_revenue = sum(float(i.total or 0) for i in month_invoices)

    alerts = []
    for item in disk_critical[:8]:
        alerts.append({"level": "critical", "title": item.title, "message": f"Risque disque/données: {item.disk_risk or item.data_loss_risk}", "url": f"/intervention/{item.id}"})
    for item in disk_warning[:8]:
        alerts.append({"level": "warning", "title": item.title, "message": f"À surveiller: {item.disk_risk or item.data_loss_risk}", "url": f"/intervention/{item.id}"})
    for ticket in open_tickets[:6]:
        alerts.append({"level": "ticket", "title": ticket.title, "message": f"Ticket {ticket.priority} · {ticket.status}", "url": "/tickets"})

    stats = {
        "clients": len(clients),
        "machines": len(machines),
        "interventions": len(interventions),
        "disk_critical": len(disk_critical),
        "disk_warning": len(disk_warning),
        "tickets_open": len(open_tickets),
        "monthly_revenue": monthly_revenue,
        "parts_stock": sum(max(p.quantity or 0, 0) for p in parts),
        "best_score": max([i.health_score for i in interventions if i.health_score is not None] or [0]),
    }

    return {
        "request": request,
        "clients": clients,
        "interventions": interventions,
        "machines": machines,
        "parts": parts,
        "invoices": invoices,
        "quotes": quotes,
        "tickets": tickets,
        "user": user,
        "logo_path": get_logo_path(),
        "stats": stats,
        "alerts": alerts[:12],
        "recent_interventions": interventions[:10],
        "recent_tickets": tickets[:8],
        "risk_machines": [m for m in machines if any(i.disk_risk and str(i.disk_risk).lower() not in {"healthy", "ok", "faible"} for i in m.interventions)][:10],
        "atelier_statuses": ["nouvelle", "en_attente", "en_cours", "termine", "livre", "facture"],
        "risk_badge": risk_badge,
        "search_query": q or "",
        "filter_status": status or "",
        "filter_sort": sort or "",
        "dashboard_specs": dashboard_machine_specs(interventions[0] if interventions else None),
    }



def intervention_url(intervention: Intervention) -> str:
    return f"/intervention/{intervention.id}"


def intervention_dir(intervention: Intervention) -> Path | None:
    if intervention.report_path:
        return (STORAGE_DIR / intervention.report_path).resolve().parent
    if intervention.archive_path:
        return REPORT_DIR / Path(intervention.archive_path).stem
    return None


def resolve_storage_path(relative_path: str) -> Path:
    target = (STORAGE_DIR / relative_path).resolve()
    if not str(target).startswith(str(STORAGE_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Chemin invalide")
    return target


app = FastAPI(title="Restor-PC RescueGrid")
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.include_router(
    init_v10_routes(
        templates, STORAGE_DIR, REPORT_DIR, sanitize_filename, intervention_dir, resolve_storage_path
    )
)


@app.on_event("startup")
def on_startup() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    init_db()
    with SessionLocal() as session:
        from .auth import create_default_admin
        create_default_admin(session)


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    session: Session = Depends(get_session),
):
    from .auth import authenticate_user, create_access_token
    user = authenticate_user(username, password, session)
    if not user:
        return templates.TemplateResponse("login.html", {"request": request, "error": "Identifiants invalides"})
    token = create_access_token({"sub": user.username})
    response = RedirectResponse("/", status_code=303)
    response.set_cookie("access_token", token, httponly=True, max_age=480*60)
    user.last_login = datetime.utcnow()
    session.commit()
    return response


@app.get("/logout")
def logout():
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie("access_token")
    return response


@app.get("/", response_class=HTMLResponse)
def dashboard(
    request: Request,
    status: str = "",
    sort: str = "",
    session: Session = Depends(get_session),
):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        "dashboard.html",
        build_dashboard_context(request, session, user, status=status or None, sort=sort or None),
    )


@app.get("/search")
def search(request: Request, q: str = "", session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse("dashboard.html", build_dashboard_context(request, session, user, q=q.strip()))


@app.get("/client/{client_id}", response_class=HTMLResponse)
def client_detail(client_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user, require_auth
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    client = session.scalars(select(Client).where(Client.id == client_id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    interventions = session.scalars(
        select(Intervention).where(Intervention.client_id == client_id).order_by(Intervention.created_at.desc())
    ).all()
    return templates.TemplateResponse(
        "client_detail.html",
        {"request": request, "client": client, "interventions": interventions, "user": user},
    )


@app.get("/machine/{machine_id}", response_class=HTMLResponse)
def machine_detail(machine_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    machine = session.scalars(select(Machine).where(Machine.id == machine_id)).first()
    if not machine:
        raise HTTPException(status_code=404, detail="Machine introuvable")
    interventions = session.scalars(
        select(Intervention).where(Intervention.machine_id == machine_id).order_by(Intervention.created_at.desc())
    ).all()

    latest = interventions[0] if interventions else None
    hardware = _hardware_for_intervention(latest)

    return templates.TemplateResponse(
        "machine_detail.html",
        {"request": request, "machine": machine, "interventions": interventions, "hardware": hardware, "best_score": max([i.health_score for i in interventions if i.health_score is not None], default=None), "user": user},
    )


@app.post("/clients")
def create_client(
    request: Request,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    client = Client(name=name.strip(), email=email or None, phone=phone or None)
    session.add(client)
    session.commit()
    return RedirectResponse("/", status_code=303)




@app.post("/client/{client_id}/update")
def update_client(
    client_id: int,
    request: Request,
    name: str = Form(...),
    email: str = Form(""),
    phone: str = Form(""),
    address: str = Form(""),
    contact_name: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    client = session.scalars(select(Client).where(Client.id == client_id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    client.name = name.strip()
    client.email = email.strip() or None
    client.phone = phone.strip() or None
    client.address = address.strip() or None
    client.contact_name = contact_name.strip() or None
    session.commit()
    return RedirectResponse(f"/client/{client_id}", status_code=303)


@app.post("/machines")
def create_machine(
    request: Request,
    bios_serial: str = Form(""),
    machine_name: str = Form(""),
    manufacturer: str = Form(""),
    model: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    machine = Machine(
        bios_serial=bios_serial or None,
        machine_name=machine_name or None,
        manufacturer=manufacturer or None,
        model=model or None,
    )
    session.add(machine)
    session.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/interventions")
def create_intervention(
    request: Request,
    title: str = Form(...),
    client_id: int = Form(...),
    machine_id: int = Form(0),
    machine_name: str = Form(""),
    status: str = Form("nouvelle"),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = Intervention(
        client_id=client_id,
        machine_id=machine_id if machine_id > 0 else None,
        title=title.strip(),
        machine_name=machine_name or None,
        status=status,
    )
    session.add(intervention)
    session.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/upload")
async def upload_intervention(
    request: Request,
    client_name: str = Form(...),
    file: UploadFile = File(...),
    upload_key: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import verify_upload_access
    if not verify_upload_access(request, session, upload_key or None):
        raise HTTPException(status_code=401, detail="Authentification requise pour l'import ZIP")
    if not file.filename or not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Archive ZIP requise")

    safe_name = sanitize_filename(client_name)
    safe_file = sanitize_filename(Path(file.filename).name)
    archive_path = UPLOAD_DIR / f"{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}_{safe_name}_{safe_file}"

    written = 0
    with archive_path.open("wb") as buffer:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            written += len(chunk)
            if written > MAX_UPLOAD_BYTES:
                archive_path.unlink(missing_ok=True)
                raise HTTPException(status_code=413, detail="Archive trop volumineuse")
            buffer.write(chunk)

    extracted_dir = REPORT_DIR / archive_path.stem
    extracted_dir.mkdir(parents=True, exist_ok=True)
    safe_extract_zip(archive_path, extracted_dir)

    inventory_path = extracted_dir / "inventory.json"
    report_path = extracted_dir / "rapport.html"
    inventory = {}
    if inventory_path.exists():
        try:
            inventory = json.loads(inventory_path.read_text(encoding="utf-8-sig"))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise HTTPException(status_code=422, detail=f"inventory.json invalide: {e}")

    # Client
    client = session.scalars(select(Client).where(Client.name == client_name)).first()
    if client is None:
        client = Client(name=client_name)
        session.add(client)
        session.commit()
        session.refresh(client)

    # Machine / Historique
    bios = inventory.get("bios") or {}
    bios_serial = bios.get("SerialNumber")
    machine_name = inventory.get("machine", {}).get("CsName")
    machine_id = None

    if bios_serial:
        machine = session.scalars(select(Machine).where(Machine.bios_serial == bios_serial)).first()
        if machine is None:
            machine = Machine(
                bios_serial=bios_serial,
                machine_name=machine_name,
                manufacturer=bios.get("Manufacturer"),
                model=inventory.get("machine", {}).get("CsModel"),
            )
            session.add(machine)
            session.commit()
            session.refresh(machine)
        machine.last_intervention = datetime.utcnow()
        machine.machine_name = machine_name
        session.commit()
        machine_id = machine.id

    # Intervention
    machine = inventory.get("machine") or {}
    health = inventory.get("health") or {}
    disk_risk = inventory.get("disk_risk") or {}
    offline_windows = inventory.get("offline_windows") or {}
    intervention = Intervention(
        client_id=client.id,
        machine_id=machine_id,
        title=archive_path.stem,
        machine_name=machine.get("CsName") or None,
        bios_serial=bios_serial,
        health_score=health.get("global_score"),
        data_loss_risk=health.get("data_loss_risk"),
        disk_risk=disk_risk.get("level") if isinstance(disk_risk, dict) else None,
        offline_windows="oui" if isinstance(offline_windows, dict) and offline_windows.get("enabled") else "non",
        status="rapport importe",
        archive_path=str(archive_path.relative_to(STORAGE_DIR)),
        report_path=str(report_path.relative_to(STORAGE_DIR)) if report_path.exists() else None,
    )
    session.add(intervention)
    session.commit()
    session.refresh(intervention)
    intervention.ai_summary = generate_ai_summary(intervention, extracted_dir)
    session.commit()
    return RedirectResponse(f"/intervention/{intervention.id}", status_code=303)


@app.post("/delete/client/{client_id}")
def delete_client(client_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_admin_or_redirect
    user, redirect = get_admin_or_redirect(request, session)
    if redirect:
        return redirect
    client = session.scalars(select(Client).where(Client.id == client_id)).first()
    if client:
        session.delete(client)
        session.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/delete/intervention/{intervention_id}")
def delete_intervention(intervention_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_admin_or_redirect
    user, redirect = get_admin_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if intervention:
        session.delete(intervention)
        session.commit()
    return RedirectResponse("/", status_code=303)


@app.get("/parts", response_class=HTMLResponse)
def parts_list(request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    parts = session.scalars(select(Part).order_by(Part.created_at.desc())).all()
    return templates.TemplateResponse("parts.html", {"request": request, "parts": parts, "user": user})


@app.post("/parts")
def create_part(
    request: Request,
    part_type: str = Form(...),
    brand: str = Form(""),
    model: str = Form(""),
    serial_number: str = Form(""),
    capacity_gb: int = Form(0),
    quantity: int = Form(1),
    notes: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    part = Part(
        part_type=part_type,
        brand=brand or None,
        model=model or None,
        serial_number=serial_number or None,
        capacity_gb=capacity_gb if capacity_gb > 0 else None,
        quantity=quantity,
        notes=notes or None,
    )
    session.add(part)
    session.commit()
    return RedirectResponse("/parts", status_code=303)


@app.post("/delete/part/{part_id}")
def delete_part(part_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_admin_or_redirect
    user, redirect = get_admin_or_redirect(request, session)
    if redirect:
        return redirect
    part = session.scalars(select(Part).where(Part.id == part_id)).first()
    if part:
        session.delete(part)
        session.commit()
    return RedirectResponse("/parts", status_code=303)


@app.post("/upload-logo")
async def upload_logo(request: Request, file: UploadFile = File(...), session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        raise HTTPException(status_code=401, detail="Non autorise")
    
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Fichier image requis")
    
    logo_dir = STORAGE_DIR / "logos"
    logo_dir.mkdir(exist_ok=True)
    logo_path = logo_dir / "logo.png"
    
    with logo_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Mettre à jour le chemin dans la session (ou base de données)
    # Pour simplifier, on utilise un fichier de config
    config_path = BASE_DIR / "logo_config.json"
    config_path.write_text(json.dumps({"logo_path": "logos/logo.png"}), encoding="utf-8")
    
    return RedirectResponse("/", status_code=303)


@app.get("/logo-config")
def get_logo_config():
    config_path = BASE_DIR / "logo_config.json"
    if config_path.exists():
        config = json.loads(config_path.read_text(encoding="utf-8"))
        return {"logo_path": config.get("logo_path")}
    return {"logo_path": None}


# ===== FACTURATION v5.0 =====
@app.get("/invoices", response_class=HTMLResponse)
def invoices_list(request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    invoices = session.scalars(select(Invoice).order_by(Invoice.created_at.desc())).all()
    interventions = session.scalars(select(Intervention).order_by(Intervention.created_at.desc())).all()
    return templates.TemplateResponse("invoices.html", {
        "request": request, "invoices": invoices, "interventions": interventions, "user": user,
        "default_billing_amount": default_billing_amount, "today_date": today_date,
    })


@app.post("/invoices")
def create_invoice(
    request: Request,
    intervention_id: int = Form(...),
    amount: float = Form(0.0),
    tax: float = Form(0.0),
    status: str = Form("draft"),
    due_date: str = Form(""),
    notes: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    if not amount or amount <= 0:
        amount = default_billing_amount(intervention)

    tax = 0.0
    total = amount
    invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{intervention_id:04d}"
    
    invoice = Invoice(
        intervention_id=intervention_id,
        client_id=intervention.client_id,
        invoice_number=invoice_number,
        amount=amount,
        tax=tax,
        total=total,
        status=status,
        due_date=datetime.strptime(due_date, "%Y-%m-%d") if due_date else None,
        notes=notes or None,
    )
    session.add(invoice)
    session.commit()
    return RedirectResponse("/invoices", status_code=303)


@app.post("/delete/invoice/{invoice_id}")
def delete_invoice(invoice_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_admin_or_redirect
    user, redirect = get_admin_or_redirect(request, session)
    if redirect:
        return redirect
    invoice = session.scalars(select(Invoice).where(Invoice.id == invoice_id)).first()
    if invoice:
        session.delete(invoice)
        session.commit()
    return RedirectResponse("/invoices", status_code=303)


# ===== TICKETS v5.0 =====
@app.get("/tickets", response_class=HTMLResponse)
def tickets_list(request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    tickets = session.scalars(select(Ticket).order_by(Ticket.created_at.desc())).all()
    return templates.TemplateResponse("tickets.html", {"request": request, "tickets": tickets, "user": user})


@app.post("/tickets")
def create_ticket(
    request: Request,
    intervention_id: int = Form(...),
    title: str = Form(...),
    description: str = Form(""),
    priority: str = Form("medium"),
    status: str = Form("open"),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    
    ticket = Ticket(
        intervention_id=intervention_id,
        client_id=intervention.client_id,
        title=title,
        description=description or None,
        priority=priority,
        status=status,
    )
    session.add(ticket)
    session.commit()
    return RedirectResponse("/tickets", status_code=303)



@app.post("/invoice/{invoice_id}/status")
def update_invoice_status(
    invoice_id: int,
    request: Request,
    status: str = Form(...),
    payment_method: str = Form(""),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    invoice = session.scalars(select(Invoice).where(Invoice.id == invoice_id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    allowed = {"draft", "issued", "paid", "cancelled"}
    if status not in allowed:
        status = "draft"
    invoice.status = status
    if status == "paid":
        invoice.paid_at = datetime.utcnow()
        invoice.payment_method = payment_method or invoice.payment_method or "cash"
    elif status != "paid":
        invoice.paid_at = None
        if status != "issued":
            invoice.payment_method = payment_method or invoice.payment_method
    session.commit()
    return RedirectResponse("/invoices", status_code=303)


@app.post("/quote/{quote_id}/status")
def update_quote_status(
    quote_id: int,
    request: Request,
    status: str = Form(...),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    quote = session.scalars(select(Quote).where(Quote.id == quote_id)).first()
    if not quote:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    allowed = {"draft", "sent", "accepted", "cancelled"}
    if status not in allowed:
        status = "draft"
    quote.status = status
    session.commit()
    return RedirectResponse("/quotes", status_code=303)


@app.post("/delete/ticket/{ticket_id}")
def delete_ticket(ticket_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_admin_or_redirect
    user, redirect = get_admin_or_redirect(request, session)
    if redirect:
        return redirect
    ticket = session.scalars(select(Ticket).where(Ticket.id == ticket_id)).first()
    if ticket:
        session.delete(ticket)
        session.commit()
    return RedirectResponse("/tickets", status_code=303)


@app.get("/export/interventions.xlsx")
def export_interventions_excel(request: Request, session: Session = Depends(get_session)):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    interventions = session.scalars(select(Intervention).order_by(Intervention.created_at.desc())).all()
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Interventions"
    ws.append(["ID", "Date", "Client", "Machine", "Titre", "Score", "Risque disque", "Offline", "Risque donnees", "Statut"])
    for item in interventions:
        ws.append([
            item.id,
            item.created_at.strftime("%Y-%m-%d %H:%M"),
            item.client.name if item.client else "",
            item.machine_name or "",
            item.title,
            item.health_score or "",
            item.disk_risk or "",
            item.offline_windows or "",
            item.data_loss_risk or "",
            item.status,
        ])
    
    from io import BytesIO
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=interventions.xlsx"},
    )



@app.get("/api/stats")
def api_stats(request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        raise HTTPException(status_code=401, detail="Non autorise")
    context = build_dashboard_context(request, session, user)
    return {"stats": context["stats"], "alerts": context["alerts"]}


@app.get("/tools", response_class=HTMLResponse)
def tools_page(request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    return templates.TemplateResponse(
        "tools.html",
        {"request": request, "user": user, "logo_path": get_logo_path()},
    )




@app.post("/intervention/{intervention_id}/status")
def update_intervention_status(
    intervention_id: int,
    request: Request,
    status: str = Form(...),
    session: Session = Depends(get_session),
):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    allowed = {"nouvelle", "en_attente", "en_cours", "termine", "livre", "facture"}
    intervention.status = status if status in allowed else "nouvelle"
    session.commit()
    return RedirectResponse(f"/intervention/{intervention_id}", status_code=303)


@app.get("/intervention/{intervention_id}/label", response_class=HTMLResponse)
def intervention_label(intervention_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    client = intervention.client
    machine = intervention.machine
    html = f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Étiquette intervention</title>
<style>
body{{font-family:Segoe UI,Arial,sans-serif;background:white;margin:20px}}
.label{{width:95mm;border:2px solid #111827;border-radius:8px;padding:12px}}
h1{{font-size:18px;margin:0 0 8px;color:#0f766e}} .id{{font-size:22px;font-weight:800}} p{{margin:4px 0}}
.qr{{width:90px;height:90px;border:1px dashed #94a3b8;display:flex;align-items:center;justify-content:center;font-size:11px;color:#64748b}}
@media print{{button{{display:none}} body{{margin:0}}}}
</style></head><body><button onclick="print()">Imprimer</button><div class="label">
<h1>Restor-PC RescueGrid</h1><div class="id">INT-{intervention.id:06d}</div>
<p><strong>Client :</strong> {(client.name if client else "")}</p>
<p><strong>Machine :</strong> {intervention.machine_name or (machine.machine_name if machine else "")}</p>
<p><strong>BIOS :</strong> {intervention.bios_serial or ""}</p>
<p><strong>Statut :</strong> {intervention.status}</p>
<p><strong>Date :</strong> {intervention.created_at.strftime("%d/%m/%Y %H:%M")}</p>
<div class="qr">QR / INT-{intervention.id:06d}</div>
</div></body></html>"""
    return HTMLResponse(html)


@app.get("/invoice/{invoice_id}/pdf", response_class=HTMLResponse)
def invoice_pdf(invoice_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_current_user
    user = get_current_user(request, session)
    if not user:
        return RedirectResponse("/login", status_code=303)
    invoice = session.scalars(select(Invoice).where(Invoice.id == invoice_id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return try_pdf_response(invoice_html(invoice), f"{invoice.invoice_number}.pdf")


@app.get("/backup/database")
def backup_database(request: Request):
    from .auth import get_current_user
    with SessionLocal() as session:
        user = get_current_user(request, session)
        if not user:
            raise HTTPException(status_code=401, detail="Non autorise")
    db_path = BASE_DIR / "rescuegrid.db"
    if not db_path.exists():
        db_path = BASE_DIR / "app.db"
    if not db_path.exists():
        raise HTTPException(status_code=404, detail="Base SQLite introuvable")
    def iterfile():
        with open(db_path, "rb") as f:
            yield from f
    return StreamingResponse(iterfile(), media_type="application/octet-stream", headers={"Content-Disposition": "attachment; filename=rescuegrid_backup.db"})


@app.get("/health")
def healthcheck():
    return {"status": "ok"}


@app.get("/storage/{file_path:path}")
def serve_storage_file(file_path: str, request: Request, session: Session = Depends(get_session)):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    target = resolve_storage_path(file_path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Fichier introuvable")
    return FileResponse(target)


@app.get("/intervention/{intervention_id}/download/zip")
def download_intervention_zip(intervention_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention or not intervention.archive_path:
        raise HTTPException(status_code=404, detail="Archive ZIP introuvable")
    target = resolve_storage_path(intervention.archive_path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Archive ZIP introuvable")
    return FileResponse(target, filename=target.name, media_type="application/zip")


@app.get("/intervention/{intervention_id}/download/report")
def download_intervention_report(intervention_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention or not intervention.report_path:
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    target = resolve_storage_path(intervention.report_path)
    if not target.is_file():
        raise HTTPException(status_code=404, detail="Rapport introuvable")
    return FileResponse(target, filename=target.name, media_type="text/html")


@app.get("/intervention/{intervention_id}/download/manifest")
def download_intervention_manifest(intervention_id: int, request: Request, session: Session = Depends(get_session)):
    from .auth import get_user_or_redirect
    user, redirect = get_user_or_redirect(request, session)
    if redirect:
        return redirect
    intervention = session.scalars(select(Intervention).where(Intervention.id == intervention_id)).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    folder = intervention_dir(intervention)
    if not folder:
        raise HTTPException(status_code=404, detail="Dossier intervention introuvable")
    target = (folder / "evidence_manifest.json").resolve()
    if not str(target).startswith(str(STORAGE_DIR.resolve())) or not target.is_file():
        raise HTTPException(status_code=404, detail="Manifeste introuvable")
    return FileResponse(target, filename="evidence_manifest.json", media_type="application/json")