# Audit des Conteneurs Azure - Performances et Configuration

**Date:** 12 mai 2026  
**Projet:** Potager EHPAD  
**Environnement:** Azure Container Apps

---

## 📋 Résumé Exécutif

### Statut Global: ⚠️ AMÉLIORATIONS NÉCESSAIRES

| Aspect | Statut | Priorité |
|--------|--------|----------|
| Allocation Ressources | 🟡 Sous-dimensionné | HAUTE |
| Scalabilité | 🟠 Problématique | HAUTE |
| Résilience | 🟡 À améliorer | MOYENNE |
| Optimisation Images | 🟢 Correct | BASSE |
| Monitoring | 🔴 Absent | HAUTE |
| Coûts | 🟢 Optimisés | - |

---

## 🎯 Problèmes Critiques Identifiés

### 1. **CRITIQUE: Scale-to-Zero Inadapté à l'Usage**

**Fichier:** `.github/workflows/deploy.yml:112-113` et `:172-173`

```yaml
--min-replicas 0 \
--max-replicas 1 \
```

#### ⚠️ Problèmes:
- **Cold Start:** Première requête peut prendre 10-30 secondes (démarrage container)
- **Perte de données:** Si backend scale à 0, la base SQLite en mémoire est perdue
- **Expérience utilisateur:** Inacceptable pour une application EHPAD (données temps réel)
- **ML Model:** Le modèle XGBoost doit être rechargé à chaque cold start (~2-5s)

#### 💡 Recommandation:
```yaml
# Backend (contient DB et modèle ML)
--min-replicas 1 \
--max-replicas 3 \

# Frontend (stateless)
--min-replicas 1 \
--max-replicas 2 \
```

#### 💰 Impact Coût:
- **Actuel:** ~0€/mois (échelle à zéro)
- **Recommandé:** ~15-25€/mois (1 instance permanente)
- **Justification:** Application de santé nécessite disponibilité 24/7

---

### 2. **HAUTE: Ressources Backend Insuffisantes**

**Fichier:** `.github/workflows/deploy.yml:114-115`

```yaml
--cpu 0.5 \
--memory 1.0Gi \
```

#### 📊 Analyse des Besoins Réels:

| Composant | Mémoire Estimée | Justification |
|-----------|-----------------|---------------|
| FastAPI + Uvicorn | ~100 MB | Runtime Python |
| XGBoost Model | ~50-200 MB | Modèle chargé en RAM |
| Pandas DataFrame | ~50-100 MB | Traitement données |
| SQLite DB | ~10-50 MB | Base locale |
| Overhead Python | ~100 MB | Interpréteur + libs |
| **TOTAL** | **~400-500 MB** | **Usage nominal** |
| **Pic** | **~700-800 MB** | **Requêtes multiples** |

#### ⚠️ Risques Actuels:
- **OOM Kill:** Container tué si dépassement 1 GB
- **Swap:** Performances dégradées si mémoire saturée
- **Garbage Collection:** Temps de pause GC Python augmenté

#### 💡 Recommandation:
```yaml
# Backend
--cpu 1.0 \         # Double le CPU pour ML inference
--memory 2.0Gi \    # Marge confortable pour pics
```

**Justification CPU:**
- XGBoost utilise multi-threading (peut utiliser >0.5 CPU)
- Prédictions ML peuvent être CPU-intensives
- Concurrent requests nécessitent plus de CPU

---

### 3. **MOYENNE: Ressources Frontend Limites**

**Fichier:** `.github/workflows/deploy.yml:174-175`

```yaml
--cpu 0.25 \
--memory 0.5Gi \
```

#### 📊 Analyse:

| Métrique | Actuel | Recommandé | Raison |
|----------|--------|------------|--------|
| CPU | 0.25 | 0.5 | Next.js SSR + concurrent users |
| Memory | 0.5Gi | 1.0Gi | Node.js heap + cache Next.js |

