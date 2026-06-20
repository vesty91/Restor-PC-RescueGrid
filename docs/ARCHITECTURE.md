# Architecture Restor-PC RescueGrid

## Vue d'ensemble

```txt
Cle USB technicien / WinPE
        -> Agent diagnostic local
        -> Dossier intervention + BlackBox
        -> Upload dashboard NAS
        -> Historique client / rapports / sauvegardes
```

## Composants

### Agent Windows portable

Role : executer le diagnostic sans installation lourde.

Fonctions MVP :

- inventaire machine ;
- disques, volumes et partitions ;
- etat BitLocker ;
- SMART via PowerShell et `smartctl` si disponible ;
- journaux systeme recents ;
- detection profils utilisateurs ;
- sauvegarde profil via `robocopy` ;
- sauvegarde dossiers essentiels avant reinstallation ;
- manifeste des fichiers recuperes ;
- classification disque sain/suspect/critique ;
- rapport HTML ;
- BlackBox JSON ;
- hashes SHA256 ;
- archive ZIP.

### Dashboard NAS

Role : centraliser clients, interventions et archives.

Stack MVP :

- FastAPI ;
- SQLModel ;
- SQLite en local, PostgreSQL via `DATABASE_URL` ;
- templates Jinja2 ;
- stockage fichier local compatible montage NAS.

### Future WinPE / Linux Rescue

WinPE lance l'agent PowerShell contre un Windows hors ligne avec `-OfflineWindowsPath`. Le MVP copie les artefacts utiles en lecture seule : ruches registre, journaux EVTX, dumps BSOD et liste des profils. Linux Rescue gere ensuite les disques instables avec `smartctl`, `ddrescue`, `ntfsfix --no-action`, Clonezilla et outils forensic.

## Regle de securite donnees

```txt
Disque sain    -> copie fichiers
Disque suspect -> image disque avant reparation
Disque mourant -> ddrescue avant toute action destructive
```

Le MVP ne lance pas `chkdsk /f`, formatage, suppression ou reparation destructive automatiquement.
