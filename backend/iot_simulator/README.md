# 📡 Simulateurs IoT Intelligents

Les capteurs simulés ne génèrent **PAS** de valeurs aléatoires. Ils sont **intelligents** et réagissent aux conditions réelles (météo, irrigation, type de sol).

## 🌱 Capteur d'humidité du sol (`soil_sensor.py`)

### Principe de fonctionnement

Le capteur simule l'évolution **réaliste** de l'humidité du sol en fonction de :

1. **🌧️ Pluie du jour actuel** (pas le total 7 jours)
2. **☀️ Évaporation** (température)
3. **💧 Irrigation** (type et efficacité)
4. **🏜️ Type de sol** (rétention d'eau)
5. **📊 Bruit gaussien** (variabilité naturelle)

### Facteurs d'influence

#### 1. Pluie (`precipitation_today`)

**Comportement intelligent :**
- Récupère la météo Open-Meteo toutes les 15 minutes
- Utilise la **pluie du jour actuel** (pas total 7 jours)
- Détecte quand il **commence à pleuvoir** (delta > 0.5mm) → boost humidité
- Pluie résiduelle (0.1-0.5mm) → gain modéré
- Pas de pluie → aucun gain

**Exemple réaliste :**
```
10h00 : precipitation_today = 0.0mm    → rain_gain = 0.0
11h00 : precipitation_today = 2.5mm    → rain_gain = 0.30 (il pleut maintenant !)
12h00 : precipitation_today = 3.1mm    → rain_gain = 0.09 (pluie ralentit)
13h00 : precipitation_today = 3.2mm    → rain_gain = 0.05 (pluie résiduelle)
```

**Formule :**
```python
rain_delta = precipitation_today - last_rain_mm

if rain_delta > 0.5:  # Il pleut actuellement
    rain_gain = min(0.35, rain_delta * 0.15 * retention)
elif precipitation_today > 0.1:  # Pluie résiduelle
    rain_gain = min(0.18, precipitation_today * 0.06 * retention)
else:
    rain_gain = 0.0
```

#### 2. Évaporation (température)

**Comportement :**
- Plus il fait **chaud**, plus l'eau s'évapore
- Seuil : 14°C (pas d'évaporation en dessous)
- Facteur : 0.015 par degré au-dessus de 14°C
- Divisé par rétention du sol (argileux évapore moins vite)

**Exemple :**
```
Température 20°C, sol limoneux (retention=1.0) :
  evaporation = max(0, 20 - 14) * 0.015 / 1.0 = 0.09

Température 28°C, sol sableux (retention=0.72) :
  evaporation = max(0, 28 - 14) * 0.015 / 0.72 = 0.29 (beaucoup plus !)
```

#### 3. Irrigation

**Comportement intelligent :**
- L'irrigation **compense** si le sol est trop sec
- Plus le sol est sec, plus l'irrigation apporte d'eau
- Efficacité selon type :
  - `aucun` : 0% (pas d'irrigation)
  - `manuel` : 65% (pertes par ruissellement)
  - `goutte_a_goutte` : 90% (très efficace)
  - `automatique` : 78% (bon compromis)

**Exemple :**
```
Sol à 30%, irrigation goutte-à-goutte :
  irrigation_gain = 0.90 * max(0, 55 - 30) * 0.008 = 0.18

Sol à 60%, irrigation goutte-à-goutte :
  irrigation_gain = 0.90 * max(0, 55 - 60) * 0.008 = 0.0 (déjà suffisant)
```

#### 4. Type de sol (rétention d'eau)

Facteurs de rétention (définis dans `common.py`) :

| Type de sol | Rétention | Comportement |
|-------------|-----------|--------------|
| Argileux | **1.25** | Retient beaucoup l'eau, évapore lentement |
| Humifère | 1.18 | Bonne rétention organique |
| Limoneux | **1.00** | Référence standard (équilibré) |
| Calcaire | 0.82 | Retient moins, draine bien |
| Sableux | **0.72** | Retient peu, sèche vite |

**Impact :**
- Argileux : humidité stable, moins d'arrosage
- Sableux : humidité fluctue beaucoup, arrosages fréquents

#### 5. Bruit gaussien

**Variabilité naturelle :**
```python
gaussian_noise(0.12)  # écart-type 0.12
```

Simule les variations naturelles :
- Hétérogénéité du sol
- Zones d'ombre
- Vent
- Microclimat

## 📊 Calcul du drift (variation d'humidité)

```python
drift = rain_gain + irrigation_gain - evaporation + gaussian_noise(0.12)
humidity = clamp(humidity + drift, 12.0, 96.0)
```

**Exemple concret :**

**Conditions :**
- Sol limoneux (retention=1.0)
- Température 23°C
- Pluie aujourd'hui : 5mm (il pleut maintenant, delta=5mm)
- Irrigation goutte-à-goutte
- Humidité actuelle : 40%

**Calculs :**
```python
evaporation = max(0, 23 - 14) * 0.015 / 1.0 = 0.135
rain_gain = min(0.35, 5.0 * 0.15 * 1.0) = 0.35
irrigation_gain = 0.90 * max(0, 55 - 40) * 0.008 = 0.108
gaussian_noise = 0.02 (exemple)

drift = 0.35 + 0.108 - 0.135 + 0.02 = +0.343

humidity_new = 40 + 0.343 = 40.3%
```

**Résultat :** L'humidité augmente de **0.3%** en 10 secondes grâce à la pluie.

Après 10 minutes (60 itérations) : **~40 + 20 = 60%** (réaliste pour une averse)

## 💧 Capteur d'irrigation (`irrigation_sensor.py`)

**Rôle :** Publie l'état du système d'irrigation

**Données publiées :**
- `irrigation` : type (manuel, goutte_a_goutte, automatique, aucun)
- `active` : true/false (irrigation en cours ou non)
- `flow_l_min` : débit en L/min

**Comportement :**
- Configuration fixe (définie par environnement)
- Peut être étendu pour simuler activation/désactivation

## 🚰 Capteur d'eau (`water_usage_sensor.py`)

**Rôle :** Mesure la consommation d'eau

**Comportement :**
- Basé sur le type d'irrigation
- Varie légèrement autour d'une valeur moyenne
- Peut être étendu pour corréler avec humidité du sol

## 🌍 Intégration météo

### WeatherCache

**Fréquence de rafraîchissement :** 15 minutes (900 secondes)

**API utilisée :** Open-Meteo (gratuite, sans clé)

**Données récupérées :**
- `temperature` : température actuelle (°C)
- `temperature_mean_7d` : température moyenne 7 jours
- `precipitation_7d` : somme pluie 7 jours (mm)
- `precipitation_today` : **pluie du jour actuel** (mm) ✨

**Paramètres API :**
```python
params = {
    "latitude": 48.1173,  # Rennes
    "longitude": -1.6778,
    "current": "temperature_2m",
    "daily": "temperature_2m_mean,precipitation_sum",
    "timezone": "auto",
    "forecast_days": 7
}
```

**Fallback :** Si Open-Meteo indisponible, génère valeurs aléatoires réalistes.

## 🔄 Cycle de simulation

```
1. Connexion MQTT (async, reconnexion auto)
2. Boucle infinie :
   a. Récupérer météo (cache 15min)
   b. Calculer facteurs (évaporation, pluie, irrigation)
   c. Calculer drift (variation humidité)
   d. Appliquer drift + clamp (12-96%)
   e. Publier MQTT
   f. Sleep (10s + jitter)
```

## 🧪 Tester la logique

### Tester avec pluie

```bash
# Vérifier météo actuelle
curl "https://api.open-meteo.com/v1/forecast?latitude=48.1173&longitude=-1.6778&current=temperature_2m&daily=precipitation_sum&forecast_days=1"

# Observer humidité monter si pluie prévue
mosquitto_sub -h localhost -p 1883 -t "farm/tomato/soil" -v
```

### Tester évaporation (chaleur)

Attendre une journée chaude (>25°C) :
- L'humidité devrait **baisser** progressivement
- Plus rapide sur sol sableux que argileux

### Tester irrigation

Changer type d'irrigation dans `.env` :
```bash
DEFAULT_IRRIGATION=aucun          # Humidité descend vite
DEFAULT_IRRIGATION=goutte_a_goutte # Humidité compensée efficacement
```

## 📈 Valeurs typiques observées

| Condition | Humidité sol | Évolution |
|-----------|--------------|-----------|
| Beau temps, pas d'irrigation | 35-45% | ⬇️ Descend lentement |
| Pluie légère (2mm) | 50-60% | ⬆️ Monte modérément |
| Forte pluie (10mm) | 70-85% | ⬆️⬆️ Monte rapidement |
| Canicule (35°C) | 25-35% | ⬇️⬇️ Descend vite |
| Goutte-à-goutte actif | 55-65% | ➡️ Stable |

## 🚀 Évolutions possibles V1

### Capteur humidité
- [ ] Corrélation avec historique arrosage réel
- [ ] Simulation infiltration progressive (pluie met du temps à pénétrer)
- [ ] Différence jour/nuit (évaporation nulle la nuit)
- [ ] Impact vent (augmente évaporation)

### Capteur irrigation
- [ ] Activation/désactivation selon humidité
- [ ] Simulation durée d'arrosage
- [ ] Usure capteur (valeurs dérivant avec le temps)

### Capteur eau
- [ ] Corrélation forte avec humidité sol
- [ ] Détection fuites (consommation anormale)
- [ ] Historique consommation

### Météo
- [ ] Prévisions heure par heure (plus précis)
- [ ] Humidité de l'air (impact évaporation)
- [ ] Radiation solaire (évaporation)

## 📝 Résumé

**Les capteurs sont intelligents car :**

✅ **Pluie réaliste** : Utilise pluie du jour actuel, pas total 7 jours  
✅ **Évaporation dynamique** : Augmente avec température  
✅ **Irrigation contextuelle** : Compense si sol sec, efficacité variable  
✅ **Type de sol respecté** : Argileux vs sableux se comportent différemment  
✅ **Météo réelle** : Open-Meteo toutes les 15 minutes  
✅ **Variabilité naturelle** : Bruit gaussien pour réalisme  

**Résultat :** L'humidité évolue de **manière cohérente** avec les conditions météo réelles !
