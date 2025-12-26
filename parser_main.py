from __future__ import annotations
import argparse
import os
from loguru import logger

from parser.project_parser import JavaProjectParser


def print_project_summary(project):
    """
    中文输出项目解析结果概览。
    """
    logger.info("========== 项目解析摘要 ==========")
    logger.info(f"项目根路径: {project.root_path}")

    # main 代码统计
    logger.info("【业务代码（main）】")
    logger.info(f"  文件数量: {len(project.main_files)}")
    logger.info(f"  包数量: {len(project.main_packages)}")
    logger.info(f"  类数量: {len([c for p in project.main_packages.values() for c in p.classes.values()])}")

    # test 代码统计
    logger.info("【测试代码（test）】")
    logger.info(f"  文件数量: {len(project.test_files)}")
    logger.info(f"  包数量: {len(project.test_packages)}")
    logger.info(f"  类数量: {len([c for p in project.test_packages.values() for c in p.classes.values()])}")

    # 全局类数量（符号表）
    logger.info("【全局符号表】")
    logger.info(f"  已注册类数量: {len(project.symbols.classes)}")
    logger.info("==================================")


def print_some_details(project, max_classes=5):
    """
    显示一些类的详细结构，方便检查解析是否正确。
    """
    logger.info("展示部分类的详细解析结果（仅展示前几个类）：")

    count = 0
    for fpath, fctx in project.main_files.items():
        for cls in fctx.classes:
            logger.info(f"[类] {cls.fqn}")
            logger.info(f"  类型: {cls.kind}")
            logger.info(f"  父类: {cls.superclass_name}")
            logger.info(f"  实现接口: {cls.interface_names}")
            logger.info(f"  字段: {list(cls.fields.keys())}")
            logger.info(f"  方法: {list(cls.methods.keys())}")

            count += 1
            if count >= max_classes:
                logger.info("（展示结束，仅显示部分类）")
                return


def main():
    parser = argparse.ArgumentParser(description="Java 项目静态解析器")
    parser.add_argument("project_root", help="项目根路径")
    parser.add_argument("main_src", help="src/main/java 路径")
    parser.add_argument("test_src", help="src/test/java 路径")

    args = parser.parse_args()

    # 基本路径检查
    if not os.path.exists(args.main_src):
        logger.error(f"业务代码路径不存在: {args.main_src}")
        return

    if not os.path.exists(args.test_src):
        logger.error(f"测试代码路径不存在: {args.test_src}")
        return

    logger.info("初始化解析器 ...")
    project_parser = JavaProjectParser()

    logger.info("开始解析 Java 项目 ...")
    project = project_parser.parse_project(
        project_root=args.project_root,
        main_src=args.main_src,
        test_src=args.test_src
    )

    logger.info("解析完成。")

    # 打印摘要
    print_project_summary(project)

    # 展示部分详细结果
    print_some_details(project)


if __name__ == "__main__":
    main()