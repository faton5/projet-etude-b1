# Cahier des charges technique — V0 Potager EHPAD tomate

## 1. Contexte du projet

Le projet consiste à créer une application web permettant d’aider un EHPAD rural ou semi-rural à gérer plus facilement un petit potager pédagogique, avec un premier focus sur la culture de tomates.

L’objectif n’est pas de rendre l’EHPAD autonome en alimentation. L’objectif est plutôt de proposer une aide simple au personnel pour savoir si les conditions sont favorables ou non pour planter des tomates, tout en gardant une activité agréable et compréhensible pour les résidents.

La V0 doit donc rester réaliste : une seule culture, peu d’écrans, une interface simple et une IA prédictive centrée sur une décision claire.

---

## 2. Objectif principal de la V0

La V0 doit permettre de prédire si le moment est favorable pour planter des tomates dans le potager de l’EHPAD.

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
- données IoT dans une version future.

À partir de ces données, le modèle prédictif doit retourner une recommandation simple :

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

---

## 3. Périmètre de la V0

### 3.1 Ce que la V0 doit faire

La V0 doit permettre de :

- afficher un dashboard simple ;
- lancer une prédiction de viabilité pour la tomate ;
- prendre en compte des données météo et agricoles ;
- utiliser un modèle XGBoost pour prédire une classe ;
- afficher une recommandation claire ;
- afficher une explication de la recommandation ;
- stocker l’historique des prédictions ;
- être lançable facilement avec Docker ;
- être déployable plus tard sur Azure.

### 3.2 Ce que la V0 ne fait pas encore

La V0 ne doit pas essayer de tout faire.

Elle ne gère pas encore :

- plusieurs légumes ;
- une vraie automatisation complète de l’arrosage ;
- une prédiction de rendement précise ;
- une reconnaissance d’image des maladies ;
- une connexion IoT obligatoire ;
- un système complexe de comptes utilisateurs ;
- une base de données lourde type PostgreSQL.

Ces éléments peuvent être prévus dans les évolutions futures.

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
| Conteneurisation | Docker / Docker Compose | Lancement simple du projet |
| Cloud | Azure étudiant | Hébergement possible |
| IoT futur | Azure IoT Hub ou API dédiée | Réception des données capteurs |

---

## 5. Architecture générale

```text
Utilisateur EHPAD
      ↓
Dashboard Next.js
      ↓
API FastAPI
      ↓
Récupération météo / saisie manuelle
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

Dans la V0, certaines valeurs peuvent être saisies manuellement si l’API météo n’est pas encore totalement intégrée.

---

## 7. Backend — FastAPI

### 7.1 Rôle du backend

Le backend est la partie centrale de l’application.

Il doit gérer :

- les routes API ;
- la récupération des données météo ;
- la préparation des données ;
- l’appel au modèle XGBoost ;
- la création d’une explication ;
- le stockage dans SQLite ;
- la récupération de l’historique.

### 7.2 Routes API nécessaires

| Route | Méthode | Rôle |
|---|---|---|
| `/health` | GET | Vérifier que l’API fonctionne |
| `/predict` | POST | Lancer une prédiction |
| `/history` | GET | Récupérer l’historique |
| `/history/{id}` | GET | Voir une prédiction précise |
| `/model/info` | GET | Voir les informations du modèle |
| `/weather` | GET | Récupérer la météo si API intégrée |

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

---

## 8. Partie IA prédictive — XGBoost

### 8.1 Objectif du modèle

Le modèle IA doit prédire la viabilité d’une plantation de tomates à partir de plusieurs données.

Il ne doit pas seulement appliquer une règle fixe comme :

```text
si température > 18 alors planter
```

Il doit apprendre à partir d’un dataset d’entraînement pour prédire une classe.

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

| Variable | Type | Source |
|---|---|---|
| culture | texte | fixe : tomate |
| saison | texte | date actuelle |
| type_sol | texte | formulaire / dataset |
| irrigation | texte | formulaire / dataset |
| humidite_sol | nombre | saisie ou capteur futur |
| temp_actuelle | nombre | météo ou capteur futur |
| temp_min_7j | nombre | API météo |
| temp_moyenne_7j | nombre | API météo |
| pluie_7j | booléen | API météo |
| risque_gel_7j | booléen | calcul backend |
| water_usage | nombre | dataset / estimation / capteur futur |

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
- des données IoT dans une version future.

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

Ces données peuvent venir d’Open-Meteo ou être simulées pour la V0.

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

---

## 10. IoT — Évolution future

### 10.1 Rôle de l’IoT

L’IoT n’est pas obligatoire dans la V0, mais il est important comme évolution.

Les capteurs permettront de récupérer des données réelles directement dans le potager de l’EHPAD.

### 10.2 Données IoT possibles

| Capteur | Donnée récupérée | Utilité |
|---|---|---|
| Capteur humidité sol | humidité du sol | Savoir si le sol est trop sec |
| Capteur température air | température réelle | Comparer météo et terrain |
| Capteur température sol | température du sol | Important pour plantation |
| Capteur luminosité | exposition solaire | Vérifier les conditions de croissance |
| Capteur niveau eau | consommation d’eau | Suivre l’arrosage |

### 10.3 Architecture IoT future

```text
Capteurs dans le potager
      ↓
Microcontrôleur type ESP32
      ↓
MQTT ou HTTP
      ↓
Azure IoT Hub ou API FastAPI
      ↓
