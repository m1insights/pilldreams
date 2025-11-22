"""
Base Agent Class for pilldreams MCP Agents

Implements the code execution pattern from:
https://www.anthropic.com/engineering/code-execution-with-mcp
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json
import os
from pathlib import Path
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


class BaseAgent(ABC):
    """
    Base class for all MCP agents in pilldreams.

    Each agent:
    - Loads tools on-demand (progressive disclosure)
    - Filters data in execution environment
    - Builds reusable skills over time
    - Caches context to avoid redundant discovery
    """

    def __init__(self, agent_dir: str):
        """
        Initialize agent with configuration.

        Args:
            agent_dir: Path to agent directory (e.g., 'agents/playwright_agent/')
        """
        self.agent_dir = Path(agent_dir)
        self.config_path = self.agent_dir / "config.json"
        self.config = self._load_config()

        self.name = self.config['name']
        self.role = self.config['role']
        self.mcp_servers = self.config.get('mcp_servers', [])

        # Paths
        self.skills_path = self.agent_dir / "skills"
        self.servers_path = self.agent_dir / "servers"
        self.context_path = self.agent_dir / "context"

        # Ensure directories exist
        self.skills_path.mkdir(exist_ok=True)
        self.context_path.mkdir(exist_ok=True)

        # Load cached context
        self.context_cache = self._load_context_cache()

        logger.info(f"Initialized {self.name}", role=self.role)

    def _load_config(self) -> Dict[str, Any]:
        """Load agent configuration from config.json"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config not found: {self.config_path}")

        with open(self.config_path) as f:
            return json.load(f)

    def _load_context_cache(self) -> Dict[str, Any]:
        """
        Load cached MCP tool definitions to avoid re-discovery.

        Returns cached tools if:
        - Cache file exists
        - Cache is not expired (based on context_cache_ttl)
        """
        cache_file = self.context_path / "tools.json"

        if not cache_file.exists():
            return {"tools": [], "last_updated": None}

        with open(cache_file) as f:
            cache = json.load(f)

        # Check if cache is expired
        ttl = self.config.get('context_cache_ttl', 3600)  # 1 hour default
        last_updated = cache.get('last_updated')

        if last_updated:
            cache_age = datetime.now() - datetime.fromisoformat(last_updated)
            if cache_age.total_seconds() > ttl:
                logger.info(f"Context cache expired for {self.name}")
                return {"tools": [], "last_updated": None}

        logger.info(f"Loaded context cache for {self.name}", tools_count=len(cache.get('tools', [])))
        return cache

    def _save_context_cache(self, tools: List[Dict[str, Any]]):
        """Save discovered tools to context cache"""
        cache_file = self.context_path / "tools.json"

        cache = {
            "last_updated": datetime.now().isoformat(),
            "tools": tools
        }

        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

        logger.info(f"Saved context cache for {self.name}", tools_count=len(tools))

    def get_available_skills(self) -> List[str]:
        """
        List all available skills in skills/ directory.

        Returns:
            List of skill names (without .py/.ts extension)
        """
        if not self.skills_path.exists():
            return []

        skills = []
        for file in self.skills_path.iterdir():
            if file.suffix in ['.py', '.ts'] and not file.name.startswith('_'):
                skills.append(file.stem)

        return skills

    def save_skill(self, name: str, code: str, description: str = "", metadata: Dict[str, Any] = None):
        """
        Save a new skill to skills/ directory.

        Args:
            name: Skill name (will be filename)
            code: Code implementation
            description: Skill description
            metadata: Additional metadata (inputs, outputs, dependencies, performance)
        """
        # Determine file extension based on code
        extension = '.py' if 'def ' in code or 'import ' in code else '.ts'
        skill_file = self.skills_path / f"{name}{extension}"

        # Create skill header with metadata
        header = f"""
\"\"\"
SKILL: {name}

Description: {description}
Created: {datetime.now().isoformat()}
"""

        if metadata:
            header += f"\nMetadata: {json.dumps(metadata, indent=2)}\n"

        header += '"""\n\n'

        # Write skill file
        with open(skill_file, 'w') as f:
            f.write(header + code)

        logger.info(f"Saved skill: {name}", agent=self.name, path=str(skill_file))

    @abstractmethod
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task and return result.

        Each agent implements this method with its specific logic.

        Args:
            task: Task dictionary with:
                - task_id: Unique task ID
                - action: Action to perform
                - params: Parameters for action
                - context: Additional context

        Returns:
            Result dictionary with:
                - task_id: Same as input
                - status: 'success' | 'error'
                - result: Task result or error message
                - tokens_used: Token count (if available)
                - execution_time_ms: Execution time
        """
        pass

    async def _retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry logic.

        Args:
            func: Async function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result

        Raises:
            Last exception if all retries fail
        """
        max_retries = self.config.get('max_retries', 3)
        base_delay = 1  # seconds

        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    logger.error(f"All retries failed for {self.name}", error=str(e))
                    raise

                delay = base_delay * (2 ** attempt)  # Exponential backoff
                logger.warning(
                    f"Retry {attempt + 1}/{max_retries} for {self.name}",
                    error=str(e),
                    delay=delay
                )

                await asyncio.sleep(delay)

    def __repr__(self):
        return f"<{self.__class__.__name__} name={self.name} role={self.role}>"
