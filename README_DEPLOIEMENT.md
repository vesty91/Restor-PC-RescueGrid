# Restor-PC RescueGrid — Guide de déploiement v4.0.0

## Installation rapide

### 1. Prérequis
- **Windows 10/11** ou **Windows PE** (pour l'agent)
- **Python 3.12+** (pour le dashboard)
- **PowerShell 5.1+** (intégré à Windows)
- **Git** (optionnel, pour le versioning)

### 2. Installation automatique
```powershell
powershell -ExecutionPolicy Bypass -File install_dependencies.ps1
```

### 3. Installation manuelle
```batch
# Dashboard
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Dossiers de stockage
mkdir storage storage\uploads storage\reports
```

---

## Commandes de lancement

| Commande | Description |
|----------|-------------|
| `start_dashboard.bat` | Dashboard web (http://localhost:8000) |
| `start_agent.bat` | Agent rapide avec paramètres en ligne |
| `start_agent_windows.bat` | Menu technicien interactif (8 options) |
| `start_winpe_menu.bat` | Menu WinPE Atelier (9 options) |
| `Build-RescueGridUSB.ps1` | Créer une clé USB bootable |

**Login dashboard** : `admin` / `rescuegrid2026`

---

## Structure des fichiers

```
restor_pc_rescuegrid/
│
├── start_dashboard.bat          ← Lancer le dashboard
├── start_agent.bat              ← Lancer l'agent rapide
├── start_agent_windows.bat      ← Menu technicien interactif
├── start_winpe_menu.bat         ← Menu WinPE Atelier
├── install_dependencies.ps1     ← Installation automatique
├── .env.example                 ← Configuration
├── README_LANCEMENT.md          ← Guide utilisateur complet
├── README_DEPLOIEMENT.md        ← Ce fichier
├── CHANGELOG.md                 ← Historique des versions
├── RELEASE_NOTES_v4.0.0.md      ← Notes de version v4.0.0
│
├── agent/
│   └── windows/
│       ├── Invoke-RescueGrid.ps1   ← Agent v4 (ddrescue, PDF, recovery)
│       ├── Start-RescueGrid.ps1    ← WinPE Atelier (9 options)
│       └── Build-RescueGridUSB.ps1 ← Build USB automatique
│
├── backend/
│   ├── app/
│   │   ├── main.py              ← API FastAPI (auth, parts, machines)
│   │   ├── models.py            ← Client, Machine, User, Part, Intervention
│   │   ├── database.py          ← SQLite + migrations auto
│   │   ├── auth.py              ← JWT + RBAC
│   │   └── __init__.py
│   ├── templates/
│   │   ├── dashboard.html       ← Dashboard 4 onglets
│   │   ├── client_detail.html   ← Détail client
│   │   ├── machine_detail.html  ← Historique machine
│   │   ├── parts.html           ← Inventaire atelier
│   │   └── login.html           ← Page connexion
│   ├── requirements.txt
│   └── Dockerfile
│
├── storage/
│   ├── uploads/                 ← Archives ZIP importées
│   └── reports/                 ← Rapports extraits
│
└── docs/
    ├── ARCHITECTURE.md
    ├── ROADMAP.md
    ├── TECHNICIAN_RUNBOOK.md
    ├── TECHNICIAN_MANUAL.md     ← Manuel technicien v4.0
    └── CLIENT_GUIDE.md          ← Guide client
```

---

## Docker

### Développement
```batch
docker-compose up --build
```

### Production (Synology)
```bash
docker-compose -f docker-compose.synology.yml up -d
```

Services : PostgreSQL + MinIO + Nginx + Backend + pgAdmin

Ou manuellement :
```batch
docker build -t restorpc-rescuegrid ./backend
docker run -p 8000:8000 -v %cd%/storage:/app/storage restorpc-rescuegrid
```

---

## Configuration

Copier `.env.example` vers `.env` et ajuster si nécessaire :

```env
# Base de données
DATABASE_URL="sqlite:///./rescuegrid.db"
# Pour PostgreSQL : DATABASE_URL="postgresql://user:password@localhost:5432/rescuegrid"

# Dashboard
DASHBOARD_PORT=8000
DASHBOARD_HOST=0.0.0.0

# Agent
BACKUP_ROOT="E:\RestorPC"
# DASHBOARD_UPLOAD_URL="http://localhost:8000/upload"

# Sécurité
SECRET_KEY="change-me-in-production-2026"
ADMIN_PASSWORD="rescuegrid2026"

# Stockage
STORAGE_PATH="./storage"
```

---

## Tests de validation

Après installation, exécuter ces vérifications :

```batch
# 1. Lancer le dashboard
start_dashboard.bat
→ Ouvrir http://localhost:8000
→ Login: admin / rescuegrid2026

# 2. Tester l'agent (diagnostic simple, sans consentement)
powershell -ExecutionPolicy Bypass -File "agent\windows\Invoke-RescueGrid.ps1" -ClientName "Test" -BackupRoot "E:\RestorPC" -SkipConsent -CreateZip
→ Vérifier que le dossier Intervention_... est créé

# 3. Importer le ZIP dans le dashboard
→ Dashboard > Importer ZIP > client "Test" + fichier .zip

# 4. Vérifier le client
→ Onglet Clients > cliquer sur "Test"
→ Vérifier les interventions listées

# 5. Vérifier la machine
→ Onglet Machines > cliquer sur la machine
→ Vérifier l'historique

# 6. Vérifier le rapport
→ Cliquer "ouvrir" sur le rapport HTML
→ Vérifier scores, jauges, photos, signature

# 7. Vérifier evidence_manifest.json
→ Ouvrir le dossier intervention
→ Vérifier que evidence_manifest.json contient tous les SHA256

# 8. Tester upload automatique
powershell -ExecutionPolicy Bypass -File "agent\windows\Invoke-RescueGrid.ps1" -ClientName "Test" -BackupRoot "E:\RestorPC" -SkipConsent -DashboardUploadUrl "http://localhost:8000/upload"
→ Vérifier que l'intervention apparaît dans le dashboard

# 9. Tester inventaire pièces
→ Dashboard > Pièces > Ajouter SSD 1To Samsung
→ Vérifier dans l'onglet Pièces

# 10. Tester build USB
powershell -ExecutionPolicy Bypass -File "agent\windows\Build-RescueGridUSB.ps1" -UsbDriveLetter "E" -SkipFormat
→ Vérifier que la clé contient les scripts RescueGrid
```

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Python introuvable | Installer Python 3.12+, cocher "Add to PATH" |
| PowerShell bloqué | `Set-ExecutionPolicy RemoteSigned` (admin) |
| Port 8000 occupé | Modifier DASHBOARD_PORT dans .env |
| ZIP non importé | Vérifier que l'agent a bien créé le fichier .zip |
| Base verrouillée | Supprimer `backend/rescuegrid.db` et relancer |
| Machine non trouvée | Vérifier que le BIOS Serial est présent dans inventory.json |
| SMART limité | Installer smartctl sur la clé USB |
| WinPE sans agent | Copier le dossier `agent/windows/` sur la clé |
| Photos absentes | Vérifier le chemin `-PhotoBefore` / `-PhotoAfter` |
| PDF non généré | Installer wkhtmltopdf |
| ddrescue absent | Installer via WSL ou copier l'exe dans `RecoveryTools` |
| Authentification échouée | Vérifier SECRET_KEY dans .env, recréer la base si nécessaire |