#### ⚠️ Problèmes:
- **Node.js:** Heap par défaut ~512 MB (limite atteinte rapidement)
- **Next.js Standalone:** ~200-300 MB minimum
- **SSR:** Server-side rendering consomme CPU/RAM
- **Concurrent Users:** 10+ utilisateurs simultanés = risque saturation

#### 💡 Recommandation:
```yaml
# Frontend
--cpu 0.5 \
--memory 1.0Gi \
```

---

### 4. **HAUTE: Absence de Monitoring et Health Checks**

#### ⚠️ Manques Critiques:

##### A. Logs et Métriques
```yaml
# MANQUANT dans deploy.yml
--enable-app-insights \
--app-insights-key ${{ secrets.APPINSIGHTS_KEY }} \
```

##### B. Alerting
Aucune configuration d'alertes:
- ❌ CPU > 80%
- ❌ Memory > 80%
- ❌ Health check failures
- ❌ Latence > 2s
- ❌ Error rate > 5%

##### C. Probes Kubernetes
```yaml
# Actuellement : healthcheck basique seulement
# MANQUANT : liveness + readiness probes
```

#### 💡 Recommandation:
Ajouter dans la config Azure Container Apps:

```yaml
# Liveness probe (redémarre si échec)
--liveness-probe-type http \
--liveness-probe-path /health \
--liveness-probe-interval 30 \
--liveness-probe-timeout 5 \

# Readiness probe (retire du load balancer si échec)
--readiness-probe-type http \
--readiness-probe-path /health/ready \
--readiness-probe-interval 10 \
--readiness-probe-timeout 3 \
```

---

## 🔍 Analyse Détaillée par Service

### Backend (FastAPI)

#### Configuration Actuelle:
```yaml
CPU: 0.5 cores
Memory: 1.0 Gi
Replicas: 0-1
Port: 8000
Ingress: external
```

#### Dépendances Lourdes:
```python
# requirements.txt
pandas==2.2.3          # ~100 MB
scikit-learn==1.6.0    # ~50 MB
xgboost==2.1.3         # ~50 MB
uvicorn[standard]      # ~20 MB (avec watchfiles, websockets)
```

#### Dockerfile - Points Positifs ✅:
```dockerfile
FROM python:3.12-slim  # ✅ Image slim (réduit taille)
ENV PYTHONUNBUFFERED=1 # ✅ Logs temps réel
--no-cache-dir         # ✅ Pas de cache pip
HEALTHCHECK            # ✅ Health check natif Docker
```

#### Dockerfile - Améliorations Possibles 🔧:
```dockerfile
# ACTUEL: Une seule étape
FROM python:3.12-slim
# ...

# RECOMMANDÉ: Multi-stage build
FROM python:3.12-slim AS builder
RUN pip install --user -r requirements.txt

FROM python:3.12-slim
COPY --from=builder /root/.local /root/.local
# Réduit taille image finale de ~20%
```

#### Performance Tuning Recommandé:
```yaml
# Environnement variables à ajouter
--set-env-vars \
  UVICORN_WORKERS=2 \              # Multi-worker (utilise CPU)
  UVICORN_LIMIT_CONCURRENCY=50 \   # Limite connexions simultanées
  UVICORN_TIMEOUT_KEEP_ALIVE=30 \  # Garde connexions ouvertes
  PYTHONOPTIMIZE=2 \               # Optimisations Python
  MODEL_PRELOAD=true               # Précharge modèle ML au démarrage
```

---

### Frontend (Next.js)

#### Configuration Actuelle:
```yaml
CPU: 0.25 cores
Memory: 0.5 Gi
Replicas: 0-1
Port: 3000
Ingress: external
```

#### Dockerfile - Points Positifs ✅:
```dockerfile
# ✅ Multi-stage build optimal (4 stages)
FROM node:22-alpine AS deps
FROM node:22-alpine AS builder
FROM node:22-alpine AS runner

# ✅ Next.js standalone output (image légère)
COPY --from=builder /app/.next/standalone ./

# ✅ User non-root (sécurité)
USER nextjs

# ✅ NEXT_TELEMETRY_DISABLED (réduit overhead)
```

