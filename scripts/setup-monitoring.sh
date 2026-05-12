#!/bin/bash
# ============================================================================
# Script: Configuration du monitoring Azure Application Insights
# Description: Active Application Insights et configure les alertes
# Date: 12 mai 2026
# ============================================================================

set -e  # Exit on error

# ── Configuration ───────────────────────────────────────────────────────────
RESOURCE_GROUP="rg-potager-ehpad"
LOCATION="westeurope"
APPINSIGHTS_NAME="potager-monitoring"
BACKEND_APP="potager-backend"
FRONTEND_APP="potager-frontend"
ACTION_GROUP_NAME="potager-alerts"
ACTION_GROUP_EMAIL="${ALERT_EMAIL:-admin@potager-ehpad.local}"

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# ── Fonctions ───────────────────────────────────────────────────────────────
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_prerequisites() {
    log_info "Vérification des prérequis..."

    if ! command -v az &> /dev/null; then
        log_error "Azure CLI n'est pas installé"
        exit 1
    fi

    if ! az account show &> /dev/null; then
        log_error "Non connecté à Azure. Exécutez: az login"
        exit 1
    fi

    # Check if extension is installed
    if ! az extension list --query "[?name=='application-insights'].name" -o tsv | grep -q "application-insights"; then
        log_info "Installation de l'extension Application Insights..."
        az extension add --name application-insights --yes
    fi

    log_success "Prérequis OK"
}

create_app_insights() {
    log_info "Vérification Application Insights '$APPINSIGHTS_NAME'..."

    if az monitor app-insights component show \
        --app $APPINSIGHTS_NAME \
        --resource-group $RESOURCE_GROUP &>/dev/null; then
        log_warning "Application Insights '$APPINSIGHTS_NAME' existe déjà"
        return 0
    fi

    log_info "Création Application Insights..."
    az monitor app-insights component create \
        --app $APPINSIGHTS_NAME \
        --location $LOCATION \
        --resource-group $RESOURCE_GROUP \
        --kind web \
        --application-type web

    log_success "Application Insights créé"
}

link_to_apps() {
    log_info "Liaison avec les Container Apps..."

    # Get instrumentation key
    INSTRUMENTATION_KEY=$(az monitor app-insights component show \
        --app $APPINSIGHTS_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "instrumentationKey" -o tsv)

    CONNECTION_STRING=$(az monitor app-insights component show \
        --app $APPINSIGHTS_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "connectionString" -o tsv)

    # Backend
    if az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP &>/dev/null; then
        log_info "Liaison avec le backend..."
        az containerapp update \
            --name $BACKEND_APP \
            --resource-group $RESOURCE_GROUP \
            --set-env-vars \
                APPLICATIONINSIGHTS_CONNECTION_STRING="$CONNECTION_STRING" \
                APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY"

        log_success "Backend lié à Application Insights"
    else
        log_warning "Backend app '$BACKEND_APP' n'existe pas encore"
    fi

    # Frontend
    if az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP &>/dev/null; then
        log_info "Liaison avec le frontend..."
        az containerapp update \
            --name $FRONTEND_APP \
            --resource-group $RESOURCE_GROUP \
            --set-env-vars \
                APPLICATIONINSIGHTS_CONNECTION_STRING="$CONNECTION_STRING" \
                APPINSIGHTS_INSTRUMENTATIONKEY="$INSTRUMENTATION_KEY"

        log_success "Frontend lié à Application Insights"
    else
        log_warning "Frontend app '$FRONTEND_APP' n'existe pas encore"
    fi
}

create_action_group() {
    log_info "Configuration des alertes email..."

    if az monitor action-group show \
        --name $ACTION_GROUP_NAME \
        --resource-group $RESOURCE_GROUP &>/dev/null; then
        log_warning "Action Group '$ACTION_GROUP_NAME' existe déjà"
        return 0
    fi

    log_info "Création du groupe d'actions (email: $ACTION_GROUP_EMAIL)..."
    az monitor action-group create \
        --name $ACTION_GROUP_NAME \
        --resource-group $RESOURCE_GROUP \
        --short-name "PotagerAlert" \
        --email-receiver \
            name="Admin" \
            email-address="$ACTION_GROUP_EMAIL" \
            use-common-alert-schema=true

    log_success "Action Group créé"
}

