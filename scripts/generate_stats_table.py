#!/usr/bin/env python3
"""生成JavaDoc质量统计表格"""
import json
from pathlib import Path

# 读取汇总统计
summary_file = Path('/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects/javadoc_analyse/summary_stats.json')
with open(summary_file) as f:
    stats = json.load(f)

# 准备表格数据
print('JavaDoc结构完整性统计（仅统计有JavaDoc的方法）')
print('='*100)
print()

# 表头
header = f"{'指标':<30} | {'commons-lang':<15} | {'gson':<15} | {'jackson-databind':<15} | {'jsoup':<15}"
print(header)
print('-'*100)

# 1. 有JavaDoc的方法数
row = f"{'有JavaDoc的方法数':<30} |"
for s in stats:
    row += f" {s['methods_with_javadoc']:<15} |"
print(row)

# 2. 有描述的占比
row = f"{'有描述 (has_description)':<30} |"
for s in stats:
    ratio = s['methods_with_description'] / s['methods_with_javadoc'] if s['methods_with_javadoc'] > 0 else 0
    row += f" {ratio:.1%}{'':<10} |"
print(row)

# 3. 平均描述长度
row = f"{'平均描述长度 (词数)':<30} |"
for s in stats:
    row += f" {s['avg_description_length']:.1f}{'':<10} |"
print(row)

# 4. 有@param的占比
row = f"{'有@param (has_param_docs)':<30} |"
for s in stats:
    ratio = s['methods_with_param_docs'] / s['methods_with_javadoc'] if s['methods_with_javadoc'] > 0 else 0
    row += f" {ratio:.1%}{'':<10} |"
print(row)

# 5. 参数覆盖率
row = f"{'参数覆盖率 (param_coverage)':<30} |"
for s in stats:
    row += f" {s['avg_param_coverage']:.1%}{'':<10} |"
print(row)

# 6. 有@return的占比
row = f"{'有@return (has_return_doc)':<30} |"
for s in stats:
    ratio = s['methods_with_return_docs'] / s['methods_with_javadoc'] if s['methods_with_javadoc'] > 0 else 0
    row += f" {ratio:.1%}{'':<10} |"
print(row)

# 7. 有@throws的占比
row = f"{'有@throws (has_throws_doc)':<30} |"
for s in stats:
    ratio = s['methods_with_throws_docs'] / s['methods_with_javadoc'] if s['methods_with_javadoc'] > 0 else 0
    row += f" {ratio:.1%}{'':<10} |"
print(row)

print('-'*100)

# 8. 平均完整性评分
row = f"{'平均完整性评分':<30} |"
for s in stats:
    row += f" {s['avg_completeness_score']:.3f}{'':<9} |"
print(row)

print()
print('注：')
print('- 统计范围：仅包含有JavaDoc的方法')
print('- 参数覆盖率：有文档的参数数 / 总参数数')
print('- 完整性评分：综合考虑描述、参数文档、返回值文档的完整性 (0-1)')
