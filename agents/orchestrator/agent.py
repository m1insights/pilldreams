"""
Orchestrator Agent - Main coordinator for pilldreams

Routes tasks to specialized agents based on task classification.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from typing import Dict, Any, List
import structlog
import asyncio

logger = structlog.get_logger()


class OrchestratorAgent(BaseAgent):
    """
    Orchestrator agent that coordinates specialist agents.

    Responsibilities:
    - Classify incoming tasks
    - Route to appropriate specialist(s)
    - Aggregate results
    - Maintain session state
    """

    def __init__(self):
        super().__init__("agents/orchestrator")
        self.specialists = {}
        self._load_specialists()

    def _load_specialists(self):
        """
        Load specialist agents from config.

        In production, this would instantiate actual agent classes.
        For now, we'll use a registry pattern.
        """
        specialist_names = self.config.get('specialist_agents', [])

        for name in specialist_names:
            # TODO: Import and instantiate actual agent classes
            self.specialists[name] = None
            logger.info(f"Registered specialist: {name}")

    def classify_task(self, query: str) -> List[str]:
        """
        Classify task to determine which specialists to invoke.

        Args:
            query: User query or task description

        Returns:
            List of specialist agent names to invoke
        """
        specialists = []

        # Database operations
        if any(kw in query.lower() for kw in ['query', 'fetch', 'database', 'trials', 'drug data']):
            specialists.append('supabase_agent')

        # Web scraping
        if any(kw in query.lower() for kw in ['scrape', 'drugbank', 'reddit', 'web']):
            specialists.append('playwright_agent')

        # Visualization
        if any(kw in query.lower() for kw in ['visualize', 'chart', 'graph', 'plot', 'display']):
            specialists.append('streamlit_agent')

        # Documentation lookup
        if any(kw in query.lower() for kw in ['how to', 'example', 'documentation', 'docs']):
            specialists.append('context7_agent')

        # Default: if no specialists matched, assume database query
        if not specialists:
            specialists.append('supabase_agent')

        logger.info("Task classified", query=query, specialists=specialists)
        return specialists

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute task by routing to appropriate specialists.

        Args:
            task: Task dictionary with:
                - task_id: Unique ID
                - query: User query
                - params: Additional parameters
                - context: Session context

        Returns:
            Aggregated results from specialists
        """
        task_id = task.get('task_id', 'unknown')
        query = task.get('query', '')

        logger.info("Orchestrator executing task", task_id=task_id, query=query)

        # Classify task
        specialist_names = self.classify_task(query)

        # Execute tasks in parallel where possible
        results = {}

        for specialist_name in specialist_names:
            # TODO: Call actual specialist agents
            # For now, return placeholder
            results[specialist_name] = {
                "status": "success",
                "message": f"{specialist_name} would handle: {query}"
            }

        return {
            "task_id": task_id,
            "status": "success",
            "specialists_used": specialist_names,
            "results": results,
            "execution_time_ms": 0  # TODO: Track actual time
        }


# Singleton instance
_orchestrator = None


def get_orchestrator() -> OrchestratorAgent:
    """Get or create orchestrator singleton"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = OrchestratorAgent()
    return _orchestrator


if __name__ == "__main__":
    # Test orchestrator
    async def test():
        orchestrator = get_orchestrator()

        task = {
            "task_id": "test-1",
            "query": "Get trial data for metformin and visualize phase distribution"
        }

        result = await orchestrator.execute_task(task)
        print(f"Result: {result}")

    asyncio.run(test())
