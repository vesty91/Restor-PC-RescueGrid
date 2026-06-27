# Guide Client — Restor-PC RescueGrid

## Votre PC entre de bonnes mains

Ce guide vous explique le déroulement d'une intervention de diagnostic et de sauvegarde réalisée par votre technicien avec l'outil Restor-PC RescueGrid.

---

## 1. Déroulement d'une intervention

### Étape 1 : Accueil et consentement
Avant toute intervention, le technicien vous lira les **4 garanties** suivantes :

1. ✅ **Aucune action destructive** n'est lancée automatiquement
2. ✅ **Aucune suppression** de vos fichiers source
3. ✅ **CHKDSK /F** (réparation disque) n'est pas exécuté sans votre accord
4. ✅ **Vos données sont collectées en lecture seule** — rien n'est modifié

Vous devrez donner votre consentement verbal ou écrit avant de continuer.

### Étape 2 : Diagnostic
Le technicien branche une clé USB contenant l'outil RescueGrid. Celui-ci analyse :

- **Votre PC** : nom, fabricant, modèle, version de Windows
- **Le BIOS** : version, numéro de série unique
- **Le processeur** : modèle, fréquence, nombre de cœurs
- **La mémoire RAM** : capacité totale
- **La carte graphique** : modèle, mémoire, pilote
- **Les disques** : état de santé, température, signes d'usure
- **BitLocker** : état du chiffrement des données

### Étape 3 : Évaluation du risque disque
Les disques sont classés automatiquement en 3 niveaux :

| Niveau | Signification | Action |
|--------|---------------|--------|
| 🟢 **Healthy** (sain) | Disque en bon état | Copie des fichiers possible |
| 🟡 **Suspect** (douteux) | Signes d'usure détectés | Image disque recommandée avant réparation |
| 🔴 **Critical** (critique) | Risque de perte imminente | Sauvegarde bloquée, priorité à la récupération d'image |

### Étape 4 : Sauvegarde (si nécessaire)
Si le disque est sain et que vous avez demandé une sauvegarde :

- **Mode complet** : tout votre profil utilisateur est copié
- **Mode essentiel** : seuls Bureau, Documents, Images, Téléchargements, Vidéos, Musique et Favoris sont copiés

La copie utilise `robocopy` qui préserve vos fichiers sans les modifier.

### Étape 5 : Rapport
Un rapport HTML complet est généré avec :

- **Score santé** global sur 100
- **Sous-scores** détaillés (Disque, RAM, Windows, Pilotes, Températures)
- **Décision de récupération** avec recommandation
- **Photos** avant/après si le technicien en a pris
- **Espace de signature** pour valider l'intervention

### Étape 6 : Signature et validation
Vous pouvez signer le rapport pour attester que vous avez pris connaissance des actions effectuées.

---

## 2. Ce qui est garanti

| Garantie | Détail |
|----------|--------|
| 🔒 **Lecture seule** | Aucun fichier n'est modifié ou supprimé |
| 📸 **Traçabilité** | Chaque action est horodatée et signée numériquement |
| 🔐 **SHA256** | Tous les fichiers de preuve sont hashés (empreinte numérique unique) |
| 🛡️ **Consentement** | Rien n'est fait sans votre accord |
| 📋 **Rapport complet** | Vous repartez avec un dossier complet de l'intervention |

---

## 3. Fichiers que vous recevez

Après l'intervention, le technicien peut vous remettre :

```
Intervention_2026-06-16_VotreNom/
├── rapport.html              ← Rapport complet (ouvrable dans un navigateur)
├── inventory.json            ← Inventaire technique de votre PC
├── blackbox.json             ← Journal d'intervention horodaté
├── evidence_manifest.json    ← Preuve cryptographique de tous les fichiers
├── backup_manifest.csv       ← Liste des fichiers sauvegardés
├── backup_client/            ← Vos données sauvegardées
└── preuves/                  ← Photos de l'intervention
```

---

## 4. Interpréter votre rapport

### Score santé
| Score | Interprétation |
|-------|---------------|
| 80-100 | ✅ Votre PC est en bonne santé |
| 55-79 | ⚠️ Une surveillance est recommandée |
| 35-54 | 🔴 Une intervention est nécessaire |
| 0-34 | 🚨 Risque critique de perte de données |

### Jaquettes de sous-scores
Le rapport affiche des barres colorées :
- **Vert** : OK
- **Orange** : À surveiller
- **Rouge** : Action requise

---

## 5. Questions fréquentes

**Q : Mes fichiers peuvent-ils être endommagés ?**
R : Non. L'outil travaille en lecture seule. Aucun fichier n'est modifié ou supprimé automatiquement.

**Q : Combien de temps dure une intervention ?**
R : Le diagnostic prend 2 à 5 minutes. La sauvegarde dépend de la quantité de données (de 5 minutes à plusieurs heures).

**Q : Puis-je assister à l'intervention ?**
R : Oui, le technicien peut vous montrer chaque étape.

**Q : Que faire du dossier d'intervention ?**
R : Conservez-le précieusement. Il contient la preuve de ce qui a été fait et les recommandations du technicien.

**Q : Mes données sont-elles conservées par le technicien ?**
R : Le technicien conserve une copie dans son dashboard atelier pour son historique. Vous pouvez demander leur suppression à tout moment.

**Q : Puis-je ouvrir le rapport chez moi ?**
R : Oui, le fichier `rapport.html` s'ouvre dans n'importe quel navigateur web (Chrome, Edge, Firefox).

---

## 6. Contact

Pour toute question après l'intervention, contactez votre technicien :

- **Atelier** : _________________________
- **Technicien** : ______________________
- **Date d'intervention** : ______________
- **Numéro d'intervention** : ____________

---

*Document généré par Restor-PC RescueGrid v3.0.0*