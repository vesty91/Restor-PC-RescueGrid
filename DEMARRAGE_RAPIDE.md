# Restor-PC RescueGrid — Démarrage rapide

## 🚀 Lancer le Dashboard (Backend)

### Méthode 1 : Script automatique (recommandé)
```batch
start_dashboard.bat
```

### Méthode 2 : Manuel
```batch
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Accès
- **URL** : http://localhost:8000
- **Login** : `admin`
- **Mot de passe** : `rescuegrid2026`

---

## 🖥️ Lancer l'Agent Windows

### Méthode 1 : Script automatique
```batch
start_agent.bat
```

### Méthode 2 : Menu technicien interactif
```batch
start_agent_windows.bat
```

### Méthode 3 : Ligne de commande PowerShell
```powershell
# Diagnostic simple
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -CreateZip

# Avec sauvegarde profil
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "E:\RestorPC" -UserProfilePath "C:\Users\Dupont" -BackupEssentialFoldersOnly -CreateZip

# Analyse Windows mort (WinPE)
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Dupont" -BackupRoot "X:\Interventions" -OfflineWindowsPath "D:\Windows" -CreateZip
```

---

## 🔧 WinPE Atelier

```batch
start_winpe_menu.bat
```

Menu 9 options :
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

## 🏗️ Build USB automatique

```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Build-RescueGridUSB.ps1 -UsbDriveLetter "E" -IncludeDataRecovery
```

Options :
- `-UsbDriveLetter "E"` : lettre du lecteur USB (obligatoire)
- `-IncludeDataRecovery` : inclure ddrescue, TestDisk, PhotoRec
- `-SkipFormat` : ne pas formater la clé

---

## 🌐 PXE Rescue Server (boot réseau)

```powershell
powershell -ExecutionPolicy Bypass -File agent\windows\Setup-PXERescueServer.ps1 -NetworkInterface "Ethernet" -InstallTFTP -InstallHTTP
```

Options :
- `-NetworkInterface "Ethernet"` : interface réseau (obligatoire)
- `-InstallTFTP` : installer serveur TFTP
- `-InstallHTTP` : installer IIS
- `-WinPEWim "C:\chemin\boot.wim"` : WinPE personnalisé

---

## 🐳 Docker / Synology

### Développement
```batch
docker-compose up --build
```

### Production (Synology)
```bash
docker-compose -f docker-compose.synology.yml up -d
```

Services :
- Backend : http://localhost:8000
- MinIO : http://localhost:9000
- pgAdmin : http://localhost:5050

---

## 📋 Vérification rapide v5.0

### 1. Tester le dashboard
```batch
start_dashboard.bat
```
→ Ouvrir http://localhost:8000
→ Login: admin / rescuegrid2026

### 2. Vérifier les 6 onglets
- ✅ Interventions
- ✅ Clients
- ✅ Machines
- ✅ Pièces
- ✅ **Factures** (nouveau v5.0)
- ✅ **Tickets** (nouveau v5.0)

### 3. Tester la facturation
- Aller sur http://localhost:8000/invoices
- Créer une facture avec une intervention
- Vérifier la numérotation automatique (INV-YYYYMMDD-XXXX)
- Tester les statuts : draft, sent, paid, cancelled

### 4. Tester les tickets
- Aller sur http://localhost:8000/tickets
- Créer un ticket avec priorité et statut
- Vérifier l'association avec une intervention

### 5. Tester la recherche
- Saisir un nom dans la barre "Recherche globale"
- Vérifier que les résultats s'affichent dans tous les onglets

### 6. Tester le dark mode
- Cliquer sur "🌓 Dark mode" dans le header
- Vérifier que le thème change
- Rafraîchir la page : le thème doit être conservé

### 7. Tester l'export Excel
- Aller sur http://localhost:8000/export/interventions.xlsx
- Vérifier que le fichier se télécharge

### 8. Tester l'upload logo
- Dashboard > Formulaire "Logo personnalisable"
- Uploader une image PNG/JPG
- Vérifier que le logo apparaît dans le header

### 9. Tester l'agent v5.0
```powershell
# Export CSV/JSON
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Test" -BackupRoot "E:\RestorPC" -ExportCSV -ExportJSON -CreateZip

# Mode silencieux
powershell -ExecutionPolicy Bypass -File agent\windows\Invoke-RescueGrid.ps1 -ClientName "Test" -BackupRoot "E:\RestorPC" -SilentMode -SkipConsent -CreateZip
```

---

## 🆘 Dépannage rapide

| Problème | Solution |
|----------|----------|
| Port 8000 occupé | Modifier `DASHBOARD_PORT=8001` dans `.env` |
| Python introuvable | Installer Python 3.12+ avec "Add to PATH" |
| PowerShell bloqué | `Set-ExecutionPolicy RemoteSigned` (admin) |
| Base verrouillée | Supprimer `backend/rescuegrid.db` |
| Module manquant | `pip install -r backend\requirements.txt` |
| wkhtmltopdf absent | Télécharger sur https://wkhtmltopdf.org/ |

---

## 📚 Documentation complète

- [README.md](README.md) — Vue d'ensemble
- [README_LANCEMENT.md](README_LANCEMENT.md) — Guide complet
- [README_DEPLOIEMENT.md](README_DEPLOIEMENT.md) — Docker, NAS
- [CHANGELOG.md](CHANGELOG.md) — Historique versions
- [RELEASE_NOTES_v3.1.0.md](RELEASE_NOTES_v3.1.0.md) — Détails v3.1
- [RELEASE_NOTES_v4.0.0.md](RELEASE_NOTES_v4.0.0.md) — Détails v4.0
- [docs/TECHNICIAN_MANUAL.md](docs/TECHNICIAN_MANUAL.md) — Manuel technicien
- [docs/CLIENT_GUIDE.md](docs/CLIENT_GUIDE.md) — Guide client

---

## 🎯 Cas d'usage

1. **Diagnostic atelier** : `start_winpe_menu.bat` → Diagnostic → Rapport HTML
2. **Sauvegarde avant réinstallation** : Agent avec `-UserProfilePath`
3. **Récupération disque critique** : ddrescue automatique si disque critical
4. **Gestion clients** : Dashboard avec historique machines
5. **Inventaire pièces** : Onglet "Pièces" + CRUD
6. **Boot réseau** : `Setup-PXERescueServer.ps1` pour PXE

---

**Bon diagnostic ! 🚀**