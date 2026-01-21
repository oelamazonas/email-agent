"""
Email classifier utilisant Ollama (local LLM)
"""
import httpx
import json
import logging
from typing import Dict, Optional, List
from datetime import datetime

from shared.config import settings
from api.models import EmailCategory

logger = logging.getLogger(__name__)


class EmailClassifier:
    """Classificateur d'emails utilisant Ollama"""
    
    def __init__(self):
        self.ollama_host = settings.OLLAMA_HOST
        self.model = settings.OLLAMA_MODEL
        self.timeout = settings.OLLAMA_TIMEOUT
        
    async def classify_email(
        self,
        subject: str,
        sender: str,
        body_preview: str,
        has_attachments: bool = False,
        attachment_names: Optional[List[str]] = None
    ) -> Dict:
        """
        Classifier un email
        
        Returns:
            {
                'category': EmailCategory,
                'confidence': int (0-100),
                'reason': str
            }
        """
        try:
            # Construire le prompt pour le LLM
            prompt = self._build_classification_prompt(
                subject, sender, body_preview, has_attachments, attachment_names
            )
            
            # Appeler Ollama
            response = await self._call_ollama(prompt)
            
            # Parser la réponse
            classification = self._parse_llm_response(response)
            
            return classification
            
        except Exception as e:
            logger.error(f"Classification error: {e}")
            return {
                'category': EmailCategory.UNKNOWN,
                'confidence': 0,
                'reason': f'Error during classification: {str(e)}'
            }
    
    def _build_classification_prompt(
        self,
        subject: str,
        sender: str,
        body_preview: str,
        has_attachments: bool,
        attachment_names: Optional[List[str]]
    ) -> str:
        """Construire le prompt pour la classification"""
        
        prompt = f"""Tu es un expert en classification d'emails. Ton objectif est de trier les emails pour une organisation efficace.

RÈGLES DE PRIORITÉ :
1. "invoice" et "receipt" sont PRIORITAIRES si l'email contient une preuve d'achat/paiement, même s'il s'agit d'un échange professionnel.
2. "spam" est prioritaire si le contenu est manifestement indésirable.
3. Si un email relève de plusieurs catégories, choisis la plus spécifique au contenu principal.

Catégories disponibles :
- invoice: Factures, demandes de paiement (contient montant, TVA, IBAN, ou pièce jointe "facture").
- receipt: Reçus, confirmations de commande/paiement.
- document: Envoi de fichiers/documents (Google Drive, WeTransfer, PJ importante sans contexte financier).
- professional: Échanges pro, réunions, projets, RH.
- newsletter: Contenu éditorial récurrent, veille.
- promotion: Offres commerciales, pubs, réductions.
- social: Notifications LinkedIn, etc.
- notification: Alertes système, confirmations automatiques (création de compte, sécurité).
- personal: Famille, amis, contexte non-pro.
- spam: Arnaques, phishing, junk.

INSTRUCTIONS DE SORTIE :
- Réponds UNIQUEMENT avec un objet JSON valide.
- N'écris AUCUN texte avant ou après le JSON.
- N'utilise PAS de balises markdown (comme ```json).

EXEMPLE DE SORTIE ATTENDUE :
{{
    "category": "invoice",
    "confidence": 95,
    "reason": "L'email contient une pièce jointe 'facture_001.pdf' et mentionne un montant à régler."
}}

EMAIL À CLASSIFIER :
---
Expéditeur: {sender}
Sujet: {subject}
Corps (aperçu): {body_preview[:1000]}
Pièces jointes: {has_attachments}
{f"Noms des pièces jointes: {', '.join(attachment_names)}" if attachment_names else ""}
---"""
        
        return prompt
    
    async def _call_ollama(self, prompt: str) -> str:
        """Appeler l'API Ollama"""
        url = f"{self.ollama_host}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.1,  # Peu de créativité, plus de cohérence
                "top_p": 0.9,
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                result = response.json()
                return result.get('response', '')
            except httpx.TimeoutException:
                logger.error("Ollama request timeout")
                raise Exception("LLM request timeout")
            except httpx.HTTPError as e:
                logger.error(f"Ollama HTTP error: {e}")
                raise Exception(f"LLM HTTP error: {e}")
    
    def _parse_llm_response(self, response: str) -> Dict:
        """Parser la réponse du LLM"""
        try:
            # Nettoyer la réponse (parfois le LLM ajoute du texte avant/après)
            response = response.strip()
            
            # Trouver le JSON dans la réponse
            start = response.find('{')
            end = response.rfind('}') + 1
            
            if start == -1 or end == 0:
                raise ValueError("No JSON found in response")
            
            json_str = response[start:end]
            data = json.loads(json_str)
            
            # Valider les champs
            category_str = data.get('category', 'unknown').lower()
            
            # Mapper vers EmailCategory
            category_mapping = {
                'invoice': EmailCategory.INVOICE,
                'receipt': EmailCategory.RECEIPT,
                'document': EmailCategory.DOCUMENT,
                'professional': EmailCategory.PROFESSIONAL,
                'newsletter': EmailCategory.NEWSLETTER,
                'promotion': EmailCategory.PROMOTION,
                'social': EmailCategory.SOCIAL,
                'notification': EmailCategory.NOTIFICATION,
                'personal': EmailCategory.PERSONAL,
                'spam': EmailCategory.SPAM,
            }
            
            category = category_mapping.get(category_str, EmailCategory.UNKNOWN)
            confidence = min(100, max(0, int(data.get('confidence', 50))))
            reason = data.get('reason', 'No reason provided')
            
            return {
                'category': category,
                'confidence': confidence,
                'reason': reason
            }
            
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Response was: {response[:200]}")
            
            # Fallback: classification basique par règles
            return self._fallback_classification(response)
    
    def _fallback_classification(self, response: str) -> Dict:
        """Classification de secours basée sur des règles simples"""
        return {
            'category': EmailCategory.UNKNOWN,
            'confidence': 20,
            'reason': 'Fallback classification - LLM response could not be parsed'
        }


# Instance globale
classifier = EmailClassifier()
