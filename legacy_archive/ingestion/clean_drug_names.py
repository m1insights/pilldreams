
import os
import sys
import json
import time
import asyncio
from typing import List, Dict
from pathlib import Path
import structlog
from dotenv import load_dotenv
from anthropic import AsyncAnthropic

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

class DrugNameCleaner:
    def __init__(self):
        self.db = get_client()
        # User requested "claude-haiku-4-5", mapping to Claude 3.5 Haiku
        self.client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-haiku-20241022" 
        self.batch_size = 20

    async def get_candidates(self) -> List[Dict]:
        """Fetch drugs that don't have a ChEMBL ID yet."""
        response = self.db.client.table("drug").select("id, name").is_("chembl_id", "null").execute()
        return response.data

    async def clean_batch(self, drugs: List[Dict]) -> List[Dict]:
        """Send a batch of drug names to LLM for cleaning."""
        names = [d["name"] for d in drugs]
        
        prompt = f"""
        You are a pharmaceutical data expert. I have a list of strings from a clinical trials database that are supposed to be drug names.
        Some are valid drugs (maybe with messy suffixes), some are procedures/tests (junk).

        For each string, determine:
        1. Is it a drug/therapeutic agent? (True/False)
           - TRUE: Small molecules, biologics, vaccines, cell therapies, dietary supplements.
           - FALSE: Procedures (surgery, radiation), diagnostics (blood test, MRI), behavioral interventions, "Standard of Care", "Placebo".
        2. If TRUE, provide the clean, normalized name.
           - Remove dosages ("10 mg"), formulations ("tablet"), salts ("hydrochloride" - optional, but keep if common).
           - Map brand names to generic if possible (e.g., "Opdualag" -> "Nivolumab + Relatlimab").
           - If it's a combination, list the main ingredients.

        Input List:
        {json.dumps(names, indent=2)}

        Return ONLY a JSON list of objects with these keys:
        - "original": The input string (exact match)
        - "is_drug": boolean
        - "clean_name": string (or null if not a drug)
        - "reason": brief string explaining why (e.g., "Diagnostic test", "Dosage removed")
        """

        try:
            message = await self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                temperature=0,
                system="You are a precise data cleaning assistant. Output valid JSON only.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            content = message.content[0].text
            # Extract JSON if there's extra text
            start = content.find('[')
            end = content.rfind(']') + 1
            if start == -1 or end == 0:
                logger.error("Failed to parse LLM response", content=content)
                return []
                
            return json.loads(content[start:end])

        except Exception as e:
            logger.error("LLM request failed", error=str(e))
            return []

    async def process_results(self, original_drugs: List[Dict], results: List[Dict]):
        """Update database based on LLM results."""
        name_to_id = {d["name"]: d["id"] for d in original_drugs}
        
        for result in results:
            original = result.get("original")
            drug_id = name_to_id.get(original)
            
            if not drug_id:
                continue
                
            if not result.get("is_drug"):
                logger.info("Marking as junk", name=original, reason=result.get("reason"))
                try:
                    self.db.client.table("trial_intervention").delete().eq("drug_id", drug_id).execute()
                    self.db.client.table("company_drug").delete().eq("drug_id", drug_id).execute()
                    self.db.client.table("drug").delete().eq("id", drug_id).execute()
                    logger.info("Deleted junk record", name=original)
                except Exception as e:
                    logger.error("Failed to delete junk", name=original, error=str(e))

            else:
                clean_name = result.get("clean_name")
                if clean_name and clean_name != original:
                    try:
                        self.db.client.table("drug").update({"name": clean_name}).eq("id", drug_id).execute()
                        logger.info("Updated drug name", original=original, new=clean_name)
                    except Exception as e:
                        logger.error("Failed to update name", original=original, error=str(e))

    async def run(self):
        candidates = await self.get_candidates()
        logger.info(f"Found {len(candidates)} drugs to clean.")
        
        for i in range(0, len(candidates), self.batch_size):
            batch = candidates[i : i + self.batch_size]
            logger.info(f"Processing batch {i} to {i+len(batch)}...")
            
            results = await self.clean_batch(batch)
            if results:
                await self.process_results(batch, results)
            
            time.sleep(0.5) # Rate limit

if __name__ == "__main__":
    cleaner = DrugNameCleaner()
    asyncio.run(cleaner.run())
