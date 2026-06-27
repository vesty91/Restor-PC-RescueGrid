# Roadmap

## Phase 1 - Outil Windows portable

- Diagnostic PC.
- Inventaire materiel.
- SMART disque.
- Sauvegarde profil utilisateur.
- Rapport HTML.
- Export ZIP intervention.
- Upload manuel vers dashboard.

## Phase 2 - Recuperation intelligente

- Classification disque sain/suspect/critique.
- Copie securisee avec `robocopy`.
- Mode sauvegarde profil complet.
- Mode sauvegarde dossiers essentiels.
- Manifeste `backup_manifest.csv`.
- Hash SHA256 des preuves et rapports.
- Journal de sauvegarde lisible client.
- Extraction Documents, Bureau, Images, Telechargements.

Statut MVP : base implementee dans l'agent Windows portable.

## Phase 3 - WinPE

- Demarrage cle USB.
- Analyse Windows hors ligne.
- Copie ruches registre hors ligne.
- Export journaux `.evtx`.
- Detection dumps BSOD.
- Detection profils utilisateurs offline.
- Verification presence partition EFI.
- Detection BitLocker via `manage-bde -status`.
- Preparation reinstallation.

Statut MVP : collecte offline en lecture seule implementee dans l'agent Windows/WinPE.

## Phase 4 - Dashboard NAS

- Authentification.
- Fiches clients.
- Interventions.
- Rapports.
- Factures.
- Alertes SMART.
- Stockage NAS / MinIO.

## Phase 5 - Rescue Server PXE

- iPXE.
- WinPE reseau.
- Linux Rescue.
- Clonezilla.
- MemTest86.
- Menu atelier centralise.
