from typing import Set
from core.method import MethodInfo
from core.types import TypeInfo
from core.symbol_table import GlobalSymbolTable


class InputMetricsCalculator:
    """计算输入复杂度指标"""

    def __init__(self, symbol_table: GlobalSymbolTable):
        self.symbol_table = symbol_table

    def calculate_field_dependency(self, method: MethodInfo) -> int:
        """计算字段依赖数"""
        return len(method.control_flow.field_accesses)

    def calculate_external_calls(self, method: MethodInfo, class_fqn: str) -> int:
        """计算外部方法调用数"""
        external_count = 0
        for call in method.method_calls:
            if call.resolved_fqn and call.resolved_fqn != class_fqn:
                external_count += 1
        return external_count

    def calculate_static_dependency(self, method: MethodInfo) -> int:
        """计算静态依赖数"""
        static_count = 0
        for call in method.method_calls:
            if call.qualifier and call.qualifier[0].isupper():
                static_count += 1
        return static_count

    def calculate_dependent_classes(self, method: MethodInfo) -> int:
        """计算依赖类数量"""
        classes = set()

        # 参数类型
        for param in method.parameters:
            if param.type.resolved_fqn:
                classes.add(param.type.resolved_fqn)

        # 返回类型
        if method.return_type and method.return_type.resolved_fqn:
            classes.add(method.return_type.resolved_fqn)

        # 方法调用
        for call in method.method_calls:
            if call.resolved_fqn:
                classes.add(call.resolved_fqn)

        return len(classes)

    def calculate_cross_package_calls(self, method: MethodInfo, class_fqn: str) -> int:
        """计算跨包调用数"""
        if not class_fqn or '.' not in class_fqn:
            return 0

        current_package = '.'.join(class_fqn.split('.')[:-1])
        cross_package = 0

        for call in method.method_calls:
            if call.resolved_fqn and '.' in call.resolved_fqn:
                call_package = '.'.join(call.resolved_fqn.split('.')[:-1])
                if call_package != current_package:
                    cross_package += 1

        return cross_package

    def calculate_unique_external_classes(self, method: MethodInfo, class_fqn: str) -> int:
        """计算唯一外部类数量（用于Mock需求度）"""
        external_classes = set()
        for call in method.method_calls:
            if call.resolved_fqn and call.resolved_fqn != class_fqn:
                # 只计算项目内的类（在符号表中的类）
                if self.symbol_table.get_class(call.resolved_fqn):
                    external_classes.add(call.resolved_fqn)
        return len(external_classes)

    def calculate_parameter_complexity(self, method: MethodInfo) -> dict:
        """计算参数复杂度"""
        total_complexity = 0
        max_nesting = 0

        for param in method.parameters:
            complexity = self.calculate_type_complexity(param.type)
            total_complexity += complexity
            nesting = self.calculate_nesting_depth(param.type, set())
            max_nesting = max(max_nesting, nesting)

        return {
            'parameter_count': len(method.parameters),
            'parameter_type_complexity': total_complexity,
            'object_nesting_depth': max_nesting,
        }

    def calculate_field_type_complexity(self, method: MethodInfo) -> int:
        """计算字段类型复杂度"""
        total_complexity = 0
        for field_name in method.control_flow.field_accesses:
            # 尝试从符号表获取字段类型
            for cls in self.symbol_table.classes.values():
                if field_name in cls.fields:
                    total_complexity += self.calculate_type_complexity(cls.fields[field_name].type)
                    break
        return total_complexity

    def calculate_type_complexity(self, type_info: TypeInfo) -> int:
        """计算类型复杂度"""
        if type_info.is_primitive:
            return 1

        base = type_info.base or type_info.raw

        # String/包装类
        if base in ['String', 'Integer', 'Long', 'Double', 'Float', 'Boolean', 'Character', 'Byte', 'Short']:
            return 2

        # 集合类：返回泛型参数的最大复杂度
        if base in ['List', 'Map', 'Set', 'Collection', 'ArrayList', 'HashMap', 'HashSet', 'LinkedList']:
            if not type_info.generics:
                return 3
            return max(self.calculate_type_complexity(arg) for arg in type_info.generics)

        # 自定义对象：4 + 嵌套层数
        nesting = self.calculate_nesting_depth(type_info, set())
        return 4 + nesting

    def calculate_nesting_depth(self, type_info: TypeInfo, visited: Set[str], depth: int = 0) -> int:
        """计算对象嵌套深度"""
        if type_info.is_primitive or depth > 5:
            return depth

        fqn = type_info.resolved_fqn
        if not fqn or fqn in visited:
            return depth

        visited.add(fqn)
        class_info = self.symbol_table.get_class(fqn)
        if not class_info:
            return depth

        max_depth = depth
        for field in class_info.fields.values():
            field_depth = self.calculate_nesting_depth(field.type, visited.copy(), depth + 1)
            max_depth = max(max_depth, field_depth)

        return max_depth
