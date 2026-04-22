#!/usr/bin/env python3
"""Parse all 4 projects and save results."""
import pickle
from pathlib import Path
from loguru import logger
from parser.project_parser import JavaProjectParser

# Project configurations
PROJECTS = [
    {
        "name": "gson",
        "root": "/Users/hanqiaoyu/Research/work/gson",
        "main_src": "/Users/hanqiaoyu/Research/work/gson/gson/src/main/java",
        "test_src": "/Users/hanqiaoyu/Research/work/gson/gson/src/test/java",
    },
    {
        "name": "jackson-databind",
        "root": "/Users/hanqiaoyu/Research/work/jackson-databind",
        "main_src": "/Users/hanqiaoyu/Research/work/jackson-databind/src/main/java",
        "test_src": "/Users/hanqiaoyu/Research/work/jackson-databind/src/test/java",
    },
    {
        "name": "commons-lang",
        "root": "/Users/hanqiaoyu/Research/work/commons-lang",
        "main_src": "/Users/hanqiaoyu/Research/work/commons-lang/src/main/java",
        "test_src": "/Users/hanqiaoyu/Research/work/commons-lang/src/test/java",
    },
    {
        "name": "jsoup",
        "root": "/Users/hanqiaoyu/Research/work/jsoup",
        "main_src": "/Users/hanqiaoyu/Research/work/jsoup/src/main/java",
        "test_src": "/Users/hanqiaoyu/Research/work/jsoup/src/test/java",
    },
]

OUTPUT_DIR = Path("/Users/hanqiaoyu/Research/work/UTbenchmark/data/parsed_projects")


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parser = JavaProjectParser()

    for proj_config in PROJECTS:
        name = proj_config["name"]
        logger.info(f"\n{'='*60}")
        logger.info(f"开始解析项目: {name}")
        logger.info(f"{'='*60}")

        try:
            project = parser.parse_project(
                project_root=proj_config["root"],
                main_src=proj_config["main_src"],
                test_src=proj_config["test_src"],
            )

            # 统计信息
            total_methods = 0
            methods_with_javadoc = 0
            total_classes = 0
            classes_with_javadoc = 0

            for fpath, fctx in project.main_files.items():
                for cls in fctx.classes:
                    total_classes += 1
                    if cls.javadoc:
                        classes_with_javadoc += 1

                    for methods in cls.methods.values():
                        for m in methods:
                            total_methods += 1
                            if m.javadoc:
                                methods_with_javadoc += 1

            logger.info(f"解析完成:")
            logger.info(f"  类总数: {total_classes}, 有JavaDoc: {classes_with_javadoc}")
            logger.info(f"  方法总数: {total_methods}, 有JavaDoc: {methods_with_javadoc}")

            # 保存
            output_file = OUTPUT_DIR / f"{name}.pkl"
            with open(output_file, "wb") as f:
                pickle.dump(project, f)
            logger.info(f"已保存到: {output_file}")

        except Exception as e:
            logger.error(f"解析 {name} 失败: {e}")
            import traceback
            traceback.print_exc()

    logger.info(f"\n{'='*60}")
    logger.info("所有项目解析完成！")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    main()
