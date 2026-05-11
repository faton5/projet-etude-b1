# Déploiement Azure — Potager EHPAD V0

Stack : **FastAPI + Next.js + SQLite** sur **Azure Container Apps**

---

## Vue d'ensemble

```
[ACR] potagerehpadacr.azurecr.io
  ├── potager-backend:v1   → Azure Container App (port 8000, external)
  └── potager-frontend:v1  → Azure Container App (port 3000, external)

[Environment] env-potager-ehpad
[Resource Group] rg-potager-ehpad
[Region] francecentral
```

---

## Prérequis

- [Azure CLI](https://learn.microsoft.com/fr-fr/cli/azure/install-azure-cli) installé
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installé
- Un abonnement Azure actif

```bash
az login
az extension add --name containerapp --upgrade
```

---

## 1. Développement local

```bash
# Copier les variables d'environnement
cp .env.example .env

# Démarrer les deux services avec hot-reload
docker compose up --build

# Frontend : http://localhost:3000
# Backend  : http://localhost:8000
# API docs : http://localhost:8000/docs
```

**Tester le build de production localement :**

```bash
docker compose -f docker-compose.prod.yml up --build
```

**Lancer les tests backend :**

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/
```

---

## 2. Créer les ressources Azure

> Remplacer `potagerehpadacr` par un nom **unique** (lettres minuscules + chiffres, sans tirets).

```bash
# Variables (à adapter)
ACR_NAME="potagerehpadacr"
RG="rg-potager-ehpad"
LOCATION="francecentral"
ENV_NAME="env-potager-ehpad"

# Groupe de ressources
az group create \
  --name $RG \
  --location $LOCATION

# Azure Container Registry
az acr create \
  --resource-group $RG \
  --name $ACR_NAME \
  --sku Basic \
  --admin-enabled true

# Environment Container Apps
az containerapp env create \
  --name $ENV_NAME \
  --resource-group $RG \
  --location $LOCATION
```

---

## 3. Build & Push des images

```bash
ACR_NAME="potagerehpadacr"

# Connexion au registry
az acr login --name $ACR_NAME

# ── Backend ──────────────────────────────────────────────────────────────────
docker build \
  -t $ACR_NAME.azurecr.io/potager-backend:v1 \
  ./backend

docker push $ACR_NAME.azurecr.io/potager-backend:v1

# ── Frontend (NEXT_PUBLIC_API_URL sera mis à jour après déploiement backend) ─
# Pour l'instant on pousse avec localhost, on rebuildera après
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://localhost:8000 \
  -t $ACR_NAME.azurecr.io/potager-frontend:v1 \
  ./frontend

docker push $ACR_NAME.azurecr.io/potager-frontend:v1
```

---

## 4. Déployer le backend

```bash
ACR_NAME="potagerehpadacr"
RG="rg-potager-ehpad"
ENV_NAME="env-potager-ehpad"

# Récupérer les credentials ACR
ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az containerapp create \
  --name potager-backend \
  --resource-group $RG \
  --environment $ENV_NAME \
  --image $ACR_NAME.azurecr.io/potager-backend:v1 \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 8000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --env-vars \
    APP_ENV=production \
    POTAGER_DB_PATH=/data/potager.db \
    MODEL_PATH=/app/models/xgboost_tomate.joblib \
    CORS_ORIGINS=http://localhost:3000

# Récupérer l'URL du backend
BACKEND_URL=$(az containerapp show \
  --name potager-backend \
  --resource-group $RG \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

echo "Backend URL : https://$BACKEND_URL"
echo "Health check : https://$BACKEND_URL/health"
```

---

## 5. Déployer le frontend

Maintenant qu'on connaît l'URL du backend, on rebuild le frontend avec la vraie URL.

```bash
ACR_NAME="potagerehpadacr"
RG="rg-potager-ehpad"
ENV_NAME="env-potager-ehpad"

# BACKEND_URL = valeur obtenue à l'étape 4
BACKEND_URL="<FQDN_DU_BACKEND>"  # ex: potager-backend.xxx.francecentral.azurecontainerapps.io

# Rebuild frontend avec la vraie URL backend
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://$BACKEND_URL \
  -t $ACR_NAME.azurecr.io/potager-frontend:v1 \
  ./frontend

docker push $ACR_NAME.azurecr.io/potager-frontend:v1

ACR_PASSWORD=$(az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv)

az containerapp create \
  --name potager-frontend \
  --resource-group $RG \
  --environment $ENV_NAME \
  --image $ACR_NAME.azurecr.io/potager-frontend:v1 \
  --registry-server $ACR_NAME.azurecr.io \
  --registry-username $ACR_NAME \
  --registry-password $ACR_PASSWORD \
  --target-port 3000 \
  --ingress external \
  --min-replicas 0 \
  --max-replicas 1 \
  --cpu 0.25 \
  --memory 0.5Gi \
  --env-vars \
    NODE_ENV=production \
    INTERNAL_API_URL=https://$BACKEND_URL

# Récupérer l'URL du frontend
FRONTEND_URL=$(az containerapp show \
  --name potager-frontend \
  --resource-group $RG \
  --query "properties.configuration.ingress.fqdn" \
  -o tsv)

echo "Frontend URL : https://$FRONTEND_URL"
```

---

## 6. Mettre à jour le CORS du backend

Une fois le frontend déployé, mettre à jour CORS_ORIGINS sur le backend.

```bash
RG="rg-potager-ehpad"
FRONTEND_URL="<FQDN_DU_FRONTEND>"  # ex: potager-frontend.xxx.francecentral.azurecontainerapps.io

az containerapp update \
  --name potager-backend \
  --resource-group $RG \
  --set-env-vars \
    CORS_ORIGINS=https://$FRONTEND_URL
```

---

## 7. Mise à jour (redéployer une nouvelle version)

```bash
ACR_NAME="potagerehpadacr"
RG="rg-potager-ehpad"
BACKEND_URL="<FQDN_DU_BACKEND>"

# ── Mettre à jour le backend ─────────────────────────────────────────────────
docker build -t $ACR_NAME.azurecr.io/potager-backend:v2 ./backend
docker push $ACR_NAME.azurecr.io/potager-backend:v2

az containerapp update \
  --name potager-backend \
  --resource-group $RG \
  --image $ACR_NAME.azurecr.io/potager-backend:v2

# ── Mettre à jour le frontend ────────────────────────────────────────────────
docker build \
  --build-arg NEXT_PUBLIC_API_URL=https://$BACKEND_URL \
  -t $ACR_NAME.azurecr.io/potager-frontend:v2 \
  ./frontend
docker push $ACR_NAME.azurecr.io/potager-frontend:v2

az containerapp update \
  --name potager-frontend \
  --resource-group $RG \
  --image $ACR_NAME.azurecr.io/potager-frontend:v2
```

---

## 8. Persistance SQLite (optionnel)

> Par défaut, les données SQLite sont perdues si le container redémarre.
> Pour la V0 / demo, c'est acceptable. Pour persister les données, utiliser Azure Files.

```bash
ACR_NAME="potagerehpadacr"
RG="rg-potager-ehpad"
ENV_NAME="env-potager-ehpad"
STORAGE_ACCOUNT="potagerehpadstorage"

# Créer le storage account
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RG \
  --location francecentral \
  --sku Standard_LRS

# Créer le file share
az storage share create \
  --name potager-data \
  --account-name $STORAGE_ACCOUNT

# Récupérer la clé
STORAGE_KEY=$(az storage account keys list \
  --resource-group $RG \
  --account-name $STORAGE_ACCOUNT \
  --query "[0].value" -o tsv)

# Lier le storage à l'environment Container Apps
az containerapp env storage set \
  --name $ENV_NAME \
  --resource-group $RG \
  --storage-name potager-data \
  --azure-file-account-name $STORAGE_ACCOUNT \
  --azure-file-account-key $STORAGE_KEY \
  --azure-file-share-name potager-data \
  --access-mode ReadWrite
```

---

## 9. Commandes utiles

```bash
RG="rg-potager-ehpad"

# Voir les logs du backend en temps réel
az containerapp logs show \
  --name potager-backend \
  --resource-group $RG \
  --follow

# Voir les logs du frontend
az containerapp logs show \
  --name potager-frontend \
  --resource-group $RG \
  --follow

# Vérifier le statut des replicas
az containerapp replica list \
  --name potager-backend \
  --resource-group $RG

# Lister toutes les container apps
az containerapp list --resource-group $RG -o table

# Supprimer toutes les ressources (attention !)
az group delete --name $RG --yes
```

---

## 10. CI/CD — GitHub Actions

Le workflow `.github/workflows/deploy.yml` automatise le pipeline complet :
`push to main` → tests → build + push ACR → deploy Container Apps

### Architecture de l'authentification

```
GitHub Actions runner
  ├── OIDC token (id-token: write)
  │     └── azure/login@v2  ──→  Managed Identity (potager-ehpad-identity)
  │                                └── Contributor sur rg-potager-ehpad
  └── ACR admin creds
        └── docker/login-action  ──→  potagerehpadacr.azurecr.io
```

### Secrets à configurer dans GitHub

Aller sur : `https://github.com/faton5/projet-etude-b1/settings/secrets/actions`

| Secret | Commande pour obtenir la valeur |
|--------|---------------------------------|
| `AZURE_CLIENT_ID` | `az identity show --name potager-ehpad-identity --resource-group rg-potager-ehpad --query clientId -o tsv` |
| `AZURE_TENANT_ID` | `az account show --query tenantId -o tsv` |
| `AZURE_SUBSCRIPTION_ID` | `az account show --query id -o tsv` |
| `ACR_USERNAME` | `az acr credential show --name potagerehpadacr --query username -o tsv` |
| `ACR_PASSWORD` | `az acr credential show --name potagerehpadacr --query "passwords[0].value" -o tsv` |

### Pipeline

```
push main
  │
  ├─ job: test
  │    └── pytest backend/tests/
  │
  └─ job: deploy  (si tests OK)
       ├── Azure Login (OIDC, sans mot de passe Azure)
       ├── Docker Login ACR
       ├── build + push backend → potagerehpadacr.azurecr.io/potager-backend:<sha>
       ├── az containerapp create|update  (backend)
       ├── Récupérer FQDN backend
       ├── build + push frontend (NEXT_PUBLIC_API_URL=https://<fqdn-backend>)
       ├── az containerapp create|update  (frontend)
       └── az containerapp update CORS backend
```

### Déclencher manuellement

Aller sur : `https://github.com/faton5/projet-etude-b1/actions` → workflow "CI/CD — Potager EHPAD" → "Run workflow"

---

## Résumé des URLs

| Service | Local | Azure |
|---------|-------|-------|
| Frontend | http://localhost:3000 | https://potager-frontend.xxx.francecentral.azurecontainerapps.io |
| Backend | http://localhost:8000 | https://potager-backend.xxx.francecentral.azurecontainerapps.io |
| API Docs | http://localhost:8000/docs | https://potager-backend.xxx.../docs |
| Health | http://localhost:8000/health | https://potager-backend.xxx.../health |
