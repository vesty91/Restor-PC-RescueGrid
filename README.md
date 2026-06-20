# Restor-PC RescueGrid v6.0

Voir `README_V6_0.md` pour les nouveautés USB Builder et dashboard atelier.

# Restor-PC RescueGrid

> Plateforme technicien pour diagnostic, sauvegarde, récupération professionnelle et rapport d'intervention.



## ✅ v5.0.0 Stable Atelier

La distribution v5 nettoie le projet et durcit le déploiement :

- archive publique sans `.git`, `.venv`, caches ni stockage local ;
- upload ZIP sécurisé contre ZipSlip et archives trop volumineuses ;
- limites configurables via `.env` ;
- Dockerfile corrigé avec healthcheck ;
- PostgreSQL/Synology prêt via `psycopg[binary]` ;
- guide `README_V5_STABLE.md`.


## 🚀 Démarrage rapide

```batch
start_dashboard.bat      ← Dashboard web (http://localhost:8000)
start_agent.bat          ← Agent rapide
start_agent_windows.bat  ← Menu technicien (8 options)
start_winpe_menu.bat     ← WinPE Atelier (9 options)
```

**Login dashboard** : `admin` / `rescuegrid2026`

## 📦 Contenu v5.0.0

### Agent PowerShell
- Diagnostic complet (BIOS, CPU, RAM, GPU, disques, SMART)
- Sauvegarde profil utilisateur (complet / dossiers essentiels)
- Récupération disque : ddrescue, TestDisk, PhotoRec (avec support WSL)
- Mode Windows hors ligne / WinPE
- **Détection matérielle avancée** : batterie, carte mère, slots RAM, réseau
- **Export CSV/JSON** : `-ExportCSV`, `-ExportJSON`
- **Mode silencieux** : `-SilentMode` pour scripts automatisés
- PDF automatique, photos, signature client
- BlackBox juridique + manifeste cryptographique SHA256
- Upload automatique vers le dashboard

### Dashboard Web (FastAPI + PostgreSQL)
- Authentification JWT + RBAC
- Clients, Machines, Interventions, Pièces
- **Facturation** : devis, factures PDF, paiements (nouveau v5.0)
- **Tickets d'intervention** : suivi temps, statuts, commentaires (nouveau v5.0)
- Import ZIP agent + extraction automatique
- Export Excel des interventions
- Recherche globale dans tout le dashboard
- Dark mode toggle + persistance
- Logo personnalisable
- Historique machine par BIOS Serial
- **6 onglets** : Interventions, Clients, Machines, Pièces, Factures, Tickets

### WinPE Atelier
- Menu 9 options : diagnostic, sauvegarde, SMART, boot repair, offline, etc.
- Build USB automatique : `Build-RescueGridUSB.ps1`

### PXE Rescue Server (v4.1)
- Boot réseau : plus besoin de clé USB
- DHCP + TFTP + HTTP automatisés
- Menu PXE : WinPE RescueGrid, mode sans échec, boot local
- Script `Setup-PXERescueServer.ps1`

### Déploiement Production
- Synology Ready : `docker-compose.synology.yml`
- PostgreSQL + MinIO + Nginx + pgAdmin

### Agent PowerShell
- Diagnostic complet (BIOS, CPU, RAM, GPU, disques, SMART)
- Sauvegarde profil utilisateur (complet / dossiers essentiels)
- Récupération disque : ddrescue, TestDisk, PhotoRec
- Mode Windows hors ligne / WinPE
- **PDF automatique** : rapport signé généré par défaut (v3.1)
- Photos avant/après + signature client
- BlackBox juridique + manifeste cryptographique SHA256
- Upload automatique vers le dashboard

### Dashboard Web (FastAPI + PostgreSQL)
- Authentification JWT + RBAC
- Clients, Machines, Interventions, Pièces
- Inventaire atelier : SSD, HDD, RAM, CPU, GPU
- Import ZIP agent + extraction automatique
- **Export Excel** des interventions (v3.1)
- **Recherche globale** dans tout le dashboard (v3.1)
- **Dark mode** toggle (v3.1)
- **Logo personnalisable** (v3.1)
- Historique machine par BIOS Serial
- 4 onglets : Interventions, Clients, Machines, Pièces

### WinPE Atelier
- Menu 9 options : diagnostic, sauvegarde, SMART, boot repair, offline, etc.
- Build USB automatique : `Build-RescueGridUSB.ps1`

### PXE Rescue Server (v4.1)
- Boot réseau : plus besoin de clé USB
- DHCP + TFTP + HTTP automatisés
- Menu PXE : WinPE RescueGrid, mode sans échec, boot local
- Script `Setup-PXERescueServer.ps1`

### Déploiement Production
- Synology Ready : `docker-compose.synology.yml`
- PostgreSQL + MinIO + Nginx + pgAdmin

### Agent PowerShell
- Diagnostic complet (BIOS, CPU, RAM, GPU, disques, SMART)
- Sauvegarde profil utilisateur (complet / dossiers essentiels)
- **Récupération disque** : ddrescue, TestDisk, PhotoRec (B1)
- Mode Windows hors ligne / WinPE
- **Génération PDF** : rapport signé (B3)
- Photos avant/après + signature client
- BlackBox juridique + manifeste cryptographique SHA256
- Upload automatique vers le dashboard

