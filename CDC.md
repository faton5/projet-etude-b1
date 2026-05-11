# Cahier des charges technique — V0 Potager EHPAD tomate

## 1. Objectif du projet

L’objectif de la V0 est de créer une application web simple permettant au personnel d’un EHPAD de savoir si les conditions sont favorables pour planter des tomates.

La solution doit analyser les conditions actuelles et les prévisions des prochains jours afin de donner une recommandation claire :

```text
Planter maintenant
Attendre quelques jours
Conditions défavorables
```

L’intérêt de l’IA prédictive est de ne pas seulement regarder la météo du jour. Par exemple, même s’il fait bon aujourd’hui, si un risque de gel est prévu dans deux jours, l’application doit recommander d’attendre.

## 2. Stack technique retenue

| Partie          | Technologie                         | Rôle                                              |
| --------------- | ----------------------------------- | ------------------------------------------------- |
| Frontend        | Next.js                             | Dashboard web                                     |
| Style           | Tailwind CSS                        | Interface propre et responsive                    |
| Backend         | FastAPI                             | API Python                                        |
| IA prédictive   | scikit-learn                        | Arbre de décision                                 |
| Modèle          | DecisionTreeClassifier              | Classification : planter / attendre / défavorable |
| Base de données | SQLite                              | Stockage léger pour la V0                         |
| Déploiement     | Docker / Docker Compose             | Lancement simple du front et du back              |
| Cloud           | Azure étudiant                      | Hébergement possible                              |
| Dataset         | Données météo + dataset semi-simulé | Entraînement du modèle                            |

## 3. Architecture générale

```text
Utilisateur EHPAD
      ↓
Dashboard Next.js
      ↓
API FastAPI
      ↓
Service météo / saisie manuelle
      ↓
Préparation des données
      ↓
Modèle IA arbre de décision
      ↓
SQLite
      ↓
Résultat affiché au dashboard
```

Le frontend ne fait pas la logique métier. Il sert surtout à afficher les informations et envoyer les données au backend.

Le backend contient la logique importante :

```text
- récupération ou saisie des données météo
- calcul des indicateurs utiles
- appel du modèle IA
- génération de l’explication
- sauvegarde de l’historique
```

## 4. Frontend — Dashboard Next.js

### 4.1 Pages nécessaires

| Page                | Rôle                                                 |
| ------------------- | ---------------------------------------------------- |
| Accueil / Dashboard | Vue principale avec la recommandation                |
| Nouvelle prédiction | Formulaire météo / localisation                      |
| Historique          | Liste des anciennes prédictions                      |
| Détails prédiction  | Explication complète d’une recommandation            |
| Paramètres          | Localisation de l’EHPAD, type de culture, mode météo |

Pour la V0, tu peux faire seulement :

```text
/dashboard
/predict
/history
```

### 4.2 Informations affichées sur le dashboard

Le dashboard doit afficher :

```text
- date de la prédiction
- localisation de l’EHPAD
- culture analysée : tomate
- température actuelle
- température minimale prévue sur 7 jours
- température moyenne prévue sur 7 jours
- risque de gel
- pluie prévue
- humidité du sol si disponible
- recommandation IA
- explication simple
```

Exemple d’affichage :

```text
Recommandation : Attendre quelques jours

Explication :
Même si la température actuelle est correcte, une température minimale de 3°C est prévue dans les prochains jours. Il vaut mieux attendre avant de planter les tomates.
```

### 4.3 Formulaire de prédiction

Le formulaire doit contenir :

| Champ                       | Type                 | Exemple |
| --------------------------- | -------------------- | ------- |
| Localisation                | texte ou coordonnées | Bruz    |
| Mois                        | nombre ou auto       | 5       |
| Température actuelle        | nombre               | 21°C    |
| Température min 7 jours     | nombre               | 8°C     |
| Température moyenne 7 jours | nombre               | 17°C    |
| Pluie prévue                | oui/non              | oui     |
| Risque de gel               | oui/non              | non     |
| Humidité du sol             | nombre optionnel     | 55 %    |

