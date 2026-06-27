# Restor-PC RescueGrid

**Plateforme atelier pour diagnostic PC, rapports d’intervention, devis/factures et envoi client.**

Restor-PC RescueGrid est un outil pensé pour un réparateur informatique indépendant : diagnostic matériel/Windows, rapport forensic, dashboard atelier, gestion clients/machines, devis/factures premium et envoi email SMTP avec PDF en pièce jointe.

## Version

**v11.8 Stable – GitHub Edition**

## Fonctionnalités principales

- Dashboard atelier noir/bleu Restor-PC
- Import ZIP d’intervention RescueGrid
- Historique clients, machines et interventions
- Diagnostic SMART / stockage / Windows
- Rapport HTML d’intervention avec score santé
- Devis et factures premium au style Restor-PC
- TVA non applicable auto-entrepreneur, article 293 B du CGI
- Signature client et signature Restor-PC
- SMTP Infomaniak avec PDF joint automatiquement
- Gestion du taux horaire par défaut : 60 €/h
- Templates `.env.example` propres, sans mots de passe

## Démarrage rapide Windows

```powershell
powershell -ExecutionPolicy Bypass -File install_dependencies.ps1
.\start_dashboard.bat
```

Puis ouvrir :

```txt
http://localhost:8000
```

Identifiants par défaut :

```txt
admin / rescuegrid2026
```

Changez le mot de passe dans `.env` avant toute utilisation réelle.

## Configuration email Infomaniak

Copiez le fichier d’exemple :

```powershell
Copy-Item .env.example .env
Copy-Item .env.example backend\.env
```

Puis configurez les variables SMTP dans `.env` et `backend\.env` :

```env
MAIL_ENABLED=true
MAIL_PROVIDER=infomaniak
MAIL_SERVER=mail.infomaniak.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USE_SSL=false
MAIL_USERNAME=contact@restor-pc.fr
MAIL_PASSWORD=VOTRE_MOT_DE_PASSE_APPLICATION_INFOMANIAK
MAIL_DEFAULT_SENDER=contact@restor-pc.fr
MAIL_FROM_NAME=RESTOR-PC

SMTP_HOST=mail.infomaniak.com
SMTP_PORT=587
SMTP_USER=contact@restor-pc.fr
SMTP_PASSWORD=VOTRE_MOT_DE_PASSE_APPLICATION_INFOMANIAK
SMTP_SENDER=contact@restor-pc.fr
SMTP_TLS=true
SMTP_SSL=false
```

Utilisez un **mot de passe d’application Infomaniak**, pas un mot de passe partagé publiquement.

## Structure

```txt
restor-pc-rescuegrid-main/
├── agent/windows/          # Agent PowerShell, WinPE, USB/PXE
├── backend/app/            # FastAPI, routes, modèles, helpers
├── backend/templates/      # Dashboard, devis, factures, clients
├── backend/static/         # Logo, signature, CSS
├── docs/                   # Documentation
├── install_dependencies.ps1
├── start_dashboard.bat
├── start_agent.bat
└── .env.example
```

## Commandes utiles

### Lancer le dashboard

```powershell
.\start_dashboard.bat
```

### Lancer l’agent Windows

```powershell
.\start_agent.bat
```

### Menu technicien

```powershell
.\start_agent_windows.bat
```

### Menu WinPE

```powershell
.\start_winpe_menu.bat
```

## Préparer le dépôt GitHub

```powershell
git init
git add .
git commit -m "Release v11.8 Stable"
git branch -M main
git remote add origin https://github.com/VOTRE_PSEUDO/restor-pc-rescuegrid.git
git push -u origin main
```

## Sécurité

Ne commitez jamais :

- `.env`
- `backend/.env`
- bases SQLite
- dossiers `storage/`
- exports d’intervention
- mots de passe SMTP
- archives clients

La `.gitignore` incluse protège ces fichiers.

## Licence

Ce projet est fourni avec une licence propriétaire par défaut. Vous pouvez remplacer `LICENSE` par MIT, GPL ou une autre licence si vous souhaitez publier le projet en open source.
