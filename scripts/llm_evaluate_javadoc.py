#!/usr/bin/env python3
"""
使用LLM作为评判器，对JavaDoc进行结构化质量评估
"""
import json
import os
import argparse
import random
from pathlib import Path
from typing import Dict, Any, List
import time
from openai import OpenAI


# API配置
API_KEY = "sk-b7c6ce88c2c04b0c8acd97718030478f"
BASE_URL = "https://api.deepseek.com"

client = OpenAI(api_key=API_KEY, base_url=BASE_URL)


def build_evaluation_prompt(method_data: Dict[str, Any]) -> str:
    """构建评估prompt"""
    method = method_data.get('method', {})
    javadoc = method.get('javadoc', {})

    # 提取信息
    signature = method.get('signature', '')
    description = javadoc.get('description', '')
    tags = javadoc.get('tags', {})

    # 格式化参数文档
    param_docs = tags.get('param', [])
    param_str = '\n'.join([f"  @param {p['name']} {p['description']}" for p in param_docs]) if param_docs else "None"

    # 格式化返回值文档
    return_doc = tags.get('return', 'None')

    # 格式化异常文档
    throws_docs = tags.get('throws', [])
    throws_str = '\n'.join([f"  @throws {t['type']} {t['description']}" for t in throws_docs]) if throws_docs else "None"

    prompt = f"""Analyze the JavaDoc of the following Java method and judge its quality as a test generation specification (spec).

Method Signature: {signature}

JavaDoc Description:
{description}

Parameter Documentation:
{param_str}

Return Documentation:
{return_doc}

Throws Documentation:
{throws_str}

Please evaluate the following dimensions (answer true/false):
1. behavior_clarity: Does it clearly describe the specific behavior/business logic of the method? (Not just a simple repetition of the method name)
2. has_precondition: Does it explicitly state the input requirements/preconditions? (e.g., parameter ranges, non-null requirements, etc.)
3. has_postcondition: Does it explicitly state the output guarantees/postconditions? (e.g., meaning of the return value, side effects, etc.)
4. mentions_edge_cases: Does it mention edge cases/exception handling? (e.g., null, empty collections, out-of-bounds, etc.)
5. input_output_mapping: Is the mapping between input and output clear? (Can the output be inferred from the input?)
6. testable: Can meaningful test cases be written based on this JavaDoc?

Return in JSON format (do not include any other text):
{{
  "behavior_clarity": true,
  "has_precondition": false,
  "has_postcondition": true,
  "mentions_edge_cases": false,
  "input_output_mapping": true,
  "testable": true,
  "reasoning": "Brief explanation (1-2 sentences)"
}}"""

    return prompt


def call_llm_judge(prompt: str, max_retries: int = 3) -> Dict[str, Any]:
    """调用LLM进行评判"""
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": "You are a professional code spec quality evaluation expert, skilled at analyzing the quality of JavaDoc. Please return the results strictly in JSON format."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=500
            )

            result_text = response.choices[0].message.content.strip()

            # 尝试解析JSON
            # 移除可能的markdown代码块标记
            if result_text.startswith("```json"):
                result_text = result_text[7:]
            if result_text.startswith("```"):
                result_text = result_text[3:]
            if result_text.endswith("```"):
                result_text = result_text[:-3]

            result = json.loads(result_text.strip())
            return result

        except json.JSONDecodeError as e:
            print(f"  JSON解析失败 (尝试 {attempt+1}/{max_retries}): {e}")
            print(f"  原始响应: {result_text[:200]}")
            if attempt == max_retries - 1:
                return {
                    "error": "JSON解析失败",
                    "raw_response": result_text
                }
            time.sleep(1)

        except Exception as e:
            print(f"  API调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                return {
                    "error": str(e)
                }
            time.sleep(2)

    return {"error": "超过最大重试次数"}


