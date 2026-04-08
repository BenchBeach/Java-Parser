from abc import ABC, abstractmethod
import re
from typing import List, Set, Dict


class MethodFilter(ABC):
    """Base class for method filters"""

    @abstractmethod
    def should_keep(self, method) -> bool:
        """Return True if method should be kept, False if filtered out"""
        pass

    def filter_methods(self, methods: List) -> List:
        """Filter a list of methods"""
        return [m for m in methods if self.should_keep(m)]


class GetterSetterFilter(MethodFilter):
    """Filter simple getter/setter methods"""

    def should_keep(self, method) -> bool:
        name = method.name

        # Check name pattern
        if not (name.startswith('get') or name.startswith('set') or name.startswith('is')):
            return True

        # Check complexity
        if hasattr(method, 'cyclomatic_complexity') and method.cyclomatic_complexity > 1:
            return True

        # Check body length
        if method.body_span:
            lines = method.body_span[1] - method.body_span[0] + 1
            if lines > 3:
                return True

        # Check getter/setter signature
        param_count = len(method.parameters) if method.parameters else 0
        has_return = method.return_type and method.return_type != 'void'

        if name.startswith('get') or name.startswith('is'):
            return not (param_count == 0 and has_return)
        elif name.startswith('set'):
            return not (param_count == 1 and not has_return)

        return True


class TestUtilityFilter(MethodFilter):
    """Filter test utility methods"""

    TEST_ANNOTATIONS = {'Before', 'After', 'BeforeEach', 'AfterEach', 'BeforeClass', 'AfterClass'}
    UTILITY_NAMES = {'setUp', 'tearDown', 'setup', 'cleanup'}

    def should_keep(self, method) -> bool:
        if method.annotations:
            for anno in method.annotations:
                if any(test_anno in anno for test_anno in self.TEST_ANNOTATIONS):
                    return False

        if method.class_name and method.class_name.endswith('Test'):
            if method.name in self.UTILITY_NAMES:
                return False
            if method.annotations and not any('Test' in a for a in method.annotations):
                return False

        return True


class MetricBasedFilter(MethodFilter):
    """Filter methods based on metric thresholds"""

    def __init__(self, min_complexity=None, max_complexity=None,
                 min_params=None, max_params=None, min_lines=None, max_lines=None):
        self.min_complexity = min_complexity
        self.max_complexity = max_complexity
        self.min_params = min_params
        self.max_params = max_params
        self.min_lines = min_lines
        self.max_lines = max_lines

    def should_keep(self, method) -> bool:
        if self.min_complexity is not None and hasattr(method, 'cyclomatic_complexity'):
            if method.cyclomatic_complexity < self.min_complexity:
                return False

        if self.max_complexity is not None and hasattr(method, 'cyclomatic_complexity'):
            if method.cyclomatic_complexity > self.max_complexity:
                return False

        param_count = len(method.parameters) if method.parameters else 0
        if self.min_params is not None and param_count < self.min_params:
            return False
        if self.max_params is not None and param_count > self.max_params:
            return False

        if method.body_span:
            lines = method.body_span[1] - method.body_span[0] + 1
            if self.min_lines is not None and lines < self.min_lines:
                return False
            if self.max_lines is not None and lines > self.max_lines:
                return False

        return True


class SimilarityFilter(MethodFilter):
    """Filter similar methods based on code similarity"""

    def __init__(self, threshold=0.85):
        self.threshold = threshold
        self.methods_to_filter: Set[str] = set()

    def _tokenize(self, body: str) -> Set[str]:
        if not body:
            return set()
        tokens = re.findall(r'\w+', body.lower())
        return set(tokens)

    def _jaccard_similarity(self, tokens1: Set[str], tokens2: Set[str]) -> float:
        if not tokens1 or not tokens2:
            return 0.0
        intersection = len(tokens1 & tokens2)
        union = len(tokens1 | tokens2)
        return intersection / union if union > 0 else 0.0

    def analyze_similarity(self, methods: List) -> None:
        method_tokens: Dict[str, Set[str]] = {}
        for method in methods:
            key = f"{method.class_name}.{method.name}"
            method_tokens[key] = self._tokenize(method.body)

        keys = list(method_tokens.keys())
        for i in range(len(keys)):
            if keys[i] in self.methods_to_filter:
                continue
            for j in range(i + 1, len(keys)):
                if keys[j] in self.methods_to_filter:
                    continue
                similarity = self._jaccard_similarity(method_tokens[keys[i]], method_tokens[keys[j]])
                if similarity >= self.threshold:
                    method_i = next(m for m in methods if f"{m.class_name}.{m.name}" == keys[i])
                    method_j = next(m for m in methods if f"{m.class_name}.{m.name}" == keys[j])
                    complexity_i = getattr(method_i, 'cyclomatic_complexity', 1)
                    complexity_j = getattr(method_j, 'cyclomatic_complexity', 1)
                    if complexity_i >= complexity_j:
                        self.methods_to_filter.add(keys[j])
                    else:
                        self.methods_to_filter.add(keys[i])

    def should_keep(self, method) -> bool:
        key = f"{method.class_name}.{method.name}"
        return key not in self.methods_to_filter
