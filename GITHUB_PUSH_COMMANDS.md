# Push vers GitHub

Créer d'abord un dépôt vide sur GitHub, puis lancer :

```powershell
git init
git add .
git commit -m "Release v11.8 Stable"
git branch -M main
git remote add origin https://github.com/VOTRE_PSEUDO/restor-pc-rescuegrid.git
git push -u origin main
```

Si GitHub demande un mot de passe, utilisez un Personal Access Token GitHub.

## Important

Avant `git add .`, vérifiez :

```powershell
git status
```

Ne jamais commiter `.env`, `backend/.env`, `storage/`, `*.db`, `Intervention_*`.
