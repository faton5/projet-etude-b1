# 🍅 Potager EHPAD - Tomate V0

Application intelligente pour aider le personnel d'un EHPAD à :
1. **Savoir quand planter des tomates** (prédiction ML viable/attendre/non_viable)
2. **Gérer l'arrosage efficacement** (conseils contextuels basés sur ML)

La V0 combine un dashboard Next.js, une API FastAPI, un modèle XGBoost avec features engineered, SQLite, Open-Meteo et une architecture IoT simulée avec MQTT/Mosquitto.

📚 **[Documentation complète](./docs/)** | 📋 **[Cahier des charges](./CDC.md)**

## Architecture

```text
Dashboard Next.js
  -> API FastAPI
  -> Open-Meteo
  -> XGBoost
  -> SQLite

Capteurs Python simules
  -> MQTT Mosquitto
  -> FastAPI MQTT consumer
  -> WebSocket /ws/iot
  -> Dashboard live
```

## Stack

- Frontend : Next.js, Tailwind CSS, lucide-react
- Backend : FastAPI, Pydantic, paho-mqtt
- IA : XGBoost, scikit-learn, pandas
- Base : SQLite
- Meteo : Open-Meteo
- IoT V0 : Mosquitto + simulateurs Python
- Deploiement : Docker Compose, Azure VM ou Azure Container Apps plus tard

## Structure

```text
📁 projet-etude-/
├── 📁 backend/
│   ├── 📁 app/
│   │   ├── main.py              # API FastAPI (routes)
│   │   ├── ml_model.py          # XGBoost + features ML
│   │   ├── recommendation.py    # Prédiction plantation
│   │   ├── watering_advice.py   # Conseil arrosage (nouveau ✨)
│   │   ├── weather.py           # Open-Meteo
│   │   ├── mqtt_consumer.py     # Consumer MQTT
│   │   ├── database.py          # SQLite
│   │   ├── schemas.py           # Pydantic models
│   │   └── ...
│   ├── 📁 iot_simulator/        # Capteurs Python simulés
│   ├── 📁 models/               # Modèle XGBoost
│   ├── 📁 scripts/              # Entraînement modèle
│   └── 📁 tests/                # Tests backend
├── 📁 frontend/
│   ├── 📁 app/                  # Pages Next.js
│   ├── 📁 components/           # Composants UI
│   └── 📁 lib/                  # Client API
├── 📁 mosquitto/                # Config broker MQTT
├── 📁 docs/                     # Documentation technique
│   ├── README.md                # Index documentation
│   ├── AUDIT_WATERING_SYSTEM.md # Audit système arrosage
│   ├── DEPLOYMENT.md            # Guide déploiement
│   └── ...
├── 📄 CDC.md                    # Cahier des charges
├── 📄 README.md                 # Ce fichier
├── 📄 docker-compose.yml        # Orchestration Docker
└── 📄 .env.example              # Variables d'environnement
```

## Configuration

```bash
cp .env.example .env
```

Variables importantes :

- `DEMO_MODE=true` : garde des donnees affichables meme sans MQTT ou Internet.
- `NEXT_PUBLIC_API_URL=http://localhost:8000`
- `INTERNAL_API_URL=http://backend:8000`
- `POTAGER_DB_PATH=/data/potager.db`
- `CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000`
- `OPEN_METEO_BASE_URL=https://api.open-meteo.com/v1/forecast`
- `OPEN_METEO_GEOCODING_URL=https://geocoding-api.open-meteo.com/v1/search`
- `MQTT_HOST=mqtt`
- `MQTT_PORT=1883`
- `MQTT_TOPIC_ROOT=farm/tomato`

## Lancement Docker

Demarrer toute la V0 :

```bash
docker compose up --build
```

Services :

- Frontend : http://localhost:3000
- Backend : http://localhost:8000
- Docs API : http://localhost:8000/docs
- MQTT local : `127.0.0.1:1883`

