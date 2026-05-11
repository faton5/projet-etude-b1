# Dataset de Culture de Tomates 🍅

## Description

Ce dataset synthétique contient **8000 lignes** de données réalistes pour la culture de tomates. Il est conçu pour entraîner un modèle de machine learning (XGBoost) qui prédit l'état du plant et donne des recommandations aux débutants.

## Colonnes du Dataset

| Colonne | Type | Description |
|---------|------|-------------|
| `date` | string | Date de l'observation (YYYY-MM-DD) |
| `jour_culture` | int | Nombre de jours depuis la plantation (1-150) |
| `temperature_air_c` | float | Température de l'air en °C (8-38°C) |
| `temperature_sol_c` | float | Température du sol en °C (10-32°C) |
| `humidite_air_pourcent` | float | Humidité de l'air en % (30-95%) |
| `humidite_sol_pourcent` | float | Humidité du sol en % (20-90%) |
| `ph_sol` | float | pH du sol (5.0-8.0, optimal 6.0-7.0) |
| `lumiere_heures_jour` | float | Heures d'ensoleillement par jour (4-15h) |
| `pluie_mm_24h` | float | Précipitations sur 24h en mm (0-50mm) |
| `arrosage_litres_jour` | float | Quantité d'eau d'arrosage en litres (0-5L) |
| `stade_croissance` | string | Stade de développement du plant |
| `hauteur_plant_cm` | float | Hauteur du plant en cm |
| `nb_fleurs` | int | Nombre de fleurs sur le plant |
| `nb_fruits` | int | Nombre de fruits sur le plant |
| `couleur_feuilles` | string | Couleur des feuilles (vert, jaune, foncé, tacheté) |
| `etat_general` | string | État général du plant |
| `recommandation` | string | **Variable cible** : recommandation pour l'action à prendre |

## Stades de Croissance

Les stades progressent naturellement avec le temps :

- **semis** (jour 1-15) : germination et premières feuilles
- **jeune_plant** (jour 15-30) : développement végétatif initial
- **croissance** (jour 30-60) : croissance rapide de la tige et des feuilles
- **floraison** (jour 60-80) : apparition des fleurs
- **fructification** (jour 80-120) : formation et grossissement des fruits
- **recolte** (jour 120-150) : fruits mûrs prêts à être récoltés

## Classes de Recommandation (Variable Cible)

| Recommandation | Description | Fréquence |
|----------------|-------------|-----------|
| `bon` | Conditions optimales, rien à faire | ~56% |
| `recolte_bientot` | Plant prêt pour la récolte | ~12% |
| `arroser` | Sol trop sec, nécessite arrosage | ~8% |
| `trop_eau` | Excès d'eau (pluie ou arrosage) | ~8% |
| `risque_froid` | Température trop basse | ~5% |
| `sol_pas_adapte` | pH du sol inadapté | ~5% |
| `manque_lumiere` | Ensoleillement insuffisant | ~3% |
| `risque_chaleur` | Température trop élevée | ~2% |

## Règles de Génération

### 1. Règles de Cohérence Temporelle

- La hauteur du plant augmente progressivement avec `jour_culture`
- Les fleurs apparaissent principalement pendant la floraison
- Les fruits apparaissent après la floraison (fructification et récolte)
- Un semis ne peut pas avoir 150 cm de haut ni des fruits

### 2. Règles de Recommandation (par ordre de priorité)

#### Priorité 1 : Conditions critiques

1. **risque_froid** : `temperature_air_c < 12°C`
2. **risque_chaleur** : `temperature_air_c > 35°C`
3. **sol_pas_adapte** : `ph_sol < 5.5 OU ph_sol > 7.5`

#### Priorité 2 : Problèmes d'eau

4. **arroser** : `humidite_sol_pourcent < 35% ET pluie_mm_24h < 5mm`
5. **trop_eau** : `humidite_sol_pourcent > 80% OU pluie_mm_24h > 25mm`

#### Priorité 3 : Autres conditions

6. **manque_lumiere** : `lumiere_heures_jour < 6h`
7. **recolte_bientot** : `stade_croissance == "recolte" ET nb_fruits > 15 ET jour_culture > 110`

#### Par défaut

8. **bon** : toutes les conditions sont satisfaisantes

### 3. Indicateurs de Stress