#### Dockerfile - Améliorations Possibles 🔧:
```dockerfile
# ACTUEL
ENV NODE_ENV=production

# RECOMMANDÉ: Ajouter tuning Node.js
ENV NODE_ENV=production \
    NODE_OPTIONS="--max-old-space-size=768" \  # Limite heap à 768MB
    NEXT_SHARP_PATH=/app/node_modules/sharp    # Optimise images
```

#### Performance Tuning Recommandé:
```yaml
# Variables environnement à ajouter
--set-env-vars \
  NODE_OPTIONS="--max-old-space-size=768" \
  NEXT_SHARP_PATH=/app/node_modules/sharp \
  PORT=3000
```

---

## 🏗️ Architecture et Résilience

### Problèmes Identifiés:

#### 1. **Stockage Non-Persistant**
```yaml
# docker-compose.prod.yml
volumes:
  backend_data:  # Volume local
```

**⚠️ Problème:** Sur Azure Container Apps, ce volume est éphémère !

**Impact:**
- ❌ Données perdues à chaque redéploiement
- ❌ Perte de données si container redémarre
- ❌ Impossible de scale horizontalement (DB SQLite locale)

**💡 Solution:**
```bash
# Option 1: Azure Files (stockage persistant)
az storage share create --name potager-data

# Option 2: Azure SQL Database (recommandé pour prod)
az sql db create --name potager-db \
  --tier Basic  # ~5€/mois
```

#### 2. **Single Point of Failure**
```yaml
max-replicas: 1  # Une seule instance
```

**⚠️ Risques:**
- Downtime pendant les déploiements
- Pas de load balancing
- Pas de failover automatique

**💡 Solution:**
```yaml
--min-replicas 2 \
--max-replicas 5 \
--scale-rule-type http \
--scale-rule-http-concurrency 50  # Scale si >50 req/instance
```

---

## 📊 Recommandations par Priorité

### 🔴 PRIORITÉ 1 - Critique (À faire immédiatement)

#### 1.1 Augmenter min-replicas à 1
```bash
# Backend
az containerapp update \
  --name potager-backend \
  --resource-group rg-potager-ehpad \
  --min-replicas 1 \
  --max-replicas 3

# Frontend
az containerapp update \
  --name potager-frontend \
  --resource-group rg-potager-ehpad \
  --min-replicas 1 \
  --max-replicas 2
```

**Impact:**
- ✅ Élimine cold starts
- ✅ Disponibilité 24/7
- 💰 Coût: +20€/mois

#### 1.2 Augmenter ressources backend
```bash
az containerapp update \
  --name potager-backend \
  --resource-group rg-potager-ehpad \
  --cpu 1.0 \
  --memory 2.0Gi
```

**Impact:**
- ✅ Évite OOM kills
- ✅ Meilleures performances ML
- 💰 Coût: +10€/mois

#### 1.3 Mettre en place stockage persistant
```bash
# Créer Azure Files share
az storage share create \
  --name potager-data \
  --quota 10  # 10 GB

# Monter dans container app
az containerapp update \
  --name potager-backend \
  --resource-group rg-potager-ehpad \
  --azure-file-volume-name data \
  --azure-file-volume-account-name <storage-account> \
  --azure-file-volume-account-key <key> \
  --azure-file-volume-share-name potager-data \
  --azure-file-volume-mount-path /data
```

**Impact:**
- ✅ Données persistantes
- ✅ Survit aux redéploiements
- 💰 Coût: +1€/mois (10 GB)

---

### 🟡 PRIORITÉ 2 - Importante (Semaine 1)

#### 2.1 Ajouter Application Insights
```bash
# Créer Application Insights
az monitor app-insights component create \
  --app potager-monitoring \
  --location westeurope \
  --resource-group rg-potager-ehpad

# Lier aux container apps
az containerapp update \
  --name potager-backend \
  --enable-app-insights \
  --app-insights-key <instrumentation-key>
```