Pour la V0, si tu n’as pas encore l’API météo, tu peux faire une **saisie manuelle**. Ensuite, tu ajoutes l’automatisation météo.

### 4.4 KPI à afficher

Les KPI sont importants pour montrer que ton dashboard est utile.

| KPI                                      | Explication                                      |
| ---------------------------------------- | ------------------------------------------------ |
| Nombre de prédictions effectuées         | Montre l’utilisation de l’outil                  |
| Nombre de recommandations “planter”      | Nombre de moments favorables détectés            |
| Nombre de recommandations “attendre”     | Montre que l’outil évite les mauvaises décisions |
| Nombre de recommandations “défavorables” | Montre les risques météo détectés                |
| Température minimale prévue              | KPI important pour le risque de gel              |
| Risque de gel détecté                    | Oui / non                                        |
| Fiabilité estimée                        | Score ou confiance du modèle                     |
| Historique des décisions                 | Permet de suivre l’évolution                     |

Pour une V0, tu peux faire simple :

```text
Total prédictions : 14
Planter : 4
Attendre : 7
Défavorable : 3
Dernier risque de gel : oui
```

## 5. Backend — FastAPI

### 5.1 Rôle du backend

Le backend est le cerveau de l’application.

Il doit gérer :

```text
- les routes API
- la récupération des données
- le nettoyage des données
- le calcul des variables météo
- l’appel au modèle IA
- la création d’une explication
- le stockage dans SQLite
```

### 5.2 Routes API nécessaires

| Route           | Méthode | Rôle                                    |
| --------------- | ------- | --------------------------------------- |
| `/health`       | GET     | Vérifier que l’API fonctionne           |
| `/predict`      | POST    | Faire une prédiction                    |
| `/history`      | GET     | Récupérer l’historique                  |
| `/history/{id}` | GET     | Voir une prédiction précise             |
| `/model/info`   | GET     | Informations sur le modèle              |
| `/weather`      | GET     | Récupérer la météo si API météo ajoutée |

### 5.3 Exemple de payload `/predict`

```json
{
  "location": "Bruz",
  "mois": 5,
  "temp_aujourdhui": 21,
  "temp_min_7j": 4,
  "temp_moyenne_7j": 15,
  "pluie_7j": 1,
  "risque_gel_7j": 1,
  "humidite_sol": 55
}
```

### 5.4 Exemple de réponse API

```json
{
  "recommandation": "conditions_defavorables",
  "score_confiance": 0.91,
  "explication": "Même si la température est correcte aujourd’hui, un risque de gel est prévu dans les prochains jours. Il vaut mieux attendre avant de planter.",
  "kpi": {
    "temp_min_7j": 4,
    "risque_gel_7j": true,
    "fenetre_analyse": "7 jours"
  }
}
```

## 6. IA prédictive

### 6.1 Pourquoi une IA prédictive ?

L’IA prédictive est importante parce que la décision de planter dépend de plusieurs critères en même temps.

Sans IA, l’application serait juste un calendrier :

```text
Mai = bonne période = planter
```

Mais avec l’IA :

```text
Mai = bonne période
Température aujourd’hui = correcte
Mais gel prévu dans 2 jours
Donc ne pas planter
```

L’IA sert donc à prendre une décision plus réaliste.

### 6.2 Type de problème IA

Ton problème est un problème de **classification**.

Le modèle ne prédit pas une température ou un rendement.
Il prédit une catégorie :

```text
planter
attendre
conditions_defavorables
```

Le modèle conseillé est donc :

```text
DecisionTreeClassifier
```

C’est léger, explicable et suffisant pour une V0.

### 6.3 Variables d’entrée du modèle

| Variable        | Type     | Utilité                                        |
| --------------- | -------- | ---------------------------------------------- |
| mois            | int      | Vérifier la période de plantation              |
| temp_aujourdhui | float    | Conditions actuelles                           |
| temp_min_7j     | float    | Détecter le froid ou le gel                    |
| temp_moyenne_7j | float    | Vérifier la stabilité météo                    |
| pluie_7j        | bool/int | Savoir si la météo est trop humide             |
| risque_gel_7j   | bool/int | Bloquer la plantation si gel                   |
| humidite_sol    | float    | Vérifier si le sol est trop sec ou trop humide |

