# Cahier des charges technique — V0 Potager EHPAD tomate

## 1. Contexte du projet

Le projet consiste à créer une application web permettant d’aider un EHPAD rural ou semi-rural à gérer plus facilement un petit potager pédagogique, avec un premier focus sur la culture de tomates.

L’objectif n’est pas de rendre l’EHPAD autonome en alimentation. L’objectif est plutôt de proposer une aide simple au personnel pour savoir si les conditions sont favorables ou non pour planter des tomates, tout en gardant une activité agréable et compréhensible pour les résidents.

La V0 doit donc rester réaliste : une seule culture, peu d’écrans, une interface simple et une IA prédictive centrée sur une décision claire.

---

## 2. Objectif principal de la V0

La V0 doit permettre de :

1. **Prédire si le moment est favorable pour planter des tomates** dans le potager de l’EHPAD
2. **Fournir des conseils d’arrosage intelligents** pour les plants déjà en terre

L’application doit analyser plusieurs données :

- saison ;
- température actuelle ;
- température minimale prévue sur les prochains jours ;
- température moyenne prévue ;
- pluie prévue ;
- risque de gel ;
- humidité du sol ;
- type de sol ;
- type d’irrigation ;
- données IoT simulées pour l’humidité du sol, l’irrigation et l’eau utilisée.

### 2.1 Prédiction de plantation

À partir de ces données, le modèle prédictif XGBoost doit retourner une recommandation simple :

```text
viable
attendre
non_viable
```

La recommandation doit toujours être accompagnée d’une explication simple, compréhensible par le personnel de l’EHPAD.

Exemple :

```text
Recommandation : attendre
Explication : les températures minimales prévues sont encore trop basses pour planter des tomates sans risque.
```

### 2.2 Conseils d’arrosage intelligents

Le système doit également fournir des conseils d’arrosage contextuels basés sur les features ML :

```text
Conseil : Arrosage recommandé dans les 24-48h
Priorité : élevée
Action : Prévoir un arrosage de 15 litres par m² dans les prochaines 48h
Vérification : Vérifier quotidiennement
```

Les conseils prennent en compte :
- Le stress hydrique calculé par le modèle ML
- Le risque de sécheresse (sol + température + pluie)
- Le type de sol (sableux, argileux, limoneux, etc.)
- Le type d’irrigation (manuel, goutte-à-goutte, automatique)
- Les prévisions météo (pluie, température)

---

## 3. Périmètre de la V0

### 3.1 Ce que la V0 doit faire

La V0 doit permettre de :

- afficher un dashboard simple ;
- lancer une prédiction de viabilité pour la tomate ;
- prendre en compte des données météo Open-Meteo et agricoles ;
- prendre en compte des données IoT simulées via MQTT ;
- utiliser un modèle XGBoost pour prédire une classe de viabilité de plantation ;
- fournir des conseils d’arrosage intelligents basés sur les features ML ;
- afficher une recommandation claire pour planter et arroser ;
- afficher une explication de la recommandation ;
- stocker l’historique des prédictions de plantation ;
- être lançable facilement avec Docker ;
- être déployable plus tard sur Azure.

### 3.2 Ce que la V0 ne fait pas encore

La V0 ne doit pas essayer de tout faire.

Elle ne gère pas encore :

- plusieurs légumes ;
- une automatisation physique complète de l’arrosage (vannes connectées) ;
- une prédiction de rendement précise ;
- une reconnaissance d’image des maladies ;
- des capteurs physiques réels (ESP32) ;
- Azure IoT Hub ;
- un système complexe de comptes utilisateurs ;
- une base de données lourde type PostgreSQL ;
- un historique des conseils d’arrosage (uniquement prédictions de plantation sauvegardées).

Ces éléments peuvent être prévus dans les évolutions futures.

### 3.3 État d’avancement actuel

| Élément | État | Commentaire |
|---|---|---|
| Dashboard Next.js | ✅ Fait | Vue principale, historique et panneau IoT live |
| Formulaire de prédiction | ✅ Fait | Mode manuel avec préremplissage météo |
| API FastAPI | ✅ Fait | Routes principales implémentées |
| Météo Open-Meteo | ✅ Fait | Température actuelle, prévisions 7 jours, pluie, gel |
| Modèle XGBoost | ✅ Fait | Modèle chargé et utilisé par l’API |
| **Conseil d’arrosage ML** | ✅ Fait | Endpoint `/advice/watering` basé sur features ML |
| Historique SQLite | ✅ Fait | Prédictions de plantation persistées |
| IoT simulé MQTT | ✅ Fait | Mosquitto, simulateurs Python, consumer FastAPI |
| WebSocket IoT live | ✅ Fait | Flux `/ws/iot` pour le dashboard |
| Profil potager | ✅ Fait | Endpoints `/garden/profile` pour configuration |
| Docker Compose | ⚙️ Configuré | Configuration valide, exécution complète à valider avec Docker Desktop |
| Dataset réel agricole | ⚠️ Partiel | Modèle basé sur données synthétiques réalistes, pas sur données terrain réelles |
| Capteurs physiques ESP32 | ❌ Non fait | Prévu en V1 sans changer les topics MQTT |
| Table `model_versions` | ❌ Non fait | Prévue mais pas encore implémentée |
| Historique conseils arrosage | ❌ Non fait | Prévu en V1 (actuellement non sauvegardé en DB) |

