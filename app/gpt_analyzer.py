#!/usr/bin/env python3
"""
Crypto Sentinel - GPT Analyzer Service

Service d'analyse IA utilisant GPT-4 pour évaluer le potentiel spéculatif
des tokens ERC20 et générer des scores et recommandations.

Author: Crypto Sentinel Team
Version: 1.0.0
"""

import asyncio
import json
import time
from typing import Optional, Dict, Any, List
from datetime import datetime

import openai
from openai import AsyncOpenAI

from app.config import settings
from app.models import (
    TokenInfo, TokenAnalysis, AIAnalysis, Recommendation,
    AnalysisStatus, create_token_analysis
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class GPTAnalyzerService:
    """Service d'analyse IA pour l'évaluation des tokens."""
    
    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self.timeout = settings.AI_ANALYSIS_TIMEOUT
        
        # Statistiques
        self.analyses_completed = 0
        self.total_tokens_used = 0
        self.total_cost_usd = 0.0
        self.average_analysis_time = 0.0
        self.last_analysis_time = None
        
        # Cache pour éviter les analyses répétées
        self._analysis_cache: Dict[str, AIAnalysis] = {}
        self._cache_ttl = settings.CACHE_TTL_SECONDS
    
    async def analyze_token(self, token_info: TokenInfo) -> TokenAnalysis:
        """Analyse complète d'un token avec IA."""
        start_time = time.time()
        
        try:
            logger.info(f"🤖 Début de l'analyse IA pour {token_info.contract_address}")
            
            # Créer l'objet d'analyse
            analysis = create_token_analysis(token_info)
            analysis.status = AnalysisStatus.PROCESSING
            
            # Vérifier le cache
            cached_result = self._get_cached_analysis(token_info.contract_address)
            if cached_result:
                logger.info(f"📋 Résultat en cache pour {token_info.contract_address}")
                analysis.ai_analysis = cached_result
                analysis.status = AnalysisStatus.COMPLETED
                analysis.analyzed_at = datetime.utcnow()
                return analysis
            
            # Préparer le prompt d'analyse
            prompt = self._build_analysis_prompt(token_info)
            
            # Appel à l'API OpenAI
            ai_result = await self._call_openai_api(prompt)
            
            if ai_result:
                # Parser la réponse IA
                ai_analysis = self._parse_ai_response(ai_result, start_time)
                
                if ai_analysis:
                    analysis.ai_analysis = ai_analysis
                    analysis.status = AnalysisStatus.COMPLETED
                    analysis.analyzed_at = datetime.utcnow()
                    
                    # Mettre en cache
                    self._cache_analysis(token_info.contract_address, ai_analysis)
                    
                    # Mettre à jour les statistiques
                    self._update_stats(ai_analysis, start_time)
                    
                    logger.info(f"✅ Analyse IA terminée - Score: {ai_analysis.score}/10")
                else:
                    analysis.status = AnalysisStatus.FAILED
                    analysis.error_message = "Erreur lors du parsing de la réponse IA"
            else:
                analysis.status = AnalysisStatus.FAILED
                analysis.error_message = "Erreur lors de l'appel à l'API OpenAI"
            
            return analysis
            
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'analyse IA: {e}")
            analysis = create_token_analysis(token_info)
            analysis.status = AnalysisStatus.FAILED
            analysis.error_message = str(e)
            return analysis
    
    def _build_analysis_prompt(self, token_info: TokenInfo) -> str:
        """Construit le prompt d'analyse pour l'IA."""
        # Calculs dérivés
        age_hours = token_info.age_hours or 0
        market_cap_formatted = self._format_number(token_info.market_cap_usd)
        liquidity_formatted = self._format_number(token_info.liquidity_usd)
        volume_formatted = self._format_number(token_info.volume_24h_usd)
        supply_formatted = self._format_number(token_info.total_supply)
        
        # Détection de patterns suspects
        suspicious_indicators = self._detect_suspicious_patterns(token_info)
        
        # Construction du prompt
        prompt = f"""
Tu es un expert en analyse de tokens crypto spécialisé dans la détection d'opportunités spéculatives précoces.

Analyse ce token ERC20 et donne-lui un score de 0 à 10 pour son potentiel spéculatif à court terme (pump possible).

=== INFORMATIONS DU TOKEN ===
Nom: {token_info.name or 'Non disponible'}
Symbole: {token_info.symbol or 'Non disponible'}
Adresse: {token_info.contract_address}
Âge: {age_hours:.1f} heures

=== MÉTRIQUES FINANCIÈRES ===
Prix: ${token_info.price_usd or 0:.8f}
Market Cap: {market_cap_formatted}
Liquidité: {liquidity_formatted}
Volume 24h: {volume_formatted}
Variation 24h: {token_info.price_change_24h or 0:.2f}%
Supply totale: {supply_formatted}
Nombre de holders: {token_info.holder_count or 0}

=== INDICATEURS TECHNIQUES ===
Nombre de transactions: {token_info.transaction_count or 0}
Ratio Liquidité/Market Cap: {self._calculate_liquidity_ratio(token_info):.2f}
Âge du token: {'Très récent (< 1h)' if age_hours < 1 else 'Récent (< 24h)' if age_hours < 24 else 'Établi'}

=== SIGNAUX D'ALERTE ===
{chr(10).join(suspicious_indicators) if suspicious_indicators else 'Aucun signal suspect détecté'}

=== CRITÈRES D'ÉVALUATION ===
1. **Potentiel viral** (25%) : Nom/symbole accrocheur, concept tendance
2. **Liquidité saine** (20%) : Liquidité suffisante sans être excessive
3. **Distribution équitable** (15%) : Pas de concentration excessive
4. **Timing optimal** (15%) : Lancé au bon moment, pas trop tôt/tard
5. **Activité communautaire** (10%) : Volume et transactions
6. **Facteurs de risque** (15%) : Détection de red flags

=== CONTEXTE MARCHÉ ===
Le marché crypto est actuellement {'haussier' if token_info.price_change_24h and token_info.price_change_24h > 0 else 'baissier'}.
Recherche des tokens avec un potentiel de x2 à x10 à court terme.

Réponds UNIQUEMENT au format JSON suivant (sans markdown, sans backticks) :
{{
  "score": 7.5,
  "reasoning": "Explication détaillée du score en 2-3 phrases",
  "risks": ["Risque principal 1", "Risque principal 2"],
  "opportunities": ["Opportunité 1", "Opportunité 2"],
  "recommendation": "BUY",
  "confidence": 0.85,
  "virality_score": 8.0,
  "liquidity_score": 7.0,
  "technical_score": 6.5,
  "community_score": 7.5
}}

Recommandations possibles: BUY (score ≥ 7), HOLD (score 5-6.9), AVOID (score < 5), RESEARCH (données insuffisantes)
"""
        
        return prompt
    
    async def _call_openai_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Appelle l'API OpenAI avec gestion d'erreurs."""
        try:
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Tu es un expert en analyse de tokens crypto. Réponds toujours en JSON valide."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    response_format={"type": "json_object"}
                ),
                timeout=self.timeout
            )
            
            return {
                "content": response.choices[0].message.content,
                "tokens_used": response.usage.total_tokens,
                "model": response.model
            }
            
        except asyncio.TimeoutError:
            logger.error("⏰ Timeout lors de l'appel à l'API OpenAI")
            return None
        except openai.RateLimitError:
            logger.error("🚫 Rate limit atteint sur l'API OpenAI")
            return None
        except openai.APIError as e:
            logger.error(f"❌ Erreur API OpenAI: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Erreur inattendue lors de l'appel OpenAI: {e}")
            return None
    
    def _parse_ai_response(self, ai_result: Dict[str, Any], start_time: float) -> Optional[AIAnalysis]:
        """Parse la réponse de l'IA en objet AIAnalysis."""
        try:
            content = ai_result["content"]
            tokens_used = ai_result.get("tokens_used", 0)
            model_used = ai_result.get("model", self.model)
            
            # Parser le JSON
            data = json.loads(content)
            
            # Validation des champs obligatoires
            required_fields = ["score", "reasoning", "recommendation", "confidence"]
            for field in required_fields:
                if field not in data:
                    logger.error(f"Champ manquant dans la réponse IA: {field}")
                    return None
            
            # Validation des valeurs
            score = float(data["score"])
            if not 0 <= score <= 10:
                logger.error(f"Score invalide: {score}")
                return None
            
            confidence = float(data["confidence"])
            if not 0 <= confidence <= 1:
                logger.error(f"Confidence invalide: {confidence}")
                return None
            
            # Validation de la recommandation
            recommendation_str = data["recommendation"].upper()
            try:
                recommendation = Recommendation(recommendation_str.lower())
            except ValueError:
                logger.error(f"Recommandation invalide: {recommendation_str}")
                recommendation = Recommendation.RESEARCH
            
            # Création de l'objet AIAnalysis
            analysis = AIAnalysis(
                score=score,
                reasoning=data["reasoning"],
                risks=data.get("risks", []),
                opportunities=data.get("opportunities", []),
                recommendation=recommendation,
                confidence=confidence,
                virality_score=data.get("virality_score"),
                liquidity_score=data.get("liquidity_score"),
                technical_score=data.get("technical_score"),
                community_score=data.get("community_score"),
                model_used=model_used,
                analysis_duration=time.time() - start_time,
                tokens_used=tokens_used
            )
            
            return analysis
            
        except json.JSONDecodeError as e:
            logger.error(f"Erreur de parsing JSON: {e}")
            logger.error(f"Contenu reçu: {ai_result.get('content', '')[:200]}...")
            return None
        except (ValueError, KeyError) as e:
            logger.error(f"Erreur de validation des données IA: {e}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors du parsing: {e}")
            return None
    
    def _detect_suspicious_patterns(self, token_info: TokenInfo) -> List[str]:
        """Détecte les patterns suspects dans le token."""
        indicators = []
        
        # Vérifications sur le nom et symbole
        name = (token_info.name or "").lower()
        symbol = (token_info.symbol or "").lower()
        
        # Patterns de noms suspects
        suspicious_keywords = [
            "safe", "moon", "rocket", "gem", "baby", "mini", "doge", "inu", "shib",
            "elon", "musk", "tesla", "100x", "1000x", "pump", "lambo"
        ]
        
        for keyword in suspicious_keywords:
            if keyword in name or keyword in symbol:
                indicators.append(f"⚠️ Nom/symbole suspect contient '{keyword}'")
                break
        
        # Vérifications sur la supply
        if token_info.total_supply and token_info.total_supply > 1e12:
            indicators.append("⚠️ Supply excessive (> 1 trillion)")
        
        # Vérifications sur la liquidité
        if token_info.liquidity_usd and token_info.liquidity_usd < 1000:
            indicators.append("⚠️ Liquidité très faible (< $1,000)")
        
        # Vérifications sur les holders
        if token_info.holder_count and token_info.holder_count < 10:
            indicators.append("⚠️ Très peu de holders (< 10)")
        
        # Vérifications sur l'âge
        age_hours = token_info.age_hours or 0
        if age_hours < 0.5:
            indicators.append("⚠️ Token extrêmement récent (< 30 min)")
        
        # Vérifications sur le prix
        if token_info.price_usd and token_info.price_usd < 1e-10:
            indicators.append("⚠️ Prix extrêmement bas (possible scam)")
        
        return indicators
    
    def _calculate_liquidity_ratio(self, token_info: TokenInfo) -> float:
        """Calcule le ratio liquidité/market cap."""
        if not token_info.liquidity_usd or not token_info.market_cap_usd:
            return 0.0
        
        if token_info.market_cap_usd == 0:
            return 0.0
        
        return token_info.liquidity_usd / token_info.market_cap_usd
    
    def _format_number(self, value: Optional[float]) -> str:
        """Formate un nombre pour l'affichage."""
        if value is None:
            return "Non disponible"
        
        if value == 0:
            return "$0"
        
        if value >= 1e9:
            return f"${value/1e9:.2f}B"
        elif value >= 1e6:
            return f"${value/1e6:.2f}M"
        elif value >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:.2f}"
    
    def _get_cached_analysis(self, contract_address: str) -> Optional[AIAnalysis]:
        """Récupère une analyse en cache si disponible."""
        cache_key = contract_address.lower()
        
        if cache_key in self._analysis_cache:
            cached_analysis, timestamp = self._analysis_cache[cache_key]
            
            # Vérifier si le cache est encore valide
            if time.time() - timestamp < self._cache_ttl:
                return cached_analysis
            else:
                # Supprimer l'entrée expirée
                del self._analysis_cache[cache_key]
        
        return None
    
    def _cache_analysis(self, contract_address: str, analysis: AIAnalysis):
        """Met en cache une analyse."""
        cache_key = contract_address.lower()
        self._analysis_cache[cache_key] = (analysis, time.time())
        
        # Nettoyer le cache si trop d'entrées
        if len(self._analysis_cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Nettoie les entrées expirées du cache."""
        current_time = time.time()
        expired_keys = [
            key for key, (_, timestamp) in self._analysis_cache.items()
            if current_time - timestamp >= self._cache_ttl
        ]
        
        for key in expired_keys:
            del self._analysis_cache[key]
        
        logger.info(f"🧹 Cache nettoyé: {len(expired_keys)} entrées supprimées")
    
    def _update_stats(self, analysis: AIAnalysis, start_time: float):
        """Met à jour les statistiques du service."""
        self.analyses_completed += 1
        self.total_tokens_used += analysis.tokens_used or 0
        
        # Calcul du coût (estimation basée sur GPT-4)
        if analysis.tokens_used:
            cost_per_token = 0.00003  # $0.03 per 1K tokens (estimation)
            self.total_cost_usd += (analysis.tokens_used / 1000) * cost_per_token
        
        # Temps d'analyse moyen
        analysis_time = time.time() - start_time
        if self.average_analysis_time == 0:
            self.average_analysis_time = analysis_time
        else:
            self.average_analysis_time = (
                (self.average_analysis_time * (self.analyses_completed - 1) + analysis_time)
                / self.analyses_completed
            )
        
        self.last_analysis_time = datetime.utcnow()
    
    async def analyze_batch(self, token_infos: List[TokenInfo]) -> List[TokenAnalysis]:
        """Analyse un lot de tokens en parallèle."""
        logger.info(f"🔄 Analyse en lot de {len(token_infos)} tokens")
        
        # Limiter la concurrence
        semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_ANALYSES)
        
        async def analyze_with_semaphore(token_info):
            async with semaphore:
                return await self.analyze_token(token_info)
        
        # Lancer les analyses en parallèle
        tasks = [analyze_with_semaphore(token_info) for token_info in token_infos]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filtrer les erreurs
        successful_analyses = [
            result for result in results
            if isinstance(result, TokenAnalysis) and result.status == AnalysisStatus.COMPLETED
        ]
        
        logger.info(f"✅ Analyse en lot terminée: {len(successful_analyses)}/{len(token_infos)} réussies")
        return successful_analyses
    
    def get_stats(self) -> Dict[str, Any]:
        """Récupère les statistiques du service."""
        return {
            "analyses_completed": self.analyses_completed,
            "total_tokens_used": self.total_tokens_used,
            "total_cost_usd": round(self.total_cost_usd, 4),
            "average_analysis_time": round(self.average_analysis_time, 2),
            "last_analysis_time": self.last_analysis_time,
            "cache_size": len(self._analysis_cache),
            "model_used": self.model
        }
    
    async def health_check(self) -> bool:
        """Vérifie l'état de santé du service."""
        try:
            # Test simple avec l'API OpenAI
            response = await asyncio.wait_for(
                self.client.chat.completions.create(
                    model="gpt-3.5-turbo",  # Modèle moins cher pour le test
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                ),
                timeout=10
            )
            return True
        except Exception as e:
            logger.error(f"Health check GPT échoué: {e}")
            return False