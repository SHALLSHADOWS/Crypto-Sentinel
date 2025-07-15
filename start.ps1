# Crypto Sentinel - Script de Démarrage Rapide (PowerShell)
# Ce script automatise l'installation et le lancement de Crypto Sentinel sur Windows

param(
    [string]$Mode = "menu"
)

# Configuration des couleurs
$Host.UI.RawUI.ForegroundColor = "White"

function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    } else {
        $input | Write-Output
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Print-Status($message) {
    Write-ColorOutput Blue "[INFO] $message"
}

function Print-Success($message) {
    Write-ColorOutput Green "[SUCCESS] $message"
}

function Print-Warning($message) {
    Write-ColorOutput Yellow "[WARNING] $message"
}

function Print-Error($message) {
    Write-ColorOutput Red "[ERROR] $message"
}

# Banner
Write-ColorOutput Cyan @"
  ╔═══════════════════════════════════════╗
  ║           CRYPTO SENTINEL            ║
  ║     Assistant IA pour Crypto         ║
  ║        Script de Démarrage           ║
  ╚═══════════════════════════════════════╝
"@

# Vérification des prérequis
Print-Status "Vérification des prérequis..."

# Vérifier Docker
try {
    $dockerVersion = docker --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker non trouvé"
    }
    Print-Success "Docker détecté: $dockerVersion"
} catch {
    Print-Error "Docker n'est pas installé ou n'est pas dans le PATH."
    Write-Host "Veuillez installer Docker Desktop: https://docs.docker.com/desktop/windows/"
    exit 1
}

# Vérifier Docker Compose
try {
    $composeVersion = docker-compose --version 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Compose non trouvé"
    }
    Print-Success "Docker Compose détecté: $composeVersion"
} catch {
    Print-Error "Docker Compose n'est pas installé."
    Write-Host "Docker Compose est généralement inclus avec Docker Desktop."
    exit 1
}

# Vérifier si Docker est en cours d'exécution
try {
    docker ps >$null 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Docker non démarré"
    }
    Print-Success "Docker est en cours d'exécution"
} catch {
    Print-Error "Docker n'est pas en cours d'exécution."
    Write-Host "Veuillez démarrer Docker Desktop."
    exit 1
}

# Vérifier si .env existe
if (-not (Test-Path ".env")) {
    Print-Warning "Fichier .env non trouvé. Création à partir du template..."
    
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Print-Success "Fichier .env créé à partir de .env.example"
        Print-Warning "IMPORTANT: Vous devez éditer le fichier .env avec vos vraies clés API!"
        Write-Host ""
        Write-Host "Variables critiques à configurer:"
        Write-Host "  - OPENAI_API_KEY"
        Write-Host "  - ALCHEMY_API_KEY (ou INFURA_API_KEY)"
        Write-Host "  - TELEGRAM_BOT_TOKEN"
        Write-Host "  - TELEGRAM_CHAT_ID"
        Write-Host ""
        $editEnv = Read-Host "Voulez-vous éditer le fichier .env maintenant? (y/N)"
        if ($editEnv -match "^[Yy]$") {
            if (Get-Command "code" -ErrorAction SilentlyContinue) {
                code .env
            } elseif (Get-Command "notepad++" -ErrorAction SilentlyContinue) {
                notepad++ .env
            } else {
                notepad .env
            }
        } else {
            Print-Warning "N'oubliez pas d'éditer .env avant de lancer l'application!"
        }
    } else {
        Print-Error "Fichier .env.example non trouvé!"
        exit 1
    }
} else {
    Print-Success "Fichier .env trouvé"
}

# Menu de sélection
if ($Mode -eq "menu") {
    Write-Host ""
    Print-Status "Choisissez le mode de déploiement:"
    Write-Host "1) Développement (application seule)"
    Write-Host "2) Production (avec MongoDB et Redis)"
    Write-Host "3) Complet (avec monitoring Prometheus/Grafana)"
    Write-Host "4) Arrêter tous les services"
    Write-Host "5) Voir les logs"
    Write-Host "6) Status des services"
    Write-Host "7) Nettoyer (supprimer containers et volumes)"
    Write-Host "8) Ouvrir les interfaces web"
    Write-Host ""
    $choice = Read-Host "Votre choix (1-8)"
} else {
    $choice = $Mode
}