---

## 4. Stack technique retenue

| Partie | Technologie | Rôle |
|---|---|---|
| Frontend | Next.js | Dashboard web |
| Style | Tailwind CSS | Interface simple et responsive |
| Backend | FastAPI | API Python |
| IA prédictive | XGBoost | Modèle de classification prédictive |
| Préparation des données | pandas, scikit-learn | Nettoyage et transformation des données |
| Base de données | SQLite | Historique des prédictions pour la V0 |
| Données météo | Open-Meteo | Prévisions et météo historique |
| IoT simulé | MQTT, Mosquitto, paho-mqtt | Simulation de capteurs et ingestion live |
| Conteneurisation | Docker / Docker Compose | Lancement simple du projet |
| Cloud | Azure étudiant | Hébergement possible |
| IoT futur | ESP32, Azure IoT Hub éventuel | Remplacement des simulateurs par de vrais capteurs |

---

## 5. Architecture générale

```text
Utilisateur EHPAD
      ↓
Dashboard Next.js
      ↓
API FastAPI
      ↓
Récupération météo Open-Meteo
      ↓
MQTT consumer FastAPI
      ↑
Mosquitto MQTT ← capteurs Python simulés
      ↓
Préparation des données
      ↓
Modèle XGBoost
      ↓
Prédiction : viable / attendre / non_viable
      ↓
SQLite : historique
      ↓
Affichage du résultat
```

Le frontend sert à afficher les informations et à envoyer les demandes de prédiction.

Le backend contient la logique principale :

- récupérer les données météo ;
- consommer les données IoT simulées depuis MQTT ;
- préparer les variables nécessaires au modèle ;
- appeler le modèle XGBoost ;
- générer une explication ;
- stocker le résultat dans SQLite ;
- renvoyer le résultat au dashboard.

---

## 6. Frontend — Next.js + Tailwind CSS

### 6.1 Objectif du frontend

Le frontend doit être très simple, car le public visé n’est pas technique.

Le personnel de l’EHPAD doit pouvoir comprendre rapidement :

- si les conditions sont bonnes ;
- pourquoi l’application recommande de planter ou d’attendre ;
- quelles données ont été prises en compte.

### 6.2 Pages prévues

| Page | Rôle |
|---|---|
| `/dashboard` | Vue principale avec la dernière recommandation |
| `/predict` | Formulaire ou bouton pour lancer une prédiction |
| `/history` | Historique des anciennes prédictions |
| `/settings` | Paramètres simples : localisation, surface, type de sol |

Pour une V0 courte, les pages prioritaires sont :

```text
/dashboard
/predict
/history
```

### 6.3 Dashboard principal

Le dashboard doit afficher :

- la culture analysée : tomate ;
- la date de la prédiction ;
- la localisation approximative de l’EHPAD ;
- la recommandation IA ;
- le score de confiance ;
- l’explication simple ;
- les principales données météo ;
- les dernières données IoT simulées si disponibles ;
- les principaux KPI.

Exemple d’affichage :

```text
Culture : Tomate
Recommandation : attendre
Confiance : 82 %
Raison : la température minimale prévue est trop basse pour planter sans risque.
```

### 6.4 KPI à afficher

| KPI | Utilité |
|---|---|
| Nombre total de prédictions | Voir l’utilisation de l’outil |
| Taux de prédictions viables | Voir les périodes favorables |
| Taux de prédictions à attendre | Voir les situations moyennes |
| Taux de prédictions non viables | Voir les risques évités |
| Température minimale prévue | Indicateur clé pour la tomate |
| Risque de gel | Indicateur critique |
| Humidité du sol | Important pour l’arrosage |
| Consommation d’eau estimée | Suivre l’arrosage |
| État MQTT | Vérifier si les données IoT live arrivent |
| Score de confiance du modèle | Rendre la prédiction plus transparente |

### 6.5 Formulaire de prédiction

Le formulaire doit permettre de saisir ou récupérer :

