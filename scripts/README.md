# Scripts d'Optimisation Azure Container Apps

Ce dossier contient les scripts pour optimiser l'infrastructure Azure du projet Potager EHPAD.

## 📋 Vue d'Ensemble

| Script | Description | Durée | Coût Additionnel |
|--------|-------------|-------|------------------|
| `update-resources.sh` | Augmente CPU/RAM et configure min-replicas | ~5 min | +26€/mois |
| `setup-storage.sh` | Configure stockage persistant Azure Files | ~10 min | +1€/mois |
| `setup-monitoring.sh` | Active Application Insights et alertes | ~10 min | +8€/mois |

**Total:** ~35€/mois pour une infrastructure production-ready

---

## 🚀 Ordre d'Exécution

### Prérequis

1. **Azure CLI installé**
   ```bash
   # Vérifier l'installation
   az --version
   
   # Installer si nécessaire
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Connexion à Azure**
   ```bash
   az login
   az account set --subscription <votre-subscription-id>
   ```

3. **Variables d'environnement (optionnel)**
   ```bash
   export ALERT_EMAIL="votre-email@example.com"
   ```

---

### Étape 1: Mise à Jour des Ressources (PRIORITÉ 1)

**Ce que ça fait:**
- Backend: 0.5 CPU → 1.0 CPU, 1 GB → 2 GB RAM
- Frontend: 0.25 CPU → 0.5 CPU, 0.5 GB → 1 GB RAM
- min-replicas: 0 → 1 (élimine cold starts)
- max-replicas: Backend 1→3, Frontend 1→2
- Configure auto-scaling HTTP

**Exécution:**
```bash
cd scripts
./update-resources.sh
```

**Impact:**
- ✅ Disponibilité 24/7 (plus de cold start)
- ✅ Performance ML x2 (plus de CPU)
- ✅ Évite les OOM kills (plus de RAM)
- 💰 +26€/mois

**Vérification:**
```bash
# Backend
az containerapp show -n potager-backend -g rg-potager-ehpad \
  --query "{cpu: properties.template.containers[0].resources.cpu, memory: properties.template.containers[0].resources.memory, minReplicas: properties.template.scale.minReplicas, maxReplicas: properties.template.scale.maxReplicas}"

# Frontend
az containerapp show -n potager-frontend -g rg-potager-ehpad \
  --query "{cpu: properties.template.containers[0].resources.cpu, memory: properties.template.containers[0].resources.memory, minReplicas: properties.template.scale.minReplicas, maxReplicas: properties.template.scale.maxReplicas}"
```

---

### Étape 2: Configuration Stockage Persistant (PRIORITÉ 1)

**Ce que ça fait:**
- Crée un Azure Storage Account
- Crée un Azure File Share (10 GB)
- Configure la base SQLite pour utiliser le stockage persistant
- Les données survivent aux redéploiements

**Exécution:**
```bash
./setup-storage.sh
```

**Action Manuelle Requise:**

Le script va créer le stockage mais le montage dans le Container App nécessite une étape manuelle via le portail Azure:

1. Aller sur https://portal.azure.com
2. Naviguer vers: **Container Apps** → **potager-backend** → **Volumes**
3. Cliquer sur **Add volume**
4. Configurer:
   - Type: **Azure File Share**
   - Storage account: `potagerehpadstorage`
   - File share: `potager-data`
   - Mount path: `/mnt/data`
   - Access mode: **Read/Write**
5. Sauvegarder

**Impact:**
- ✅ Données persistantes (survivent aux redéploiements)
- ✅ Backup automatique (géré par Azure)
- ✅ Partage entre instances (si scale horizontal)
- 💰 +1€/mois

**Vérification:**
```bash
# Tester l'accès au File Share
az storage file list \
  --share-name potager-data \
  --account-name potagerehpadstorage \
  --output table
```

---

### Étape 3: Configuration Monitoring (PRIORITÉ 2)

**Ce que ça fait:**
- Crée Application Insights
- Lie les Container Apps à Application Insights
- Configure Action Group (alertes email)
- Configure 5 alertes critiques

**Exécution:**
```bash
# Définir votre email pour les alertes
export ALERT_EMAIL="votre-email@example.com"