Le niveau de stress est calculé en fonction de :
- Température hors plage optimale (15-32°C)
- Humidité sol hors plage optimale (40-80%)
- pH hors plage optimale (5.8-7.2)
- Lumière insuffisante (< 6h)
- Pluie excessive (> 20mm)

État général :
- **bon** : 0 facteur de stress
- **stress_leger** : 1-2 facteurs
- **stress_moyen** : 3-4 facteurs
- **mauvais** : 5+ facteurs

### 4. Couleur des Feuilles (indicateur visuel)

- **vert** : plant en bonne santé (70% des cas normaux)
- **jaune** : manque d'eau, de nutriments ou excès d'eau
- **fonce** : stress thermique (froid/chaleur)
- **tachete** : maladies, excès d'eau, pH inadapté

### 5. Paramètres Environnementaux Réalistes

- **Température air** : suit une distribution normale centrée sur 22°C
- **Température sol** : légèrement inférieure à l'air (-2°C en moyenne)
- **Humidité sol** : réduite après arrosage ou pluie
- **Pluie** : distribution exponentielle (pluies légères fréquentes, fortes rares)
- **Arrosage** : ajusté selon pluie et humidité sol

## Utilisation

### Générer un nouveau dataset

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install pandas numpy

# Générer le dataset
python generate_tomato_dataset.py
```

### Charger le dataset

```python
import pandas as pd

# Charger le CSV
df = pd.read_csv('tomato_dataset.csv')

# Vérifier les dimensions
print(f"Nombre de lignes : {len(df)}")
print(f"Nombre de colonnes : {len(df.columns)}")

# Afficher les premières lignes
print(df.head())

# Distribution de la variable cible
print(df['recommandation'].value_counts())
```

### Entraîner un modèle XGBoost

```python
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder

# Charger les données
df = pd.read_csv('tomato_dataset.csv')

# Encoder les variables catégorielles
le_stade = LabelEncoder()
le_couleur = LabelEncoder()
le_etat = LabelEncoder()
le_recommandation = LabelEncoder()

df['stade_croissance_encoded'] = le_stade.fit_transform(df['stade_croissance'])
df['couleur_feuilles_encoded'] = le_couleur.fit_transform(df['couleur_feuilles'])
df['etat_general_encoded'] = le_etat.fit_transform(df['etat_general'])
df['recommandation_encoded'] = le_recommandation.fit_transform(df['recommandation'])

# Séparer features et target
features = ['jour_culture', 'temperature_air_c', 'temperature_sol_c', 
            'humidite_air_pourcent', 'humidite_sol_pourcent', 'ph_sol',
            'lumiere_heures_jour', 'pluie_mm_24h', 'arrosage_litres_jour',
            'stade_croissance_encoded', 'hauteur_plant_cm', 'nb_fleurs', 
            'nb_fruits', 'couleur_feuilles_encoded', 'etat_general_encoded']

X = df[features]
y = df['recommandation_encoded']

# Split train/test
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Entraîner XGBoost
model = xgb.XGBClassifier(
    objective='multi:softmax',
    num_class=8,
    max_depth=6,
    learning_rate=0.1,
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# Évaluer
accuracy = model.score(X_test, y_test)
print(f"Précision : {accuracy:.2%}")
```

## Distribution du Dataset

Le dataset est **équilibré** pour permettre un apprentissage efficace :
- Classe majoritaire "bon" : ~55% (pas de déséquilibre excessif)
- Classes minoritaires bien représentées (2-13%)
- Total : 8 classes de recommandation

## Points Forts du Dataset

✅ **Cohérence temporelle** : progression réaliste des stades de croissance
✅ **Relations causales** : les recommandations suivent des règles logiques claires
✅ **Variabilité réaliste** : distributions inspirées de conditions réelles de culture
✅ **Équilibrage** : suffisamment de diversité pour l'apprentissage
✅ **Complétude** : aucune valeur manquante
✅ **Spécifique aux tomates** : paramètres adaptés uniquement à cette culture

## Améliorations Possibles

- Ajouter des séries temporelles (plusieurs observations d'un même plant)
- Intégrer des données de variétés de tomates (cerise, cœur de bœuf, etc.)
- Ajouter des informations sur les maladies et parasites
- Inclure des données de rendement final
- Ajouter des informations sur le type de culture (serre, plein champ)

---

**Auteur** : Généré pour un projet étudiant V0  
**Date** : Mai 2026  
**Licence** : Libre d'utilisation pour projets éducatifs
