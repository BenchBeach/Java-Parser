from __future__ import annotations
import argparse
import os
import pickle
from pathlib import Path
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


def save_project(project, save_path: str):
    """
    将解析后的project保存为二进制文件。
    """
    try:
        save_file = Path(save_path)
        save_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(save_file, 'wb') as f:
            pickle.dump(project, f)
        
        logger.info(f"项目已保存到: {save_path}")
    except Exception as e:
        logger.error(f"保存项目失败: {e}")


def load_project(load_path: str):
    """
    从二进制文件加载project。
    """
    try:
        load_file = Path(load_path)
        if not load_file.exists():
            logger.warning(f"加载文件不存在: {load_path}")
            return None
        
        with open(load_file, 'rb') as f:
            project = pickle.load(f)
        
        logger.info(f"项目已从文件加载: {load_path}")
        return project
    except Exception as e:
        logger.error(f"加载项目失败: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Java 项目静态解析器")
    parser.add_argument("project_root", help="项目根路径")
    parser.add_argument("main_src", help="src/main/java 路径")
    parser.add_argument("test_src", help="src/test/java 路径")
    parser.add_argument("--save", "-s", type=str, default="", help="保存解析后的project到指定路径（二进制文件）")
    parser.add_argument("--load", "-l", type=str, default="", help="从指定路径加载已解析的project（二进制文件）")
    parser.add_argument("--force-parse", "-f", action="store_true", help="强制重新解析，即使指定了load路径")

    args = parser.parse_args()

    project = None

    # 尝试加载已保存的项目
    if args.load and not args.force_parse:
        logger.info(f"尝试从文件加载项目: {args.load}")
        project = load_project(args.load)
        if project:
            logger.info("成功从文件加载项目，跳过解析步骤。")
        else:
            logger.info("加载失败，将重新解析项目。")
            project = None

    # 如果需要重新解析（未加载成功或强制解析）
    if project is None:
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

    # 如果指定了保存路径，保存项目
    if args.save:
        save_project(project, args.save)

    # 打印摘要
    print_project_summary(project)

    # 展示部分详细结果
    print_some_details(project)


if __name__ == "__main__":
    main()