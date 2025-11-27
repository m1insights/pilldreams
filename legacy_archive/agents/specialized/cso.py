"""
Chief Scientific Officer (CSO) Agent
Role: Research / Synthesis
Responsibility: Synthesizes scientific data (ChEMBL, UniProt, PubMed) and validates claims.
"""

import asyncio
import structlog
from typing import Dict, Any, List, Optional
import sys
from pathlib import Path
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from core.supabase_client import get_client

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

class CSOAgent(BaseAgent):
    def __init__(self):
        self.agent_dir = Path(__file__).parent
        self.name = "Chief Scientific Officer"
        self.role = "Research"
        self.db = get_client()
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.warning("No Gemini API key found. AI features will be disabled.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task for the CSO.
        
        Supported actions:
        - synthesize_mechanism: Generate MoA summary for a drug
        - validate_science: Check scientific validity of a drug
        """
        action = task.get("action")
        
        if action == "synthesize_mechanism":
            return await self.synthesize_mechanism(task.get("params", {}))
        elif action == "validate_science":
            return await self.validate_science(task.get("params", {}))
        elif action == "validate_science":
            return await self.validate_science(task.get("params", {}))
        elif action == "explain_mechanism":
            return await self.explain_mechanism(task.get("params", {}))
        elif action == "compare_drugs":
            return await self.compare_drugs(task.get("params", {}))
        elif action == "explain_disease_landscape":
            return await self.explain_disease_landscape(task.get("params", {}))
        else:
            return {
                "status": "error",
                "result": f"Unknown action: {action}"
            }

    async def synthesize_mechanism(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize Mechanism of Action (MoA) summary.
        """
        drug_id = params.get("drug_id")
        if not drug_id:
            return {"status": "error", "result": "Missing drug_id"}
            
        try:
            # Fetch drug data
            drug = self.db.client.table("drug").select("*").eq("id", drug_id).single().execute()
            if not drug.data:
                return {"status": "error", "result": "Drug not found"}
                
            drug_data = drug.data
            drug_name = drug_data.get("name")
            
            # Fetch targets
            targets = self.db.client.table("drugtarget").select("*, target(*)").eq("drug_id", drug_id).execute()
            
            # Synthesize summary (Mock logic for now as we don't have LLM integration here yet)
            # In a real scenario, we would call an LLM with the target data and PubMed abstracts.
            
            target_names = [t["target"]["symbol"] for t in targets.data] if targets.data else []
            target_str = ", ".join(target_names) if target_names else "unknown targets"
            
            summary = f"{drug_name} acts primarily by targeting {target_str}. "
            if targets.data:
                primary_target = targets.data[0]
                affinity = primary_target.get("affinity_value")
                unit = primary_target.get("affinity_unit")
                if affinity:
                    summary += f"It shows a binding affinity of {affinity} {unit} against {primary_target['target']['symbol']}."
            
            # Store summary
            # Note: This might fail if the table doesn't exist (migration failed)
            try:
                self.db.client.table("scientificsummary").upsert({
                    "drug_id": drug_id,
                    "mechanism_of_action": summary,
                    "science_score": 85.0 if targets.data else 40.0
                }).execute()
            except Exception as e:
                logger.warning("Failed to save summary to DB (table might be missing)", error=str(e))
            
            # Synthesize summary
            if self.model:
                prompt = f"""
                Explain the mechanism of action for {drug_name}.
                Targets: {target_str}
                
                Explain:
                1. How it works (molecular level)
                2. Why it matters for Neuropsych (Depression/Anxiety/ADHD)
                3. Key differences from standard of care
                
                Keep it concise (under 200 words).
                """
                try:
                    response = self.model.generate_content(prompt)
                    summary = response.text
                except Exception as e:
                    logger.error("Gemini generation failed", error=str(e))
                    # Fallback to simple summary
                    summary = f"{drug_name} acts primarily by targeting {target_str}."
            else:
                summary = f"{drug_name} acts primarily by targeting {target_str}."
            
            if targets.data:
                primary_target = targets.data[0]
                affinity = primary_target.get("affinity_value")
                unit = primary_target.get("affinity_unit")
                if affinity:
                    summary += f" It shows a binding affinity of {affinity} {unit} against {primary_target['target']['symbol']}."
            
            # Store summary
            # Note: This might fail if the table doesn't exist (migration failed)
            try:
                self.db.client.table("scientificsummary").upsert({
                    "drug_id": drug_id,
                    "mechanism_of_action": summary,
                    "science_score": 85.0 if targets.data else 40.0
                }).execute()
            except Exception as e:
                logger.warning("Failed to save summary to DB (table might be missing)", error=str(e))
            
            return {
                "status": "success",
                "summary": summary
            }
            
        except Exception as e:
            logger.error("Error synthesizing mechanism", error=str(e))
            return {"status": "error", "result": str(e)}

    async def validate_science(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate scientific claims.
        """
        drug_id = params.get("drug_id")
        if not drug_id:
            return {"status": "error", "result": "Missing drug_id"}
            
        try:
            # Fetch targets and affinity
            targets = self.db.client.table("drugtarget").select("*").eq("drug_id", drug_id).execute()
            
            warnings = []
            score = 100.0
            
            if not targets.data:
                warnings.append("No known targets found in ChEMBL")
                score -= 40.0
            else:
                for target in targets.data:
                    # Check for weak affinity (e.g. > 1000 nM)
                    affinity = target.get("affinity_value")
                    unit = target.get("affinity_unit")
                    
                    if unit == "nM" and affinity and affinity > 1000:
                        warnings.append(f"Weak affinity ({affinity} nM) for target")
                        score -= 20.0
                        
            return {
                "status": "success",
                "score": max(0.0, score),
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error("Error validating science", error=str(e))
            return {"status": "error", "result": str(e)}
    async def explain_mechanism(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Alias for synthesize_mechanism for now, but could be more detailed."""
        return await self.synthesize_mechanism(params)

    async def compare_drugs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Compare two drugs using AI."""
        drug_a_name = params.get("drug_a")
        drug_b_name = params.get("drug_b")
        
        if not drug_a_name or not drug_b_name:
            return {"status": "error", "result": "Missing drug names"}
            
        if not self.model:
            return {"status": "error", "result": "AI not available"}
            
        prompt = f"""
        Compare {drug_a_name} vs {drug_b_name} for Neuropsych indications (Depression/Anxiety/ADHD).
        
        Create a comparison table (JSON format) with columns:
        - Mechanism
        - Onset Speed
        - Side Effects
        - Evidence Strength
        - Regulatory Status
        
        Return JSON ONLY.
        """
        
        try:
            response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
            return {"status": "success", "comparison": json.loads(response.text)}
        except Exception as e:
            return {"status": "error", "result": str(e)}

    async def explain_disease_landscape(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Explain the landscape for a disease."""
        indication = params.get("indication")
        if not indication:
            return {"status": "error", "result": "Missing indication"}
            
        if not self.model:
            return {"status": "error", "result": "AI not available"}
            
        prompt = f"""
        Explain the drug development landscape for {indication}.
        
        Cover:
        1. Validated targets
        2. Emerging targets
        3. Key pathways
        4. Most innovative drugs in development
        
        Return as Markdown.
        """
        
        try:
            response = self.model.generate_content(prompt)
            return {"status": "success", "landscape": response.text}
        except Exception as e:
            return {"status": "error", "result": str(e)}
if __name__ == "__main__":
    # Simple test
    agent = CSOAgent()
    # We can't really test without a valid drug_id, so just print initialized
    print(f"Initialized {agent.name}")
