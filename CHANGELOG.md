

## v10.0.0 — Business Edition

### Devis
- Modèle `Quote`, page `/quotes`, numérotation DEV-YYYYMMDD-####
- PDF (wkhtmltopdf si installé, sinon HTML imprimable)
- Conversion devis → facture en un clic

### Factures
- Paiements : statut payé, date, mode de paiement
- PDF amélioré

### Intervention détaillée (`/intervention/{id}`)
- Téléchargements Rapport / ZIP / Manifest
- Photos avant/pendant/après
- Signature client (canvas souris/tactile)
- Main d'œuvre (minutes + tarif)
- Pièces utilisées (déstockage auto)
- Analyse assistée heuristique (SMART, Windows, score)

### Atelier pro
- Multi-utilisateurs (`/users`) + journal (`/activity`)
- Paramètres : changement mot de passe (`/settings`)
- Filtres dashboard (statut, tri score/date)
- Export CSV interventions
- Auth bcrypt directe (fix warning passlib)

---

## v6.0.0 — Atelier/Synology + USB Builder

### Dashboard UX
- Header compact sticky.
- KPI atelier : clients, machines, interventions, disques critiques, tickets ouverts, CA du mois.
- Import ZIP RescueGrid promu comme workflow principal.
- Alertes visuelles disque/ticket.
- Tableaux plus lisibles avec badges de risque.
- Responsive mobile.
- Recherche globale enrichie.

### Backend
- Ajout `build_dashboard_context`.
- Ajout endpoint `/api/stats`.
- Ajout page `/tools`.
- Relations SQLAlchemy Client/Machine/Intervention corrigées pour les templates.

### USB RescueGrid
- Nouveau `agent/windows/Create-RescueGridUSB.ps1`.
- Nouveau `start_usb_builder.bat`.
- Génération structure clé USB, configuration dashboard, lanceur Windows et `startnet.cmd` WinPE.

### Documentation
- Ajout `README_V6_0.md`.

# Changelog — Restor-PC RescueGrid

## v5.0.0 (2026-06-17) — Version Business

### Nouvelles fonctionnalités

#### 💰 Facturation
- Modèle `Invoice` avec numérotation automatique
- Statuts : draft, sent, paid, cancelled
- Calcul automatique HT + TVA = TTC
- Gestion des échéances et paiements
- Page dédiée `/invoices` avec CRUD complet

#### 🎫 Tickets d'intervention
- Modèle `Ticket` avec priorités et statuts
- Suivi temps passé (time_spent_minutes)
- Priorités : low, medium, high, critical
- Statuts : open, in_progress, resolved, closed
- Page dédiée `/tickets` avec CRUD complet
- Association automatique avec intervention/client

#### 📊 Détection matérielle avancée
- Fonction `Get-AdvancedHardwareInfo` (v5.0)
- Batterie : charge, statut, voltage
- Carte mère : fabricant, modèle, serial
- Slots RAM : capacité, vitesse, part number
- Réseau : adaptateurs physiques, MAC, vitesse

#### 🌐 Support WSL pour outils Linux
- ddrescue via WSL si non disponible en natif
- TestDisk via WSL
- PhotoRec via WSL
- Fallback automatique vers WSL

#### 📤 Export CSV/JSON
- Paramètre `-ExportCSV` pour export CSV
- Paramètre `-ExportJSON` pour export JSON
- Fichiers : `inventory.csv`, `inventory.json`, `blackbox.json`

#### 🤖 Mode silencieux
- Paramètre `-SilentMode` pour scripts automatisés
- Pas d'interaction utilisateur
- Idéal pour déploiement en masse

#### 🖥️ Dashboard amélioré
- 6 onglets : Interventions, Clients, Machines, Pièces, Factures, Tickets
- Intégration factures et tickets dans le dashboard principal
- Templates responsive pour invoices et tickets

---

## v3.1.0 (2026-06-16) — Améliorations UX