| Champ | Type | Exemple |
|---|---|---|
| Localisation | texte | Rennes |
| Saison | automatique ou liste | printemps |
| Type de sol | liste | limoneux |
| Type d’irrigation | liste | manuel / goutte-à-goutte |
| Humidité du sol | nombre | 55 % |
| Température actuelle | nombre | 20 °C |
| Température minimale sur 7 jours | nombre | 8 °C |
| Température moyenne sur 7 jours | nombre | 16 °C |
| Pluie prévue | oui / non | oui |
| Risque de gel | oui / non | non |
| Eau utilisée | nombre | 80 L estimés |

Dans la V0 actuelle, les données météo peuvent être récupérées automatiquement depuis Open-Meteo. Les champs restent modifiables manuellement pour garder un mode secours.

Les données locales du potager peuvent venir soit du formulaire, soit de l’architecture IoT simulée :

- humidité du sol ;
- type d’irrigation ;
- consommation ou usage estimé de l’eau.

---

## 7. Backend — FastAPI

### 7.1 Rôle du backend

Le backend est la partie centrale de l’application.

Il doit gérer :

- les routes API ;
- la récupération des données météo ;
- la consommation des messages MQTT IoT simulés ;
- la préparation des données ;
- l’appel au modèle XGBoost ;
- la création d’une explication ;
- le stockage dans SQLite ;
- la récupération de l’historique.

### 7.2 Routes API nécessaires

| Route | Méthode | Rôle |
|---|---|---|
| `/health` | GET | Vérifier que l’API fonctionne |
| `/predict` | POST | Lancer une prédiction de plantation |
| `/predict/iot` | POST | Lancer une prédiction avec météo + IoT simulé |
| `/advice/watering` | POST | Obtenir un conseil d’arrosage intelligent (ML) |
| `/history` | GET | Récupérer l’historique |
| `/history/{id}` | GET | Voir une prédiction précise |
| `/model/info` | GET | Voir les informations du modèle |
| `/weather` | GET | Récupérer la météo Open-Meteo |
| `/iot/live` | GET | Récupérer les dernières données IoT reçues |
| `/ws/iot` | WebSocket | Diffuser les données IoT live au dashboard |
| `/garden/profile` | GET | Récupérer le profil du potager (localisation, sol, irrigation) |
| `/garden/profile` | PUT | Mettre à jour le profil du potager |

### 7.3 Exemple de payload `/predict`

```json
{
  "location": "Rennes",
  "culture": "tomate",
  "saison": "printemps",
  "type_sol": "limoneux",
  "irrigation": "manuel",
  "humidite_sol": 55,
  "temp_actuelle": 20,
  "temp_min_7j": 7,
  "temp_moyenne_7j": 15,
  "pluie_7j": 1,
  "risque_gel_7j": 0,
  "water_usage": 80
}
```

### 7.4 Exemple de réponse API

```json
{
  "recommandation": "attendre",
  "score_confiance": 0.82,
  "explication": "Les conditions ne sont pas catastrophiques, mais la température minimale prévue reste trop basse pour planter les tomates sans risque.",
  "facteurs_importants": [
    "temp_min_7j",
    "saison",
    "humidite_sol"
  ]
}
```

### 7.5 Exemple de payload `/predict/iot`

Le mode IoT demande moins de champs au frontend, car le backend complète les données avec Open-Meteo et les dernières valeurs MQTT reçues.

```json
{
  "location": "Rennes",
  "culture": "tomate",
  "type_sol": "limoneux"
}
```

Le backend complète automatiquement :

- saison ;
- température actuelle ;
- température minimale sur 7 jours ;
- température moyenne sur 7 jours ;
- pluie prévue ;
- risque de gel ;
- humidité du sol IoT ;
- irrigation IoT ;
- eau utilisée IoT.

### 7.6 Exemple de payload `/advice/watering`

Le conseil d'arrosage peut fonctionner en mode manuel (données complètes) ou automatique (complété par météo + IoT).

```json
{
  "location": "Rennes",
  "type_sol": "limoneux",
  "irrigation": "manuel",
  "humidite_sol": 35
}
```

### 7.7 Exemple de réponse `/advice/watering`

```json
{
  "conseil": "Arrosage recommandé dans les 24-48h",
  "priorite": "eleve",
  "explication": "Le risque de sécheresse est élevé (32.5/100). Sol à 35%, température moyenne de 23°C et aucune pluie prévue. Les conditions vont se dégrader rapidement.",
  "facteurs_cles": [
    "humidite_sol_basse",
    "aucune_pluie_prevue",
    "temperature_elevee"
  ],
  "score_stress_hydrique": 22.5,
  "score_risque_secheresse": 32.5,
  "recommandation_action": "Prévoir un arrosage de 12 litres par m² dans les prochaines 48h.",
  "prochaine_verification": "Vérifier quotidiennement"
}
```

