from core.method import MethodInfo


class ComplexityCalculator:
    """计算方法的复杂度指标"""

    @staticmethod
    def calculate_cyclomatic_complexity(method: MethodInfo) -> int:
        """计算圈复杂度: CC = 决策点数 + 1"""
        cf = method.control_flow
        decision_points = (
            cf.if_count +
            cf.switch_count +
            cf.for_count +
            cf.while_count +
            cf.do_count +
            cf.catch_count +
            cf.ternary_count +
            cf.logical_and_count +
            cf.logical_or_count
        )
        return decision_points + 1

    @staticmethod
    def calculate_branch_count(method: MethodInfo) -> int:
        """计算分支数量"""
        return method.control_flow.if_count + method.control_flow.switch_count

    @staticmethod
    def calculate_loop_count(method: MethodInfo) -> int:
        """计算循环数量"""
        cf = method.control_flow
        return cf.for_count + cf.while_count + cf.do_count

    @staticmethod
    def calculate_exception_paths(method: MethodInfo) -> int:
        """计算异常处理路径数"""
        cf = method.control_flow
        return cf.try_count + cf.catch_count