### Nouvelles fonctionnalités

#### 📄 PDF Automatique
- Génération PDF automatique par défaut (sans flag `-GeneratePDF`)
- Option `-NoPDF` pour désactiver si nécessaire
- Rapport signé avec horodatage

#### 📊 Export Excel
- Route `/export/interventions.xlsx`
- Export complet : ID, Date, Client, Machine, Titre, Score, Risque disque, Offline, Risque données, Statut
- Compatible Excel/LibreOffice

#### 🔍 Recherche Globale
- Barre de recherche dans le dashboard
- Recherche dans : Clients, Machines, Interventions, Pièces
- Filtres ILIKE sur tous les champs pertinents

#### 🌓 Dark Mode
- Toggle dans le header du dashboard
- Sauvegarde préférence dans localStorage
- Thèmes light/dark avec variables CSS

#### 🖼️ Logo Personnalisable
- Upload logo via formulaire dashboard
- Stockage dans `storage/logos/logo.png`
- Affichage dans le header avec `logo_config.json`

---

## v3.0.0 (2026-06-16) — Version atelier

### Nouvelles fonctionnalités

#### 🖴 SMART Avancé (Niveau 1)
- Détection des températures disques avec seuils colorés dans le rapport HTML
- Attribution SMART via smartctl (Reallocated, Pending, Uncorrectable sectors)
- CrystalDiskInfo CLI automatique si présent
- Export smart.txt enrichi avec températures

#### 📊 Score Santé Détaillé (Niveau 2)
- 5 sous-scores pondérés : Disque (25), RAM (10), Windows (30), Drivers (20), Températures (15)
- Jauges CSS visuelles (vert/orange/rouge) dans le rapport HTML
- Risque perte données basé sur le score global

#### 🔒 BlackBox Juridique (Niveau 6)
- Photos avant/après intervention (`-PhotoBefore`, `-PhotoAfter`)
- Signature client numérique (`-SignatureFile`)
- Horodatage signé dans la BlackBox et le rapport HTML
- Consentement client horodaté

#### ⚠️ Risque Disque Automatique (Point 1)
- Seuils SMART : température > 60°C critique, reallocated > 10 critique
- Mode recommandé automatique : ddrescue, image disque, sauvegarde prioritaire
- Blocage automatique de la sauvegarde si disque suspect/critical

#### 🔐 Manifeste Cryptographique (Point 2)
- `evidence_manifest.json` avec SHA256 de tous les fichiers
- BIOS Serial, case_id, client_name, horodatage

#### 🖥️ Dashboard Pro (Point 3)
- Nouveau modèle `Machine` avec historique par BIOS Serial
- 3 onglets : Interventions, Clients, Machines
- Pages détail client et machine
- Suppression client/intervention
- Association automatique machine à l'import ZIP

#### 🏢 WinPE Atelier (Point 5)
- Nouveau script `Start-RescueGrid.ps1` avec menu 9 options
- Diagnostic, sauvegarde, SMART, boot repair, rapport, réinstallation, offline, system check
- Détection automatique des installations Windows
- Mode dégradé si l'agent est absent

#### 🚀 Packaging
- `start_agent.bat` : agent rapide avec paramètres
- `start_winpe_menu.bat` : lancement WinPE
- `install_dependencies.ps1` : installation automatique
- `.env.example` : configuration
- `README_DEPLOIEMENT.md` : guide de déploiement
- `CHANGELOG.md` : ce fichier

### Corrections
- Comparaison `health_status` (entier vs chaîne) dans `Get-DiskRiskAssessment`
- Upload dashboard fonctionne sans `-CreateZip`
- Vérification existence ZIP avant upload
- Gestion robuste de l'absence d'`inventory.json` dans le backend

---

## v2.0.0 (2026-06-16) — Version technicien

