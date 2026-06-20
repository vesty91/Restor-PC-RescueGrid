it# Restor-PC RescueGrid — Guide de lancement

## Installation

### 1. Prérequis
- **Windows 10/11** ou **Windows PE** (pour l'agent)
- **Python 3.12+** (pour le dashboard)
- **PowerShell 5.1+** (intégré à Windows)

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

**Login dashboard** : `admin` / `rescuegrid2026`

---

## Utilisation de l'agent

### Diagnostic simple
```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -CreateZip
```

### Sauvegarde avant réinstallation
```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -UserProfilePath "C:\Users\Dupont" -BackupEssentialFoldersOnly -CreateZip
```

### Analyse Windows mort (WinPE)
```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "X:\Interventions" -OfflineWindowsPath "D:\Windows" -CreateZip
```

### Avec PDF + photos + signature
```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -GeneratePDF -PhotoBefore "C:\photos\avant.jpg" -PhotoAfter "C:\photos\apres.jpg" -SignatureFile "C:\signature.png" -CreateZip
```

### Avec récupération disque (ddrescue)
```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -CreateZip
# Si disque critical, l'agent proposera automatiquement ddrescue
```

### Upload automatique vers le dashboard
```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -DashboardUploadUrl "http://localhost:8000/upload" -CreateZip
```

---

## Dashboard Web

### Accès
1. Lancer `start_dashboard.bat`
2. Ouvrir http://localhost:8000
3. Login : `admin` / `rescuegrid2026`

### Fonctionnalités
- **Interventions** : liste chronologique avec scores, risque disque, lien rapport
- **Clients** : fiches clients avec historique
- **Machines** : historique par BIOS Serial
- **Pièces** : inventaire atelier (SSD, HDD, RAM, CPU, GPU)
- **Import ZIP** : importer les archives de l'agent

### Onglets
| Onglet | Contenu |
|--------|---------|
| Interventions | Liste des interventions avec scores, risque, statut |
| Clients | Fiches clients + historique interventions |
| Machines | Historique par machine (BIOS Serial) |
| Pièces | Inventaire stock atelier |

---

## WinPE Atelier

### Démarrage
```batch
start_winpe_menu.bat
```

### Menu 9 options
1. Diagnostic complet
2. Sauvegarde utilisateur
3. Analyse SMART disques
4. Réparation boot Windows
5. Export rapport seul
6. Réinstallation (préparation)
7. Analyse Windows hors ligne
8. Vérification intégrité système
9. Quitter

---

## Build USB automatique

```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Build-RescueGridUSB.ps1 -UsbDriveLetter "E" -IncludeDataRecovery
```

### Options
- `-UsbDriveLetter` : lettre du lecteur USB (obligatoire)
- `-IncludeDataRecovery` : inclure ddrescue, TestDisk, PhotoRec
- `-SkipFormat` : ne pas formater la clé

---

## PXE Rescue Server (boot réseau)

```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Setup-PXERescueServer.ps1 -NetworkInterface "Ethernet" -InstallTFTP -InstallHTTP
```

### Options
- `-NetworkInterface` : interface réseau (obligatoire)
- `-InstallTFTP` : installer serveur TFTP
- `-InstallHTTP` : installer IIS pour servir les fichiers
- `-WinPEWim` : chemin vers boot.wim personnalisé

### Avantages
- Plus besoin de clé USB
- Boot réseau sur tous les PC de l'atelier
- Menu PXE : WinPE RescueGrid, mode sans échec, boot local

### Options
- `-UsbDriveLetter` : lettre du lecteur USB (obligatoire)
- `-IncludeDataRecovery` : inclure ddrescue, TestDisk, PhotoRec
- `-SkipFormat` : ne pas formater la clé

### Contenu de la clé
```
X:\
├── boot.wim (WinPE)
├── RescueGrid\
│   ├── Invoke-RescueGrid.ps1
│   ├── Start-RescueGrid.ps1
│   └── Build-RescueGridUSB.ps1
├── smartctl\
├── RecoveryTools\ (si -IncludeDataRecovery)
├── Docs\
└── autorun.inf
```

---

## Déploiement production (Synology)

```bash
docker-compose -f docker-compose.synology.yml up -d
```

### Services
- **PostgreSQL** : base de données
- **MinIO** : stockage S3 (port 9000)
- **Nginx** : reverse proxy (ports 80/443)
- **Backend** : API FastAPI (port 8000)
- **pgAdmin** : administration DB (port 5050)

### Variables d'environnement
Copier `.env.example` vers `.env` et ajuster :
```env
POSTGRES_USER=rescuegrid
POSTGRES_PASSWORD=rescuegrid2026
SECRET_KEY=change-me-in-production-2026
ADMIN_PASSWORD=rescuegrid2026
```

---

## Fonctionnalités v5.0

### Facturation
- Page `/invoices` avec CRUD complet
- Numérotation automatique : INV-YYYYMMDD-XXXX
- Statuts : draft, sent, paid, cancelled
- Calcul automatique HT + TVA = TTC
- Gestion des échéances et paiements

### Tickets d'intervention
- Page `/tickets` avec CRUD complet
- Priorités : low, medium, high, critical
- Statuts : open, in_progress, resolved, closed
- Suivi temps passé (`time_spent_minutes`)
- Association automatique avec intervention/client

### Détection matérielle avancée
- Batterie : charge, statut, voltage
- Carte mère : fabricant, modèle, serial
- Slots RAM : capacité, vitesse, part number
- Réseau : adaptateurs, MAC, vitesse

### Support WSL
- ddrescue, TestDisk, PhotoRec via WSL
- Fallback automatique si outils natifs absents

### Export CSV/JSON
- `-ExportCSV` : génère inventory.csv
- `-ExportJSON` : confirme export JSON
- Mode silencieux : `-SilentMode` pour scripts automatisés

### Dashboard 6 onglets
- Interventions, Clients, Machines, Pièces, **Factures**, **Tickets**

---

## Fonctionnalités v3.1

### PDF automatique
- Le PDF est généré automatiquement par défaut (plus besoin de `-GeneratePDF`)
- Option `-NoPDF` pour désactiver si nécessaire
- Rapport signé avec horodatage

### Export Excel
- Route `/export/interventions.xlsx`
- Export complet : ID, Date, Client, Machine, Titre, Score, Risque disque, Offline, Risque données, Statut
- Compatible Excel/LibreOffice

### Recherche globale
- Barre de recherche dans le dashboard
- Recherche dans : Clients, Machines, Interventions, Pièces
- Filtres ILIKE sur tous les champs pertinents

### Dark mode
- Toggle dans le header du dashboard
- Sauvegarde préférence dans localStorage
- Thèmes light/dark avec variables CSS

### Logo personnalisable
- Upload logo via formulaire dashboard
- Stockage dans `storage/logos/logo.png`
- Affichage dans le header avec `logo_config.json`

---

## Dépannage

| Problème | Solution |
|----------|----------|
| Python introuvable | Installer Python 3.12+, cocher "Add to PATH" |
| PowerShell bloqué | `Set-ExecutionPolicy RemoteSigned` (admin) |
| Port 8000 occupé | Modifier dans `start_dashboard.bat` ou `.env` |
| Base verrouillée | Supprimer `backend/rescuegrid.db` |
| Machine non trouvée | Vérifier BIOS Serial dans `inventory.json` |
| SMART limité | Installer smartctl sur la clé USB |
| WinPE sans agent | Copier le dossier `agent/windows/` sur la clé |
| Photos absentes | Vérifier le chemin `-PhotoBefore` / `-PhotoAfter` |
| PDF non généré | Installer wkhtmltopdf |
| ddrescue absent | Installer via WSL ou copier l'exe dans `RecoveryTools` |

---

## Structure des fichiers d'intervention

```
Intervention_2026-06-16_Dupont/
├── rapport.html              ← Rapport HTML (scores, jauges, photos)
├── inventory.json            ← Inventaire complet
├── blackbox.json             ← BlackBox juridique
├── evidence_manifest.json    ← Manifeste cryptographique SHA256
├── hashes.sha256.txt         ← Empreintes SHA256
├── actions_log.txt           ← Journal horodaté
├── backup_log.txt            ← Journal robocopy
├── backup_manifest.csv       ← Manifeste fichiers récupérés
├── smart.txt                 ← Résumé SMART
├── smart_disk0.txt           ← SMART détaillé
├── crystal_disk0.txt         ← CrystalDiskInfo
├── eventlogs/                ← Journaux .evtx
├── registry_hives/           ← Ruches registre
├── bsod_dumps/               ← Dumps BSOD
├── preuves/                  ← Photos + signature
│   ├── photo_avant.jpg
│   ├── photo_apres.jpg
│   └── signature_client.png
├── backup_client/            ← Données sauvegardées
└── Intervention_2026-06-16_Dupont.zip ← Archive ZIP
```

---

## Références

| Document | Description |
|----------|-------------|
| [README.md](README.md) | Vue d'ensemble du projet |
| [Guide de déploiement](README_DEPLOIEMENT.md) | Docker, NAS, configuration |
| [Manuel technicien](docs/TECHNICIAN_MANUAL.md) | Workflow, commandes, dépannage |
| [Guide client](docs/CLIENT_GUIDE.md) | Explication pour les clients |
| [Architecture](docs/ARCHITECTURE.md) | Architecture technique |
| [Roadmap](docs/ROADMAP.md) | Feuille de route |
| [Changelog](CHANGELOG.md) | Historique des versions |
| [Release Notes v4.0.0](RELEASE_NOTES_v4.0.0.md) | Détails de la version actuelle |