./setup-monitoring.sh
```

**Alertes Configurées:**
- 🔔 Backend CPU > 80%
- 🔔 Backend Memory > 80%
- 🔔 Backend restarts > 3 en 15 min
- 🔔 Frontend CPU > 80%
- 🔔 Taux d'erreur > 5%

**Impact:**
- ✅ Visibilité complète (logs + métriques)
- ✅ Alertes proactives (email)
- ✅ Debugging facile (stack traces)
- ✅ Dashboard temps réel
- 💰 +8€/mois

**Accès au Dashboard:**
```bash
# Le script affiche l'URL du dashboard
# Ou manuellement:
echo "https://portal.azure.com/#@/resource/subscriptions/$(az account show --query id -o tsv)/resourceGroups/rg-potager-ehpad/providers/microsoft.insights/components/potager-monitoring/overview"
```

**Logs en temps réel:**
```bash
# Backend
az containerapp logs tail -n potager-backend -g rg-potager-ehpad --follow

# Frontend
az containerapp logs tail -n potager-frontend -g rg-potager-ehpad --follow
```

---

## 🔄 Déploiement Complet (3 étapes)

Pour exécuter tous les scripts d'un coup:

```bash
cd scripts

# Étape 1: Ressources
./update-resources.sh

# Étape 2: Stockage (puis faire l'action manuelle)
./setup-storage.sh

# Étape 3: Monitoring
export ALERT_EMAIL="votre-email@example.com"
./setup-monitoring.sh
```

**Temps total:** ~25 minutes (+ action manuelle)  
**Coût total:** +35€/mois

---

## 📊 Validation Post-Déploiement

### Checklist Technique

- [ ] **Backend**
  - [ ] min-replicas = 1 (pas de cold start)
  - [ ] CPU = 1.0, Memory = 2.0Gi
  - [ ] Auto-scale configuré (max 3 instances)
  - [ ] Health check répond en <1s

- [ ] **Frontend**
  - [ ] min-replicas = 1
  - [ ] CPU = 0.5, Memory = 1.0Gi
  - [ ] Auto-scale configuré (max 2 instances)
  - [ ] Page charge en <2s

- [ ] **Stockage**
  - [ ] Azure Files créé (10 GB)
  - [ ] Volume monté dans backend
  - [ ] SQLite accessible via /mnt/data
  - [ ] Données persistent après redéploiement

- [ ] **Monitoring**
  - [ ] Application Insights actif
  - [ ] Métriques visibles dans dashboard
  - [ ] Alertes email reçues (tester)
  - [ ] Logs accessibles en temps réel

### Tests de Performance

```bash
# 1. Test latence backend
curl -w "@-" -o /dev/null -s https://$(az containerapp show -n potager-backend -g rg-potager-ehpad --query "properties.configuration.ingress.fqdn" -o tsv)/health <<'EOF'
    time_namelookup:  %{time_namelookup}\n
       time_connect:  %{time_connect}\n
    time_appconnect:  %{time_appconnect}\n
      time_redirect:  %{time_redirect}\n
   time_starttransfer:  %{time_starttransfer}\n
                     ----------\n
         time_total:  %{time_total}\n
EOF

# Attendu: time_total < 500ms

# 2. Test auto-scaling (load test)
# Installer Apache Bench
sudo apt-get install apache2-utils

# Générer charge (100 req, 10 concurrent)
BACKEND_URL="https://$(az containerapp show -n potager-backend -g rg-potager-ehpad --query "properties.configuration.ingress.fqdn" -o tsv)"
ab -n 100 -c 10 $BACKEND_URL/health

# Observer auto-scaling dans portal Azure

# 3. Test persistance données
# Créer une donnée
curl -X POST https://backend-url/api/measures -d '{"value": 123}'

# Redéployer backend
az containerapp revision restart -n potager-backend -g rg-potager-ehpad --revision <latest>

