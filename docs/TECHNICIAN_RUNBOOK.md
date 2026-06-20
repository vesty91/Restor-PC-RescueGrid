# Runbook Technicien

## Avant toute intervention

1. Identifier le client et la machine.
2. Brancher l'alimentation secteur.
3. Ne pas lancer de reparation disque avant diagnostic SMART.
4. Si le disque claque, disparait ou remonte des erreurs critiques, arreter les copies classiques et passer en image/ddrescue.

## Diagnostic Windows demarre

```powershell
powershell -ExecutionPolicy Bypass -File .\agent\windows\Invoke-RescueGrid.ps1 -ClientName "Client" -BackupRoot "E:\RestorPC" -CreateZip
```

## Sauvegarde profil

```powershell
powershell -ExecutionPolicy Bypass -File .\agent\windows\Invoke-RescueGrid.ps1 -ClientName "Client" -BackupRoot "E:\RestorPC" -UserProfilePath "C:\Users\Client" -CreateZip
```

## Sauvegarde avant reinstallation

Utiliser le mode dossiers essentiels pour limiter le volume et accelerer le transfert :

```powershell
powershell -ExecutionPolicy Bypass -File .\agent\windows\Invoke-RescueGrid.ps1 -ClientName "Client" -BackupRoot "E:\RestorPC" -UserProfilePath "C:\Users\Client" -BackupEssentialFoldersOnly -CreateZip
```

Dossiers inclus si presents : Bureau, Documents, Telechargements, Images, Videos, Musique, Favoris.

Le fichier `backup_manifest.csv` liste les fichiers copies avec taille et date de modification.

## Analyse Windows hors ligne WinPE

Depuis WinPE, identifier la lettre du Windows client avec `diskpart`, `Get-Volume` ou l'explorateur.

Exemple si Windows est monte en `D:\Windows` :

```powershell
powershell -ExecutionPolicy Bypass -File .\agent\windows\Invoke-RescueGrid.ps1 -ClientName "Client" -BackupRoot "E:\RestorPC" -OfflineWindowsPath "D:\Windows" -CreateZip
```

Artefacts copies en lecture seule :

- ruches `SYSTEM`, `SOFTWARE`, `SAM`, `SECURITY`, `DEFAULT` ;
- journaux `System.evtx`, `Application.evtx`, `Setup.evtx`, Windows Update si present ;
- dumps `MEMORY.DMP` et `Minidump` ;
- liste des profils sous `Users` ;
- etat BitLocker et partitions EFI visibles depuis l'environnement.

## Interpretation rapide score

- Vert : OK.
- Orange : a surveiller.
- Rouge : intervention recommandee.
- Noir : risque critique donnees.

## A ne pas faire automatiquement

- Pas de `chkdsk /f` sur disque suspect.
- Si le rapport indique `critical`, prioriser image disque/ddrescue avant toute nouvelle copie.
- Pas de reinitialisation Windows avant sauvegarde.
- Pas de suppression source pendant recuperation.
- Pas de collecte de donnees hors besoin intervention.
- Ne pas charger/modifier les ruches registre client depuis le MVP offline.