---

## 8. Partie IA prédictive — XGBoost

### 8.1 Objectif du modèle

Le modèle IA a deux objectifs principaux :

1. **Prédire la viabilité d’une plantation de tomates** à partir de plusieurs données
2. **Fournir des features ML réutilisables** pour d’autres fonctionnalités (ex: conseils d’arrosage)

Il ne doit pas seulement appliquer une règle fixe comme :

```text
si température > 18 alors planter
```

Il doit apprendre à partir d’un dataset d’entraînement pour prédire une classe, et calculer des features intermédiaires intelligentes.

### 8.2 Modèle retenu

Le modèle retenu est :

```text
XGBoost Classifier
```

XGBoost est un modèle de machine learning basé sur le gradient boosting. Il peut être utilisé pour des problèmes de classification ou de régression.

Dans ce projet, il est utilisé pour faire de la classification.

### 8.3 Pourquoi XGBoost est adapté

XGBoost est adapté car :

- il fonctionne bien sur des données tabulaires ;
- il peut croiser plusieurs variables ;
- il donne une prédiction avec un score de confiance ;
- il ne demande pas forcément de GPU ;
- il est plus crédible qu’un simple arbre de décision ;
- il peut être amélioré plus tard avec des données IoT.

### 8.4 Type de problème

Le problème est un problème de classification supervisée.

Le modèle reçoit des données en entrée :

```text
saison, type_sol, irrigation, humidite_sol, temperature, pluie, risque_gel...
```

Et il prédit une classe :

```text
viable
attendre
non_viable
```

### 8.5 Variables d’entrée du modèle

#### Variables brutes

| Variable | Type | Source |
|---|---|---|
| culture | texte | fixe : tomate |
| saison | texte | date actuelle |
| type_sol | texte | formulaire / configuration locale |
| irrigation | texte | formulaire ou IoT simulé |
| humidite_sol | nombre | saisie ou IoT simulé |
| temp_actuelle | nombre | API météo Open-Meteo |
| temp_min_7j | nombre | API météo |
| temp_moyenne_7j | nombre | API météo |
| pluie_7j | booléen | API météo |
| risque_gel_7j | booléen | calcul backend |
| water_usage | nombre | estimation ou IoT simulé |

#### Features calculées par le modèle (engineered features)

Le modèle calcule des features intermédiaires intelligentes :

| Feature | Formule | Utilité |
|---|---|---|
| `confort_thermique` | `10 - abs(temp_moyenne - 20) * 0.5` ajusté si temp_min < 8°C | Adaptation de la plante aux températures |
| `stress_hydrique` | `max(0, 50 - humidite_sol) * (1.0 si pas de pluie sinon 0.3)` × 1.5 si irrigation=aucun | Tension sur la plante due au manque d’eau |
| `risque_secheresse` | `max(0, 40 - humidite_sol) + max(0, temp_moyenne - 25) * 2.5 + bonus si sol sec sans pluie` | Risque combiné (sol + température + pluie) |
| `score_saison_tomate` | Score 0.1 à 0.9 selon saison et température | Période optimale pour la tomate |

Ces features sont **réutilisées** pour le système de conseil d’arrosage (`/advice/watering`).

### 8.6 Sortie du modèle

| Classe | Signification |
|---|---|
| `viable` | Les conditions sont favorables pour planter maintenant |
| `attendre` | Les conditions sont moyennes, il vaut mieux attendre |
| `non_viable` | Les conditions sont trop risquées |

### 8.7 Exemple de prédiction

```text
Entrée :
- saison = printemps
- temp_actuelle = 20 °C
- temp_min_7j = 3 °C
- risque_gel_7j = oui
- humidite_sol = 55 %

Sortie :
non_viable

Explication :
Un risque de gel est prévu dans les prochains jours. Il est donc déconseillé de planter les tomates maintenant.
```

---

## 9. Dataset et entraînement

### 9.1 Problème du dataset

Il est difficile de trouver un dataset parfait qui indique directement :

```text
planter aujourd’hui : oui / non
```

La stratégie retenue est donc de construire un dataset final à partir de plusieurs sources.

### 9.2 Sources possibles

Le dataset final peut être construit avec :

- un dataset agricole Kaggle ;
- des données météo Open-Meteo ;
- des règles agronomiques simples liées à la tomate ;
- des données IoT simulées pour tester l’architecture.

### 9.3 Dataset agricole de base

Un dataset agricole peut contenir des colonnes comme :

