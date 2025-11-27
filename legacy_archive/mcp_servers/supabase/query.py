"""
Supabase MCP Tool: Query

Wrapper for Supabase query operations
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from client import callMCPTool
from typing import Dict, Any, List, Optional


async def query(
    table: str,
    filters: Optional[Dict[str, Any]] = None,
    select: str = "*",
    limit: Optional[int] = None,
    order_by: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Query Supabase table.

    Args:
        table: Table name (e.g., 'Drug', 'Trial')
        filters: Filter conditions (e.g., {'name': 'metformin'})
        select: Fields to select (default: all)
        limit: Max number of rows
        order_by: Sort field

    Returns:
        List of records

    Example:
        drugs = await query('Drug', filters={'is_approved': True}, limit=10)
    """
    params = {
        'table': table,
        'select': select
    }

    if filters:
        params['filters'] = filters
    if limit:
        params['limit'] = limit
    if order_by:
        params['order_by'] = order_by

    # TODO: Map to actual Supabase MCP tool name
    result = await callMCPTool('mcp__supabase__query', params)

    return result.get('data', [])
