# parser/body_parser.py
from __future__ import annotations
from typing import Optional

from tree_sitter import Node

from core.variables import LocalVariableInfo
from core.method import MethodCallInfo
from core.types import TypeInfo

from parser.utils import query_captures
from parser.type_parser import parse_type_node


LOCAL_VAR_QUERY = """
(local_variable_declaration) @var
"""

LOCAL_VAR_ATTR_QUERY = """
(local_variable_declaration
    type: (_) @type
    declarator: (variable_declarator name: (identifier) @name)
)
"""

CALL_QUERY = """
(method_invocation) @call
"""

CALL_ATTR_QUERY = """
(method_invocation
    object: (_) @object
    name: (_) @name
    arguments: (argument_list) @args
)
"""

CONTROL_FLOW_QUERIES = {
    'if': '(if_statement) @if',
    'switch': '(switch_expression) @switch',
    'for': '(for_statement) @for',
    'while': '(while_statement) @while',
    'do': '(do_statement) @do',
    'try': '(try_statement) @try',
    'catch': '(catch_clause) @catch',
    'ternary': '(ternary_expression) @ternary',
    'and': '(binary_expression operator: "&&" @and)',
    'or': '(binary_expression operator: "||" @or)',
}

FIELD_ACCESS_QUERY = '(field_access) @field'


def parse_method_body(method_ctx, body_node: Optional[Node], code: str):
    """
    解析方法体，提取：
        - 局部变量 LocalVariableInfo
        - 方法调用 MethodCallInfo
    """
    if body_node is None:
        return

    # -------- 1) 局部变量 --------
    var_nodes = query_captures(LOCAL_VAR_QUERY, "var", body_node)

    for vnode in var_nodes:
        attrs = query_captures(LOCAL_VAR_ATTR_QUERY, None, vnode)
        tlist = attrs.get("type", [])
        nlist = attrs.get("name", [])

        for tnode, nnode in zip(tlist, nlist):
            method_ctx.local_variables.append(
                LocalVariableInfo(
                    name=nnode.text.decode("utf-8"),
                    content=vnode.text.decode("utf-8"),
                    type=parse_type_node(tnode, code),
                    span=None,
                )
            )

    # -------- 2) 方法调用 --------
    call_nodes = query_captures(CALL_QUERY, "call", body_node)
    for cnode in call_nodes:
        attrs = query_captures(CALL_ATTR_QUERY, None, cnode)

        obj = attrs.get("object", [None])[0]
        name = attrs.get("name", [None])[0]

        call = MethodCallInfo(
            qualifier=obj.text.decode("utf-8") if obj else None,
            method_name=name.text.decode("utf-8") if name else "",
            argument_types=[],
            span=None,
            content=cnode.text.decode("utf-8"),
        )

        method_ctx.method_calls.append(call)

    # -------- 3) 控制流信息 --------
    method_ctx.control_flow.if_count = len(query_captures(CONTROL_FLOW_QUERIES['if'], 'if', body_node))
    method_ctx.control_flow.switch_count = len(query_captures(CONTROL_FLOW_QUERIES['switch'], 'switch', body_node))
    method_ctx.control_flow.for_count = len(query_captures(CONTROL_FLOW_QUERIES['for'], 'for', body_node))
    method_ctx.control_flow.while_count = len(query_captures(CONTROL_FLOW_QUERIES['while'], 'while', body_node))
    method_ctx.control_flow.do_count = len(query_captures(CONTROL_FLOW_QUERIES['do'], 'do', body_node))
    method_ctx.control_flow.try_count = len(query_captures(CONTROL_FLOW_QUERIES['try'], 'try', body_node))
    method_ctx.control_flow.catch_count = len(query_captures(CONTROL_FLOW_QUERIES['catch'], 'catch', body_node))
    method_ctx.control_flow.ternary_count = len(query_captures(CONTROL_FLOW_QUERIES['ternary'], 'ternary', body_node))
    method_ctx.control_flow.logical_and_count = len(query_captures(CONTROL_FLOW_QUERIES['and'], 'and', body_node))
    method_ctx.control_flow.logical_or_count = len(query_captures(CONTROL_FLOW_QUERIES['or'], 'or', body_node))

    # -------- 4) 字段访问 --------
    field_nodes = query_captures(FIELD_ACCESS_QUERY, 'field', body_node)
    for fnode in field_nodes:
        field_text = fnode.text.decode("utf-8")
        if field_text not in method_ctx.control_flow.field_accesses:
            method_ctx.control_flow.field_accesses.append(field_text)