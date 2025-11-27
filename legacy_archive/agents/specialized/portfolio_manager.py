
"""
Portfolio Manager Agent
Role: Synthesis / Analysis
Responsibility: Cross-references pipeline data with financials to generate investment insights.
"""

import asyncio
import json
import os
from dotenv import load_dotenv
import google.generativeai as genai
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from core.supabase_client import get_client

from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

class PortfolioManagerAgent(BaseAgent):
    def __init__(self):
        self.agent_dir = Path(__file__).parent
        self.name = "Portfolio Manager"
        self.role = "Analysis"
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
        Execute a task for the Portfolio Manager.
        
        Supported actions:
        - analyze_company: Analyze a specific company
        - generate_insights: Generate insights for all companies
        """
        action = task.get("action")
        
        if action == "analyze_company":
            return await self.analyze_company(task.get("params", {}))
        elif action == "generate_insights":
            return await self.generate_insights()
        elif action == "predict_catalysts":
            return await self.predict_catalysts(task.get("params", {}))
        else:
            return {
                "status": "error",
                "result": f"Unknown action: {action}"
            }

    async def analyze_company(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze a company for risks and opportunities.
        """
        company_id = params.get("company_id")
        if not company_id:
            return {"status": "error", "result": "Missing company_id"}
            
        try:
            # Fetch company data (financials)
            company = self.db.client.table("company").select("*").eq("id", company_id).single().execute()
            if not company.data:
                return {"status": "error", "result": "Company not found"}
                
            company_data = company.data
            cash_runway = company_data.get("cash_runway_months", 12) # Default to 12 if missing
            
            # Fetch pipeline (trials)
            # We need to join company -> company_drug -> drug -> trial
            # This is complex with Supabase client, so we'll approximate by fetching company_drug first
            
            company_drugs = self.db.client.table("company_drug").select("drug_id").eq("company_id", company_id).execute()
            drug_ids = [d["drug_id"] for d in company_drugs.data]
            
            insights = []
            
            if drug_ids:
                trials = self.db.client.table("trial").select("*").in_("drug_id", drug_ids).execute()
                
                for trial in trials.data:
                    completion_date_str = trial.get("primary_completion_date")
                    if completion_date_str:
                        completion_date = datetime.strptime(completion_date_str, "%Y-%m-%d")
                        runway_end_date = datetime.now() + timedelta(days=cash_runway * 30)
                        
                        # Insight: Dilution Risk
                        if completion_date > runway_end_date:
                            insights.append({
                                "type": "RISK",
                                "severity": "HIGH",
                                "title": "Dilution Risk",
                                "description": f"Trial {trial['nct_id']} reads out in {completion_date_str}, but cash runway ends in {int(cash_runway)} months.",
                                "supporting_data": {"trial_id": trial['nct_id'], "runway_months": cash_runway}
                            })
                            
                        # Insight: Near-term Catalyst
                        days_to_readout = (completion_date - datetime.now()).days
                        if 0 < days_to_readout < 90:
                            insights.append({
                                "type": "CATALYST",
                                "severity": "MEDIUM",
                                "title": "Near-term Readout",
                                "description": f"Trial {trial['nct_id']} reads out in {days_to_readout} days.",
                                "supporting_data": {"trial_id": trial['nct_id'], "days_to_readout": days_to_readout}
                            })

            # Save insights
            for insight in insights:
                try:
                    self.db.client.table("investmentinsight").insert({
                        "company_id": company_id,
                        "insight_type": insight["type"],
                        "severity": insight["severity"],
                        "title": insight["title"],
                        "description": insight["description"],
                        "supporting_data": insight["supporting_data"]
                    }).execute()
                except Exception as e:
                    logger.warning("Failed to save insight", error=str(e))
                    
            return {
                "status": "success",
                "insights": insights
            }
            
        except Exception as e:
            logger.error("Error analyzing company", error=str(e))
    async def predict_catalysts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Predict catalysts for a company using trial data + AI.
        """
        company_id = params.get("company_id")
        if not company_id:
            return {"status": "error", "result": "Missing company_id"}
            
        try:
            # 1. Get Trials
            # Mocking the join for now
            company_drugs = self.db.client.table("company_drug").select("drug_id").eq("company_id", company_id).execute()
            drug_ids = [d["drug_id"] for d in company_drugs.data]
            
            trials = []
            if drug_ids:
                trials_res = self.db.client.table("trial").select("*").in_("drug_id", drug_ids).execute()
                trials = trials_res.data
                
            # 2. Use AI to predict impact
            catalysts = []
            
            for trial in trials:
                completion_date = trial.get("primary_completion_date")
                if not completion_date:
                    continue
                    
                # Simple date check
                days_to_readout = (datetime.strptime(completion_date, "%Y-%m-%d") - datetime.now()).days
                
                if 0 < days_to_readout < 180: # Next 6 months
                    impact_prediction = "UNKNOWN"
                    confidence = 0.5
                    
                    if self.model:
                        prompt = f"""
                        Predict the market impact of this clinical trial readout:
                        Trial: {trial.get('nct_id')}
                        Phase: {trial.get('phase')}
                        Condition: {trial.get('condition')}
                        Title: {trial.get('title')}
                        
                        Output JSON:
                        {{
                            "impact": "HIGH" | "MEDIUM" | "LOW",
                            "rationale": "string",
                            "confidence": 0.0-1.0
                        }}
                        """
                        try:
                            res = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                            ai_data = json.loads(res.text)
                            impact_prediction = ai_data.get("impact", "UNKNOWN")
                            confidence = ai_data.get("confidence", 0.5)
                        except Exception as e:
                            logger.error("AI prediction failed", error=str(e))
                            
                    catalysts.append({
                        "trial_id": trial.get("nct_id"),
                        "date": completion_date,
                        "impact": impact_prediction,
                        "confidence": confidence
                    })
            
            return {
                "status": "success",
                "catalysts": catalysts
            }
            
        except Exception as e:
            logger.error("Error predicting catalysts", error=str(e))
            return {"status": "error", "result": str(e)}

    async def generate_insights(self) -> Dict[str, Any]:
        """
        Generate insights for all companies (batch job).
        """
        # In a real app, we would iterate over all companies.
        # For now, we'll just return a placeholder.
        return {"status": "success", "message": "Batch analysis not yet implemented"}

if __name__ == "__main__":
    agent = PortfolioManagerAgent()
    print(f"Initialized {agent.name}")