```text
Farm_ID
Crop_Type
Irrigation_Type
Soil_Type
Season
Farm_Area
Fertilizer_Used
Pesticide_Used
Water_Usage
Yield
```

Ce dataset est utile pour récupérer des informations sur :

- la culture ;
- le type de sol ;
- la saison ;
- l’irrigation ;
- l’eau utilisée ;
- le rendement.

Mais il ne suffit pas seul, car il ne contient pas forcément les prévisions météo ni le risque de gel.

### 9.4 Données météo à ajouter

Il faut enrichir le dataset avec :

```text
temp_actuelle
temp_min_7j
temp_moyenne_7j
pluie_7j
risque_gel_7j
```

Ces données viennent d’Open-Meteo dans l’application actuelle. Elles peuvent aussi être simulées ou fixées dans les tests pour valider le backend sans dépendre du réseau.

### 9.5 Création de la colonne cible

Comme le dataset ne contient pas forcément la colonne `recommandation`, elle sera créée.

Exemple de classes :

```text
viable
attendre
non_viable
```

Exemple de règles de création :

```text
Si risque_gel_7j = 1 → non_viable
Si temp_min_7j < 8 °C → attendre
Si saison hors période favorable → attendre ou non_viable
Si temp_moyenne_7j entre 18 et 27 °C et pas de gel → viable
Si sol trop sec et pas de pluie → attendre
```

Ces règles servent à construire un dataset d’entraînement. Ensuite, le modèle XGBoost apprend à retrouver ces comportements à partir des données.

### 9.6 Exemple de dataset final

```csv
culture,saison,type_sol,irrigation,humidite_sol,temp_actuelle,temp_min_7j,temp_moyenne_7j,pluie_7j,risque_gel_7j,water_usage,recommandation
tomate,printemps,limoneux,manuel,55,20,13,18,1,0,80,viable
tomate,printemps,sableux,manuel,45,17,7,13,1,0,60,attendre
tomate,printemps,limoneux,goutte_a_goutte,60,18,2,11,1,1,90,non_viable
tomate,ete,limoneux,manuel,20,34,22,29,0,0,120,attendre
```

### 9.7 Évaluation du modèle

Pour vérifier que le modèle fonctionne, il faudra mesurer :

- accuracy ;
- precision ;
- recall ;
- matrice de confusion ;
- score de confiance moyen ;
- cohérence des prédictions sur des cas tests.

Le but n’est pas d’avoir un modèle parfait, mais de montrer que la logique prédictive fonctionne.

État actuel : le modèle intégré est entraîné sur un dataset synthétique probabiliste réaliste. Ce choix est acceptable pour une V0 étudiante, mais il ne doit pas être présenté comme un modèle agronomique validé sur données terrain réelles.

---

## 10. IoT — Simulation V0 et évolution future

### 10.1 Rôle de l’IoT

L’IoT physique n’est pas obligatoire dans la V0, mais l’architecture est maintenant simulée pour rendre le projet plus crédible techniquement.

La V0 ne dépend d’aucun capteur réel. Des scripts Python simulent les capteurs et publient des messages MQTT. Plus tard, ces scripts pourront être remplacés par de vrais ESP32 sans changer les topics ni le consumer FastAPI.

### 10.2 Données IoT possibles

| Capteur | Donnée récupérée | Utilité |
|---|---|---|
| Capteur humidité sol simulé | humidité du sol | Savoir si le sol est trop sec |
| Capteur irrigation simulé | type d’irrigation, débit, état actif | Suivre l’arrosage |
| Capteur eau simulé | consommation d’eau estimée | Suivre l’eau utilisée |
| Capteur température air réel | température locale | Évolution future |
| Capteur température sol réel | température du sol | Évolution future |
| Capteur luminosité réel | exposition solaire | Évolution future |

### 10.3 Architecture IoT simulée V0

```text
Capteurs Python simulés
      ↓
MQTT
      ↓
Broker Mosquitto
      ↓
FastAPI MQTT Consumer
      ↓
Préparation des données
      ↓
Modèle XGBoost
      ↓
SQLite
      ↓
Dashboard
```

Topics MQTT utilisés :

```text
farm/tomato/soil
farm/tomato/irrigation
farm/tomato/water_usage
```

Payload exemple humidité sol :

```json
{
  "sensor_id": "soil_sensor_1",
  "farm_id": "farm_1",
  "humidity": 43.2,
  "timestamp": "2026-05-11T18:00:00Z"
}
```

Payload exemple eau :

```json
{
  "sensor_id": "water_sensor_1",
  "farm_id": "farm_1",
  "water_usage": 12.4,
  "timestamp": "2026-05-11T18:00:00Z"
}
```

