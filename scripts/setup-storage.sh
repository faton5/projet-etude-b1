#!/bin/bash
# ============================================================================
# Script: Configuration du stockage persistant Azure
# Description: Configure Azure Files pour persistance des données SQLite
# Date: 12 mai 2026
# ============================================================================

set -e  # Exit on error

# ── Configuration ───────────────────────────────────────────────────────────
RESOURCE_GROUP="rg-potager-ehpad"
LOCATION="westeurope"
STORAGE_ACCOUNT="potagerehpadstorage"
FILE_SHARE="potager-data"
SHARE_QUOTA=10  # GB
BACKEND_APP="potager-backend"
MOUNT_PATH="/mnt/data"

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

    log_success "Prérequis OK"
}

create_storage_account() {
    log_info "Vérification du Storage Account '$STORAGE_ACCOUNT'..."

    if az storage account show --name $STORAGE_ACCOUNT --resource-group $RESOURCE_GROUP &>/dev/null; then
        log_warning "Storage Account '$STORAGE_ACCOUNT' existe déjà"
        return 0
    fi

    log_info "Création du Storage Account..."
    az storage account create \
        --name $STORAGE_ACCOUNT \
        --resource-group $RESOURCE_GROUP \
        --location $LOCATION \
        --sku Standard_LRS \
        --kind StorageV2 \
        --https-only true \
        --min-tls-version TLS1_2

    log_success "Storage Account créé"
}

create_file_share() {
    log_info "Vérification du File Share '$FILE_SHARE'..."

    # Get storage key
    STORAGE_KEY=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name $STORAGE_ACCOUNT \
        --query '[0].value' -o tsv)

    # Check if share exists
    if az storage share show \
        --name $FILE_SHARE \
        --account-name $STORAGE_ACCOUNT \
        --account-key $STORAGE_KEY &>/dev/null; then
        log_warning "File Share '$FILE_SHARE' existe déjà"
        return 0
    fi

    log_info "Création du File Share (${SHARE_QUOTA} GB)..."
    az storage share create \
        --name $FILE_SHARE \
        --account-name $STORAGE_ACCOUNT \
        --account-key $STORAGE_KEY \
        --quota $SHARE_QUOTA

    log_success "File Share créé"
}

mount_to_backend() {
    log_info "Montage du volume dans le backend..."

    # Vérifier si l'app existe
    if ! az containerapp show --name $BACKEND_APP --resource-group $RESOURCE_GROUP &>/dev/null; then
        log_warning "Backend app '$BACKEND_APP' n'existe pas encore"
        log_warning "Le volume sera monté lors du premier déploiement"
        return 0
    fi

    # Get storage key
    STORAGE_KEY=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name $STORAGE_ACCOUNT \
        --query '[0].value' -o tsv)

    log_info "Configuration du volume Azure Files..."

    # Note: Azure Container Apps ne supporte pas --azure-file-volume-* directement
    # Il faut créer un storage mount via l'API ou le portail
    # Voici la commande alternative:

    az containerapp update \
        --name $BACKEND_APP \
        --resource-group $RESOURCE_GROUP \
        --replace-env-vars \
            POTAGER_DB_PATH=/mnt/data/potager.db \
            MODEL_PATH=/app/models/xgboost_tomate.joblib

    log_warning "⚠️  Configuration manuelle requise:"
    echo ""
    echo "Le montage Azure Files doit être configuré via le portail Azure:"
    echo ""
    echo "1. Aller sur: https://portal.azure.com"
    echo "2. Naviguer vers: Container Apps > $BACKEND_APP > Volumes"
    echo "3. Cliquer sur 'Add volume'"
    echo "4. Sélectionner 'Azure File Share'"
    echo "5. Configurer:"
    echo "   - Storage account: $STORAGE_ACCOUNT"
    echo "   - File share: $FILE_SHARE"
    echo "   - Mount path: $MOUNT_PATH"
    echo "   - Access mode: Read/Write"
    echo ""
    echo "Ou utiliser Azure CLI avec le format YAML:"
    echo ""
    cat > /tmp/volume-config.yaml <<EOF
properties:
  template:
    volumes:
    - name: data-volume
      storageType: AzureFile
      storageName: $STORAGE_ACCOUNT
      shareName: $FILE_SHARE
    containers:
    - name: potager-backend
      volumeMounts:
      - volumeName: data-volume
        mountPath: $MOUNT_PATH
EOF
    echo "Configuration YAML sauvegardée dans: /tmp/volume-config.yaml"
    echo ""

    log_success "Variable d'environnement POTAGER_DB_PATH mise à jour"
}

test_storage() {
    log_info "Test du stockage..."

    STORAGE_KEY=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name $STORAGE_ACCOUNT \
        --query '[0].value' -o tsv)

    # Create test file
    echo "Test file created on $(date)" > /tmp/test-storage.txt

    log_info "Upload d'un fichier de test..."
    az storage file upload \
        --share-name $FILE_SHARE \
        --account-name $STORAGE_ACCOUNT \
        --account-key $STORAGE_KEY \
        --source /tmp/test-storage.txt \
        --path test.txt

    log_info "Vérification du fichier..."
    if az storage file exists \
        --share-name $FILE_SHARE \
        --account-name $STORAGE_ACCOUNT \
        --account-key $STORAGE_KEY \
        --path test.txt \
        --query "exists" -o tsv | grep -q "true"; then
        log_success "Stockage fonctionne correctement!"
    else
        log_error "Problème de stockage détecté"
        exit 1
    fi

    # Cleanup
    rm /tmp/test-storage.txt
}

display_summary() {
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    log_success "Configuration du stockage terminée!"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
    echo "📦 Storage Account: $STORAGE_ACCOUNT"
    echo "📁 File Share: $FILE_SHARE ($SHARE_QUOTA GB)"
    echo "🔗 Mount Path: $MOUNT_PATH"
    echo ""
    echo "💾 Informations de connexion:"

    STORAGE_KEY=$(az storage account keys list \
        --resource-group $RESOURCE_GROUP \
        --account-name $STORAGE_ACCOUNT \
        --query '[0].value' -o tsv)

    echo "   Account Name: $STORAGE_ACCOUNT"
    echo "   Account Key: ${STORAGE_KEY:0:20}... (masqué)"
    echo ""
    echo "📊 Coût estimé: ~1€/mois pour 10 GB"
    echo ""
    echo "⚠️  ACTION REQUISE:"
    echo "   Le montage du volume doit être finalisé manuellement via le portail Azure"
    echo "   Voir les instructions ci-dessus"
    echo ""
    echo "✅ Prochaine étape: ./setup-monitoring.sh (Application Insights)"
    echo "═══════════════════════════════════════════════════════════════════"
}

# ── Main ────────────────────────────────────────────────────────────────────
main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════════╗"
    echo "║          Configuration Stockage Persistant Azure Files           ║"
    echo "╚═══════════════════════════════════════════════════════════════════╝"
    echo ""

    check_prerequisites
    create_storage_account
    create_file_share
    mount_to_backend
    test_storage
    display_summary
}

# Exécuter
main
