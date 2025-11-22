"""
Streamlit Agent - UI/visualization expert

Handles Streamlit component creation and data visualization.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from base_agent import BaseAgent
from typing import Dict, Any
import structlog

logger = structlog.get_logger()


class StreamlitAgent(BaseAgent):
    """
    Streamlit agent for UI and visualization tasks.

    Responsibilities:
    - Create Streamlit components (charts, tables, metrics)
    - Design data visualizations (Plotly, Altair)
    - Implement best practices for Streamlit apps
    - Optimize performance (caching, lazy loading)
    - Call other agents when needed (Context7 for docs, Supabase for data)
    """

    def __init__(self):
        super().__init__("agents/streamlit_agent")
        self.knowledge_path = self.agent_dir / self.config.get('knowledge_path', 'knowledge')
        self.knowledge_path.mkdir(exist_ok=True)

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute UI/visualization task.

        Args:
            task: Task with action and params
                - action: 'create_chart' | 'create_layout' | etc.
                - params: Chart type, data, options

        Returns:
            Component code or configuration
        """
        task_id = task.get('task_id', 'unknown')
        action = task.get('action')
        params = task.get('params', {})

        logger.info(f"Streamlit agent executing task", task_id=task_id, action=action)

        # Route to appropriate handler
        handlers = {
            'create_radar_chart': self._create_radar_chart,
            'create_timeline': self._create_timeline,
            'create_metric_cards': self._create_metric_cards,
            'create_bar_chart': self._create_bar_chart,
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
            logger.error(f"Streamlit task failed", task_id=task_id, error=str(e))
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }

    async def _create_radar_chart(self, params: Dict[str, Any]) -> str:
        """
        Create radar/spider chart for drug scores.

        Returns Plotly code as string.
        """
        scores = params.get('scores', {})

        logger.info(f"Would create radar chart for scores: {list(scores.keys())}")

        # Placeholder - would generate actual Plotly code
        code = """
import plotly.graph_objects as go

# Radar chart for drug scores
fig = go.Figure(data=go.Scatterpolar(
    r=list(scores.values()),
    theta=list(scores.keys()),
    fill='toself'
))

fig.update_layout(
    polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
    showlegend=False
)

st.plotly_chart(fig, use_container_width=True)
"""
        return code

    async def _create_timeline(self, params: Dict[str, Any]) -> str:
        """Create trial timeline visualization"""
        trials = params.get('trials', [])
        logger.info(f"Would create timeline for {len(trials)} trials")
        return "# Timeline code placeholder"

    async def _create_metric_cards(self, params: Dict[str, Any]) -> str:
        """Create metric card grid"""
        metrics = params.get('metrics', {})
        logger.info(f"Would create {len(metrics)} metric cards")
        return "# Metric cards code placeholder"

    async def _create_bar_chart(self, params: Dict[str, Any]) -> str:
        """Create bar chart (adverse events, etc.)"""
        data = params.get('data', [])
        logger.info(f"Would create bar chart with {len(data)} items")
        return "# Bar chart code placeholder"


# Singleton instance
_streamlit_agent = None


def get_streamlit_agent() -> StreamlitAgent:
    """Get or create streamlit agent singleton"""
    global _streamlit_agent
    if _streamlit_agent is None:
        _streamlit_agent = StreamlitAgent()
    return _streamlit_agent