### 6.4 Sortie du modèle

| Sortie                    | Signification                                   |
| ------------------------- | ----------------------------------------------- |
| `planter`                 | Conditions favorables                           |
| `attendre`                | Conditions pas idéales mais pas catastrophiques |
| `conditions_defavorables` | Risque trop élevé                               |

### 6.5 Logique attendue

Même si c’est un modèle IA, tu dois garder une logique compréhensible.

Exemple :

```text
Si risque_gel_7j = oui
→ conditions défavorables

Sinon si température minimale 7j < 10°C
→ attendre

Sinon si mois entre mai et juin et température moyenne entre 18°C et 27°C
→ planter

Sinon si température trop haute et sol sec
→ attendre

Sinon
→ attendre
```

L’arbre de décision va apprendre ce genre de règles à partir du dataset.

## 7. Dataset

### 7.1 Ce qu’il faut chercher

Tu ne vas peut-être pas trouver un dataset parfait qui dit directement :

```text
dois-je planter des tomates aujourd’hui ?
```

Il faut plutôt chercher des datasets avec :

```text
- température
- pluie
- humidité
- sol
- rendement agricole
- tomate
- météo historique
- données de culture
```

Ensuite tu peux créer ta colonne cible toi-même :

```text
recommandation = planter / attendre / défavorable
```

### 7.2 Datasets possibles

Voici des pistes de datasets ou sources utiles.

| Nom / Source                                                     | Données intéressantes                                                        | Utilité pour ton projet                |
| ---------------------------------------------------------------- | ---------------------------------------------------------------------------- | -------------------------------------- |
| Open-Meteo Forecast API                                          | Prévisions météo, température, pluie                                         | Récupérer météo sur 7 jours            |
| Open-Meteo Historical Weather API                                | Données météo historiques depuis 1940, température, humidité, précipitations | Créer un dataset météo réaliste        |
| Open-Meteo Historical Forecast API                               | Anciennes prévisions météo archivées depuis 2022                             | Comparer prévisions et météo réelle    |
| Kaggle — Crop Yield dataset based on weather set                 | Crop, température, rainfall, humidity, sunlight, soil pH, nutriments         | Base utile pour rendement/culture      |
| Kaggle — Crop Recommendation Dataset                             | NPK, température, humidité, pH, rainfall, crop recommandé                    | Bon exemple de dataset agricole ML     |
| Figshare — Crop Recommendation dataset                           | Données pluie, climat, fertilisant                                           | Alternative académique                 |
| Kaggle — Tomato Greenhouse Environment, Growth & Disease         | Environnement de serre, croissance tomate, météo multi-années                | Plus proche de la tomate               |
| Mendeley — Crop Recommendation using Soil Properties and Weather | Sol, localisation, pH, nutriments, météo                                     | Données plus complètes sur sol + météo |

Open-Meteo est intéressant car il fournit une API météo gratuite/open-source pour un usage non commercial, sans clé API, et propose aussi des prévisions météo par localisation.  Son API historique permet d’accéder à des données météo passées, avec température, humidité relative, précipitations et autres variables utiles.

Pour les datasets agricoles, Kaggle propose par exemple un dataset de rendement basé sur la météo avec température, rainfall, humidity, sunlight, soil pH et nutriments.  Le Crop Recommendation Dataset contient aussi des variables classiques pour recommander une culture selon les conditions agro-climatiques.  Il existe également un dataset Kaggle sur les tomates en serre qui mélange environnement, croissance et maladies, mais il est plus orienté serre que potager extérieur.

### 7.3 Stratégie réaliste pour toi

Je te conseille cette méthode :

```text
1. Chercher un dataset météo/agricole proche.
2. Garder seulement les colonnes utiles.
3. Ajouter une colonne recommandation.
4. Générer des cas réalistes pour la tomate.
5. Entraîner l’arbre de décision.
6. Utiliser Open-Meteo pour la prédiction en temps réel.
```

