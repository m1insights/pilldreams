"""
Research Agent
Role: Active Research
Responsibility: Performs specific scientific queries and triggers data ingestion if needed.
"""

import sys
import json
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
import structlog
from duckduckgo_search import DDGS
import google.generativeai as genai
import os
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from core.supabase_client import get_client

load_dotenv()
logger = structlog.get_logger()

class ResearchAgent(BaseAgent):
    """
    AI Agent that researches companies and drugs using Web Search + LLM.
    """
    
    def __init__(self):
        self.agent_dir = Path(__file__).parent
        self.name = "Research Agent"
        self.role = "Research"
        self.db = get_client()
        
        # Initialize Gemini
        api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            logger.error("No Gemini API key found.")
            self.model = None
        else:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-flash-latest')

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task for the Research Agent.
        
        Supported actions:
        - research_company: Deep dive into a company
        - find_rcts: Find recent RCTs for a drug
        """
        action = task.get("action")
        
        if action == "research_company":
            return await self.research_company(task.get("params", {}))
        elif action == "find_rcts":
            return await self.find_rcts(task.get("params", {}))
        else:
            return {
                "status": "error",
                "result": f"Unknown action: {action}"
            }

    async def search_web(self, query: str, max_results: int = 5) -> str:
        """Helper to search web."""
        logger.info(f"Searching: {query}")
        results_text = ""
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results, backend="api"))
                for r in results:
                    results_text += f"Title: {r['title']}\nURL: {r['href']}\nSnippet: {r['body']}\n\n"
        except Exception as e:
            logger.error(f"Search failed for {query}", error=str(e))
        return results_text

    async def research_company(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Research a company's pipeline and focus."""
        ticker = params.get("ticker")
        company_name = params.get("company_name")
        
        if not ticker and not company_name:
            return {"status": "error", "result": "Missing ticker or company_name"}
            
        query = f"{company_name or ticker} investor relations pipeline corporate overview neuropsych"
        content = await self.search_web(query)
        
        if not content:
            return {"status": "warning", "result": "No search results found"}
            
        # Analyze with LLM
        if self.model:
            prompt = f"""
            You are a Biotech Research Analyst. 
            I have performed a web search for "{company_name or ticker}". 
            
            Search Results:
            {content}
            
            Your Task:
            1. Write a professional 1-paragraph "Company Description" (Business model, core technology, key disease areas).
            2. Identify "Preclinical/Discovery" assets that might be missing from clinical registries.
            
            Return JSON ONLY:
            {{
                "description": "string",
                "preclinical_assets": [
                    {{
                        "name": "string (e.g. VK0214)",
                        "mechanism": "string",
                        "indication": "string",
                        "source_url": "string (from search results)"
                    }}
                ]
            }}
            """
            try:
                response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                data = json.loads(response.text)
                
                # Save results (simplified logic from original script)
                # In a real scenario, we would update the DB here.
                
                return {"status": "success", "data": data}
            except Exception as e:
                return {"status": "error", "result": str(e)}
        
        return {"status": "success", "data": {"raw_content": content}}

    async def find_rcts(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Find recent RCTs for a drug."""
        drug_name = params.get("drug_name")
        if not drug_name:
            return {"status": "error", "result": "Missing drug_name"}
            
        query = f"{drug_name} randomized controlled trial clinical trial results 2024 2025"
        content = await self.search_web(query)
        
        if self.model:
            prompt = f"""
            Identify key RCT results for {drug_name} from these search results.
            
            Search Results:
            {content}
            
            Return a list of trials/results in JSON.
            """
            try:
                response = self.model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
                return {"status": "success", "rcts": json.loads(response.text)}
            except Exception as e:
                return {"status": "error", "result": str(e)}
                
        return {"status": "success", "data": content}

if __name__ == "__main__":
    agent = ResearchAgent()
    print(f"Initialized {agent.name}")
