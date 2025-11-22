"""
Supabase Agent - Database operations specialist

Handles all Supabase/PostgreSQL queries using Supabase MCP.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


class SupabaseAgent(BaseAgent):
    """
    Supabase agent for database operations.

    Responsibilities:
    - Query drugs, trials, safety data, scores
    - Insert/update records from ingestion
    - Aggregate data for scoring engine
    - Filter and transform results in execution environment
    """

    def __init__(self):
        super().__init__("agents/supabase_agent")

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute database task.

        Args:
            task: Task with action and params
                - action: 'query' | 'insert' | 'update' | etc.
                - params: Action-specific parameters

        Returns:
            Query results or operation status
        """
        task_id = task.get('task_id', 'unknown')
        action = task.get('action')
        params = task.get('params', {})

        logger.info(f"Supabase agent executing task", task_id=task_id, action=action)

        # Route to appropriate handler
        handlers = {
            'query_drugs': self._query_drugs,
            'query_trials': self._query_trials,
            'query_safety': self._query_safety,
            'query_scores': self._query_scores,
            'insert': self._insert,
            'update': self._update,
        }

        handler = handlers.get(action)
        if not handler:
            return {
                "task_id": task_id,
                "status": "error",
                "error": f"Unknown action: {action}"
            }

        try:
            result = await handler(params)
            return {
                "task_id": task_id,
                "status": "success",
                "result": result
            }
        except Exception as e:
            logger.error(f"Supabase task failed", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    async def _query_drugs(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query Drug table.

        TODO: Implement using Supabase MCP tools
        """
        drug_name = params.get('drug_name')
        limit = params.get('limit', 10)

        logger.info(f"Would query drugs", drug_name=drug_name, limit=limit)

        # Placeholder
        return []

    async def _query_trials(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Query and aggregate trial data.

        This demonstrates filtering in execution environment:
        - Fetch all trials
        - Filter active trials
        - Return summary (not all rows)
        """
        drug_id = params.get('drug_id')

        logger.info(f"Would query trials for drug_id: {drug_id}")

        # TODO: Implement with Supabase MCP
        # trials = await supabase.query('Trial', {'drug_id': drug_id})
        # active = [t for t in trials if t['status'] in ['Recruiting', 'Active']]
        # return {'total': len(trials), 'active': len(active), 'sample': active[:5]}

        # Placeholder
        return {
            "total_trials": 0,
            "active_trials": 0,
            "phases": {},
            "sample_trials": []
        }

    async def _query_safety(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Query SafetyAggregate table"""
        drug_id = params.get('drug_id')
        logger.info(f"Would query safety data for drug_id: {drug_id}")
        return []

    async def _query_scores(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Query DrugScores table"""
        drug_id = params.get('drug_id')
        logger.info(f"Would query scores for drug_id: {drug_id}")
        return {}

    async def _insert(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Insert records"""
        table = params.get('table')
        records = params.get('records', [])
        logger.info(f"Would insert {len(records)} records into {table}")
        return {"inserted": len(records)}

    async def _update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update records"""
        table = params.get('table')
        updates = params.get('updates', {})
        logger.info(f"Would update {table} with {updates}")
        return {"updated": 1}


# Singleton instance
_supabase_agent = None


def get_supabase_agent() -> SupabaseAgent:
    """Get or create supabase agent singleton"""
    global _supabase_agent
    if _supabase_agent is None:
        _supabase_agent = SupabaseAgent()
    return _supabase_agent