### 10.4 Architecture IoT future avec vrais capteurs

```text
Capteurs dans le potager
      ↓
ESP32
      ↓
MQTT
      ↓
Mosquitto ou Azure IoT Hub
      ↓
FastAPI / service d’ingestion
      ↓
SQLite ou base cloud
      ↓
Dashboard
```

### 10.5 Intérêt pour le modèle

Avec l’IoT, le modèle ne dépend plus seulement de données météo générales.

Il peut utiliser des données locales :

- température réelle du site ;
- humidité réelle du sol ;
- luminosité réelle ;
- historique des conditions du potager.

Cela rend les prédictions plus proches de la réalité de l’EHPAD.

---

## 11. Base de données — SQLite

### 11.1 Pourquoi SQLite ?

SQLite est suffisant pour une V0 car :

- simple à installer ;
- pas besoin de serveur de base de données ;
- facile à utiliser avec FastAPI ;
- suffisant pour stocker un historique simple ;
- léger pour un projet étudiant.

### 11.2 Tables prévues

#### Table `predictions`

| Champ | Type | Rôle |
|---|---|---|
| id | integer | Identifiant |
| created_at | datetime | Date de prédiction |
| location | text | Localisation approximative |
| culture | text | Tomate |
| saison | text | Saison |
| type_sol | text | Type de sol |
| irrigation | text | Type d’irrigation |
| humidite_sol | float | Humidité du sol |
| temp_actuelle | float | Température actuelle |
| temp_min_7j | float | Température minimale prévue |
| temp_moyenne_7j | float | Température moyenne prévue |
| pluie_7j | integer | Pluie prévue |
| risque_gel_7j | integer | Risque de gel |
| water_usage | float | Eau utilisée ou estimée |
| recommandation | text | Résultat du modèle |
| score_confiance | float | Confiance du modèle |
| explication | text | Explication affichée |

#### Table `iot_readings`

| Champ | Type | Rôle |
|---|---|---|
| id | integer | Identifiant |
| created_at | datetime | Date d’insertion |
| topic | text | Topic MQTT reçu |
| sensor_id | text | Identifiant du capteur simulé |
| farm_id | text | Identifiant du potager |
| observed_at | datetime | Timestamp envoyé par le capteur |
| payload | text/json | Message MQTT brut |

#### Table `model_versions`

| Champ | Type | Rôle |
|---|---|---|
| id | integer | Identifiant |
| version | text | Version du modèle |
| trained_at | datetime | Date d’entraînement |
| dataset_name | text | Dataset utilisé |
| accuracy | float | Score principal |
| notes | text | Commentaires |

État actuel : `predictions` et `iot_readings` sont implémentées. `model_versions` reste prévue mais n’est pas encore implémentée.

---

## 12. Docker et déploiement

### 12.1 Conteneurs prévus

Le projet peut être lancé avec plusieurs conteneurs simples :

```text
frontend
backend
mqtt
iot-simulator
```

Et des volumes pour la base SQLite et les données MQTT :

```text
backend_data
mqtt_data
mqtt_log
```

### 12.2 Exemple de `docker-compose.yml`

```yaml
services:
  mqtt:
    image: eclipse-mosquitto:2
    ports:
      - "1883:1883"

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      - backend

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
      - ./backend/models:/app/models
    environment:
      - DATABASE_URL=sqlite:///app/data/database.db
      - MODEL_PATH=/app/models/xgboost_tomate.pkl
      - MQTT_HOST=mqtt

  iot-simulator:
    build: ./backend
    command: python -m iot_simulator.run_all
    depends_on:
      - mqtt
```

### 12.3 Déploiement local

Commande attendue :

```bash
docker compose up --build
```

Le frontend sera disponible sur :

```text
http://localhost:3000
```

L’API sera disponible sur :

```text
http://localhost:8000
```

Le broker MQTT sera disponible sur :

```text
localhost:1883
```

État actuel : la configuration Docker Compose est présente et valide. L’exécution complète `docker compose up --build` doit encore être validée sur une machine avec Docker Desktop lancé.

---

## 13. Réseau, cloud et sécurité

### 13.1 Déploiement recommandé

Pour une V0, il n’est pas obligatoire d’utiliser une VM.

Le plus simple :

```text
Docker local
ou
Azure Container Apps / App Service for Containers
```

Une VM peut être envisagée si l’équipe veut tout gérer manuellement.

### 13.2 Architecture avec VM si nécessaire

```text
Internet
   ↓
Nginx reverse proxy
   ↓
Frontend Next.js container
      ↓
Backend FastAPI container
      ↓
Mosquitto MQTT container
      ↓
SQLite volume
```

