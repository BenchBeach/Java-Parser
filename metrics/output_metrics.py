from core.method import MethodInfo, MethodCallInfo
from core.types import TypeInfo
from typing import Optional, List


class OutputMetricsCalculator:
    """计算输出复杂度指标"""

    @staticmethod
    def calculate_mock_requirement(unique_external_classes: int) -> int:
        """计算Mock需求度：唯一外部类数量（已废弃，使用calculate_mock_complexity）"""
        return unique_external_classes

    @staticmethod
    def calculate_mock_complexity(method: MethodInfo, class_fqn: str) -> float:
        """计算Mock复杂度（改进版）

        综合考虑：
        1. 外部类数量
        2. 每个类的方法数
        3. Mock返回值构造复杂度
        4. 参数匹配器复杂度
        """
        # 筛选外部调用
        external_calls = [
            c for c in method.method_calls
            if c.resolved_fqn and c.resolved_fqn != class_fqn
        ]

        if not external_calls:
            return 0.0

        # 1. 基础分：需要mock的类数量
        unique_classes = len(set(c.resolved_fqn for c in external_calls))
        base_score = unique_classes * 2.0

        # 2. 每个类需要stub的方法数
        methods_per_class = {}
        for call in external_calls:
            if call.resolved_fqn not in methods_per_class:
                methods_per_class[call.resolved_fqn] = set()
            methods_per_class[call.resolved_fqn].add(call.method_name)

        method_score = sum(len(methods) * 1.5 for methods in methods_per_class.values())

        # 3. 返回值构造复杂度（基于方法名推断）
        return_score = OutputMetricsCalculator._calculate_mock_return_complexity(external_calls)

        # 4. 参数匹配器复杂度
        matcher_score = OutputMetricsCalculator._calculate_matcher_complexity(external_calls)

        total = base_score + method_score + return_score + matcher_score
        return min(total, 30.0)  # 限制最大值

    @staticmethod
    def _calculate_mock_return_complexity(calls: List[MethodCallInfo]) -> float:
        """计算Mock方法返回值构造复杂度"""
        complexity = 0.0

        for call in calls:
            method_name = call.method_name.lower()

            # void方法（set/update/delete/save等）
            if any(prefix in method_name for prefix in ['set', 'update', 'delete', 'save', 'remove', 'add']):
                complexity += 0.5
            # 返回集合（find/list/get等复数形式）
            elif method_name.endswith('s') or 'list' in method_name or 'all' in method_name:
                complexity += 3.0
            # 返回单个对象
            elif any(prefix in method_name for prefix in ['get', 'find', 'load', 'fetch']):
                complexity += 2.0
            # 返回简单类型（is/has/count等）
            elif any(prefix in method_name for prefix in ['is', 'has', 'count', 'size']):
                complexity += 1.0
            else:
                complexity += 1.5

        return complexity

    @staticmethod
    def _calculate_matcher_complexity(calls: List[MethodCallInfo]) -> float:
        """计算参数匹配器复杂度"""
        complexity = 0.0

        for call in calls:
            arg_count = len(call.argument_types)

            if arg_count == 0:
                complexity += 0.5  # when(mock.method()).thenReturn()
            elif arg_count == 1:
                complexity += 1.0  # when(mock.method(any())).thenReturn()
            elif arg_count == 2:
                complexity += 1.5  # when(mock.method(any(), any())).thenReturn()
            else:
                # 多参数需要多个matcher
                complexity += arg_count * 0.8

        return complexity

    @staticmethod
    def calculate_setup_complexity(param_complexity: int, field_complexity: int) -> int:
        """计算Setup复杂度：参数复杂度 + 字段复杂度"""
        return param_complexity + field_complexity

    @staticmethod
    def calculate_return_complexity(return_type: Optional[TypeInfo]) -> int:
        """计算返回类型复杂度"""
        if return_type is None or return_type.raw == 'void':
            return 5

        if return_type.is_primitive:
            return 1

        base = return_type.base or return_type.raw
        if base in ['String', 'Integer', 'Long', 'Double', 'Float', 'Boolean']:
            return 2

        return 3

    @staticmethod
    def calculate_side_effect_indicator(method: MethodInfo) -> int:
        """计算副作用指示器：修改的字段数量"""
        is_void = method.return_type is None or method.return_type.raw == 'void'
        if not is_void:
            return 0
        return len(method.control_flow.field_accesses)

    @staticmethod
    def calculate_assertion_complexity(method: MethodInfo, external_calls: int) -> int:
        """计算断言构造难度：需要验证的点数量"""
        return_type = method.return_type

        # void方法：需要验证副作用
        if return_type is None or return_type.raw == 'void':
            # 字段修改数 + 外部调用数（需要verify）
            field_modifications = len(method.control_flow.field_accesses)
            return field_modifications + external_calls

        # 有返回值：基础1个断言 + 集合/对象需要额外验证
        base = return_type.base or return_type.raw
        if base in ['List', 'Map', 'Set', 'Collection']:
            return 3  # 验证非null、size、内容
        elif return_type.is_primitive:
            return 1
        else:
            return 2  # 验证非null + 属性
