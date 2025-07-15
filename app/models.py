#!/usr/bin/env python3
"""
Crypto Sentinel - Data Models

Modèles de données Pydantic pour la validation et sérialisation des informations
de tokens, analyses IA, et statuts système.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
from bson import ObjectId


class PyObjectId(ObjectId):
    """Classe personnalisée pour gérer les ObjectId MongoDB avec Pydantic."""
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


class TokenSource(str, Enum):
    """Sources de détection des tokens."""
    ETHEREUM_WEBSOCKET = "ethereum_websocket"
    DEXSCREENER = "dexscreener"
    DEXTOOLS = "dextools"
    TELEGRAM = "telegram"
    TWITTER = "twitter"
    MANUAL = "manual"


class AnalysisStatus(str, Enum):
    """Statuts d'analyse des tokens."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class RiskLevel(str, Enum):
    """Niveaux de risque."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Recommendation(str, Enum):
    """Recommandations d'investissement."""
    BUY = "buy"
    HOLD = "hold"
    AVOID = "avoid"
    RESEARCH = "research"


class TokenInfo(BaseModel):
    """Informations de base d'un token ERC20."""
    
    contract_address: str = Field(..., description="Adresse du contrat")
    name: Optional[str] = Field(None, description="Nom du token")
    symbol: Optional[str] = Field(None, description="Symbole du token")
    decimals: Optional[int] = Field(None, description="Nombre de décimales")
    total_supply: Optional[float] = Field(None, description="Supply totale")
    
    # Informations de marché
    price_usd: Optional[float] = Field(None, description="Prix en USD")
    market_cap_usd: Optional[float] = Field(None, description="Market cap en USD")
    liquidity_usd: Optional[float] = Field(None, description="Liquidité en USD")
    volume_24h_usd: Optional[float] = Field(None, description="Volume 24h en USD")
    price_change_24h: Optional[float] = Field(None, description="Variation prix 24h (%)")
    
    # Informations techniques
    holder_count: Optional[int] = Field(None, description="Nombre de holders")
    transaction_count: Optional[int] = Field(None, description="Nombre de transactions")
    creation_block: Optional[int] = Field(None, description="Block de création")
    creation_timestamp: Optional[datetime] = Field(None, description="Timestamp de création")
    
    # Métadonnées
    source: TokenSource = Field(..., description="Source de détection")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Moment de détection")
    
    @validator('contract_address')
    def validate_contract_address(cls, v):
        if not v or len(v) != 42 or not v.startswith('0x'):
            raise ValueError('Invalid Ethereum contract address')
        return v.lower()
    
    @validator('price_usd', 'market_cap_usd', 'liquidity_usd', 'volume_24h_usd')
    def validate_positive_amounts(cls, v):
        if v is not None and v < 0:
            raise ValueError('Amount must be positive')
        return v
    
    @property
    def age_hours(self) -> Optional[float]:
        """Âge du token en heures."""
        if self.creation_timestamp:
            delta = datetime.utcnow() - self.creation_timestamp
            return delta.total_seconds() / 3600
        return None
    
    @property
    def is_new_token(self) -> bool:
        """Vérifie si le token est récent (< 24h)."""
        age = self.age_hours
        return age is not None and age < 24


