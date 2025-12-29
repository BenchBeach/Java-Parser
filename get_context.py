import argparse
import os
import sys
import json
from pathlib import Path
from loguru import logger
from parser.project_parser import JavaProjectParser
from core.project import ProjectContext
from core.clazz import ClassInfo
from core.method import MethodInfo
from core.types import TypeInfo
from core.variables import FieldInfo, ParameterInfo

def collect_class_info(cls: ClassInfo, symbol_table, visited=None):
    """
    提取类信息，包括变量信息、所有函数签名，不递归参数/返回值
    """
    if visited is None:
        visited = set()
    if cls.fqn in visited:
        return {"fqn": cls.fqn, "recursion": True}
    visited.add(cls.fqn)

    info = {
        "class_name": cls.name,
        "fqn": cls.fqn,
        "fields": [],
        "methods": []
    }
    for field in cls.fields.values():
        # 提取 value 兜底: 若无initializer_src, 从原始文本寻找'='部分
        value = getattr(field, 'initializer_src', None)
        if not value:
            content = getattr(field, 'content', None)
            if content and '=' in content:
                eq_pos = content.find('=')
                # 简单拿=右边到末尾（或分号前）
                rest = content[eq_pos+1:].strip()
                if rest.endswith(';'):
                    rest = rest[:-1].rstrip()
                value = rest
        info["fields"].append({
            "name": field.name,
            "type": field.type.resolved_fqn or field.type.raw,
            "modifiers": list(field.modifiers),
            "annotations": field.annotations,
            "raw_text": field.content if hasattr(field, 'content') else None,
            "value": value
        })
    for method_list in cls.methods.values():
        for method in method_list:
            # return_type 优先 resolved_fqn，fallback 到 raw
            ret_type = None
            if method.return_type:
                ret_type = method.return_type.resolved_fqn or method.return_type.raw
            # signature 带上 modifiers、注解和返回值类型
            modifiers_str = " ".join(method.modifiers) if method.modifiers else ""
            annotations_str = " ".join(getattr(method, "annotations", []))
            sig_parts = []
            if annotations_str:
                sig_parts.append(annotations_str)
            if modifiers_str:
                sig_parts.append(modifiers_str)
            if ret_type:
                sig_parts.append(ret_type)
            sig_parts.append(method.signature_key())
            sig_with_ret = " ".join(sig_parts)
            structured_method = {
                "name": method.name,
                "signature": sig_with_ret,
                "return_type": ret_type,
                "modifiers": list(method.modifiers),
                "annotations": getattr(method, "annotations", []),
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type.resolved_fqn or p.type.raw,
                        "annotations": getattr(p, "annotations", [])
                    }
                    for p in method.parameters
                ],
                "raw_text": method.content if hasattr(method, "content") else None
            }
            info["methods"].append(structured_method)
    return info

def class_struct_deep(typeinfo: TypeInfo, symbol_table, visited=None, context_cls: ClassInfo = None):
    """
    根据类型递归拉取类定义，只考虑已知项目类
    支持 fallback：
      1. resolved_fqn
      2. 直接 raw/base 在符号表中
      3. 用 context_cls 的包名拼 raw/base
      4. 用 context_cls 的 fqn+'.'+raw/base（内部类场景）
    """
    if typeinfo is None or typeinfo.is_primitive:
        return None
    candidates = []
    # 1. resolved_fqn
    if typeinfo.resolved_fqn:
        candidates.append(typeinfo.resolved_fqn)
    # 2. raw/base 直接
    if typeinfo.base:
        candidates.append(typeinfo.base)
    if typeinfo.raw and typeinfo.raw != typeinfo.base:
        candidates.append(typeinfo.raw)
    # 3. 用 context_cls 的包名拼
    if context_cls and context_cls.package and typeinfo.base:
        candidates.append(f"{context_cls.package}.{typeinfo.base}")
    # 4. 用 context_cls 的 fqn+'.'+base（内部类）
    if context_cls and typeinfo.base:
        candidates.append(f"{context_cls.fqn}.{typeinfo.base}")
        # 也可能是外层类的内部类
        if context_cls.outer_class:
            candidates.append(f"{context_cls.outer_class.fqn}.{typeinfo.base}")
    for fqn in candidates:
        if fqn in symbol_table.classes:
            return collect_class_info(symbol_table.classes[fqn], symbol_table, visited)
    return None

