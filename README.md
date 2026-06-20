# Restor-PC RescueGrid v10 Business

> Plateforme technicien : diagnostic PC, suivi d'interventions, devis, factures et dossier atelier complet.

## Démarrage rapide

```batch
start_dashboard.bat      ← Dashboard (http://localhost:8000)
start_agent.bat          ← Agent rapide
run_tests.bat            ← 26 tests d'intégration
```

**Login par défaut** : `admin` / `rescuegrid2026` — changez via **Paramètres** ou `.env`

## Fonctionnalités v10

### Agent Windows
- Diagnostic, SMART, rapport HTML, BlackBox SHA256, ZIP
- Upload automatique vers dashboard (`-UploadApiKey` si configuré)

### Dashboard Business
| Module | Fonctionnalités |
|--------|-----------------|
| **Interventions** | Dossier détaillé, photos, signature, MO, pièces, analyse IA |
| **Devis** | CRUD, numérotation, PDF, conversion → facture |
| **Factures** | HT/TVA/TTC, PDF, marquer payé, mode paiement |
| **Tickets** | Priorités, statuts, temps passé |
| **Clients / Machines** | Historique complet par serial BIOS |
| **Pièces** | Stock atelier + liaison intervention |
| **Multi-users** | Admin + techniciens, journal d'activité |
| **Exports** | Excel, CSV, backup BDD |
| **Filtres** | Statut intervention, tri par score/date |

### Sécurité
- Auth JWT sur toutes les routes CRUD
- Suppressions réservées admin
- `UPLOAD_API_KEY` pour upload agent en production
- Changement mot de passe dans `/settings`

### Déploiement
- Local : SQLite + `start_dashboard.bat`
- NAS : `docker-compose.synology.yml` (PostgreSQL, Nginx, MinIO)

## Tests

```batch
run_tests.bat
```

26 tests : auth, upload ZIP, téléchargements, devis, paramètres, CSV.

## Configuration production

```env
SECRET_KEY="change-me"
ADMIN_PASSWORD="change-me"
UPLOAD_API_KEY="change-me-upload-key"
DATABASE_URL="postgresql://..."
```

## Documentation

| Document | Description |
|----------|-------------|
| [Démarrage rapide](DEMARRAGE_RAPIDE.md) | Installation |
| [Déploiement](README_DEPLOIEMENT.md) | Docker, NAS |
| [Architecture](docs/ARCHITECTURE.md) | Technique |
| [Changelog](CHANGELOG.md) | Historique |

## Statut

**v10 Business** — exploitable en atelier + facturation de base.

Prochaines évolutions : SaaS multi-atelier, MinIO intégré, IA cloud.
