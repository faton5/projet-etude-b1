# 📚 Documentation Technique - Potager EHPAD Tomate V0

Ce dossier contient toute la documentation technique du projet.

---

## 🎯 Documents Essentiels

### À Lire en Premier

1. **[../README.md](../README.md)** - 🚀 Guide démarrage rapide
2. **[../CDC.md](../CDC.md)** - 📋 Cahier des charges complet (35 pages)
3. **[../PROJECT_STATUS.md](../PROJECT_STATUS.md)** - 📊 État actuel du projet
4. **[../CHANGELOG.md](../CHANGELOG.md)** - 📝 Historique des modifications

---

## 📖 Documentation Complète

### 🏗️ Architecture et Développement

- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture technique détaillée du projet
- **[AGENTS.md](./AGENTS.md)** - Configuration des agents Claude Code

### 🚀 Déploiement et Infrastructure

- **[DEPLOYMENT.md](./DEPLOYMENT.md)** - Guide de déploiement Docker Compose
- **[GUIDE_AZURE_PRODUCTION.md](./GUIDE_AZURE_PRODUCTION.md)** - 🆕 **Guide complet Azure production-ready**
  - Fusion de 5 documents (START_HERE, QUOI_DE_NEUF, RESUME, OPTIMISATIONS, INDEX)
  - Plan d'exécution (55 minutes)
  - Scripts d'automatisation
  - Analyse coûts et ROI (62x)
  - Validation et monitoring

### 🔍 Audits et Analyses

#### Audits Fonctionnels
- **[AUDIT_INITIAL.md](./AUDIT_INITIAL.md)** - Audit initial du projet (V0.1.0)
- **[AUDIT_WATERING_SYSTEM.md](./AUDIT_WATERING_SYSTEM.md)** - Système de conseil d'arrosage intelligent (V0.2.0)
  - Problème identifié (logique if/else simpliste)
  - Solution (réutilisation features ML)
  - Comparaison avant/après

#### Audits Azure Infrastructure
- **[AUDIT_AZURE_CONTAINERS.md](./AUDIT_AZURE_CONTAINERS.md)** - Audit technique Azure Container Apps (15 pages)
  - 6 problèmes critiques identifiés
  - Recommandations par priorité
  - Scripts d'optimisation
- **[AUDIT_AZURE_OPTIMIZATION.md](./AUDIT_AZURE_OPTIMIZATION.md)** - Comparatif avant/après détaillé (17 pages)
  - Métriques complètes
  - Scénarios utilisateur
  - Checklist validation

### 🗄️ Archives

- **[archives/session-2026-05-12/](./archives/session-2026-05-12/)** - Documentation de session (10 fichiers archivés)
  - Documents de travail fusionnés dans GUIDE_AZURE_PRODUCTION.md
  - Conservés pour référence historique

## Architecture du projet

```
potager-ehpad-tomate/
├── backend/          # API FastAPI + modèle ML
├── frontend/         # Dashboard Next.js
├── dataset/          # Données d'entraînement
├── mosquitto/        # Config MQTT
├── docs/            # Documentation (vous êtes ici)
└── CDC.md           # Cahier des charges
```

## Démarrage rapide

```bash
# Lancer le projet complet
docker compose up --build

# Accéder au dashboard
http://localhost:3000

# API backend
http://localhost:8000/docs
```

## Endpoints principaux

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/predict` | POST | Prédire la viabilité de plantation (viable/attendre/non_viable) |
| `/predict/iot` | POST | Prédiction avec données IoT + météo auto |
| `/advice/watering` | POST | Conseil d'arrosage intelligent (ML) |
| `/weather` | GET | Récupérer la météo Open-Meteo |
| `/iot/live` | GET | Données IoT en temps réel |
| `/history` | GET | Historique des prédictions |

## Modèle ML

Le projet utilise **XGBoost Classifier** avec les features suivantes :
- `stress_hydrique` - Tension hydrique de la plante
- `risque_secheresse` - Risque combiné (sol + température + pluie)
- `confort_thermique` - Adaptation aux températures
- Données météo (température, pluie, gel)
- Données IoT (humidité sol, irrigation, eau)

## Contributions

Pour toute modification, vérifier la cohérence avec le CDC.md et mettre à jour la documentation correspondante.