def build_context_prompt(info: dict) -> str:
    """
    根据上下文信息生成用于大模型理解的文本 prompt
    """
    lines = []
    
    # 待测方法信息
    lines.append("// This is the context of method under test")
    lines.append(f"Method Signature: {info.get('method_signature', '')}")
    lines.append(f"Return Type: {info.get('return_type', 'void')}")
    if info.get('method_body'):
        lines.append("Method Body:")
        lines.append(info['method_body'])
    lines.append("")
    
    # 待测类信息
    class_info = info.get('class_info', {})
    if class_info and not class_info.get('recursion'):
        lines.append("// This is the context of class under test")
        lines.append(f"Class Name: {class_info.get('class_name', '')}")
        lines.append(f"Full Qualified Name: {class_info.get('fqn', '')}")
        # 字段
        fields = class_info.get('fields', [])
        if fields:
            lines.append("Fields:")
            for f in fields:
                lines.append(f"  {f.get('raw_text', '')}")
        # 其他方法签名（区分构造函数和普通方法）
        methods = class_info.get('methods', [])
        constructors = []
        normal_methods = []
        for m in methods:
            if isinstance(m, dict):
                if m.get('return_type') is None:
                    constructors.append(m.get('signature', ''))
                else:
                    normal_methods.append(m.get('signature', ''))
            else:
                normal_methods.append(m)
        if constructors:
            lines.append("Constructors:")
            for sig in constructors:
                lines.append(f"  {sig}")
        if normal_methods:
            lines.append("Other Methods:")
            for sig in normal_methods:
                lines.append(f"  {sig}")
        lines.append("")
    
    # 返回值类信息
    ret_class_info = info.get('return_class_info', {})
    if ret_class_info and not ret_class_info.get('recursion'):
        lines.append("// This is the context of return type class")
        lines.append(f"Class Name: {ret_class_info.get('class_name', '')}")
        lines.append(f"Full Qualified Name: {ret_class_info.get('fqn', '')}")
        fields = ret_class_info.get('fields', [])
        if fields:
            lines.append("Fields:")
            for f in fields:
                lines.append(f"  {f.get('raw_text', '')}")
        methods = ret_class_info.get('methods', [])
        constructors = []
        normal_methods = []
        for m in methods:
            if isinstance(m, dict):
                if m.get('return_type') is None:
                    constructors.append(m.get('signature', ''))
                else:
                    normal_methods.append(m.get('signature', ''))
            else:
                normal_methods.append(m)
        if constructors:
            lines.append("Constructors:")
            for sig in constructors:
                lines.append(f"  {sig}")
        if normal_methods:
            lines.append("Methods:")
            for sig in normal_methods:
                lines.append(f"  {sig}")
        lines.append("")
    
    # 参数类信息
    param_class_info_list = info.get('parameter_class_info', [])
    if param_class_info_list:
        for pc in param_class_info_list:
            param_name = pc.get('param', '')
            pci = pc.get('class_info', {})
            if pci and not pci.get('recursion'):
                lines.append(f"// This is the context of parameter '{param_name}' class")
                lines.append(f"Class Name: {pci.get('class_name', '')}")
                lines.append(f"Full Qualified Name: {pci.get('fqn', '')}")
                fields = pci.get('fields', [])
                if fields:
                    lines.append("Fields:")
                    for f in fields:
                        lines.append(f"  {f.get('raw_text', '')}")
                methods = pci.get('methods', [])
                constructors = []
                normal_methods = []
                for m in methods:
                    if isinstance(m, dict):
                        if m.get('return_type') is None:
                            constructors.append(m.get('signature', ''))
                        else:
                            normal_methods.append(m.get('signature', ''))
                    else:
                        normal_methods.append(m)
                if constructors:
                    lines.append("Constructors:")
                    for sig in constructors:
                        lines.append(f"  {sig}")
                if normal_methods:
                    lines.append("Methods:")
                    for sig in normal_methods:
                        lines.append(f"  {sig}")
                lines.append("")
    
    return "\n".join(lines)

def collect_method_context(method: MethodInfo, cls: ClassInfo, symbol_table):
    # return_type 优先 resolved_fqn，fallback 到 raw
    ret_type = None
    if method.return_type:
        ret_type = method.return_type.resolved_fqn or method.return_type.raw
    info = {
        "class_info": collect_class_info(cls, symbol_table),
        "method_signature": method.signature_key(),
        "method_body": method.content,
        "parameters": [],
        "return_type": ret_type
    }
    # 参数深入
    param_class_info = []
    for param in method.parameters:
        param_struct = class_struct_deep(param.type, symbol_table, context_cls=cls)
        if param_struct:
            param_class_info.append({"param": param.name, "class_info": param_struct})
    if param_class_info:
        info["parameter_class_info"] = param_class_info
    # 返回值类型深入
    ret_class_struct = class_struct_deep(method.return_type, symbol_table, context_cls=cls)
    if ret_class_struct:
        info["return_class_info"] = ret_class_struct
    # 生成 context_prompt
    info["context_prompt"] = build_context_prompt(info)
    return info

def find_target_method(symbol_table, full_signature: str):
    """
    从符号表中查找方法，full_signature=类FQN#方法签名
    """
    method = symbol_table.get_method(full_signature)
    if not method:
        # 提示所有可用key
        keys = list(symbol_table.methods.keys())
        raise KeyError(f"方法未找到: {full_signature}, 可用: {keys}")
    # 还要取到类对象
    class_fqn = full_signature.split("#")[0]
    cls = symbol_table.get_class(class_fqn)
    return method, cls

def main():
    parser = argparse.ArgumentParser(description="Java函数上下文提取")
    parser.add_argument("project_root", help="项目根路径")
    parser.add_argument("main_src", help="src/main/java 路径")
    parser.add_argument("test_src", help="src/test/java 路径")
    parser.add_argument("method_key", help="待分析方法的完整签名（类FQN#方法签名）")
    parser.add_argument("--load", type=str, default="", help="已保存的二进制解析文件")
    parser.add_argument("--output", type=str, default="", help="结果输出到指定文件（可选）")
    args = parser.parse_args()
    
    project = None
    if args.load and os.path.exists(args.load):
        # 从二进制加载
        from parser_main import load_project
        project = load_project(args.load)
    if not project:
        parser_inst = JavaProjectParser()
        project = parser_inst.parse_project(
            args.project_root, args.main_src, args.test_src
        )
    symbol_table = project.symbols
    try:
        method, cls = find_target_method(symbol_table, args.method_key)
    except KeyError as e:
        print(str(e))
        sys.exit(1)
    context_json = collect_method_context(method, cls, symbol_table)
    out_json = json.dumps(context_json, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_json)
    else:
        print(out_json)


if __name__ == '__main__':
    main()
