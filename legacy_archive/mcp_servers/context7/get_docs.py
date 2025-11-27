"""
Context7 MCP Tool: Get Library Docs

Wrapper for mcp__context7__get-library-docs
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from client import callMCPTool
from typing import Dict, Any, List, Optional


async def get_library_docs(
    library_id: str,
    topic: Optional[str] = None,
    page: int = 1
) -> List[Dict[str, Any]]:
    """
    Fetch library documentation from Context7.

    Args:
        library_id: Context7 library ID (e.g., '/streamlit/streamlit')
        topic: Optional topic to focus on (e.g., 'charts', 'caching')
        page: Page number for pagination (1-10)

    Returns:
        List of documentation entries with code examples

    Example:
        docs = await get_library_docs('/streamlit/streamlit', topic='charts')
    """
    params = {
        'context7CompatibleLibraryID': library_id,
        'page': page
    }

    if topic:
        params['topic'] = topic

    result = await callMCPTool('mcp__context7__get-library-docs', params)

    return result.get('docs', [])
