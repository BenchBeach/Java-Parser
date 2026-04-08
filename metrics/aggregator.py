class MetricsAggregator:
    """指标聚合和评分"""

    @staticmethod
    def aggregate_input_complexity(metrics: dict) -> float:
        """聚合输入复杂度"""
        normalized = {
            'cyclomatic': min(metrics.get('cyclomatic_complexity', 0) / 20, 1.0),
            'branches': min(metrics.get('branch_count', 0) / 10, 1.0),
            'loops': min(metrics.get('loop_count', 0) / 5, 1.0),
            'exceptions': min(metrics.get('exception_paths', 0) / 5, 1.0),
            'field_deps': min(metrics.get('field_dependency_count', 0) / 10, 1.0),
            'external_calls': min(metrics.get('external_call_count', 0) / 15, 1.0),
            'dependent_classes': min(metrics.get('dependent_class_count', 0) / 10, 1.0),
            'param_complexity': min(metrics.get('parameter_type_complexity', 0) / 20, 1.0),
            'nesting': min(metrics.get('object_nesting_depth', 0) / 5, 1.0),
        }

        weights = {
            'cyclomatic': 0.20,
            'branches': 0.10,
            'loops': 0.10,
            'exceptions': 0.05,
            'field_deps': 0.10,
            'external_calls': 0.15,
            'dependent_classes': 0.10,
            'param_complexity': 0.15,
            'nesting': 0.05,
        }

        return sum(normalized[k] * weights[k] for k in weights)

    @staticmethod
    def aggregate_output_complexity(metrics: dict) -> float:
        """聚合输出复杂度"""
        normalized = {
            'mock': min(metrics.get('mock_requirement_score', 0) / 10, 1.0),
            'setup': min(metrics.get('setup_complexity', 0) / 20, 1.0),
            'return': min(metrics.get('return_type_complexity', 0) / 5, 1.0),
            'assertion': min(metrics.get('assertion_complexity', 0) / 5, 1.0),
        }

        weights = {
            'mock': 0.30,
            'setup': 0.30,
            'return': 0.20,
            'assertion': 0.20,
        }

        return sum(normalized[k] * weights[k] for k in weights)

    @staticmethod
    def calculate_overall_difficulty(input_score: float, output_score: float) -> float:
        """计算总体难度分数"""
        return input_score * 0.6 + output_score * 0.4

    @staticmethod
    def classify_difficulty(score: float) -> str:
        """难度分级"""
        if score < 0.33:
            return 'easy'
        elif score < 0.67:
            return 'medium'
        else:
            return 'hard'