Arreter :

```bash
docker compose down
```

Remettre a zero les volumes locaux :

```bash
docker compose down -v
```

## Lancement local

Backend :

```bash
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Frontend :

```bash
cd frontend
npm ci
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Simulateurs IoT, avec un broker MQTT deja lance :

```bash
cd backend
.\.venv\Scripts\python.exe -m iot_simulator.run_all
```

Capteurs separes :

```bash
.\.venv\Scripts\python.exe -m iot_simulator.soil_sensor
.\.venv\Scripts\python.exe -m iot_simulator.irrigation_sensor
.\.venv\Scripts\python.exe -m iot_simulator.water_usage_sensor
```

## Mode demo

`DEMO_MODE=true` permet de presenter le projet meme si :

- Open-Meteo est indisponible ;
- Mosquitto n'est pas lance ;
- aucun message MQTT n'a encore ete recu.

Le backend genere alors des donnees meteo et IoT de secours. Ce mode ne remplace pas le flux MQTT reel, il evite seulement une demo vide.

## MQTT

Topics :

- `farm/tomato/soil`
- `farm/tomato/irrigation`
- `farm/tomato/water_usage`

Ecouter les messages :

```bash
mosquitto_sub -h localhost -p 1883 -t "farm/tomato/#" -v
```

Publier un message de test :

```bash
mosquitto_pub -h localhost -p 1883 -t "farm/tomato/soil" -m "{\"sensor_id\":\"soil_sensor_1\",\"farm_id\":\"farm_1\",\"humidity\":43.2,\"timestamp\":\"2026-05-11T18:00:00Z\"}"
```

Le port MQTT est expose seulement sur `127.0.0.1` dans Docker Compose. En production, ne pas exposer `1883` publiquement sans authentification/TLS.

## Endpoints API

### Prédiction de plantation
- `POST /predict` : prédiction de viabilité de plantation (viable/attendre/non_viable)
- `POST /predict/iot` : prédiction avec météo + dernières données MQTT automatiques
- `GET /history` : historique des prédictions de plantation
- `GET /history/{id}` : détail d'une prédiction

### Conseil d'arrosage (nouveau ✨)
- `POST /advice/watering` : conseil d'arrosage intelligent basé sur features ML
  - Entrée : localisation, type sol, irrigation, humidité sol (optionnelle)
  - Sortie : conseil, priorité, explication, action recommandée, scores ML
  - Auto-complétion avec météo et IoT si données manquantes

### Données et monitoring
- `GET /health` : statut API, MQTT, modèle, SQLite, WebSocket
- `GET /weather` : météo Open-Meteo ou fallback demo
- `GET /iot/live` : dernières données IoT reçues
- `WS /ws/iot` : flux IoT live (WebSocket)
- `GET /model/info` : version et métriques du modèle XGBoost

### Configuration potager
- `GET /garden/profile` : profil du potager (localisation, sol, irrigation)
- `PUT /garden/profile` : mise à jour du profil

## Tests et verification

Backend :

```bash
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend :

```bash
cd frontend
npm test
npm run build
```

Docker :

```bash
docker compose config
docker compose up --build
```

## Azure

Option simple pour une soutenance ou une V0 :

- Azure VM Ubuntu + Docker Compose.
- Ports publics : 80/443 via reverse proxy.
- Ne pas exposer MQTT publiquement.
- SQLite sur volume persistant.

Commandes utiles sur VM :

```bash
docker compose pull
docker compose up -d --build
docker compose logs -f backend
docker compose ps
```

## Limites V0

- Le modele est entraine sur donnees synthetiques realistes, pas sur donnees terrain validees.
- Les capteurs sont simules ; de vrais ESP32 pourront publier les memes payloads MQTT plus tard.
- Pas de comptes utilisateurs, PostgreSQL, Kubernetes ou Azure IoT Hub en V0.
