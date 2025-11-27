"""
News Hound Agent
Role: Event / News
Responsibility: Watches RSS feeds and contextualizes news for the database.
"""

import asyncio
import structlog
from typing import Dict, Any, List, Optional
from datetime import datetime
import sys
from pathlib import Path
import feedparser

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from core.supabase_client import get_client

logger = structlog.get_logger()

class NewsHoundAgent(BaseAgent):
    def __init__(self):
        self.agent_dir = Path(__file__).parent
        self.name = "News Hound"
        self.role = "Event"
        self.db = get_client()
        
        # RSS Feeds to watch
        self.feeds = {
            "fda_approvals": "https://www.fda.gov/about-fda/contact-fda/stay-informed/rss-feeds/fda-news-releases/rss.xml",
            "sec_filings": "https://www.sec.gov/news/pressreleases.rss", # Placeholder
            "biotech_news": "https://feeds.feedburner.com/FierceBiotech" # Placeholder
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task for the News Hound.
        
        Supported actions:
        - check_feeds: Check RSS feeds for new items
        - process_news: Process a specific news item
        """
        action = task.get("action")
        
        if action == "check_feeds":
            return await self.check_feeds()
        elif action == "process_news":
            return await self.process_news(task.get("params", {}))
        else:
            return {
                "status": "error",
                "result": f"Unknown action: {action}"
            }

    async def check_feeds(self) -> Dict[str, Any]:
        """
        Check all configured RSS feeds.
        """
        new_events = []
        
        for feed_name, feed_url in self.feeds.items():
            try:
                logger.info(f"Checking feed: {feed_name}")
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:5]: # Check top 5
                    # Check if already processed (simple check by title)
                    # In production, use a dedicated tracking table or hash
                    existing = self.db.client.table("newsevent").select("id").eq("title", entry.title).execute()
                    
                    if not existing.data:
                        # New event!
                        event = await self.process_news({
                            "title": entry.title,
                            "url": entry.link,
                            "source": feed_name,
                            "published_at": entry.get("published", datetime.now().isoformat()),
                            "summary": entry.get("summary", "")
                        })
                        new_events.append(event)
                        
            except Exception as e:
                logger.error(f"Error checking feed {feed_name}", error=str(e))
                
        return {
            "status": "success",
            "new_events_count": len(new_events),
            "new_events": new_events
        }

    async def process_news(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a news item and link it to DB entities.
        """
        title = params.get("title")
        url = params.get("url")
        source = params.get("source")
        published_at = params.get("published_at")
        summary = params.get("summary")
        
        # 1. Contextualize: Find related companies/drugs
        # Simple keyword matching for now
        related_company_ids = []
        related_drug_ids = []
        
        # Fetch all companies (inefficient, but works for small DB)
        companies = self.db.client.table("company").select("id, name, ticker").execute()
        for company in companies.data:
            if company["name"].lower() in title.lower() or (company["ticker"] and company["ticker"] in title):
                related_company_ids.append(company["id"])
                
        # Fetch all drugs
        drugs = self.db.client.table("drug").select("id, name").execute()
        for drug in drugs.data:
            if drug["name"].lower() in title.lower():
                related_drug_ids.append(drug["id"])
                
        # 2. Determine Event Type
        event_type = "GENERAL"
        if "approval" in title.lower() or "approved" in title.lower():
            event_type = "FDA_APPROVAL"
        elif "trial" in title.lower() or "phase" in title.lower():
            event_type = "CLINICAL_TRIAL"
        elif "earnings" in title.lower() or "financial" in title.lower():
            event_type = "FINANCIAL"
            
        # 3. Save to DB
        try:
            result = self.db.client.table("newsevent").insert({
                "title": title,
                "url": url,
                "source": source,
                "published_at": published_at, # Needs parsing if raw string
                "summary": summary,
                "related_company_ids": related_company_ids,
                "related_drug_ids": related_drug_ids,
                "event_type": event_type
            }).execute()
            
            logger.info("Saved news event", title=title)
            
            # 4. Trigger updates (e.g. update trial status)
            # If it's a trial update, we might want to flag it for the Data Steward
            if event_type == "CLINICAL_TRIAL" and related_drug_ids:
                await self._log_event("INFO", f"Potential trial update for drugs: {related_drug_ids}")
                
            return result.data[0] if result.data else {}
            
        except Exception as e:
            logger.error("Failed to save news event", error=str(e))
            return {}

    async def _log_event(self, level: str, message: str):
        """Log event to database"""
        try:
            self.db.client.table("agentlog").insert({
                "agent_name": self.name,
                "log_level": level,
                "message": message
            }).execute()
        except Exception as e:
            logger.error("Failed to write to AgentLog", error=str(e))

if __name__ == "__main__":
    agent = NewsHoundAgent()
    print(f"Initialized {agent.name}")
