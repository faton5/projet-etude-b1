# Potager EHPAD - Tomate

Application V0 pour aider le personnel d'un EHPAD a evaluer si les conditions sont favorables pour planter des tomates.

La V0 cible un dashboard Next.js, une API FastAPI, un modele XGBoost de classification et un historique SQLite des predictions.

## Stack prevue

- Frontend : Next.js avec Tailwind CSS
- Backend : FastAPI
- IA : XGBoost, pandas, scikit-learn
- Base locale : SQLite
- Meteo : Open-Meteo
- Conteneurisation : Docker Compose

## Structure

```text
.
+-- backend/          # API FastAPI, logique de prediction, SQLite, modele
+-- frontend/         # Dashboard Next.js et pages utilisateur
+-- CDC.md           # Cahier des charges technique
+-- docker-compose.yml
+-- .env.example
+-- README.md
```

## Configuration

Creer un fichier `.env` local a partir de l'exemple :

```bash
cp .env.example .env
```

Le fichier `.env` reste local et ne doit pas etre commit.

## Lancement avec Docker

```bash
docker compose up --build
```

Services attendus :

- Frontend : http://localhost:3000
- Backend : http://localhost:8000
- Documentation API : http://localhost:8000/docs

Si ces ports sont deja utilises :

```bash
BACKEND_PORT=8001 FRONTEND_PORT=3001 \
NEXT_PUBLIC_API_URL=http://localhost:8001 \
CORS_ORIGINS=http://localhost:3001 \
docker compose up --build
```

Arreter les services :

```bash
docker compose down
```

## Lancement local sans Docker

Backend :

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend :

```bash
cd frontend
npm run dev
```

## Commandes utiles

```bash
docker compose up --build
docker compose down
cd backend && pytest
cd backend && .venv/bin/python scripts/train_model.py
cd frontend && npm test
```

## IA predictive

Le backend charge un modele XGBoost depuis `backend/models/xgboost_tomate.joblib`.
Le modele classe chaque demande en `viable`, `attendre` ou `non_viable`, puis l'API
ajoute une explication simple et les facteurs importants. Si le fichier modele est
absent, l'API repasse automatiquement sur les regles metier V0.

Pour recreer le modele :

```bash
cd backend
.venv/bin/python scripts/train_model.py
```

## Variables principales

Les variables disponibles sont documentees dans `.env.example`.

Les valeurs importantes pour la V0 sont :

- `NEXT_PUBLIC_API_URL` : URL publique du backend cote navigateur.
- `INTERNAL_API_URL` : URL interne du backend depuis le conteneur frontend.
- `POTAGER_DB_PATH` : fichier SQLite utilise par le backend actuel.
- `DATABASE_URL` : URL SQLite reservee aux integrations futures.
- `CORS_ORIGINS` : origines autorisees pour appeler l'API.
- `OPEN_METEO_BASE_URL` : endpoint Open-Meteo.

## Notes de contribution

- Ne pas committer `.env`, bases SQLite runtime, environnements virtuels, `node_modules`, builds ou artefacts de modele lourds.
- Garder le vocabulaire metier du cahier des charges : `prediction`, `weather`, `soil`, `recommendation`, `history`.
- Documenter toute nouvelle commande de build, test ou developpement dans ce README.
