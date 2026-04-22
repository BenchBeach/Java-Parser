#!/usr/bin/env python3
"""
统计所有LLM评估维度都为True的方法数量
"""
import json
from pathlib import Path

def count_perfect_methods(eval_file: Path) -> dict:
    """统计所有维度都为True的方法"""
    with open(eval_file, 'r', encoding='utf-8') as f:
        methods = json.load(f)

    total = len(methods)
    perfect_count = 0
    perfect_methods = []
    testable_and_clear_count = 0
    testable_and_clear_methods = []

    dimensions = ['behavior_clarity', 'has_precondition', 'has_postcondition',
                  'mentions_edge_cases', 'input_output_mapping', 'testable']

    # 统计各维度
    dimension_counts = {dim: 0 for dim in dimensions}
    valid_count = 0  # 有效评估数（排除错误）

    for method in methods:
        evaluation = method.get('llm_evaluation', {})

        # 跳过有错误的评估
        if 'error' in evaluation:
            continue

        valid_count += 1

        # 统计各维度
        for dim in dimensions:
            if evaluation.get(dim, False):
                dimension_counts[dim] += 1

        # 检查所有维度是否都为True
        all_true = all(evaluation.get(dim, False) for dim in dimensions)

        if all_true:
            perfect_count += 1
            perfect_methods.append({
                'class_fqn': method.get('class', {}).get('fqn'),
                'signature': method.get('method', {}).get('signature'),
                'des_length': method.get('method',{}).get('javadoc', {}).get('description', '').split().__len__()  # 描述长度（词数）
            })

        # 检查是否行为清晰且可测试
        if evaluation.get('behavior_clarity', False) and evaluation.get('testable', False):
            testable_and_clear_count += 1
            testable_and_clear_methods.append({
                'class_fqn': method.get('class', {}).get('fqn'),
                'signature': method.get('method', {}).get('signature'),
                'des_length': method.get('method',{}).get('javadoc', {}).get('description', '').split().__len__()
            })


    return {
        'total': total,
        'valid_count': valid_count,
        'perfect_count': perfect_count,
        'perfect_methods': perfect_methods,
        'testable_and_clear_count': testable_and_clear_count,
        'testable_and_clear_methods': testable_and_clear_methods,
        'dimension_counts': dimension_counts
    }


def main():
    eval_dir = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects/llm_evaluation")

    projects = ['gson', 'commons-lang', 'jackson-databind', 'jsoup']

    print("="*80)
    print("统计所有LLM评估维度都为True的方法")
    print("="*80)
    print()

    all_results = {}
    total_perfect = 0
    total_methods = 0
    total_testable_and_clear = 0
    total_dimension_counts = {
        'behavior_clarity': 0,
        'has_precondition': 0,
        'has_postcondition': 0,
        'mentions_edge_cases': 0,
        'input_output_mapping': 0,
        'testable': 0
    }
    total_valid = 0

    for project in projects:
        eval_file = eval_dir / f"{project}_with_llm_eval_random.json"

        if not eval_file.exists():
            print(f"⚠ 未找到文件: {eval_file.name}")
            continue

        result = count_perfect_methods(eval_file)
        all_results[project] = result

        total_perfect += result['perfect_count']
        total_methods += result['total']
        total_valid += result['valid_count']
        total_testable_and_clear += result['testable_and_clear_count']

        # 累加各维度统计
        for dim, count in result['dimension_counts'].items():
            total_dimension_counts[dim] += count

        print(f"{project}:")
        print(f"  评估方法数: {result['total']}")
        print(f"  完美方法数: {result['perfect_count']} ({result['perfect_count']/result['valid_count']:.1%})")
        print(f"  行为清晰且可测试: {result['testable_and_clear_count']} ({result['testable_and_clear_count']/result['valid_count']:.1%})")

        # 显示各维度百分比
        print(f"  各维度统计:")
        for dim, count in result['dimension_counts'].items():
            percentage = count / result['valid_count'] if result['valid_count'] > 0 else 0
            print(f"    {dim}: {count}/{result['valid_count']} ({percentage:.1%})")

        if result['perfect_methods']:
            print(f"  完美方法列表:")
            for m in result['perfect_methods']:
                print(f"    - {m['class_fqn']}.{m['signature']}: 描述长度={m['des_length']}词")

        if result['testable_and_clear_methods']:
            print(f"  行为清晰且可测试的方法列表:")
            for m in result['testable_and_clear_methods'][:5]:  # 只显示前5个
                print(f"    - {m['class_fqn']}.{m['signature']}: 描述长度={m['des_length']}词")
            if len(result['testable_and_clear_methods']) > 5:
                print(f"    ... 还有 {len(result['testable_and_clear_methods']) - 5} 个")
        print()

    print("="*80)
    print(f"总计:")
    print(f"  评估方法数: {total_methods}")
    print(f"  有效评估数: {total_valid}")
    print(f"  完美方法数: {total_perfect} ({total_perfect/total_valid:.1%})")
    print(f"  行为清晰且可测试: {total_testable_and_clear} ({total_testable_and_clear/total_valid:.1%})")
    print()
    print(f"各维度总体统计:")
    for dim, count in total_dimension_counts.items():
        percentage = count / total_valid if total_valid > 0 else 0
        print(f"  {dim}: {count}/{total_valid} ({percentage:.1%})")
    print("="*80)


if __name__ == "__main__":
    main()