**Métriques collectées:**
- Requêtes/sec
- Latence (p50, p95, p99)
- Taux d'erreurs
- CPU/Memory usage
- Custom metrics (prédictions ML, etc.)

**💰 Coût:** ~5-10€/mois (1 GB data/mois)

#### 2.2 Configurer Alertes
```bash
# Alerte CPU > 80%
az monitor metrics alert create \
  --name potager-high-cpu \
  --resource potager-backend \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --action-group <email-group>

# Alerte Memory > 80%
az monitor metrics alert create \
  --name potager-high-memory \
  --resource potager-backend \
  --condition "avg WorkingSetBytes > 1600000000" \  # 1.6GB (80% de 2GB)
  --window-size 5m
```

#### 2.3 Optimiser Frontend Resources
```bash
az containerapp update \
  --name potager-frontend \
  --cpu 0.5 \
  --memory 1.0Gi
```

---

### 🟢 PRIORITÉ 3 - Optimisations (Semaine 2-3)

#### 3.1 Multi-stage Build Backend
Modifier `backend/Dockerfile`:
```dockerfile
FROM python:3.12-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
COPY app ./app
COPY models ./models
COPY iot_simulator ./iot_simulator
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

**Gains:**
- 🔽 Taille image: -20% (~100 MB économisés)
- ⚡ Temps de pull: -30%
- 💰 Bandwidth ACR: réduit

#### 3.2 Activer Autoscaling Intelligent
```bash
az containerapp update \
  --name potager-backend \
  --min-replicas 1 \
  --max-replicas 5 \
  --scale-rule-name http-scale \
  --scale-rule-type http \
  --scale-rule-http-concurrency 50 \  # Scale si >50 req/instance
  --scale-rule-cooldown-period 300    # 5 min avant scale down
```

**Scénarios:**
- 0-50 req/sec: 1 instance
- 50-150 req/sec: 2-3 instances
- >150 req/sec: 4-5 instances

#### 3.3 CDN pour Assets Statiques
```bash
# Créer Azure CDN
az cdn profile create \
  --name potager-cdn \
  --resource-group rg-potager-ehpad \
  --sku Standard_Microsoft

az cdn endpoint create \
  --name potager-frontend \
  --profile-name potager-cdn \
  --origin <frontend-fqdn>
```

**Gains:**
- ⚡ Latence réduite (cache edge locations)
- 📉 Charge réduite sur frontend
- 💰 Coût: ~3-5€/mois

---

## 💰 Analyse Coûts Détaillée

### Configuration Actuelle (Scale-to-Zero)
```
Backend:  0.5 CPU × 1 GB × 0h/mois  = 0€
Frontend: 0.25 CPU × 0.5 GB × 0h/mois = 0€
ACR: Storage + bandwidth = ~2€/mois
TOTAL: ~2€/mois
```

### Configuration Recommandée (Priorité 1)
```
Backend:  1.0 CPU × 2 GB × 730h/mois  = ~18€
Frontend: 0.5 CPU × 1 GB × 730h/mois  = ~8€
Storage:  Azure Files 10 GB           = ~1€
ACR:      Storage + bandwidth         = ~2€/mois
TOTAL:    ~29€/mois
```

### Configuration Optimale (Toutes recommandations)
```
Backend:     1.0 CPU × 2 GB × 730h    = ~18€
Frontend:    0.5 CPU × 1 GB × 730h    = ~8€
Storage:     Azure Files 10 GB        = ~1€
Monitoring:  Application Insights     = ~8€
CDN:         Azure CDN                = ~4€
ACR:         Storage + bandwidth      = ~2€
TOTAL:       ~41€/mois
```

**📊 Ratio Coût/Valeur:**
- **Actuel:** 2€/mois mais service peu fiable (cold starts, pertes données)
- **Recommandé:** 29€/mois avec service production-ready
- **Optimal:** 41€/mois avec monitoring complet et CDN

**💡 Pour un projet EHPAD (santé), les 29-41€/mois sont justifiés.**

---

## 🔧 Scripts de Déploiement Optimisés

### Script 1: Mise à Jour Ressources (Priorité 1)
```bash
#!/bin/bash
# update-resources.sh