### Ajouts
- Scripts `start_dashboard.bat` et `start_agent_windows.bat`
- `README_LANCEMENT.md` complet
- Agent enrichi : BIOS, CPU, GPU, EventLog legacy
- Consentement client obligatoire
- Logs horodatés (`actions_log.txt`)
- Mode lecture seule si disque suspect/critical

---

## v4.1.0 (2026-06-16) — PXE Rescue Server

### Nouvelles fonctionnalités

#### 🌐 PXE Rescue Server
- Script `Setup-PXERescueServer.ps1` pour créer un serveur PXE complet
- DHCP + TFTP + HTTP (IIS ou Python)
- Menu de boot PXE personnalisé (WinPE RescueGrid, mode sans échec, boot local)
- Structure de dossiers automatique (Boot, Scripts, Tools, WinPE)
- Configuration IIS avec types MIME pour WIM/PS1
- Alternative serveur HTTP Python simple

---

## v4.0.0 (2026-06-16) — Version Récupération Pro

### Nouvelles fonctionnalités

#### 🖴 Récupération Disque (B1)
- Intégration ddrescue, TestDisk, PhotoRec dans l'agent
- Workflow automatique : disque sain → copie, suspect → image, critique → ddrescue
- Fonctions `Invoke-Ddrescue`, `Invoke-TestDisk`, `Invoke-PhotoRec`
- `Get-RecoveryWorkflow` : actions recommandées selon le risque
- Blocage automatique sauvegarde si disque critical

#### 🔐 Authentification Dashboard (B2)
- JWT + cookies HttpOnly (durée 8h)
- Rôles : admin, technicien
- RBAC : `require_auth`, `require_admin`
- Page login (`/login`) + logout
- Admin par défaut : `admin` / `rescuegrid2026`
- Journal last_login dans la base

#### 📄 PDF Natif (B3)
- Génération PDF via wkhtmltopdf (option `-GeneratePDF`)
- Rapport signé avec horodatage
- Fallback gracieux si wkhtmltopdf absent

#### 📦 Inventaire Atelier (B4)
- Modèle `Part` : SSD, HDD, RAM, CPU, GPU
- Page `/parts` + CRUD complet
- Suivi stock (quantité, numéro de série, capacité, date d'achat)
- Intégré dans le dashboard (onglet "Pièces")

#### 🏗️ Build USB Automatique (B5)
- Script `Build-RescueGridUSB.ps1`
- Formatage, copie scripts, WinPE, smartctl, outils récupération
- Documentation incluse sur la clé
- `autorun.inf` pour lancement automatique

#### 🏢 Synology Ready (B6)
- `docker-compose.synology.yml` : PostgreSQL + MinIO + Nginx + backend
- Healthchecks sur tous les services
- Volumes persistants
- pgAdmin inclus pour administration DB
- Variables d'environnement configurables

---

## v1.0.0 (2026-06-15) — MVP Initial

- Agent PowerShell portable (diagnostic, inventaire, SMART)
- Sauvegarde profil utilisateur (complet + dossiers essentiels)
- Mode Windows hors ligne / WinPE
- Rapport HTML professionnel
- BlackBox JSON + SHA256
- ZIP intervention
- Dashboard FastAPI (clients, interventions, import ZIP)
- Dockerisation
- Documentation complète

## v5.0.1 Hotfix

- Correction install_dependencies.ps1 : opérateur `-and` avec `Test-Path`.
- Sélection automatique Python 3.12/3.11.
- Correction start_dashboard.bat pour utiliser le venv et `python -m uvicorn`.


## v6.0.1 Hotfix

- Correction BlackBox vide.
- Correction sous-scores santé et division par zéro.
- Correction variables HTML vides.
- Correction récupération infos machine.
- Tableau températures SMART robuste.
- Validation automatique avant rapport.


## v8.6 Hotfix

- Scoring SMART/NTFS renforcé.
- Risque perte données cohérent avec NTFS ID55.
- Résumé exécutif enrichi avec état SMART.
- Jauges colorées selon le statut réel.