# Vérifier que la donnée existe toujours
curl https://backend-url/api/measures
```

---

## 🔙 Rollback

Si besoin de revenir en arrière:

### Rollback Ressources
```bash
az containerapp update \
  --name potager-backend \
  --resource-group rg-potager-ehpad \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.5 \
  --memory 1.0Gi

az containerapp update \
  --name potager-frontend \
  --resource-group rg-potager-ehpad \
  --min-replicas 1 \
  --max-replicas 1 \
  --cpu 0.25 \
  --memory 0.5Gi
```

**⚠️ NE PAS revenir à min-replicas=0** (cold starts problématiques)

### Rollback depuis Backup
```bash
# Restaurer depuis backup (créé automatiquement)
az containerapp update \
  --name potager-backend \
  --resource-group rg-potager-ehpad \
  --yaml ./backups/backup-backend-<timestamp>.json
```

### Supprimer Monitoring (si besoin)
```bash
# Supprimer alertes
az monitor metrics alert delete --name potager-backend-high-cpu -g rg-potager-ehpad
az monitor metrics alert delete --name potager-backend-high-memory -g rg-potager-ehpad
# ... etc

# Supprimer Application Insights
az monitor app-insights component delete \
  --app potager-monitoring \
  --resource-group rg-potager-ehpad
```

---

## 💡 Commandes Utiles

### Monitoring

```bash
# Voir métriques CPU/Memory
az monitor metrics list \
  --resource $(az containerapp show -n potager-backend -g rg-potager-ehpad --query id -o tsv) \
  --metric "UsageNanoCores" "WorkingSetBytes" \
  --start-time $(date -u -d '1 hour ago' '+%Y-%m-%dT%H:%M:%S')Z

# Voir toutes les alertes actives
az monitor metrics alert list -g rg-potager-ehpad --output table

# Voir révisions (historique déploiements)
az containerapp revision list -n potager-backend -g rg-potager-ehpad --output table

# Scaler manuellement
az containerapp update -n potager-backend -g rg-potager-ehpad --min-replicas 2
```

### Debugging

```bash
# Logs erreurs seulement
az containerapp logs tail -n potager-backend -g rg-potager-ehpad | grep ERROR

# Exec dans le container (debug)
az containerapp exec -n potager-backend -g rg-potager-ehpad --command /bin/bash

# Voir variables environnement
az containerapp show -n potager-backend -g rg-potager-ehpad \
  --query "properties.template.containers[0].env" --output table
```

### Coûts

```bash
# Voir coûts actuels
az consumption usage list \
  --start-date $(date -u -d '30 days ago' '+%Y-%m-%d') \
  --end-date $(date -u '+%Y-%m-%d') \
  --query "[?contains(instanceName, 'potager')].{Resource:instanceName, Cost:pretaxCost}" \
  --output table
```

---

## 📚 Documentation

- **Guide complet:** `../AVANT_APRES_OPTIMISATION.md`
- **Audit détaillé:** `../AUDIT_AZURE_CONTAINERS.md`
- **Déploiement Azure:** `../DEPLOYMENT.md`

---

## 🆘 Support

En cas de problème:

1. **Vérifier logs:**
   ```bash
   az containerapp logs tail -n potager-backend -g rg-potager-ehpad --follow
   ```

2. **Vérifier health:**
   ```bash
   curl https://$(az containerapp show -n potager-backend -g rg-potager-ehpad --query "properties.configuration.ingress.fqdn" -o tsv)/health
   ```

3. **Vérifier dashboard Application Insights**

4. **Rollback si critique** (voir section Rollback)

---

## ⚠️ Notes Importantes

- **Jamais de min-replicas=0 en production** (cold starts)
- **Toujours tester en dev avant prod**
- **Backups automatiques créés** (dossier `./backups/`)
- **Monitoring = investissement crucial** (détection précoce problèmes)
- **Coûts ~ 35€/mois** mais ROI immédiat (disponibilité + performance)

---

**Créé par:** Claude Code  
**Date:** 12 mai 2026  
**Version:** 1.0