Sur la VM, il faudra prévoir :

- Ubuntu Server ;
- Docker ;
- Docker Compose ;
- Nginx ;
- certificat HTTPS ;
- firewall ;
- ports 80 et 443 ouverts ;
- port SSH limité ;
- sauvegarde de la base SQLite.

### 13.3 Sécurité minimale

| Élément | Mesure |
|---|---|
| HTTPS | Obligatoire si déployé en ligne |
| API | CORS limité au frontend |
| Secrets | Variables dans `.env`, jamais dans Git |
| Docker | Pas de secrets dans les images |
| Backend | Ne pas exposer directement si possible |
| MQTT | Ne pas exposer publiquement le port 1883 en production sans authentification |
| SQLite | Sauvegardes régulières |
| Authentification | Optionnelle en V0, utile en V1 |
| Logs | Ne pas stocker de données personnelles inutiles |
| Azure | Managed Identity si services Azure utilisés |
| RGPD | Collecte minimale |

### 13.4 RGPD

La V0 ne doit pas collecter de données personnelles inutiles.

Données autorisées :

- localisation approximative de l’EHPAD ;
- données météo ;
- données agricoles ;
- données IoT techniques du potager ;
- prédictions ;
- historique technique.

Données à éviter :

- nom des résidents ;
- données médicales ;
- données personnelles du personnel ;
- informations sensibles sans utilité technique.

Phrase à intégrer :

> La V0 limite la collecte de données aux informations nécessaires à la prédiction. Aucune donnée médicale ou nominative sur les résidents n’est collectée.

---

## 14. Fonctionnement complet de la prédiction

```text
1. L’utilisateur ouvre le dashboard.
2. Il renseigne ou confirme la localisation de l’EHPAD.
3. Le frontend appelle l’API FastAPI.
4. Le backend récupère les données météo Open-Meteo.
5. Le backend calcule les variables utiles :
   - température minimale sur 7 jours ;
   - température moyenne sur 7 jours ;
   - pluie prévue ;
   - risque de gel.
6. Le backend ajoute les données agricoles et IoT :
   - type de sol ;
   - irrigation ;
   - humidité du sol ;
   - eau utilisée ;
   - culture.
7. Si le mode IoT est utilisé, les dernières valeurs MQTT sont récupérées depuis l’état live FastAPI.
8. Les données sont envoyées au modèle XGBoost.
9. Le modèle prédit : viable, attendre ou non_viable.
10. Le backend récupère le score de confiance.
11. Le backend génère une explication simple.
12. Le résultat est stocké dans SQLite.
13. Le dashboard affiche la recommandation.
```

---

## 15. Critères de réussite de la V0

| Critère | Objectif | État actuel |
|---|---|---|
| Dashboard fonctionnel | L’utilisateur peut lancer une prédiction | Fait |
| API fonctionnelle | `/predict` répond correctement | Fait |
| Modèle XGBoost intégré | Le modèle retourne une classe | Fait |
| Recommandation claire | `viable`, `attendre`, `non_viable` | Fait |
| Explication affichée | Le personnel comprend la recommandation | Fait |
| Historique disponible | Les prédictions sont sauvegardées | Fait |
| Données météo prises en compte | Température, pluie, gel | Fait avec Open-Meteo |
| IoT simulé | MQTT, capteurs simulés, live dashboard | Fait |
| WebSocket live | Affichage temps réel des données IoT | Fait côté code |
| Docker fonctionnel | Le projet se lance avec une commande | Configuré, runtime complet à valider |
| Dataset exploitable | Dataset synthétique réaliste enrichi météo | Partiel, non validé terrain |
| Sécurité minimale | `.env`, CORS, pas de données sensibles | Fait pour la V0 locale |

---

## 16. Risques techniques

| Risque | Impact | Solution |
|---|---|---|
| Dataset pas parfaitement adapté | Modèle moins fiable | Créer un dataset enrichi météo + règles tomate |
| Modèle trop complexe | Perte de temps | Garder XGBoost avec peu de variables au début |
| API météo indisponible | Prédiction impossible | Prévoir une saisie manuelle en secours |
| Trop de fonctionnalités | V0 non terminée | Se concentrer uniquement sur la tomate |
| IoT trop complexe | Retard projet | Garder Mosquitto + simulateurs simples, pas Azure IoT Hub en V0 |
| Docker non validé en runtime complet | Démo fragile | Tester `docker compose up --build` avant soutenance |
| MQTT exposé sans sécurité | Risque si déployé publiquement | Ne pas exposer 1883 sur Internet sans auth/TLS |
| Interface trop complexe | Personnel perdu | Dashboard simple avec peu d’actions |
| Mauvaise interprétation de l’IA | Manque de confiance | Afficher une explication claire |
| Données personnelles inutiles | Risque RGPD | Ne collecter aucune donnée nominative |