class AIAnalysis(BaseModel):
    """Résultat de l'analyse IA d'un token."""
    
    score: float = Field(..., ge=0, le=10, description="Score IA (0-10)")
    reasoning: str = Field(..., description="Explication du score")
    risks: List[str] = Field(default_factory=list, description="Risques identifiés")
    opportunities: List[str] = Field(default_factory=list, description="Opportunités")
    recommendation: Recommendation = Field(..., description="Recommandation")
    confidence: float = Field(..., ge=0, le=1, description="Niveau de confiance (0-1)")
    
    # Scores détaillés
    virality_score: Optional[float] = Field(None, ge=0, le=10, description="Score de viralité")
    liquidity_score: Optional[float] = Field(None, ge=0, le=10, description="Score de liquidité")
    technical_score: Optional[float] = Field(None, ge=0, le=10, description="Score technique")
    community_score: Optional[float] = Field(None, ge=0, le=10, description="Score communauté")
    
    # Métadonnées
    model_used: str = Field(default="gpt-4", description="Modèle IA utilisé")
    analysis_duration: Optional[float] = Field(None, description="Durée d'analyse (secondes)")
    tokens_used: Optional[int] = Field(None, description="Tokens OpenAI utilisés")
    
    @property
    def risk_level(self) -> RiskLevel:
        """Détermine le niveau de risque basé sur le score."""
        if self.score >= 8:
            return RiskLevel.LOW
        elif self.score >= 6:
            return RiskLevel.MEDIUM
        elif self.score >= 4:
            return RiskLevel.HIGH
        else:
            return RiskLevel.CRITICAL
    
    @property
    def is_high_potential(self) -> bool:
        """Vérifie si le token a un potentiel élevé."""
        return self.score >= 7.0 and self.confidence >= 0.7


class SocialMetrics(BaseModel):
    """Métriques des réseaux sociaux."""
    
    telegram_mentions: Optional[int] = Field(None, description="Mentions Telegram")
    twitter_mentions: Optional[int] = Field(None, description="Mentions Twitter")
    reddit_mentions: Optional[int] = Field(None, description="Mentions Reddit")
    
    sentiment_score: Optional[float] = Field(None, ge=-1, le=1, description="Score sentiment (-1 à 1)")
    buzz_score: Optional[float] = Field(None, ge=0, le=10, description="Score de buzz (0-10)")
    
    trending_keywords: List[str] = Field(default_factory=list, description="Mots-clés tendance")
    influencer_mentions: List[str] = Field(default_factory=list, description="Mentions d'influenceurs")
    
    last_updated: datetime = Field(default_factory=datetime.utcnow, description="Dernière mise à jour")


class TokenAnalysis(BaseModel):
    """Analyse complète d'un token."""
    
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    # Informations du token
    token_info: TokenInfo = Field(..., description="Informations du token")
    
    # Analyses
    ai_analysis: Optional[AIAnalysis] = Field(None, description="Analyse IA")
    social_metrics: Optional[SocialMetrics] = Field(None, description="Métriques sociales")
    
    # Statut
    status: AnalysisStatus = Field(default=AnalysisStatus.PENDING, description="Statut d'analyse")
    error_message: Optional[str] = Field(None, description="Message d'erreur")
    
    # Métadonnées
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Date de création")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Dernière mise à jour")
    analyzed_at: Optional[datetime] = Field(None, description="Date d'analyse")
    
    # Notifications
    notification_sent: bool = Field(default=False, description="Notification envoyée")
    notification_sent_at: Optional[datetime] = Field(None, description="Date d'envoi notification")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
    
    @property
    def ai_score(self) -> Optional[float]:
        """Score IA du token."""
        return self.ai_analysis.score if self.ai_analysis else None
    
    @property
    def should_notify(self) -> bool:
        """Vérifie si une notification doit être envoyée."""
        return (
            not self.notification_sent and
            self.ai_analysis is not None and
            self.ai_analysis.is_high_potential and
            self.status == AnalysisStatus.COMPLETED
        )
    
    def mark_notified(self):
        """Marque comme notifié."""
        self.notification_sent = True
        self.notification_sent_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class SystemStatus(BaseModel):
    """Statut du système."""
    
    status: str = Field(..., description="Statut général (healthy/degraded/down)")
    database_connected: bool = Field(..., description="Base de données connectée")
    ethereum_connected: bool = Field(..., description="Ethereum connecté")
    services_running: int = Field(..., description="Nombre de services actifs")
    uptime: float = Field(..., description="Temps de fonctionnement (secondes)")
    
    # Métriques
    tokens_analyzed_today: Optional[int] = Field(None, description="Tokens analysés aujourd'hui")
    notifications_sent_today: Optional[int] = Field(None, description="Notifications envoyées aujourd'hui")
    average_analysis_time: Optional[float] = Field(None, description="Temps moyen d'analyse (secondes)")
    
    # Erreurs
    last_error: Optional[str] = Field(None, description="Dernière erreur")
    error_count_24h: Optional[int] = Field(None, description="Nombre d'erreurs 24h")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Timestamp du statut")


