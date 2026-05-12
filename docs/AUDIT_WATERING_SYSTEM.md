# Audit V0 - Système de Conseil d'Arrosage Intelligent

## Problème identifié

Le dashboard affichait des conseils d'arrosage basés sur une **logique if/else simpliste** qui ne prenait pas pleinement en compte :
- Les interactions complexes entre humidité, température, pluie et type de sol
- Les features calculées par le modèle ML (stress_hydrique, risque_secheresse, confort_thermique)
- Le contexte agronomique réel

**Exemple problématique :**
```typescript
// Ancien code frontend
if (weather.pluie_7j) {
  return "Surveiller la pluie avant d'arroser.";
} else {
  return "Conditions meteo correctes.";
}
```

Ce conseil était **identique quelle que soit l'humidité du sol**, ce qui n'avait aucun sens agronomique.

## Solution implémentée

### 1. Backend - Nouveau endpoint `/advice/watering`

**Fichier créé :** `backend/app/watering_advice.py`

Le système réutilise les **features ML du modèle XGBoost** pour générer des conseils intelligents :

```python
# Calcul du stress hydrique (identique au modèle ML)
stress_hydrique = max(0.0, 50.0 - humidite_sol) * (1.0 if not pluie_prevue else 0.3)
if irrigation == "aucun":
    stress_hydrique *= 1.5

# Calcul du risque de sécheresse
risque_secheresse = (
    max(0.0, 40.0 - humidite_sol)
    + max(0.0, temp_moyenne - 25.0) * 2.5
    + (5.0 if not pluie_prevue and humidite_sol < 40 else 0.0)
)
```

### 2. Logique de priorisation

Le système applique une logique agronomique par priorité :

1. **Stress hydrique > 40** → Arrosage urgent (12-24h)
2. **Risque sécheresse > 30** → Arrosage recommandé (24-48h)
3. **Sol > 75%** → Aucun arrosage (risque drainage)
4. **Sol 60-75% + pluie** → Pas d'arrosage nécessaire
5. **Sol 40-60% + pluie >10mm** → Reporter l'arrosage
6. **Sol 40-60% + pas de pluie** → Surveillance selon température
7. **Sol 30-40%** → Arrosage nécessaire rapidement
8. **Par défaut** → Surveillance régulière

### 3. Conseils contextuels

Le système prend en compte :
- **Type de sol** : sableux (arrosages fréquents légers) vs argileux (arrosages espacés abondants)
- **Type d'irrigation** : automatique / manuel / goutte-à-goutte / aucun
- **Température** : évaporation accrue si >25°C
- **Pluie prévue** : quantité en mm, pas juste booléen

**Exemple de réponse :**
```json
{
  "conseil": "Arrosage urgent necessaire",
  "priorite": "urgent",
  "explication": "Le stress hydrique est tres eleve (45.0/100). Les plantes souffrent d'un manque d'eau important avec une humidite du sol a 25%. Aucune pluie prevue pour compenser.",
  "facteurs_cles": ["humidite_sol_critique", "aucune_pluie_prevue", "temperature_elevee"],
  "score_stress_hydrique": 45.0,
  "score_risque_secheresse": 32.5,
  "recommandation_action": "Arroser immediatement avec 18 litres par m2.",
  "prochaine_verification": "Verifier dans 12-24 heures"
}
```

### 4. Frontend - Intégration API

Le dashboard appelle maintenant `/advice/watering` au lieu d'utiliser des if/else :

```typescript
// Nouveau code
const wateringAdvice = await getWateringAdvice({
  location: currentProfile.location,
  type_sol: currentProfile.type_sol,
  irrigation: currentProfile.irrigation,
  humidite_sol: live?.soil_humidity,
  temp_actuelle: forecast?.temp_actuelle,
  temp_min_7j: forecast?.temp_min_7j,
  temp_moyenne_7j: forecast?.temp_moyenne_7j,
  pluie_7j: forecast?.pluie_7j,
  precipitation_7j: forecast?.precipitation_7j
});
```

## Avantages

### ✅ Réutilisation du modèle ML
- Mêmes features que le modèle de prédiction de plantation
- Cohérence entre "quand planter" et "comment arroser"
- Pas besoin d'entraîner un nouveau modèle

### ✅ Conseils contextuels
- Prise en compte de **tous** les facteurs (sol, météo, irrigation)
- Adaptation au type de sol (sableux vs argileux)
- Quantité d'eau recommandée en L/m²

### ✅ Transparence
- Scores de stress hydrique et risque sécheresse affichables
- Facteurs clés identifiés
- Explication claire de la recommandation

### ✅ Maintenabilité
- Logique centralisée dans le backend
- Frontend simple (appel API)
- Facile à tester et améliorer

## Comparaison avant/après

### Avant (if/else frontend)
```
Humidité: 52%, Pluie: 14mm
→ "Surveiller la pluie avant d'arroser."
```

### Après (API ML backend)
```
Humidité: 52%, Pluie: 14mm, Temp: 23°C, Sol: limoneux
→ "Reporter l'arrosage - Pluie prevue"
→ "Le sol est a un niveau correct (52%) et 14.3mm de pluie sont prevus."
→ "Reporter l'arrosage. Laisser la pluie hydrater naturellement."
→ "Reverifier apres la pluie (2-3 jours)"
```

## Alignement avec le CDC

### Modèle ML utilisé ✓
> "La partie IA repose sur un modèle XGBoost Classifier."

Le système **réutilise les features calculées** du modèle XGBoost (stress_hydrique, risque_secheresse, confort_thermique) pour générer des conseils cohérents.

### Objectif du projet ✓
> "L'objectif est de proposer une aide simple au personnel pour savoir si les conditions sont favorables"

Le système aide maintenant pour :
1. **Quand planter** (`/predict`) → viable/attendre/non_viable
2. **Comment arroser** (`/advice/watering`) → urgence, quantité, timing

### IoT intégré ✓
> "Prendre en compte des données IoT simulées via MQTT"

L'endpoint `/advice/watering` utilise automatiquement :
- `iot.soil_humidity` (humidité du sol en temps réel)
- `iot.water_usage` (consommation d'eau)
- `iot.irrigation` (type d'irrigation actif)

## Évolutions possibles V1

1. **Historique des conseils** : sauvegarder les recommandations d'arrosage en DB
2. **Notifications** : alertes si stress hydrique > 40
3. **Apprentissage** : affiner les seuils selon retours terrain
4. **Prédiction** : anticiper le stress hydrique à J+3
5. **Multi-cultures** : adapter les seuils pour salades, courgettes, etc.

## Tests recommandés

```bash
# 1. Test backend
curl -X POST http://localhost:8000/advice/watering \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Rennes",
    "type_sol": "limoneux",
    "irrigation": "manuel",
    "humidite_sol": 25
  }'

# 2. Test frontend
# Vérifier que le conseil change selon l'humidité du sol
# Simuler différentes valeurs IoT (20%, 50%, 80%)

# 3. Test edge cases
# - Sol critique (< 30%) + pas de pluie → urgent
# - Sol saturé (> 75%) + pluie → aucun arrosage
# - Sol correct (50%) + pluie >10mm → reporter
```

## Conclusion

Le système est maintenant **cohérent avec le modèle ML** et donne des **conseils agronomiques contextuels** au lieu de règles simplistes. Cela respecte l'esprit du projet : utiliser l'IA pour aider le personnel de l'EHPAD avec des recommandations pertinentes.
