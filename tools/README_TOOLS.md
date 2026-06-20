# Outils externes RescueGrid

RescueGrid peut fonctionner sans outils externes, mais les températures SMART avancées nécessitent généralement :

## smartmontools
- Exécutable attendu : `smartctl.exe`
- Chemins détectés automatiquement :
  - PATH Windows
  - `tools\smartmontools\bin\smartctl.exe`
  - `Program Files\smartmontools\bin\smartctl.exe`

## CrystalDiskInfo
- Exécutables attendus : `DiskInfo64.exe`, `DiskInfo32.exe`, `DiskInfo.exe`
- Chemins détectés automatiquement :
  - PATH Windows
  - `tools\CrystalDiskInfo\`
  - `Program Files\CrystalDiskInfo\`

## Installation automatique

Depuis la racine du projet :

```powershell
.\start_tools_install.bat
```

ou :

```powershell
powershell -ExecutionPolicy Bypass -File .\Install-RescueGridTools.ps1
```

Les binaires tiers ne sont pas inclus dans ce dépôt. L'installateur les installe via winget si disponible.