Tu peux donc assumer un **dataset semi-simulé**.

C’est acceptable parce que ton objectif est une V0 démonstrative, pas un produit agricole certifié.

## 8. Base de données SQLite

### 8.1 Pourquoi SQLite ?

SQLite est suffisant pour la V0 parce que :

```text
- pas besoin d’installer un serveur de base de données
- facile à intégrer dans FastAPI
- parfait pour stocker un historique simple
- très léger
```

### 8.2 Tables recommandées

#### Table `predictions`

| Champ           | Type     | Rôle                 |
| --------------- | -------- | -------------------- |
| id              | integer  | Identifiant          |
| created_at      | datetime | Date de prédiction   |
| location        | text     | Localisation         |
| mois            | integer  | Mois                 |
| temp_aujourdhui | float    | Température actuelle |
| temp_min_7j     | float    | Température minimale |
| temp_moyenne_7j | float    | Température moyenne  |
| pluie_7j        | integer  | Pluie prévue         |
| risque_gel_7j   | integer  | Risque de gel        |
| humidite_sol    | float    | Humidité             |
| recommandation  | text     | Résultat IA          |
| explication     | text     | Explication affichée |
| score_confiance | float    | Confiance du modèle  |

#### Table `model_versions`

| Champ        | Type     | Rôle                |
| ------------ | -------- | ------------------- |
| id           | integer  | Identifiant         |
| version      | text     | Version du modèle   |
| trained_at   | datetime | Date d’entraînement |
| dataset_name | text     | Nom du dataset      |
| accuracy     | float    | Score du modèle     |

## 9. Réseau, déploiement et sécurité

### 9.1 Architecture recommandée pour la V0

Pour ton cas, je recommande de ne pas partir directement sur une VM.

Le plus propre :

```text
Frontend container
Backend container
SQLite volume
Reverse proxy optionnel
```

En local :

```text
Docker Compose
```

Sur Azure :

```text
Azure Container Apps
ou
Azure App Service for Containers
```

Azure Container Apps recommande notamment l’usage des identités managées pour accéder aux ressources Azure sans gérer manuellement des mots de passe ou clés.  Azure documente aussi la sécurisation réseau des Container Apps avec des réseaux virtuels, NSG et règles de trafic entrant/sortant.

### 9.2 Est-ce qu’il faut une VM ?

Pour la V0 : **non obligatoire**.

Une VM sert si tu veux tout gérer toi-même :

```text
- Linux
- Docker
- Nginx
- certificats SSL
- firewall
- mises à jour
- monitoring
```

Mais pour un projet étudiant, c’est plus lourd.

Tu peux quand même l’aborder dans le CDC comme **option d’évolution**.

### 9.3 Architecture avec VM si demandée

```text
Internet
   ↓
Nginx reverse proxy
   ↓
Frontend container Next.js
   ↓
Backend container FastAPI
   ↓
SQLite volume
```

Sur la VM, il faudrait :

```text
- Ubuntu Server
- Docker + Docker Compose
- Nginx
- Certbot pour HTTPS
- UFW firewall
- ports ouverts : 80 et 443 uniquement
- port 22 SSH limité
- fail2ban
- sauvegarde régulière de SQLite
```

### 9.4 Sécurité minimale

| Élément             | Mesure                                          |
| ------------------- | ----------------------------------------------- |
| HTTPS               | Obligatoire si déployé en ligne                 |
| API                 | CORS limité au domaine frontend                 |
| Variables sensibles | `.env`, jamais dans Git                         |
| Authentification    | Pas obligatoire en V0, mais recommandée ensuite |
| Logs                | Ne pas stocker de données personnelles inutiles |
| SQLite              | Sauvegarde régulière                            |
| Docker              | Images légères, pas de secrets dans l’image     |
| Réseau              | Backend non exposé directement si possible      |
| Azure               | Managed Identity si services Azure              |
| RGPD                | Limiter les données collectées                  |

### 9.5 RGPD

Ton app ne doit pas collecter de données personnelles inutiles.