RG="rg-potager-ehpad"

echo "🚀 Mise à jour Backend..."
az containerapp update \
  --name potager-backend \
  --resource-group $RG \
  --min-replicas 1 \
  --max-replicas 3 \
  --cpu 1.0 \
  --memory 2.0Gi \
  --set-env-vars \
    UVICORN_WORKERS=2 \
    PYTHONOPTIMIZE=2

echo "🚀 Mise à jour Frontend..."
az containerapp update \
  --name potager-frontend \
  --resource-group $RG \
  --min-replicas 1 \
  --max-replicas 2 \
  --cpu 0.5 \
  --memory 1.0Gi \
  --set-env-vars \
    NODE_OPTIONS="--max-old-space-size=768"

echo "✅ Ressources mises à jour!"
```

### Script 2: Setup Monitoring (Priorité 2)
```bash
#!/bin/bash
# setup-monitoring.sh

RG="rg-potager-ehpad"
LOCATION="westeurope"

echo "📊 Création Application Insights..."
APPINSIGHTS_KEY=$(az monitor app-insights component create \
  --app potager-monitoring \
  --location $LOCATION \
  --resource-group $RG \
  --query instrumentationKey -o tsv)

echo "🔗 Liaison avec Container Apps..."
az containerapp update \
  --name potager-backend \
  --resource-group $RG \
  --enable-app-insights \
  --app-insights-key $APPINSIGHTS_KEY

az containerapp update \
  --name potager-frontend \
  --resource-group $RG \
  --enable-app-insights \
  --app-insights-key $APPINSIGHTS_KEY

echo "🔔 Configuration alertes..."
az monitor metrics alert create \
  --name potager-high-cpu \
  --resource-group $RG \
  --scopes $(az containerapp show -n potager-backend -g $RG --query id -o tsv) \
  --condition "avg Percentage CPU > 80" \
  --window-size 5m \
  --evaluation-frequency 1m

echo "✅ Monitoring configuré!"
```

### Script 3: Setup Stockage Persistant (Priorité 1)
```bash
#!/bin/bash
# setup-storage.sh

RG="rg-potager-ehpad"
LOCATION="westeurope"
STORAGE_ACCOUNT="potagerehpadstorage"

echo "💾 Création Storage Account..."
az storage account create \
  --name $STORAGE_ACCOUNT \
  --resource-group $RG \
  --location $LOCATION \
  --sku Standard_LRS

echo "📁 Création File Share..."
az storage share create \
  --name potager-data \
  --account-name $STORAGE_ACCOUNT \
  --quota 10

STORAGE_KEY=$(az storage account keys list \
  --resource-group $RG \
  --account-name $STORAGE_ACCOUNT \
  --query '[0].value' -o tsv)

echo "🔗 Montage dans Backend Container App..."
az containerapp update \
  --name potager-backend \
  --resource-group $RG \
  --replace-env-vars POTAGER_DB_PATH=/mnt/data/potager.db \
  --azure-file-volume-name data \
  --azure-file-volume-account-name $STORAGE_ACCOUNT \
  --azure-file-volume-account-key $STORAGE_KEY \
  --azure-file-volume-share-name potager-data \
  --azure-file-volume-mount-path /mnt/data