create_alerts() {
    log_info "Configuration des alertes..."

    # Get action group ID
    ACTION_GROUP_ID=$(az monitor action-group show \
        --name $ACTION_GROUP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "id" -o tsv)

    # Backend alerts
    if az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP &>/dev/null; then
        BACKEND_ID=$(az containerapp show \
            --name $BACKEND_APP \
            --resource-group $RESOURCE_GROUP \
            --query "id" -o tsv)

        # Alert: High CPU
        log_info "Création alerte: CPU élevé backend..."
        az monitor metrics alert create \
            --name "potager-backend-high-cpu" \
            --resource-group $RESOURCE_GROUP \
            --scopes "$BACKEND_ID" \
            --condition "avg UsageNanoCores > 800000000" \
            --window-size 5m \
            --evaluation-frequency 1m \
            --description "Backend CPU > 80%" \
            --action "$ACTION_GROUP_ID" \
            --severity 2 || log_warning "Alerte CPU existe déjà"

        # Alert: High Memory
        log_info "Création alerte: Mémoire élevée backend..."
        az monitor metrics alert create \
            --name "potager-backend-high-memory" \
            --resource-group $RESOURCE_GROUP \
            --scopes "$BACKEND_ID" \
            --condition "avg WorkingSetBytes > 1600000000" \
            --window-size 5m \
            --evaluation-frequency 1m \
            --description "Backend Memory > 80% (1.6GB/2GB)" \
            --action "$ACTION_GROUP_ID" \
            --severity 2 || log_warning "Alerte Memory existe déjà"

        # Alert: Container restarts
        log_info "Création alerte: Redémarrages backend..."
        az monitor metrics alert create \
            --name "potager-backend-restarts" \
            --resource-group $RESOURCE_GROUP \
            --scopes "$BACKEND_ID" \
            --condition "total RestartCount > 3" \
            --window-size 15m \
            --evaluation-frequency 5m \
            --description "Backend redémarre trop souvent" \
            --action "$ACTION_GROUP_ID" \
            --severity 1 || log_warning "Alerte Restarts existe déjà"

        log_success "Alertes backend configurées"
    fi

    # Frontend alerts
    if az containerapp show --name $FRONTEND_APP --resource-group $RESOURCE_GROUP &>/dev/null; then
        FRONTEND_ID=$(az containerapp show \
            --name $FRONTEND_APP \
            --resource-group $RESOURCE_GROUP \
            --query "id" -o tsv)

        # Alert: High CPU
        log_info "Création alerte: CPU élevé frontend..."
        az monitor metrics alert create \
            --name "potager-frontend-high-cpu" \
            --resource-group $RESOURCE_GROUP \
            --scopes "$FRONTEND_ID" \
            --condition "avg UsageNanoCores > 400000000" \
            --window-size 5m \
            --evaluation-frequency 1m \
            --description "Frontend CPU > 80%" \
            --action "$ACTION_GROUP_ID" \
            --severity 2 || log_warning "Alerte CPU frontend existe déjà"

        log_success "Alertes frontend configurées"
    fi

    # Application Insights alerts
    APPINSIGHTS_ID=$(az monitor app-insights component show \
        --app $APPINSIGHTS_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "id" -o tsv)

    # Alert: High error rate
    log_info "Création alerte: Taux d'erreur élevé..."
    az monitor metrics alert create \
        --name "potager-high-error-rate" \
        --resource-group $RESOURCE_GROUP \
        --scopes "$APPINSIGHTS_ID" \
        --condition "avg requests/failed > 5" \
        --window-size 5m \
        --evaluation-frequency 1m \
        --description "Taux d'erreur > 5%" \
        --action "$ACTION_GROUP_ID" \
        --severity 1 || log_warning "Alerte Error Rate existe déjà"

    log_success "Toutes les alertes configurées"
}

display_dashboard_link() {
    log_info "Génération du lien vers le dashboard..."

    APPINSIGHTS_ID=$(az monitor app-insights component show \
        --app $APPINSIGHTS_NAME \
        --resource-group $RESOURCE_GROUP \
        --query "id" -o tsv)

    SUBSCRIPTION_ID=$(az account show --query "id" -o tsv)

    echo ""
    echo "📊 Dashboard Application Insights:"
    echo "   https://portal.azure.com/#@/resource${APPINSIGHTS_ID}/overview"
    echo ""
    echo "📈 Métriques disponibles:"
    echo "   • Requêtes/sec"
    echo "   • Latence (p50, p95, p99)"
    echo "   • Taux d'erreurs"
    echo "   • CPU/Memory par container"
    echo "   • Dépendances (API externes)"
    echo "   • Custom events"
    echo ""
}

display_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    log_success "Configuration du monitoring terminée!"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "📊 Application Insights: $APPINSIGHTS_NAME"
    echo "🔔 Action Group: $ACTION_GROUP_NAME (email: $ACTION_GROUP_EMAIL)"
    echo ""
    echo "🚨 Alertes configurées:"
    echo "   • Backend CPU > 80%"
    echo "   • Backend Memory > 80%"
    echo "   • Backend restarts > 3 en 15 min"
    echo "   • Frontend CPU > 80%"
    echo "   • Taux d'erreur > 5%"
    echo ""

    display_dashboard_link

    echo "💰 Coût estimé: ~5-8€/mois (1 GB logs/mois)"
    echo ""
    echo "📚 Logs en temps réel:"
    echo "   az containerapp logs tail -n $BACKEND_APP -g $RESOURCE_GROUP --follow"
    echo ""
    echo "✅ Monitoring opérationnel!"
    echo "═══════════════════════════════════════════════════════════════════"
}

# ── Main ────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║         Configuration Monitoring - Application Insights          ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""

    # Check for email override
    if [ -z "$ALERT_EMAIL" ]; then
        log_warning "Variable ALERT_EMAIL non définie, utilisation de: $ACTION_GROUP_EMAIL"
        echo "Pour définir votre email: export ALERT_EMAIL=votre@email.com"
        echo ""
        read -p "Continuer avec $ACTION_GROUP_EMAIL? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "Script annulé"
            exit 1
        fi
    fi

    check_prerequisites
    create_app_insights
    link_to_apps
    create_action_group
    create_alerts
    display_summary
}

# Exécuter
main