def evaluate_methods(methods: List[Dict[str, Any]], limit: int = None, random_sample: bool = False, seed: int = 42) -> List[Dict[str, Any]]:
    """评估方法列表，返回包含完整字段的数据

    Args:
        methods: 方法列表
        limit: 评估数量限制
        random_sample: 是否随机抽样（默认False，按顺序取前N个）
        seed: 随机种子（默认42）
    """
    results = []

    # 只评估有JavaDoc的方法
    methods_with_javadoc = [m for m in methods if m.get('method', {}).get('javadoc')]

    if limit:
        if random_sample:
            # 固定随机种子，保证可重复性
            random.seed(seed)
            methods_with_javadoc = random.sample(methods_with_javadoc, min(limit, len(methods_with_javadoc)))
        else:
            # 按顺序取前N个
            methods_with_javadoc = methods_with_javadoc[:limit]

    total = len(methods_with_javadoc)
    print(f"开始评估 {total} 个方法...")
    if random_sample:
        print(f"  (随机抽样，种子={seed})")
    else:
        print(f"  (顺序取样)")

    for idx, method_data in enumerate(methods_with_javadoc, 1):
        print(f"\n[{idx}/{total}] 评估: {method_data.get('class', {}).get('fqn')}.{method_data.get('method', {}).get('name')}")

        # 构建prompt
        prompt = build_evaluation_prompt(method_data)

        # 调用LLM
        evaluation = call_llm_judge(prompt)

        # 在原始数据上添加评估结果
        method_data_copy = method_data.copy()
        method_data_copy['llm_evaluation'] = evaluation
        results.append(method_data_copy)

        # 显示评估结果
        if 'error' not in evaluation:
            print(f"  结果: {evaluation.get('reasoning', 'N/A')}")
            print(f"  可测试性: {evaluation.get('testable', False)}")
        else:
            print(f"  错误: {evaluation.get('error')}")

        # 避免请求过快
        time.sleep(0.5)

    return results


def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='使用LLM评估JavaDoc质量')
    parser.add_argument('--project', type=str, required=True,
                        help='项目名称 (gson, jackson-databind, commons-lang, jsoup)')
    parser.add_argument('--limit', type=int, default=None,
                        help='评估的方法数量限制（默认评估所有有JavaDoc的方法）')
    parser.add_argument('--random', action='store_true',
                        help='使用随机抽样（默认按顺序取样）')
    parser.add_argument('--seed', type=int, default=42,
                        help='随机种子（默认42）')
    args = parser.parse_args()

    # 配置
    data_dir = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects")
    output_dir = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects/llm_evaluation")
    output_dir.mkdir(parents=True, exist_ok=True)

    project_name = args.project
    sample_size = args.limit

    print("="*60)
    print("JavaDoc质量LLM评估 - 方案A：结构化判断")
    print("="*60)
    print(f"项目: {project_name}")
    print(f"样本数: {sample_size if sample_size else '全部'}")
    print()

    # 加载数据
    json_file = data_dir / f"{project_name}.json"
    if not json_file.exists():
        print(f"错误：找不到文件 {json_file}")
        return

    with open(json_file, 'r', encoding='utf-8') as f:
        methods = json.load(f)

    print(f"加载了 {len(methods)} 个方法")

    # 评估
    results = evaluate_methods(methods, limit=sample_size, random_sample=args.random, seed=args.seed)

    # 保存结果（包含完整字段的数据）
    suffix = "_random" if args.random else ""
    output_file = output_dir / f"{project_name}_with_llm_eval{suffix}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"评估完成！结果已保存到: {output_file}")

    # 统计
    successful = [r for r in results if 'error' not in r.get('llm_evaluation', {})]
    if successful:
        testable_count = sum(1 for r in successful if r['llm_evaluation'].get('testable', False))
        behavior_clear = sum(1 for r in successful if r['llm_evaluation'].get('behavior_clarity', False))
        has_precond = sum(1 for r in successful if r['llm_evaluation'].get('has_precondition', False))
        has_postcond = sum(1 for r in successful if r['llm_evaluation'].get('has_postcondition', False))
        has_edge = sum(1 for r in successful if r['llm_evaluation'].get('mentions_edge_cases', False))

        print(f"\n统计结果 (n={len(successful)}):")
        print(f"  可测试: {testable_count} ({testable_count/len(successful):.1%})")
        print(f"  行为清晰: {behavior_clear} ({behavior_clear/len(successful):.1%})")
        print(f"  输入输出映射明确: {sum(1 for r in successful if r['llm_evaluation'].get('input_output_mapping', False))} ")
        print(f"  有前置条件: {has_precond} ({has_precond/len(successful):.1%})")
        print(f"  有后置条件: {has_postcond} ({has_postcond/len(successful):.1%})")
        print(f"  提到边界情况: {has_edge} ({has_edge/len(successful):.1%})")

    print(f"{'='*60}")


if __name__ == "__main__":
    main()