Base de données
      ↓
Modèle XGBoost
      ↓
Dashboard
```

### 10.4 Intérêt pour le modèle

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

#### Table `model_versions`

| Champ | Type | Rôle |
|---|---|---|
| id | integer | Identifiant |
| version | text | Version du modèle |
| trained_at | datetime | Date d’entraînement |
| dataset_name | text | Dataset utilisé |
| accuracy | float | Score principal |
| notes | text | Commentaires |

---

## 12. Docker et déploiement

### 12.1 Conteneurs prévus

Le projet peut être lancé avec deux conteneurs :

```text
frontend
backend
```

Et un volume pour la base SQLite :

```text
sqlite_data
```

### 12.2 Exemple de `docker-compose.yml`

```yaml
services:
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
4. Le backend récupère ou reçoit les données météo.
5. Le backend calcule les variables utiles :
   - température minimale sur 7 jours ;
   - température moyenne sur 7 jours ;
   - pluie prévue ;
   - risque de gel.
6. Le backend ajoute les données agricoles :
   - type de sol ;
   - irrigation ;
   - humidité du sol ;
   - culture.
7. Les données sont envoyées au modèle XGBoost.
8. Le modèle prédit : viable, attendre ou non_viable.
9. Le backend récupère le score de confiance.
10. Le backend génère une explication simple.
11. Le résultat est stocké dans SQLite.
12. Le dashboard affiche la recommandation.
```

---

## 15. Critères de réussite de la V0

| Critère | Objectif |
|---|---|
| Dashboard fonctionnel | L’utilisateur peut lancer une prédiction |
| API fonctionnelle | `/predict` répond correctement |
| Modèle XGBoost intégré | Le modèle retourne une classe |
| Recommandation claire | `viable`, `attendre`, `non_viable` |
| Explication affichée | Le personnel comprend la recommandation |
| Historique disponible | Les prédictions sont sauvegardées |
| Docker fonctionnel | Le projet se lance avec une commande |
| Données météo prises en compte | Température, pluie, gel |
| Dataset exploitable | Dataset agricole enrichi météo |
| Sécurité minimale | `.env`, CORS, pas de données sensibles |

---

## 16. Risques techniques

| Risque | Impact | Solution |
|---|---|---|
| Dataset pas parfaitement adapté | Modèle moins fiable | Créer un dataset enrichi météo + règles tomate |
| Modèle trop complexe | Perte de temps | Garder XGBoost avec peu de variables au début |
| API météo indisponible | Prédiction impossible | Prévoir une saisie manuelle en secours |
| Trop de fonctionnalités | V0 non terminée | Se concentrer uniquement sur la tomate |
| IoT trop long à intégrer | Retard projet | Garder l’IoT en évolution future |
| Interface trop complexe | Personnel perdu | Dashboard simple avec peu d’actions |
| Mauvaise interprétation de l’IA | Manque de confiance | Afficher une explication claire |
| Données personnelles inutiles | Risque RGPD | Ne collecter aucune donnée nominative |

---

## 17. V0 vs évolutions futures

### 17.1 V0

```text
- tomate uniquement
- modèle XGBoost Classifier
- dataset agricole enrichi météo
- météo Open-Meteo ou saisie manuelle
- dashboard simple
- FastAPI
- SQLite
- Docker local
- historique des prédictions
```

### 17.2 V1 / évolutions

```text
- plusieurs légumes
- vraie connexion IoT
- capteurs humidité sol / température / luminosité
- Azure IoT Hub
- PostgreSQL
- authentification
- alertes email ou notifications
- conseil d’arrosage
- prédiction de rendement
- reconnaissance d’image des maladies
- dashboard avancé
```

---

## 18. Phrase de synthèse pour le dossier

La solution technique repose sur une architecture web simple et containerisée. Le frontend est développé avec Next.js et Tailwind CSS afin de proposer un dashboard clair au personnel de l’EHPAD. Le backend est développé avec FastAPI en Python, car il permet d’intégrer facilement une API, une base SQLite et un modèle d’intelligence artificielle.

La partie IA repose sur un modèle XGBoost Classifier. Ce modèle prédictif analyse plusieurs données agricoles et météo afin d’estimer si une plantation de tomates est viable, à attendre ou non viable. Pour la V0, le modèle est entraîné à partir d’un dataset agricole enrichi avec des données météo. Dans une version future, des capteurs IoT installés sur le site permettront d’ajouter des données plus précises comme l’humidité du sol, la température locale et la luminosité.

Le projet est déployable avec Docker, ce qui facilite les tests, le lancement local et une future mise en production sur Azure. La solution limite les données collectées aux informations nécessaires à la prédiction, sans données personnelles ou médicales liées aux résidents.

---

## 19. Résumé court pour l’oral

Pour la V0, nous développons une application web qui aide un EHPAD à savoir si les conditions sont favorables pour planter des tomates. Le frontend est fait en Next.js avec Tailwind, le backend en FastAPI, et les prédictions sont stockées dans SQLite.

La partie IA utilise XGBoost, un modèle de classification prédictive. Il analyse des données comme la saison, la météo, le risque de gel, le type de sol, l’irrigation et l’humidité du sol. Le modèle prédit ensuite une classe : viable, attendre ou non viable.

Dans une version future, des capteurs IoT pourront être ajoutés dans le potager pour récupérer des données réelles directement sur site. Cela permettra d’améliorer la précision des prédictions.