switch ($choice) {
    "1" {
        Print-Status "Lancement en mode développement..."
        docker-compose up -d crypto-sentinel
    }
    "2" {
        Print-Status "Lancement en mode production..."
        docker-compose up -d
    }
    "3" {
        Print-Status "Lancement avec monitoring complet..."
        docker-compose --profile monitoring up -d
    }
    "4" {
        Print-Status "Arrêt de tous les services..."
        docker-compose down
        Print-Success "Services arrêtés"
        exit 0
    }
    "5" {
        Print-Status "Affichage des logs..."
        docker-compose logs -f --tail=50
        exit 0
    }
    "6" {
        Print-Status "Status des services..."
        docker-compose ps
        Write-Host ""
        Print-Status "Santé de l'application:"
        Start-Sleep 2
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
            $health | ConvertTo-Json -Depth 3
        } catch {
            Write-Host "Application non accessible"
        }
        exit 0
    }
    "7" {
        Print-Warning "Cette action va supprimer tous les containers et volumes!"
        $confirm = Read-Host "Êtes-vous sûr? (y/N)"
        if ($confirm -match "^[Yy]$") {
            Print-Status "Nettoyage en cours..."
            docker-compose down -v --remove-orphans
            docker system prune -f
            Print-Success "Nettoyage terminé"
        }
        exit 0
    }
    "8" {
        Print-Status "Ouverture des interfaces web..."
        Start-Process "http://localhost:8000"
        Start-Process "http://localhost:8000/docs"
        if ((docker-compose ps | Select-String "grafana").Count -gt 0) {
            Start-Process "http://localhost:3000"
            Start-Process "http://localhost:9090"
        }
        exit 0
    }
    default {
        Print-Error "Choix invalide"
        exit 1
    }
}

# Attendre que les services démarrent
Print-Status "Démarrage des services..."
Start-Sleep 10

# Vérifier le statut
Print-Status "Vérification du statut des services..."
docker-compose ps

Write-Host ""
Print-Status "Test de connectivité..."

# Tester l'application
$maxAttempts = 30
for ($i = 1; $i -le $maxAttempts; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -TimeoutSec 5 -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            Print-Success "Application démarrée avec succès!"
            break
        }
    } catch {
        if ($i -eq $maxAttempts) {
            Print-Error "L'application n'a pas pu démarrer dans les temps"
            Print-Status "Vérifiez les logs avec: docker-compose logs crypto-sentinel"
            exit 1
        }
        Write-Host -NoNewline "."
        Start-Sleep 2
    }
}

Write-Host ""
Print-Success "🚀 Crypto Sentinel est opérationnel!"
Write-Host ""
Write-Host "📊 Interfaces disponibles:"
Write-Host "  • Application: http://localhost:8000"
Write-Host "  • API Docs: http://localhost:8000/docs"
Write-Host "  • Health Check: http://localhost:8000/health"

if ((docker-compose ps | Select-String "grafana").Count -gt 0) {
    Write-Host "  • Grafana: http://localhost:3000 (admin/cryptosentinel2024)"
    Write-Host "  • Prometheus: http://localhost:9090"
}

Write-Host ""
Write-Host "📋 Commandes utiles:"
Write-Host "  • Voir les logs: docker-compose logs -f crypto-sentinel"
Write-Host "  • Arrêter: docker-compose down"
Write-Host "  • Redémarrer: docker-compose restart crypto-sentinel"
Write-Host "  • Status: docker-compose ps"
Write-Host "  • Relancer ce script: .\start.ps1"

Write-Host ""
Print-Status "Vérification de la santé de l'application..."
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
    $health | ConvertTo-Json -Depth 3
} catch {
    Write-Host "Erreur lors de la vérification de santé"
}

Write-Host ""
Print-Success "Installation terminée! 🎉"
Print-Warning "N'oubliez pas de configurer vos clés API dans le fichier .env"

# Proposer d'ouvrir les interfaces
$openBrowser = Read-Host "Voulez-vous ouvrir les interfaces web dans votre navigateur? (y/N)"
if ($openBrowser -match "^[Yy]$") {
    Start-Process "http://localhost:8000"
    Start-Process "http://localhost:8000/docs"
}