echo "✅ Stockage persistant configuré!"
```

---

## 📈 Métriques à Surveiller

### Backend
| Métrique | Seuil Normal | Seuil Alerte | Action |
|----------|--------------|--------------|--------|
| CPU Usage | 20-50% | >80% | Scale up |
| Memory Usage | 500-1000 MB | >1600 MB | Augmenter limite |
| Request Latency p95 | <500ms | >2s | Optimiser code |
| Error Rate | <1% | >5% | Investiguer logs |
| ML Inference Time | <100ms | >500ms | Optimiser modèle |

### Frontend
| Métrique | Seuil Normal | Seuil Alerte | Action |
|----------|--------------|--------------|--------|
| CPU Usage | 10-30% | >70% | Scale up |
| Memory Usage | 200-500 MB | >800 MB | Augmenter limite |
| Page Load Time | <2s | >5s | Optimiser bundle |
| Error Rate | <0.5% | >3% | Investiguer logs |

### Infrastructure
| Métrique | Seuil Normal | Seuil Alerte | Action |
|----------|--------------|--------------|--------|
| Cold Starts | 0/jour | >10/jour | Augmenter min-replicas |
| Restart Count | 0/jour | >5/jour | Investiguer crashes |
| HTTP 5xx | <0.1% | >1% | Check backend health |
| ACR Pull Time | <30s | >60s | Optimiser image size |

---

## ✅ Checklist de Déploiement Production

### Avant Déploiement
- [ ] Ressources dimensionnées correctement (CPU/Memory)
- [ ] Min-replicas ≥ 1 (pas de scale-to-zero)
- [ ] Stockage persistant configuré (Azure Files)
- [ ] Application Insights activé
- [ ] Alertes configurées
- [ ] Health checks validés
- [ ] Variables environnement prod définies
- [ ] Secrets stockés dans Azure Key Vault
- [ ] CORS configuré correctement
- [ ] SSL/TLS terminé par Azure (automatique)

### Après Déploiement
- [ ] Vérifier logs Application Insights
- [ ] Tester cold start (si min-replicas=0)
- [ ] Vérifier persistence données après restart
- [ ] Load test (50-100 req/sec)
- [ ] Vérifier temps de réponse <2s
- [ ] Tester fail-over (kill container)
- [ ] Vérifier alerting (déclencher manuellement)
- [ ] Valider backup/restore données

### Monitoring Continu
- [ ] Dashboard Application Insights configuré
- [ ] Revue hebdomadaire métriques
- [ ] Logs error rate < 1%
- [ ] Coûts suivis mensuellement
- [ ] Capacity planning (6 mois)

---

## 🎯 Conclusion et Prochaines Étapes

### Résumé des Problèmes Critiques:
1. ❌ **Scale-to-zero inadapté** → Cold starts + perte données
2. ❌ **Ressources insuffisantes** → Risque OOM kills
3. ❌ **Pas de monitoring** → Aucune visibilité problèmes
4. ❌ **Stockage non-persistant** → Perte données redéploiements

### Plan d'Action Recommandé:

#### Semaine 1 (Priorité 1):
1. Exécuter `update-resources.sh` (1h)
2. Exécuter `setup-storage.sh` (2h)
3. Tester et valider changements (2h)

#### Semaine 2 (Priorité 2):
1. Exécuter `setup-monitoring.sh` (1h)
2. Créer dashboard Application Insights (2h)
3. Configurer alertes email/SMS (1h)

#### Semaine 3 (Priorité 3):
1. Optimiser Dockerfiles (multi-stage) (3h)
2. Configurer autoscaling (1h)
3. Setup CDN Azure (2h)

### Coût Total Recommandé:
- **Minimal (P1):** ~29€/mois (production-ready)
- **Optimal (P1+P2+P3):** ~41€/mois (monitoring + CDN)

### Impact Attendu:
- ✅ Disponibilité: 99.5%+ (vs ~95% actuel)
- ✅ Latence: <500ms p95 (vs 2-10s avec cold starts)
- ✅ Résilience: Survit aux crashes/redéploiements
- ✅ Observabilité: Dashboards et alertes complets

---

**Audit réalisé par:** Claude Code  
**Contact:** Voir DEPLOYMENT.md pour détails infrastructure
