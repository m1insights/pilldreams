"""
Context7 Agent - Documentation lookup specialist

Fetches up-to-date library documentation using Context7 MCP.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from typing import Dict, Any, List
import structlog

logger = structlog.get_logger()


class Context7Agent(BaseAgent):
    """
    Context7 agent for documentation lookup.

    Responsibilities:
    - Fetch library docs (Streamlit, Plotly, RDKit, etc.)
    - Provide code examples for UI components
    - Answer technical questions about dependencies
    - Cache frequently-accessed docs
    """

    def __init__(self):
        super().__init__("agents/context7_agent")
        self.common_libraries = self.config.get('commonly_used_libraries', [])

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute documentation lookup task.

        Args:
            task: Task with action and params
                - action: 'get_docs' | 'search_examples' | etc.
                - params: Library name, topic, etc.

        Returns:
            Documentation or code examples
        """
        task_id = task.get('task_id', 'unknown')
        action = task.get('action')
        params = task.get('params', {})

        logger.info(f"Context7 agent executing task", task_id=task_id, action=action)

        # Route to appropriate handler
        handlers = {
            'get_docs': self._get_docs,
            'search_examples': self._search_examples,
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
            logger.error(f"Context7 task failed", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    async def _get_docs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get library documentation.

        TODO: Implement using Context7 MCP tools:
        - mcp__context7__resolve-library-id
        - mcp__context7__get-library-docs
        """
        library_name = params.get('library_name')
        topic = params.get('topic')

        logger.info(f"Would fetch docs", library=library_name, topic=topic)

        # Placeholder
        return {
            "library": library_name,
            "topic": topic,
            "docs": [],
            "examples": []
        }

    async def _search_examples(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for code examples.

        Filters examples in execution environment before returning.
        """
        library_name = params.get('library_name')
        search_term = params.get('search_term')

        logger.info(f"Would search examples", library=library_name, term=search_term)

        # TODO: Implement with Context7 MCP
        # docs = await context7.get_library_docs(library_id, topic=search_term)
        # examples = [d for d in docs if d.type == 'code_snippet']
        # return examples[:3]  # Top 3 only

        # Placeholder
        return []


# Singleton instance
_context7_agent = None


def get_context7_agent() -> Context7Agent:
    """Get or create context7 agent singleton"""
    global _context7_agent
    if _context7_agent is None:
        _context7_agent = Context7Agent()
    return _context7_agent
