import yaml
import re
from typing import Dict, List, Any
from .method_filter import (
    MethodFilter,
    GetterSetterFilter,
    TestUtilityFilter,
    MetricBasedFilter,
    SimilarityFilter
)
from .test_coverage_filter import TestCoverageFilter


class ConfigFilter:
    """Load and apply filters based on YAML configuration"""

    def __init__(self, config_path: str, project=None):
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        self.project = project
        self.filters: List[MethodFilter] = []
        self._build_filters()

    def _build_filters(self):
        filter_config = self.config.get('filters', {})

        if filter_config.get('getter_setter', False):
            self.filters.append(GetterSetterFilter())

        if filter_config.get('test_utility', False):
            self.filters.append(TestUtilityFilter())

        metric_config = filter_config.get('metric_based', {})
        if metric_config.get('enabled', False):
            self.filters.append(MetricBasedFilter(
                min_complexity=metric_config.get('min_cyclomatic_complexity'),
                max_complexity=metric_config.get('max_cyclomatic_complexity'),
                min_params=metric_config.get('min_parameters'),
                max_params=metric_config.get('max_parameters')
            ))

        similarity_config = filter_config.get('similarity', {})
        if similarity_config.get('enabled', False):
            self.filters.append(SimilarityFilter(
                threshold=similarity_config.get('threshold', 0.85)
            ))

        test_coverage_config = filter_config.get('test_coverage', {})
        if test_coverage_config.get('enabled', False) and self.project:
            self.filters.append(TestCoverageFilter(
                project=self.project,
                require_tests=test_coverage_config.get('require_tests', True),
                min_test_count=test_coverage_config.get('min_test_count', 1)
            ))

    def _matches_pattern(self, text: str, patterns: List[str]) -> bool:
        for pattern in patterns:
            if re.match(pattern, text):
                return True
        return False

    def should_keep_by_pattern(self, method) -> bool:
        full_name = f"{method.package_name}.{method.class_name}.{method.name}" if method.package_name else f"{method.class_name}.{method.name}"

        exclude_patterns = self.config.get('exclude_patterns', [])
        if self._matches_pattern(full_name, exclude_patterns):
            return False

        exclude_methods = self.config.get('exclude_methods', [])
        if method.name in exclude_methods:
            return False

        include_patterns = self.config.get('include_patterns', [])
        if include_patterns and not self._matches_pattern(full_name, include_patterns):
            return False

        return True

    def filter_methods(self, methods: List) -> List:
        result = [m for m in methods if self.should_keep_by_pattern(m)]

        for filter_obj in self.filters:
            if isinstance(filter_obj, SimilarityFilter):
                filter_obj.analyze_similarity(result)
            result = filter_obj.filter_methods(result)

        return result