---

## 17. V0 vs évolutions futures

### 17.1 V0

```text
✅ Prédiction de plantation
- tomate uniquement
- modèle XGBoost Classifier avec features engineered
- dataset synthétique réaliste enrichi météo
- prédiction viable/attendre/non_viable
- explication claire et facteurs importants
- historique des prédictions sauvegardé (SQLite)

✅ Conseil d'arrosage intelligent
- endpoint /advice/watering
- réutilise les features ML (stress_hydrique, risque_secheresse)
- conseils contextuels (type sol, irrigation, météo)
- priorité (urgent/élevé/moyen/faible/aucun)
- quantité d'eau recommandée en L/m²
- timing et prochaine vérification

✅ Infrastructure
- météo Open-Meteo avec saisie manuelle en secours
- IoT simulé via MQTT / Mosquitto
- **simulateurs Python intelligents** (humidité sol / irrigation / eau) ✨
  - réagissent à la météo réelle (pluie du jour, température)
  - évaporation dynamique selon chaleur
  - irrigation contextuelle (compense si sol sec)
  - type de sol respecté (rétention argileux vs sableux)
  - bruit gaussien pour variabilité naturelle
- consumer MQTT FastAPI
- endpoint /iot/live et /garden/profile
- WebSocket /ws/iot pour données live
- dashboard Next.js simple et responsive
- FastAPI backend
- SQLite base de données
- Docker Compose local
```

### 17.2 V1 / évolutions

```text
🌱 Cultures
- plusieurs légumes (salades, courgettes, radis, etc.)
- adaptation des seuils ML par culture
- rotation des cultures

🤖 IoT physique
- vrais capteurs ESP32
- capteurs humidité sol / température / luminosité physiques
- Azure IoT Hub
- automatisation physique (vannes d’arrosage connectées)

💾 Base de données
- PostgreSQL (à la place de SQLite)
- historique des conseils d’arrosage sauvegardé
- table model_versions implémentée
- analytics et statistiques

🔐 Sécurité et utilisateurs
- authentification (comptes personnel EHPAD)
- rôles (administrateur / jardinier / consultation)
- logs d’activité

📱 Notifications
- alertes email ou notifications push
- rappels d’arrosage
- alertes gel ou sécheresse

📊 Prédictions avancées
- prédiction de rendement
- détection précoce de maladies (ML sur images)
- optimisation de l’eau (apprentissage historique)

🎨 Dashboard avancé
- graphiques d’évolution (humidité, température)
- calendrier de plantation et récolte
- vue multi-parcelles
```

---

## 18. Phrase de synthèse pour le dossier

La solution technique repose sur une architecture web simple et containerisée. Le frontend est développé avec Next.js et Tailwind CSS afin de proposer un dashboard clair au personnel de l’EHPAD. Le backend est développé avec FastAPI en Python, car il permet d’intégrer facilement une API, une base SQLite et un modèle d’intelligence artificielle.

La partie IA repose sur un modèle XGBoost Classifier. Ce modèle prédictif analyse plusieurs données agricoles et météo afin d’estimer si une plantation de tomates est viable, à attendre ou non viable. Pour la V0, le modèle est entraîné à partir d’un dataset synthétique réaliste enrichi avec des données météo. L’architecture IoT est simulée avec MQTT, Mosquitto et des capteurs Python afin de préparer une future connexion à de vrais ESP32.

Le projet est déployable avec Docker, ce qui facilite les tests, le lancement local et une future mise en production sur Azure. La solution limite les données collectées aux informations nécessaires à la prédiction, sans données personnelles ou médicales liées aux résidents.

---

## 19. Résumé court pour l’oral

Pour la V0, nous développons une application web qui aide un EHPAD à savoir si les conditions sont favorables pour planter des tomates. Le frontend est fait en Next.js avec Tailwind, le backend en FastAPI, et les prédictions sont stockées dans SQLite.

La partie IA utilise XGBoost, un modèle de classification prédictive. Il analyse des données comme la saison, la météo, le risque de gel, le type de sol, l’irrigation et l’humidité du sol. Le modèle prédit ensuite une classe : viable, attendre ou non viable.

La V0 inclut aussi une architecture IoT simulée : des capteurs Python publient l’humidité du sol, l’irrigation et l’eau utilisée via MQTT. FastAPI consomme ces messages, les expose au dashboard et peut lancer une prédiction avec météo réelle + données IoT simulées. Dans une version future, ces simulateurs pourront être remplacés par de vrais capteurs ESP32.
