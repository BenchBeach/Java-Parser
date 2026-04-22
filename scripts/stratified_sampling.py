#!/usr/bin/env python3
"""
分层随机取样脚本 - 根据JavaDoc描述长度进行分层抽样
"""
import json
import random
from pathlib import Path
from typing import List, Dict, Any
from collections import defaultdict


def count_words(text: str) -> int:
    """统计文本中的单词数"""
    if not text:
        return 0
    return len(text.split())


def load_methods_from_json(json_file: Path) -> List[Dict[str, Any]]:
    """从JSON文件加载方法数据"""
    with open(json_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def stratified_sampling_by_javadoc_length(
    methods: List[Dict[str, Any]],
    strata_config: List[Dict[str, Any]],
    random_seed: int = 42
) -> Dict[str, List[Dict[str, Any]]]:
    """
    根据JavaDoc描述长度进行分层抽样

    Args:
        methods: 方法列表
        strata_config: 分层配置，格式如：
            [
                {"name": "short", "min_words": 0, "max_words": 10, "sample_size": 2},
                {"name": "long", "min_words": 50, "max_words": None, "sample_size": 2}
            ]
        random_seed: 随机种子

    Returns:
        分层抽样结果字典
    """
    random.seed(random_seed)

    # 按层分组
    strata = defaultdict(list)

    for method in methods:
        javadoc = method.get('method', {}).get('javadoc')
        if not javadoc:
            continue

        description = javadoc.get('description', '')
        word_count = count_words(description)

        # 判断属于哪一层
        for config in strata_config:
            min_words = config.get('min_words', 0)
            max_words = config.get('max_words')

            if max_words is None:
                # 无上限
                if word_count >= min_words:
                    strata[config['name']].append({
                        'method': method,
                        'word_count': word_count
                    })
            else:
                # 有上限
                if min_words <= word_count <= max_words:
                    strata[config['name']].append({
                        'method': method,
                        'word_count': word_count
                    })

    # 从每层抽样
    samples = {}
    for config in strata_config:
        stratum_name = config['name']
        sample_size = config['sample_size']

        stratum_data = strata[stratum_name]

        if len(stratum_data) < sample_size:
            print(f"警告: {stratum_name} 层只有 {len(stratum_data)} 个样本，少于需要的 {sample_size} 个")
            samples[stratum_name] = stratum_data
        else:
            samples[stratum_name] = random.sample(stratum_data, sample_size)

        print(f"{stratum_name} 层: 总数={len(stratum_data)}, 抽样={len(samples[stratum_name])}")

    return samples


def main():
    # 配置
    data_dir = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects")
    output_dir = Path("/data/parsed_projects/samples")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 分层配置
    strata_config = [
        {
            "name": "short_description",
            "min_words": 0,
            "max_words": 10,
            "sample_size": 2
        },
        {
            "name": "long_description",
            "min_words": 50,
            "max_words": None,
            "sample_size": 2
        }
    ]

    # 处理所有项目
    all_samples = {}

    for json_file in data_dir.glob("*.json"):
        if json_file.stem.endswith("_stats") or json_file.stem == "summary":
            continue

        project_name = json_file.stem
        print(f"\n{'='*60}")
        print(f"处理项目: {project_name}")
        print(f"{'='*60}")

        methods = load_methods_from_json(json_file)
        print(f"总方法数: {len(methods)}")

        # 统计有JavaDoc的方法
        methods_with_javadoc = [m for m in methods if m.get('method', {}).get('javadoc')]
        print(f"有JavaDoc的方法: {len(methods_with_javadoc)}")

        # 分层抽样
        samples = stratified_sampling_by_javadoc_length(methods_with_javadoc, strata_config)
        all_samples[project_name] = samples

        # 保存该项目的样本
        project_output = output_dir / f"{project_name}_samples.json"

        # 格式化输出（去掉word_count，只保留method）
        formatted_samples = {}
        for stratum_name, stratum_samples in samples.items():
            formatted_samples[stratum_name] = [s['method'] for s in stratum_samples]

        with open(project_output, 'w', encoding='utf-8') as f:
            json.dump(formatted_samples, f, indent=2, ensure_ascii=False)

        print(f"样本已保存到: {project_output}")

    # 保存汇总统计
    summary = {
        "strata_config": strata_config,
        "projects": {}
    }

    for project_name, samples in all_samples.items():
        summary["projects"][project_name] = {
            stratum_name: len(stratum_samples)
            for stratum_name, stratum_samples in samples.items()
        }

    summary_file = output_dir / "sampling_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"所有样本已保存到: {output_dir}")
    print(f"汇总信息: {summary_file}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
