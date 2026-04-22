#!/usr/bin/env python3
"""Export parsed projects to JSON format."""
import json
import pickle
from pathlib import Path
from loguru import logger

INPUT_DIR = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects")
OUTPUT_DIR = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects")


def export_project_to_json(pkl_file: Path):
    """Export a single project from pickle to JSON."""
    logger.info(f"加载项目: {pkl_file.name}")

    with open(pkl_file, "rb") as f:
        project = pickle.load(f)

    # 收集所有方法数据
    methods_data = []

    for fpath, fctx in project.main_files.items():
        for cls in fctx.classes:
            # 类级信息
            class_info = {
                "fqn": cls.fqn,
                "name": cls.name,
                "package": cls.package,
                "kind": cls.kind,
                "modifiers": list(cls.modifiers),
                "javadoc": cls.javadoc,
            }

            # 遍历类中的所有方法
            for method_name, method_list in cls.methods.items():
                for method in method_list:
                    method_data = {
                        "project": pkl_file.stem,
                        "file_path": fpath,
                        "class": class_info,
                        "method": {
                            "name": method.name,
                            "signature": method.signature_key(),
                            "is_constructor": method.is_constructor,
                            "modifiers": list(method.modifiers),
                            "return_type": {
                                "base": method.return_type.base if method.return_type else None,
                                "resolved_fqn": method.return_type.resolved_fqn if method.return_type else None,
                            } if method.return_type else None,
                            "parameters": [
                                {
                                    "name": p.name,
                                    "type": p.type.base if p.type else None,
                                    "type_fqn": p.type.resolved_fqn if p.type else None,
                                }
                                for p in method.parameters
                            ],
                            "javadoc": method.javadoc,
                            "content": method.content,
                            "span": method.span,
                        }
                    }
                    methods_data.append(method_data)

    # 保存为JSON
    output_file = OUTPUT_DIR / f"{pkl_file.stem}.json"
    logger.info(f"导出 {len(methods_data)} 个方法到: {output_file}")

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(methods_data, f, indent=2, ensure_ascii=False)

    # 同时保存一个统计文件
    stats = {
        "project": pkl_file.stem,
        "total_methods": len(methods_data),
        "methods_with_javadoc": sum(1 for m in methods_data if m["method"]["javadoc"]),
        "javadoc_coverage": sum(1 for m in methods_data if m["method"]["javadoc"]) / len(methods_data) if methods_data else 0,
    }

    stats_file = OUTPUT_DIR / f"{pkl_file.stem}_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)

    logger.info(f"统计信息: {stats}")
    return stats


def main():
    logger.info("开始导出项目到JSON格式...")

    pkl_files = list(INPUT_DIR.glob("*.pkl"))
    logger.info(f"找到 {len(pkl_files)} 个项目文件")

    all_stats = []
    for pkl_file in pkl_files:
        try:
            stats = export_project_to_json(pkl_file)
            all_stats.append(stats)
        except Exception as e:
            logger.error(f"导出 {pkl_file.name} 失败: {e}")
            import traceback
            traceback.print_exc()

    # 保存总体统计
    summary_file = OUTPUT_DIR / "summary.json"
    with open(summary_file, "w", encoding="utf-8") as f:
        json.dump(all_stats, f, indent=2, ensure_ascii=False)

    logger.info(f"\n{'='*60}")
    logger.info("导出完成！")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
