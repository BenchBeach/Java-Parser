# parser/utils.py
from __future__ import annotations
from typing import Dict, List, Optional

from tree_sitter import Node
from configs.config import JAVA_LANGUAGE


def query_captures(query_str: str, cap: Optional[str], node: Node):
    """
    Tree-sitter Query 辅助函数。
    兼容 tree-sitter 0.25+ 版本

    行为约定：
        - cap 不为 None：返回该 capture 名称对应的节点列表 List[Node]
        - cap 为 None：返回完整 dict，用于提取多个 capture
    """
    from tree_sitter import Query, QueryCursor

    query = Query(JAVA_LANGUAGE, query_str)
    cursor = QueryCursor(query)
    matches = cursor.matches(node)

    captures: Dict[str, List[Node]] = {}
    for pattern_index, capture_dict in matches:
        for capture_name, nodes in capture_dict.items():
            if capture_name not in captures:
                captures[capture_name] = []
            captures[capture_name].extend(nodes)

    if cap is not None:
        return captures.get(cap, [])
    return captures