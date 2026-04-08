#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.project import ProjectContext
from parser.project_parser import JavaProjectParser
from metrics import ComplexityCalculator, InputMetricsCalculator, OutputMetricsCalculator, MetricsAggregator
import pickle


def calculate_method_difficulty(method_key: str, project: ProjectContext) -> dict:
    """计算单个方法的难度指标"""
    method = project.symbols.methods.get(method_key)
    if not method:
        return {'error': f'Method not found: {method_key}'}

    # 获取方法所属类
    class_fqn = None
    for fqn, cls in project.symbols.classes.items():
        if method_key in cls.methods:
            class_fqn = fqn
            break

    # 初始化计算器
    complexity_calc = ComplexityCalculator()
    input_calc = InputMetricsCalculator(project.symbols)
    output_calc = OutputMetricsCalculator()
    aggregator = MetricsAggregator()

    # 计算细粒度指标
    fine_grained = {
        '函数内部复杂度': {
            'cyclomatic_complexity': complexity_calc.calculate_cyclomatic_complexity(method),
            'branch_count': complexity_calc.calculate_branch_count(method),
            'loop_count': complexity_calc.calculate_loop_count(method),
            'exception_paths': complexity_calc.calculate_exception_paths(method),
        },
        '上下文依赖复杂度': {
            'field_dependency_count': input_calc.calculate_field_dependency(method),
            'external_call_count': input_calc.calculate_external_calls(method, class_fqn or ''),
            'static_dependency_count': input_calc.calculate_static_dependency(method),
        },
        '跨文件模块复杂度': {
            'dependent_class_count': input_calc.calculate_dependent_classes(method),
            'cross_package_call_count': input_calc.calculate_cross_package_calls(method, class_fqn or ''),
        },
    }

    param_metrics = input_calc.calculate_parameter_complexity(method)
    fine_grained['输入构造复杂度'] = param_metrics

    field_complexity = input_calc.calculate_field_type_complexity(method)
    mock_complexity = output_calc.calculate_mock_complexity(method, class_fqn or '')
    fine_grained['测试结构复杂度'] = {
        'mock_requirement_score': mock_complexity,
        'setup_complexity': output_calc.calculate_setup_complexity(param_metrics['parameter_type_complexity'], field_complexity),
    }

    fine_grained['测试范围'] = {
        'minimum_test_case_count': fine_grained['函数内部复杂度']['cyclomatic_complexity'],
    }

    fine_grained['交互复杂度'] = {
        'object_collaboration_count': (
            param_metrics['parameter_count'] +
            fine_grained['上下文依赖复杂度']['field_dependency_count'] +
            fine_grained['跨文件模块复杂度']['dependent_class_count']
        ),
    }

    side_effect_count = output_calc.calculate_side_effect_indicator(method)
    fine_grained['可观测性难度'] = {
        'return_type_complexity': output_calc.calculate_return_complexity(method.return_type),
        'side_effect_count': side_effect_count,
    }

    external_calls = fine_grained['上下文依赖复杂度']['external_call_count']
    fine_grained['断言构造难度'] = {
        'assertion_complexity': output_calc.calculate_assertion_complexity(method, external_calls),
    }

    # 聚合所有指标用于评分
    all_metrics = {}
    for category in fine_grained.values():
        all_metrics.update(category)

    # 计算维度聚合分数
    input_score = aggregator.aggregate_input_complexity(all_metrics)
    output_score = aggregator.aggregate_output_complexity(all_metrics)
    overall_score = aggregator.calculate_overall_difficulty(input_score, output_score)
    difficulty_level = aggregator.classify_difficulty(overall_score)

    return {
        'method_fqn': method_key,
        '细粒度指标': fine_grained,
        '维度聚合分数': {
            'input_complexity': round(input_score, 2),
            'output_complexity': round(output_score, 2),
        },
        '总体难度分数': round(overall_score, 2),
        '难度等级': difficulty_level,
    }


def main():
    parser = argparse.ArgumentParser(description='计算Java方法的单元测试难度指标')
    parser.add_argument('project_root', nargs='?', help='项目根目录')
    parser.add_argument('main_src', nargs='?', help='主代码目录')
    parser.add_argument('test_src', nargs='?', help='测试代码目录')
    parser.add_argument('--method', help='特定方法FQN#signature')
    parser.add_argument('--output', help='输出JSON文件路径')
    parser.add_argument('--load', help='加载已解析的项目JSON文件')

    args = parser.parse_args()

    if not args.load and not all([args.project_root, args.main_src, args.test_src]):
        parser.error('需要提供 project_root, main_src, test_src 或使用 --load')

    # 解析或加载项目
    if args.load:
        print(f"Loading project from {args.load}...")
        with open(args.load, 'rb') as f:
            project = pickle.load(f)
    else:
        print(f"Parsing project at {args.project_root}...")
        parser = JavaProjectParser()
        project = parser.parse_project(args.project_root, args.main_src, args.test_src)

    # 计算指标
    if args.method:
        result = calculate_method_difficulty(args.method, project)
        results = [result]
    else:
        print(f"Calculating difficulty for {len(project.symbols.methods)} methods...")
        results = []
        for method_key in project.symbols.methods:
            result = calculate_method_difficulty(method_key, project)
            results.append(result)

    # 输出结果
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Results saved to {args.output}")
    else:
        print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()

