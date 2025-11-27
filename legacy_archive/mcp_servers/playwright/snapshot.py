"""
Playwright MCP Tool: Snapshot

Wrapper for mcp__playwright__browser_snapshot
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from client import callMCPTool
from typing import Dict, Any


async def snapshot() -> Dict[str, Any]:
    """
    Capture accessibility snapshot of current page.

    This is better than screenshots for scraping - returns structured data.

    Returns:
        Page snapshot with accessibility tree

    Example:
        snap = await snapshot()
        # Find element: snap.find(role='region', name='Mechanism')
    """
    return await callMCPTool('mcp__playwright__browser_snapshot', {})