class NotificationAlert(BaseModel):
    """Alerte de notification."""
    
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    
    token_address: str = Field(..., description="Adresse du token")
    token_name: Optional[str] = Field(None, description="Nom du token")
    token_symbol: Optional[str] = Field(None, description="Symbole du token")
    
    ai_score: float = Field(..., description="Score IA")
    recommendation: Recommendation = Field(..., description="Recommandation")
    
    message: str = Field(..., description="Message de notification")
    sent_at: datetime = Field(default_factory=datetime.utcnow, description="Date d'envoi")
    
    # Métadonnées Telegram
    telegram_message_id: Optional[int] = Field(None, description="ID du message Telegram")
    telegram_chat_id: Optional[str] = Field(None, description="ID du chat Telegram")
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}


class AnalyticsData(BaseModel):
    """Données d'analytics."""
    
    date: datetime = Field(..., description="Date")
    
    # Compteurs
    tokens_detected: int = Field(default=0, description="Tokens détectés")
    tokens_analyzed: int = Field(default=0, description="Tokens analysés")
    notifications_sent: int = Field(default=0, description="Notifications envoyées")
    
    # Scores
    average_ai_score: Optional[float] = Field(None, description="Score IA moyen")
    high_score_tokens: int = Field(default=0, description="Tokens avec score élevé")
    
    # Performance
    average_analysis_time: Optional[float] = Field(None, description="Temps moyen d'analyse")
    api_calls_made: int = Field(default=0, description="Appels API effectués")
    errors_count: int = Field(default=0, description="Nombre d'erreurs")
    
    # Sources
    source_breakdown: Dict[str, int] = Field(default_factory=dict, description="Répartition par source")
    
    class Config:
        arbitrary_types_allowed = True


class WebSocketMessage(BaseModel):
    """Message WebSocket Ethereum."""
    
    method: str = Field(..., description="Méthode")
    params: Dict[str, Any] = Field(..., description="Paramètres")
    
    # Données de transaction
    transaction_hash: Optional[str] = Field(None, description="Hash de transaction")
    block_number: Optional[int] = Field(None, description="Numéro de block")
    from_address: Optional[str] = Field(None, description="Adresse expéditeur")
    to_address: Optional[str] = Field(None, description="Adresse destinataire")
    value: Optional[str] = Field(None, description="Valeur")
    gas: Optional[str] = Field(None, description="Gas")
    gas_price: Optional[str] = Field(None, description="Prix du gas")
    input_data: Optional[str] = Field(None, description="Données d'entrée")
    
    received_at: datetime = Field(default_factory=datetime.utcnow, description="Reçu à")
    
    @property
    def is_contract_creation(self) -> bool:
        """Vérifie si c'est une création de contrat."""
        return self.to_address is None or self.to_address == "0x"
    
    @property
    def has_input_data(self) -> bool:
        """Vérifie si la transaction a des données d'entrée."""
        return self.input_data is not None and len(self.input_data) > 2


# === FONCTIONS UTILITAIRES ===

def create_token_analysis(token_info: TokenInfo) -> TokenAnalysis:
    """Crée une nouvelle analyse de token."""
    return TokenAnalysis(
        token_info=token_info,
        status=AnalysisStatus.PENDING
    )


def create_notification_alert(
    token_analysis: TokenAnalysis,
    message: str
) -> NotificationAlert:
    """Crée une alerte de notification."""
    return NotificationAlert(
        token_address=token_analysis.token_info.contract_address,
        token_name=token_analysis.token_info.name,
        token_symbol=token_analysis.token_info.symbol,
        ai_score=token_analysis.ai_score or 0,
        recommendation=token_analysis.ai_analysis.recommendation if token_analysis.ai_analysis else Recommendation.RESEARCH,
        message=message
    )