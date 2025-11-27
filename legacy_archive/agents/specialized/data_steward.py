"""
Data Steward Agent
Role: Infrastructure / Orchestration
Responsibility: Orchestrates ingestion scripts, self-healing, and QA checks.
"""

import asyncio
import structlog
from typing import Dict, Any, List
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from agents.base_agent import BaseAgent
from core.supabase_client import get_client

logger = structlog.get_logger()

class DataStewardAgent(BaseAgent):
    def __init__(self):
        # Initialize with hardcoded config for now since we're in a specialized directory
        self.agent_dir = Path(__file__).parent
        self.name = "Data Steward"
        self.role = "Infrastructure"
        self.db = get_client()
        
        # Define ingestion jobs
        # Define ingestion jobs
        self.jobs = {
            "clinical_trials": {
                "script": "ingestion/clinicaltrials.py",
                "dependencies": [],
                "frequency": "daily"
            },
            "chembl": {
                "script": "ingestion/chembl_binding.py",
                "dependencies": ["clinical_trials"], # Needs drugs first
                "frequency": "weekly"
            },
            "uniprot": {
                "script": "ingestion/uniprot.py",
                "dependencies": ["chembl"], # Needs targets from ChEMBL
                "frequency": "weekly"
            },
            "opentargets": {
                "script": "ingestion/opentargets.py",
                "dependencies": ["uniprot"], # Needs target info
                "frequency": "weekly"
            },
            "pubmed": {
                "script": "ingestion/pubmed.py",
                "dependencies": ["clinical_trials"], # Needs drugs
                "frequency": "daily"
            },
            "openfda": {
                "script": "ingestion/openfda.py",
                "dependencies": ["clinical_trials"], # Needs drugs
                "frequency": "weekly"
            },
            "nrdd": {
                "script": "ingestion/nrdd.py",
                "dependencies": ["clinical_trials"], # Needs drugs
                "frequency": "monthly"
            }
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task for the Data Steward.
        
        Supported actions:
        - run_ingestion: Run specific or all ingestion scripts
        - run_qa_checks: Run data quality checks
        """
        action = task.get("action")
        
        if action == "run_ingestion":
            return await self.run_ingestion_pipeline(task.get("params", {}))
        elif action == "run_qa_checks":
            return await self.run_qa_checks()
        else:
            return {
                "status": "error",
                "result": f"Unknown action: {action}"
            }

    async def run_ingestion_pipeline(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Orchestrate the ingestion pipeline.
        """
        target_job = params.get("job")
        test_mode = params.get("test_mode", False)
        
        results = {}
        
        # Determine execution order
        jobs_to_run = []
        if target_job:
            if target_job not in self.jobs:
                return {"status": "error", "result": f"Unknown job: {target_job}"}
            jobs_to_run = [target_job]
        else:
            # Simple topological sort (hardcoded for now as we only have 2 jobs)
            jobs_to_run = ["clinical_trials", "chembl"]
            
        for job_name in jobs_to_run:
            job_config = self.jobs[job_name]
            script_path = job_config["script"]
            
            logger.info(f"Starting job: {job_name}", script=script_path)
            
            try:
                # Construct command
                cmd = [sys.executable, script_path]
                if test_mode:
                    cmd.append("--test")
                    
                # Run script
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0:
                    logger.info(f"Job completed successfully: {job_name}")
                    results[job_name] = "success"
                    await self._log_event("INFO", f"Job {job_name} completed successfully")
                else:
                    logger.error(f"Job failed: {job_name}", stderr=stderr.decode())
                    results[job_name] = "failed"
                    await self._log_event("ERROR", f"Job {job_name} failed: {stderr.decode()[:200]}")
                    
                    # Simple retry logic could go here
                    
            except Exception as e:
                logger.error(f"Error running job {job_name}", error=str(e))
                results[job_name] = "error"
                await self._log_event("ERROR", f"Exception in job {job_name}: {str(e)}")
                
        return {
            "status": "success",
            "results": results
        }

    async def run_qa_checks(self) -> Dict[str, Any]:
        """
        Run data quality checks.
        """
        issues = []
        
        try:
            # Check 1: Trials with "Unknown" status
            unknown_status = self.db.client.table("trial").select("nct_id", count="exact").eq("status", "UNKNOWN").execute()
            if unknown_status.count > 0:
                issues.append(f"{unknown_status.count} trials have UNKNOWN status")
                
            # Check 2: Drugs with no targets (after ChEMBL run)
            # This is a bit complex to query directly via Supabase client without raw SQL, 
            # so we'll skip for now or use a simpler check.
            
            if issues:
                await self._log_event("WARNING", f"QA Checks found issues: {'; '.join(issues)}")
                return {"status": "warning", "issues": issues}
            
            await self._log_event("INFO", "QA Checks passed")
            return {"status": "success", "issues": []}
            
        except Exception as e:
            return {"status": "error", "result": str(e)}

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
    # Simple test
    agent = DataStewardAgent()
    asyncio.run(agent.execute_task({"action": "run_qa_checks"}))
