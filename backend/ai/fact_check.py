"""
Fact-Check Service using Perplexity API

Verifies drug/target/company information against current web sources.
Returns discrepancies for admin review.

Usage:
    from backend.ai.fact_check import FactCheckService

    service = FactCheckService()
    result = await service.verify_drug("TAZEMETOSTAT", our_data={
        "company": "Ipsen",
        "phase": 4,
        "indications": ["Follicular lymphoma", "Epithelioid sarcoma"],
        "target": "EZH2"
    })
"""

import os
import json
import httpx
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"


class FactCheckService:
    """Service for fact-checking drug/target data using Perplexity API."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or PERPLEXITY_API_KEY
        if not self.api_key:
            raise ValueError("PERPLEXITY_API_KEY must be set in environment or passed to constructor")

    async def _call_perplexity(self, prompt: str, system_prompt: str = None) -> dict:
        """Make a call to Perplexity API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": "sonar-pro",  # Best model for fact-checking with citations
            "messages": messages,
            "temperature": 0.1,  # Low temperature for factual accuracy
            "max_tokens": 1500,
            "return_citations": True,
            "search_recency_filter": "month"  # Focus on recent information
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                PERPLEXITY_API_URL,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            return response.json()

    async def verify_drug(self, drug_name: str, our_data: dict) -> dict:
        """
        Verify drug information against current web sources.

        Args:
            drug_name: Name of the drug to verify
            our_data: Our current database record with fields:
                - company: str - Company developing/marketing the drug
                - phase: int - Clinical trial phase (1-4) or 0 for preclinical
                - indications: list[str] - Approved/investigated indications
                - target: str - Primary molecular target
                - chembl_id: str (optional) - ChEMBL identifier

        Returns:
            dict with:
                - verified_data: Perplexity's findings
                - discrepancies: List of differences found
                - has_discrepancies: bool
                - citations: List of sources used
                - raw_response: Full API response
        """
        system_prompt = """You are a pharmaceutical data verification assistant.
Your task is to verify drug development information against current sources.
Be precise and cite specific sources. If information conflicts, note it.
Focus on: current owner/developer, approval status, clinical phases, and indications."""

        prompt = f"""Verify the following information about the drug "{drug_name}":

OUR DATABASE CLAIMS:
- Developer/Owner: {our_data.get('company', 'Unknown')}
- Clinical Phase: {our_data.get('phase', 'Unknown')} {"(Approved)" if our_data.get('phase') == 4 else ""}
- Target: {our_data.get('target', 'Unknown')}
- Indications: {', '.join(our_data.get('indications', [])) or 'Unknown'}
{f"- ChEMBL ID: {our_data.get('chembl_id')}" if our_data.get('chembl_id') else ""}

Please verify each claim and respond with a JSON object:
{{
    "drug_name": "{drug_name}",
    "verified_company": "Current developer/marketer based on sources",
    "verified_phase": 0-4 (4 if approved, or highest clinical phase),
    "verified_target": "Primary molecular target",
    "verified_indications": ["list", "of", "current", "indications"],
    "approval_status": "approved/clinical/preclinical/discontinued",
    "recent_news": "Any significant recent developments (acquisitions, new approvals, trial results)",
    "discrepancies": [
        {{"field": "field_name", "ours": "our value", "verified": "correct value", "notes": "explanation"}}
    ],
    "confidence": 0.0-1.0,
    "verification_date": "{datetime.now().strftime('%Y-%m-%d')}"
}}

Only include discrepancies for fields where our data differs from verified sources.
Respond ONLY with the JSON object."""

        try:
            response = await self._call_perplexity(prompt, system_prompt)

            # Extract content from response
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = response.get("citations", [])

            # Parse JSON from response
            # Clean up response - remove markdown if present
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            try:
                verified_data = json.loads(content)
            except json.JSONDecodeError:
                verified_data = {"error": "Failed to parse response", "raw": content}

            discrepancies = verified_data.get("discrepancies", [])

            return {
                "drug_name": drug_name,
                "our_data": our_data,
                "verified_data": verified_data,
                "discrepancies": discrepancies,
                "has_discrepancies": len(discrepancies) > 0,
                "citations": citations,
                "checked_at": datetime.now().isoformat(),
                "raw_response": response
            }

        except httpx.HTTPStatusError as e:
            return {
                "drug_name": drug_name,
                "our_data": our_data,
                "error": f"API error: {e.response.status_code}",
                "error_detail": str(e),
                "checked_at": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "drug_name": drug_name,
                "our_data": our_data,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }

    async def verify_target(self, target_symbol: str, our_data: dict) -> dict:
        """
        Verify target information.

        Args:
            target_symbol: Gene/protein symbol (e.g., "EZH2", "HDAC1")
            our_data: Our current database record with fields:
                - name: str - Full name
                - family: str - Target family
                - class: str - Target class
                - drugs_in_development: list[str] - Known drugs targeting this
        """
        system_prompt = """You are a molecular biology data verification assistant.
Your task is to verify protein target information for drug development.
Focus on: gene function, druggability, and current drug development status."""

        prompt = f"""Verify information about the drug target "{target_symbol}":

OUR DATABASE CLAIMS:
- Full Name: {our_data.get('name', 'Unknown')}
- Family: {our_data.get('family', 'Unknown')}
- Class: {our_data.get('class', 'Unknown')}
- Drugs in Development: {', '.join(our_data.get('drugs_in_development', [])) or 'Unknown'}

Respond with a JSON object:
{{
    "target_symbol": "{target_symbol}",
    "verified_name": "Correct full name",
    "verified_family": "Protein family",
    "verified_function": "Brief description of biological function",
    "verified_drugs": ["list", "of", "known", "drugs", "targeting", "this"],
    "druggability": "high/medium/low",
    "discrepancies": [
        {{"field": "field_name", "ours": "our value", "verified": "correct value"}}
    ],
    "confidence": 0.0-1.0
}}

Respond ONLY with the JSON object."""

        try:
            response = await self._call_perplexity(prompt, system_prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = response.get("citations", [])

            # Parse JSON
            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            try:
                verified_data = json.loads(content)
            except json.JSONDecodeError:
                verified_data = {"error": "Failed to parse response", "raw": content}

            discrepancies = verified_data.get("discrepancies", [])

            return {
                "target_symbol": target_symbol,
                "our_data": our_data,
                "verified_data": verified_data,
                "discrepancies": discrepancies,
                "has_discrepancies": len(discrepancies) > 0,
                "citations": citations,
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "target_symbol": target_symbol,
                "our_data": our_data,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }

    async def verify_company(self, company_name: str, our_data: dict) -> dict:
        """
        Verify company information.

        Args:
            company_name: Company name
            our_data: Our current database record with fields:
                - ticker: str - Stock ticker
                - market_cap: float - Market capitalization
                - pipeline_drugs: list[str] - Known pipeline drugs
        """
        prompt = f"""Verify information about the pharmaceutical company "{company_name}":

OUR DATABASE CLAIMS:
- Stock Ticker: {our_data.get('ticker', 'Unknown')}
- Market Cap: ${our_data.get('market_cap', 'Unknown')}
- Pipeline Drugs: {', '.join(our_data.get('pipeline_drugs', [])) or 'Unknown'}

Respond with JSON:
{{
    "company_name": "{company_name}",
    "verified_ticker": "Correct ticker",
    "verified_exchange": "NYSE/NASDAQ/etc",
    "is_public": true/false,
    "verified_pipeline": ["list", "of", "epigenetic", "drugs"],
    "recent_news": "Recent acquisitions, partnerships, trial results",
    "discrepancies": [...],
    "confidence": 0.0-1.0
}}

Respond ONLY with the JSON object."""

        try:
            response = await self._call_perplexity(prompt)
            content = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            citations = response.get("citations", [])

            if "```" in content:
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            try:
                verified_data = json.loads(content)
            except json.JSONDecodeError:
                verified_data = {"error": "Failed to parse response", "raw": content}

            discrepancies = verified_data.get("discrepancies", [])

            return {
                "company_name": company_name,
                "our_data": our_data,
                "verified_data": verified_data,
                "discrepancies": discrepancies,
                "has_discrepancies": len(discrepancies) > 0,
                "citations": citations,
                "checked_at": datetime.now().isoformat()
            }

        except Exception as e:
            return {
                "company_name": company_name,
                "our_data": our_data,
                "error": str(e),
                "checked_at": datetime.now().isoformat()
            }


# Convenience functions for direct use
async def verify_drug(drug_name: str, our_data: dict) -> dict:
    """Verify a drug record. See FactCheckService.verify_drug for details."""
    service = FactCheckService()
    return await service.verify_drug(drug_name, our_data)


async def verify_target(target_symbol: str, our_data: dict) -> dict:
    """Verify a target record. See FactCheckService.verify_target for details."""
    service = FactCheckService()
    return await service.verify_target(target_symbol, our_data)


async def verify_company(company_name: str, our_data: dict) -> dict:
    """Verify a company record. See FactCheckService.verify_company for details."""
    service = FactCheckService()
    return await service.verify_company(company_name, our_data)
