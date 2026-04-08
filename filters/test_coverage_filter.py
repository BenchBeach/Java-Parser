from .method_filter import MethodFilter
from typing import Dict, Set
import re


class TestCoverageFilter(MethodFilter):
    """Filter methods based on test coverage"""

    def __init__(self, project, require_tests=True, min_test_count=1):
        self.require_tests = require_tests
        self.min_test_count = min_test_count
        self.method_test_map = self._build_test_map(project)

    def _extract_tested_method(self, test_name: str) -> str:
        """Extract tested method name from test method name"""
        # testMethodName -> methodName
        # test_method_name -> method_name
        # shouldDoSomething -> doSomething
        patterns = [
            r'^test(.+)',
            r'^should(.+)',
            r'^(.+)Test$',
            r'^(.+)_test$'
        ]
        for pattern in patterns:
            match = re.match(pattern, test_name, re.IGNORECASE)
            if match:
                name = match.group(1)
                return name[0].lower() + name[1:] if name else test_name
        return test_name

    def _build_test_map(self, project) -> Dict[str, int]:
        """Build map of method name to test count using method calls"""
        test_map = {}

        for cls in project.symbols.classes.values():
            if not cls.name.endswith('Test'):
                continue

            for method_list in cls.methods.values():
                for test_method in method_list:
                    if not test_method.name.startswith('test'):
                        continue

                    # Use method calls to find tested methods
                    for call in test_method.method_calls:
                        if call.method_name:
                            # Simple key: just method name
                            test_map[call.method_name] = test_map.get(call.method_name, 0) + 1

        return test_map

    def should_keep(self, method) -> bool:
        test_count = self.method_test_map.get(method.name, 0)

        if self.require_tests and test_count == 0:
            return False

        if test_count < self.min_test_count:
            return False

        return True

