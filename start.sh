#!/bin/bash

# Crypto Sentinel - Script de Démarrage Rapide
# Ce script automatise l'installation et le lancement de Crypto Sentinel

set -e  # Arrêter en cas d'erreur

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction d'affichage
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Banner
echo -e "${BLUE}"
echo "  ╔═══════════════════════════════════════╗"
echo "  ║           CRYPTO SENTINEL            ║"
echo "  ║     Assistant IA pour Crypto         ║"
echo "  ║        Script de Démarrage           ║"
echo "  ╚═══════════════════════════════════════╝"
echo -e "${NC}"

# Vérification des prérequis
print_status "Vérification des prérequis..."

# Vérifier Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker n'est pas installé. Veuillez installer Docker d'abord."
    echo "Installation: https://docs.docker.com/get-docker/"
    exit 1
fi

# Vérifier Docker Compose
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose n'est pas installé. Veuillez installer Docker Compose d'abord."
    echo "Installation: https://docs.docker.com/compose/install/"
    exit 1
fi

print_success "Docker et Docker Compose sont installés"

# Vérifier si .env existe
if [ ! -f ".env" ]; then
    print_warning "Fichier .env non trouvé. Création à partir du template..."
    
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_success "Fichier .env créé à partir de .env.example"
        print_warning "IMPORTANT: Vous devez éditer le fichier .env avec vos vraies clés API!"
        echo
        echo "Variables critiques à configurer:"
        echo "  - OPENAI_API_KEY"
        echo "  - ALCHEMY_API_KEY (ou INFURA_API_KEY)"
        echo "  - TELEGRAM_BOT_TOKEN"
        echo "  - TELEGRAM_CHAT_ID"
        echo
        read -p "Voulez-vous éditer le fichier .env maintenant? (y/N): " edit_env
        if [[ $edit_env =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env
        else
            print_warning "N'oubliez pas d'éditer .env avant de lancer l'application!"
        fi
    else
        print_error "Fichier .env.example non trouvé!"
        exit 1
    fi
else
    print_success "Fichier .env trouvé"
fi

# Menu de sélection
echo
print_status "Choisissez le mode de déploiement:"
echo "1) Développement (application seule)"
echo "2) Production (avec MongoDB et Redis)"
echo "3) Complet (avec monitoring Prometheus/Grafana)"
echo "4) Arrêter tous les services"
echo "5) Voir les logs"
echo "6) Status des services"
echo "7) Nettoyer (supprimer containers et volumes)"
echo
read -p "Votre choix (1-7): " choice

case $choice in
    1)
        print_status "Lancement en mode développement..."
        docker-compose up -d crypto-sentinel
        ;;
    2)
        print_status "Lancement en mode production..."
        docker-compose up -d
        ;;
    3)
        print_status "Lancement avec monitoring complet..."
        docker-compose --profile monitoring up -d
        ;;
    4)
        print_status "Arrêt de tous les services..."
        docker-compose down
        print_success "Services arrêtés"
        exit 0
        ;;
    5)
        print_status "Affichage des logs..."
        docker-compose logs -f --tail=50
        exit 0
        ;;
    6)
        print_status "Status des services..."
        docker-compose ps
        echo
        print_status "Santé de l'application:"
        sleep 2
        curl -s http://localhost:8000/health 2>/dev/null | jq . || echo "Application non accessible"
        exit 0
        ;;
    7)
        print_warning "Cette action va supprimer tous les containers et volumes!"
        read -p "Êtes-vous sûr? (y/N): " confirm
        if [[ $confirm =~ ^[Yy]$ ]]; then
            print_status "Nettoyage en cours..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            print_success "Nettoyage terminé"
        fi
        exit 0
        ;;
    *)
        print_error "Choix invalide"
        exit 1
        ;;
esac

# Attendre que les services démarrent
print_status "Démarrage des services..."
sleep 10

# Vérifier le statut
print_status "Vérification du statut des services..."
docker-compose ps

echo
print_status "Test de connectivité..."

# Tester l'application
for i in {1..30}; do
    if curl -s http://localhost:8000/health >/dev/null 2>&1; then
        print_success "Application démarrée avec succès!"
        break
    else
        if [ $i -eq 30 ]; then
            print_error "L'application n'a pas pu démarrer dans les temps"
            print_status "Vérifiez les logs avec: docker-compose logs crypto-sentinel"
            exit 1
        fi
        echo -n "."
        sleep 2
    fi
done

echo
print_success "🚀 Crypto Sentinel est opérationnel!"
echo
echo "📊 Interfaces disponibles:"
echo "  • Application: http://localhost:8000"
echo "  • API Docs: http://localhost:8000/docs"
echo "  • Health Check: http://localhost:8000/health"

if docker-compose ps | grep -q grafana; then
    echo "  • Grafana: http://localhost:3000 (admin/cryptosentinel2024)"
    echo "  • Prometheus: http://localhost:9090"
fi

echo
echo "📋 Commandes utiles:"
echo "  • Voir les logs: docker-compose logs -f crypto-sentinel"
echo "  • Arrêter: docker-compose down"
echo "  • Redémarrer: docker-compose restart crypto-sentinel"
echo "  • Status: docker-compose ps"

echo
print_status "Vérification de la santé de l'application..."
curl -s http://localhost:8000/health | jq . || echo "Erreur lors de la vérification"

echo
print_success "Installation terminée! 🎉"
print_warning "N'oubliez pas de configurer vos clés API dans le fichier .env"