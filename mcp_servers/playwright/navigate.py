"""
Playwright MCP Tool: Navigate

Wrapper for mcp__playwright__browser_navigate
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from client import callMCPTool
from typing import Dict, Any


async def navigate(url: str) -> Dict[str, Any]:
    """
    Navigate to a URL using Playwright browser.

    Args:
        url: URL to navigate to

    Returns:
        Navigation result

    Example:
        result = await navigate('https://go.drugbank.com/drugs/DB00316')
    """
    return await callMCPTool('mcp__playwright__browser_navigate', {'url': url})
