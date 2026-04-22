#!/usr/bin/env python3
"""
JavaDoc质量分析 - 结构完整性统计
"""
import json
from pathlib import Path
from typing import Dict, Any, List
from collections import defaultdict


def analyze_javadoc_structure(method_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    分析单个方法的JavaDoc结构完整性

    Returns:
        {
            'has_description': bool,
            'description_length': int,
            'has_param_docs': bool,
            'param_coverage': float,
            'has_return_doc': bool,
            'has_throws_doc': bool,
            'completeness_score': float
        }
    """
    method = method_data.get('method', {})
    javadoc = method.get('javadoc')

    # 如果没有JavaDoc，返回全False
    if not javadoc:
        return {
            'has_javadoc': False,
            'has_description': False,
            'description_length': 0,
            'has_param_docs': False,
            'param_coverage': 0.0,
            'has_return_doc': False,
            'has_throws_doc': False,
            'completeness_score': 0.0
        }

    # 1. 描述分析
    description = javadoc.get('description', '')
    has_description = len(description.strip()) > 0
    description_length = len(description.split())

    # 2. @param 分析
    tags = javadoc.get('tags', {})
    param_docs = tags.get('param', [])
    has_param_docs = len(param_docs) > 0

    # 计算参数覆盖率
    method_params = method.get('parameters', [])
    total_params = len(method_params)

    if total_params > 0:
        documented_params = set(p['name'] for p in param_docs)
        actual_params = set(p['name'] for p in method_params)
        covered_params = documented_params & actual_params
        param_coverage = len(covered_params) / total_params
    else:
        param_coverage = 1.0  # 无参数视为100%覆盖

    # 3. @return 分析
    has_return_doc = 'return' in tags
    return_type = method.get('return_type')
    is_void = return_type is None or return_type.get('base') == 'void'

    # 4. @throws/@exception 分析
    has_throws_doc = 'throws' in tags or 'exception' in tags

    # 5. 计算完整性评分
    score_components = []

    # 描述存在且有意义（长度>=3词）
    if has_description and description_length >= 3:
        score_components.append(1.0)
    else:
        score_components.append(0.0)

    # 参数覆盖率
    score_components.append(param_coverage)

    # 返回值文档（void方法不要求）
    if is_void:
        score_components.append(1.0)
    else:
        score_components.append(1.0 if has_return_doc else 0.0)

    # 异常文档（有则加分，无不扣分）
    # 这里不计入总分，因为不是所有方法都抛异常

    completeness_score = sum(score_components) / len(score_components)

    return {
        'has_javadoc': True,
        'has_description': has_description,
        'description_length': description_length,
        'has_param_docs': has_param_docs,
        'param_coverage': param_coverage,
        'param_count': total_params,
        'documented_param_count': len(param_docs),
        'has_return_doc': has_return_doc,
        'is_void_method': is_void,
        'has_throws_doc': has_throws_doc,
        'throws_count': len(tags.get('throws', [])),
        'completeness_score': completeness_score
    }


def analyze_project(json_file: Path) -> Dict[str, Any]:
    """分析整个项目的JavaDoc质量"""
    print(f"\n分析项目: {json_file.stem}")

    with open(json_file, 'r', encoding='utf-8') as f:
        methods = json.load(f)

    # 统计数据
    stats = {
        'project_name': json_file.stem,
        'total_methods': len(methods),
        'methods_with_javadoc': 0,
        'methods_with_description': 0,
        'methods_with_param_docs': 0,
        'methods_with_return_docs': 0,
        'methods_with_throws_docs': 0,
        'avg_description_length': 0.0,
        'avg_param_coverage': 0.0,
        'avg_completeness_score': 0.0,
        'quality_distribution': {
            'high': 0,      # score >= 0.8
            'medium': 0,    # 0.5 <= score < 0.8
            'low': 0        # score < 0.5
        }
    }

    # 详细分析结果
    detailed_results = []

    description_lengths = []
    param_coverages = []
    completeness_scores = []

    for method_data in methods:
        analysis = analyze_javadoc_structure(method_data)

        # 添加方法标识信息
        result = {
            'project': json_file.stem,
            'class_fqn': method_data.get('class', {}).get('fqn'),
            'method_name': method_data.get('method', {}).get('name'),
            'signature': method_data.get('method', {}).get('signature'),
            'analysis': analysis
        }
        detailed_results.append(result)

        # 统计
        if analysis['has_javadoc']:
            stats['methods_with_javadoc'] += 1

            if analysis['has_description']:
                stats['methods_with_description'] += 1
                description_lengths.append(analysis['description_length'])

            if analysis['has_param_docs']:
                stats['methods_with_param_docs'] += 1

            if analysis['has_return_doc']:
                stats['methods_with_return_docs'] += 1

            if analysis['has_throws_doc']:
                stats['methods_with_throws_docs'] += 1

            param_coverages.append(analysis['param_coverage'])
            completeness_scores.append(analysis['completeness_score'])

            # 质量分布
            score = analysis['completeness_score']
            if score >= 0.8:
                stats['quality_distribution']['high'] += 1
            elif score >= 0.5:
                stats['quality_distribution']['medium'] += 1
            else:
                stats['quality_distribution']['low'] += 1

    # 计算平均值
    if description_lengths:
        stats['avg_description_length'] = sum(description_lengths) / len(description_lengths)
    if param_coverages:
        stats['avg_param_coverage'] = sum(param_coverages) / len(param_coverages)
    if completeness_scores:
        stats['avg_completeness_score'] = sum(completeness_scores) / len(completeness_scores)

    # 计算覆盖率
    if stats['total_methods'] > 0:
        stats['javadoc_coverage'] = stats['methods_with_javadoc'] / stats['total_methods']

    print(f"  总方法数: {stats['total_methods']}")
    print(f"  有JavaDoc: {stats['methods_with_javadoc']} ({stats['javadoc_coverage']:.1%})")
    print(f"  平均完整性评分: {stats['avg_completeness_score']:.3f}")
    print(f"  质量分布: 高={stats['quality_distribution']['high']}, "
          f"中={stats['quality_distribution']['medium']}, "
          f"低={stats['quality_distribution']['low']}")

    return {
        'stats': stats,
        'detailed_results': detailed_results
    }


def main():
    data_dir = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects")
    output_dir = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects/javadoc_analyse")
    output_dir.mkdir(parents=True, exist_ok=True)

    print("="*60)
    print("JavaDoc 结构完整性分析")
    print("="*60)

    all_stats = []

    for json_file in sorted(data_dir.glob("*.json")):
        if json_file.stem.endswith("_stats") or json_file.stem == "summary":
            continue

        result = analyze_project(json_file)
        all_stats.append(result['stats'])

        # 保存详细结果
        detail_file = output_dir / f"{json_file.stem}_analysis.json"
        with open(detail_file, 'w', encoding='utf-8') as f:
            json.dump(result['detailed_results'], f, indent=2, ensure_ascii=False)
        print(f"  详细结果已保存: {detail_file.name}")

    # 保存汇总统计
    summary_file = output_dir / "summary_stats.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"分析完成！结果保存在: {output_dir}")
    print(f"汇总统计: {summary_file}")
    print(f"{'='*60}")

    # 打印总体统计
    print("\n总体统计:")
    print(f"{'项目':<20} {'方法数':<10} {'JavaDoc覆盖':<15} {'平均完整性':<15} {'高质量数':<10}")
    print("-" * 80)
    for stat in all_stats:
        print(f"{stat['project_name']:<20} "
              f"{stat['total_methods']:<10} "
              f"{stat['javadoc_coverage']:.1%}{'':>10} "
              f"{stat['avg_completeness_score']:.3f}{'':>10} "
              f"{stat['quality_distribution']['high']:<10}")


if __name__ == "__main__":
    main()