Pour la V0, tu peux stocker :

```text
- localisation approximative de l’EHPAD
- données météo
- prédictions
```

Évite de stocker :

```text
- noms des résidents
- données médicales
- informations personnelles du personnel
```

Tu peux écrire :

> La V0 limite la collecte de données aux informations nécessaires à la prédiction : localisation approximative, météo, température et historique des recommandations. Aucune donnée médicale ou nominative sur les résidents n’est collectée.

## 10. Docker

### 10.1 Services Docker

Tu peux prévoir 2 containers :

```text
frontend
backend
```

Et un volume :

```text
sqlite_data
```

### 10.2 Exemple `docker-compose.yml`

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
    environment:
      - DATABASE_URL=sqlite:///app/data/database.db
      - MODEL_PATH=/app/model/decision_tree.pkl
```

## 11. Fonctionnement complet de la prédiction

```text
1. L’utilisateur ouvre le dashboard.
2. Il choisit la localisation de l’EHPAD.
3. Le frontend appelle le backend.
4. Le backend récupère la météo sur 7 jours ou utilise les données saisies.
5. Le backend calcule :
   - température minimale sur 7 jours
   - température moyenne sur 7 jours
   - pluie prévue
   - risque de gel
6. Le backend envoie ces variables au modèle IA.
7. Le modèle retourne :
   - planter
   - attendre
   - conditions défavorables
8. Le backend génère une explication simple.
9. Le résultat est stocké dans SQLite.
10. Le frontend affiche la recommandation.
```

## 12. Critères de réussite de la V0

| Critère                        | Objectif                                 |
| ------------------------------ | ---------------------------------------- |
| Le dashboard fonctionne        | L’utilisateur peut lancer une prédiction |
| Le backend répond              | API `/predict` opérationnelle            |
| Le modèle IA fonctionne        | Retourne une des 3 classes               |
| L’explication est claire       | Le personnel comprend pourquoi           |
| L’historique fonctionne        | Les anciennes prédictions sont visibles  |
| Docker fonctionne              | Projet lançable avec une commande        |
| Données météo prises en compte | Au minimum météo simulée ou saisie       |
| Risque de gel géré             | Si gel prévu, la plantation est bloquée  |

## 13. Version V0 vs évolution

### V0

```text
- tomate uniquement
- arbre de décision simple
- dataset maison ou semi-simulé
- SQLite
- dashboard simple
- météo saisie manuellement ou Open-Meteo
- Docker local
```

### Version future

```text
- plusieurs légumes
- vraie API météo automatique
- PostgreSQL
- authentification
- capteurs humidité/température
- alertes email
- recommandation d’arrosage
- dashboard plus complet
- hébergement cloud Azure
```

## 14. Phrase propre pour ton dossier

Tu peux mettre ça :

> La solution technique repose sur une architecture web simple et containerisée. Le frontend est développé avec Next.js et Tailwind CSS afin de proposer un dashboard clair au personnel de l’EHPAD. Le backend est développé avec FastAPI en Python, car il permet de créer facilement une API et d’intégrer un modèle d’intelligence artificielle.
>
> L’IA prédictive repose sur un arbre de décision entraîné avec un dataset météo et agronomique adapté à la culture de la tomate. Le modèle prend en compte la période de plantation, la température actuelle, les prévisions des prochains jours, la température minimale prévue, la pluie, l’humidité du sol et le risque de gel. Il retourne une recommandation simple : planter maintenant, attendre quelques jours ou conditions défavorables.
>
> Pour la V0, SQLite est utilisé comme base de données afin de stocker l’historique des prédictions. Le projet est déployable avec Docker, ce qui facilite les tests, le lancement local et une future mise en production sur Azure. La solution limite les données collectées afin de rester simple et conforme au RGPD.

Mon conseil : pour ton oral, ne dis pas “on va entraîner un gros modèle”. Dis plutôt : **“on fait une IA prédictive légère, explicable, basée sur un arbre de décision et des données météo sur 7 jours.”** Ça fait beaucoup plus sérieux et faisable.