### Dashboard Web (FastAPI + PostgreSQL)
- Authentification JWT + RBAC (B2)
- Clients, Machines, Interventions, Pièces
- **Inventaire atelier** : SSD, HDD, RAM, CPU, GPU (B4)
- Import ZIP agent + extraction automatique
- Historique machine par BIOS Serial
- 4 onglets : Interventions, Clients, Machines, Pièces

### WinPE Atelier
- Menu 9 options : diagnostic, sauvegarde, SMART, boot repair, offline, etc.
- **Build USB automatique** : `Build-RescueGridUSB.ps1` (B5)

### Déploiement Production
- **Synology Ready** : `docker-compose.synology.yml` (B6)
- PostgreSQL + MinIO + Nginx + pgAdmin

### PXE Rescue Server (v4.1)
- **Boot réseau** : plus besoin de clé USB
- DHCP + TFTP + HTTP automatisés
- Menu PXE : WinPE RescueGrid, mode sans échec, boot local
- Script `Setup-PXERescueServer.ps1`

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [Guide de lancement](README_LANCEMENT.md) | Installation et commandes |
| [Guide de déploiement](README_DEPLOIEMENT.md) | Docker, NAS, configuration |
| [Manuel technicien](docs/TECHNICIAN_MANUAL.md) | Workflow, commandes, dépannage |
| [Guide client](docs/CLIENT_GUIDE.md) | Explication pour les clients |
| [Architecture](docs/ARCHITECTURE.md) | Architecture technique |
| [Roadmap](docs/ROADMAP.md) | Feuille de route |
| [Release Notes v3.0.0](RELEASE_NOTES_v3.0.0.md) | Détails version atelier |
| [Release Notes v4.0.0](RELEASE_NOTES_v4.0.0.md) | Détails version récupération pro |
| [Changelog](CHANGELOG.md) | Historique complet |

## 🎯 Cas d'usage

1. **Diagnostic atelier** : brancher la clé USB WinPE, lancer le menu, générer le rapport
2. **Sauvegarde avant réinstallation** : copie du profil utilisateur (mode essentiel ou complet)
3. **Récupération disque critique** : ddrescue + TestDisk + PhotoRec
4. **Gestion clients** : dashboard avec historique machines et interventions
5. **Inventaire pièces** : suivi stock SSD, RAM, HDD, CPU, GPU
6. **Déploiement NAS** : stack Docker complète sur Synology

## 🔧 Commandes essentielles

```powershell
# Diagnostic simple
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -CreateZip

# Sauvegarde avant réinstallation
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -UserProfilePath "C:\Users\Dupont" -BackupEssentialFoldersOnly -CreateZip

# Analyse Windows mort (WinPE)
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "X:\Interventions" -OfflineWindowsPath "D:\Windows" -CreateZip

# Avec PDF + photos + signature
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -GeneratePDF -PhotoBefore "C:\photos\avant.jpg" -PhotoAfter "C:\photos\apres.jpg" -SignatureFile "C:\signature.png" -CreateZip

# Build USB
powershell -ExecutionPolicy Bypass -File agent\windows\Build-RescueGridUSB.ps1 -UsbDriveLetter "E" -IncludeDataRecovery
```

## 📊 Structure du projet

```
restor_pc_rescuegrid/
├── start_dashboard.bat
├── start_agent.bat
├── start_agent_windows.bat
├── start_winpe_menu.bat
├── install_dependencies.ps1
├── .env.example
├── README.md
├── README_LANCEMENT.md
├── README_DEPLOIEMENT.md
├── CHANGELOG.md
├── RELEASE_NOTES_v3.0.0.md
├── RELEASE_NOTES_v4.0.0.md
├── docker-compose.yml
├── docker-compose.synology.yml
├── agent/windows/
│   ├── Invoke-RescueGrid.ps1
│   ├── Start-RescueGrid.ps1
│   └── Build-RescueGridUSB.ps1
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── database.py
│   │   ├── auth.py
│   │   └── __init__.py
│   ├── templates/
│   │   ├── dashboard.html
│   │   ├── client_detail.html
│   │   ├── machine_detail.html
│   │   ├── parts.html
│   │   └── login.html
│   ├── requirements.txt
│   └── Dockerfile
├── docs/
│   ├── ARCHITECTURE.md
│   ├── ROADMAP.md
│   ├── TECHNICIAN_RUNBOOK.md
│   ├── TECHNICIAN_MANUAL.md
│   └── CLIENT_GUIDE.md
└── storage/ (créé au lancement)
    ├── uploads/
    └── reports/
```

## 🏆 Statut

**v4.0.0** — Version Récupération Pro

- ✅ Agent PowerShell v4 (ddrescue, TestDisk, PhotoRec, PDF)
- ✅ Dashboard FastAPI avec auth JWT + RBAC
- ✅ WinPE Atelier + Build USB automatique
- ✅ Inventaire atelier (pièces détachées)
- ✅ Synology Ready (Docker Compose production)
- ✅ Documentation complète (manuel technicien + guide client)

**Prochaines étapes** : voir [docs/ROADMAP.md](docs/ROADMAP.md)