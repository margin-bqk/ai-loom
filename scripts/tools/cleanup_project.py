#!/usr/bin/env python3
"""
项目清理脚本
用于整理项目目录结构，移动临时文件和测试文件到合适的位置
"""

import os
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Tuple


class ProjectCleanup:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.stats = {"moved": 0, "deleted": 0, "skipped": 0, "errors": 0}

    def analyze_root_files(self) -> Dict[str, List[str]]:
        """分析根目录中的文件，分类识别"""
        categories = {
            "debug_files": [],  # debug_*.py 文件
            "test_files": [],  # test_*.py 文件
            "verify_files": [],  # verify_*.py 文件
            "temp_files": [],  # 其他临时文件
            "config_files": [],  # 配置文件
            "important_files": [],  # 重要文件（不应移动）
        }

        # 重要文件列表（不应移动）
        important_files = {
            ".env.example",
            ".flake8",
            ".gitignore",
            ".pre-commit-config.yaml",
            "CHANGELOG.md",
            "docker-compose.yml",
            "Dockerfile",
            "pyproject.toml",
            "README.md",
            "RELEASE_CHECKLIST_v0.10.0.md",
            "RELEASE_CHECKLIST.md",
            "requirements.txt",
            "loom.db",
        }

        for item in self.project_root.iterdir():
            if item.is_file():
                filename = item.name

                # 检查是否重要文件
                if filename in important_files:
                    categories["important_files"].append(str(item))
                    continue

                # 分类文件
                if filename.startswith("debug_") and filename.endswith(".py"):
                    categories["debug_files"].append(str(item))
                elif filename.startswith("test_") and filename.endswith(".py"):
                    categories["test_files"].append(str(item))
                elif filename.startswith("verify_") and filename.endswith(".py"):
                    categories["verify_files"].append(str(item))
                elif filename in ["test_input.txt", "search_config_list.py"]:
                    categories["temp_files"].append(str(item))
                elif filename.endswith(".yaml") or filename.endswith(".yml"):
                    categories["config_files"].append(str(item))
                else:
                    # 其他文件暂时不处理
                    pass

        return categories

    def create_directories(self):
        """创建必要的目录结构"""
        directories = [
            "scripts/debug",
            "scripts/deploy",
            "scripts/test_utils",
            "scripts/verification",
            "scripts/tools",
            "scripts/setup",
            "tests/temp",
            "tests/verify",
        ]

        for dir_path in directories:
            full_path = self.project_root / dir_path
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"[OK] 创建目录: {dir_path}")

    def move_debug_files(self, debug_files: List[str]) -> int:
        """移动debug文件到scripts/debug目录"""
        moved_count = 0
        debug_dir = self.project_root / "scripts" / "debug"

        for file_path in debug_files:
            try:
                src = Path(file_path)
                dst = debug_dir / src.name

                if dst.exists():
                    # 如果目标文件已存在，添加后缀
                    base_name = src.stem
                    extension = src.suffix
                    counter = 1
                    while dst.exists():
                        new_name = f"{base_name}_{counter}{extension}"
                        dst = debug_dir / new_name
                        counter += 1

                shutil.move(str(src), str(dst))
                print(f"[OK] 移动debug文件: {src.name} -> scripts/debug/{dst.name}")
                moved_count += 1
            except Exception as e:
                print(f"[ERROR] 移动debug文件失败 {src.name}: {e}")
                self.stats["errors"] += 1

        return moved_count

    def move_test_files(self, test_files: List[str]) -> int:
        """移动临时测试文件到tests/temp目录"""
        moved_count = 0
        temp_dir = self.project_root / "tests" / "temp"

        for file_path in test_files:
            try:
                src = Path(file_path)
                dst = temp_dir / src.name

                if dst.exists():
                    # 如果目标文件已存在，添加后缀
                    base_name = src.stem
                    extension = src.suffix
                    counter = 1
                    while dst.exists():
                        new_name = f"{base_name}_{counter}{extension}"
                        dst = temp_dir / new_name
                        counter += 1

                shutil.move(str(src), str(dst))
                print(f"[OK] 移动测试文件: {src.name} -> tests/temp/{dst.name}")
                moved_count += 1
            except Exception as e:
                print(f"[ERROR] 移动测试文件失败 {src.name}: {e}")
                self.stats["errors"] += 1

        return moved_count

    def move_verify_files(self, verify_files: List[str]) -> int:
        """移动verify文件到tests/verify目录"""
        moved_count = 0
        verify_dir = self.project_root / "tests" / "verify"

        for file_path in verify_files:
            try:
                src = Path(file_path)
                dst = verify_dir / src.name

                if dst.exists():
                    # 如果目标文件已存在，添加后缀
                    base_name = src.stem
                    extension = src.suffix
                    counter = 1
                    while dst.exists():
                        new_name = f"{base_name}_{counter}{extension}"
                        dst = verify_dir / new_name
                        counter += 1

                shutil.move(str(src), str(dst))
                print(f"[OK] 移动verify文件: {src.name} -> tests/verify/{dst.name}")
                moved_count += 1
            except Exception as e:
                print(f"[ERROR] 移动verify文件失败 {src.name}: {e}")
                self.stats["errors"] += 1

        return moved_count

    def cleanup_temp_files(self, temp_files: List[str]) -> int:
        """清理临时文件（移动到临时目录或删除）"""
        cleaned_count = 0
        temp_dir = self.project_root / "temp_backup"
        temp_dir.mkdir(exist_ok=True)

        for file_path in temp_files:
            try:
                src = Path(file_path)

                # 对于文本文件，可以移动到备份目录
                if src.suffix in [".txt", ".log", ".tmp"]:
                    dst = temp_dir / src.name
                    shutil.move(str(src), str(dst))
                    print(f"[OK] 备份临时文件: {src.name} -> temp_backup/")
                    cleaned_count += 1
                else:
                    # 其他文件询问是否删除（这里先移动到备份）
                    dst = temp_dir / src.name
                    shutil.move(str(src), str(dst))
                    print(f"[WARN] 移动未知临时文件到备份: {src.name}")
                    cleaned_count += 1

            except Exception as e:
                print(f"[ERROR] 处理临时文件失败 {src.name}: {e}")
                self.stats["errors"] += 1

        return cleaned_count

    def reorganize_scripts_directory(self) -> Dict[str, int]:
        """重组scripts目录结构"""
        stats = {"moved": 0, "errors": 0}
        scripts_dir = self.project_root / "scripts"

        if not scripts_dir.exists():
            print(f"[INFO] scripts目录不存在: {scripts_dir}")
            return stats

        # 定义文件分类规则
        file_categories = {
            "deploy": ["deploy_verify.py", "release.py", "rollback.py"],
            "test_utils": ["test_*.py", "run_phase1_tests.py"],
            "verification": ["verify_*.py"],
            "tools": [
                "cleanup_project.py",
                "organize_docs.py",
                "update_terminology.py",
                "run_example.py",
                "cleanup_plan.md",
            ],
            "setup": ["setup_*.sh", "setup_*.py"],
        }

        # 实际的文件移动映射
        file_mapping = {
            "deploy": ["deploy_verify.py", "release.py", "rollback.py"],
            "test_utils": [
                "test_component_imports_fixed.py",
                "test_enhanced_reasoning_simple.py",
                "test_memory_integration.py",
                "test_performance_monitoring_integration.py",
                "test_rule_components.py",
                "test_rules_interpretation_simple.py",
                "test_runtime_integration.py",
                "run_phase1_tests.py",
            ],
            "verification": [
                "verify_components_ascii.py",
                "verify_enhanced_components_simple.py",
                "verify_llm_provider_enhancements.py",
                "verify_memory_simple.py",
                "verify_performance_monitoring_simple.py",
                "verify_rule_simple.py",
                "verify_runtime.py",
                "verify_terminology.py",
            ],
            "tools": [
                "cleanup_project.py",
                "organize_docs.py",
                "update_terminology.py",
                "run_example.py",
                "cleanup_plan.md",
            ],
            "setup": ["setup_dev.sh", "setup_env.sh"],
        }

        # 移动文件
        for category, files in file_mapping.items():
            target_dir = scripts_dir / category
            target_dir.mkdir(exist_ok=True)

            for filename in files:
                src = scripts_dir / filename
                if src.exists():
                    try:
                        dst = target_dir / filename
                        if dst.exists():
                            # 如果目标文件已存在，添加后缀
                            base_name = src.stem
                            extension = src.suffix if src.suffix else ".md"
                            counter = 1
                            while dst.exists():
                                new_name = f"{base_name}_{counter}{extension}"
                                dst = target_dir / new_name
                                counter += 1

                        shutil.move(str(src), str(dst))
                        print(f"[OK] 移动文件到scripts/{category}/: {filename}")
                        stats["moved"] += 1
                    except Exception as e:
                        print(f"[ERROR] 移动文件失败 {filename}: {e}")
                        stats["errors"] += 1

        print(f"[INFO] scripts目录重组完成: 移动了 {stats['moved']} 个文件")
        return stats

    def run_dry_run(self) -> Dict[str, List[str]]:
        """模拟运行，显示将要执行的操作"""
        print("=" * 60)
        print("模拟清理运行（不会实际移动文件）")
        print("=" * 60)

        categories = self.analyze_root_files()

        print(f"\n发现 {len(categories['debug_files'])} 个debug文件:")
        for f in categories["debug_files"]:
            print(f"  - {Path(f).name}")

        print(f"\n发现 {len(categories['test_files'])} 个测试文件:")
        for f in categories["test_files"]:
            print(f"  - {Path(f).name}")

        print(f"\n发现 {len(categories['verify_files'])} 个verify文件:")
        for f in categories["verify_files"]:
            print(f"  - {Path(f).name}")

        print(f"\n发现 {len(categories['temp_files'])} 个临时文件:")
        for f in categories["temp_files"]:
            print(f"  - {Path(f).name}")

        print(f"\n发现 {len(categories['important_files'])} 个重要文件（不会移动）:")
        for f in categories["important_files"]:
            print(f"  - {Path(f).name}")

        return categories

    def run_cleanup(self, confirm: bool = True) -> bool:
        """执行清理操作"""
        print("=" * 60)
        print("开始项目清理")
        print("=" * 60)

        # 分析文件
        categories = self.analyze_root_files()

        if confirm:
            print("\n将要执行以下操作:")
            print(f"  1. 移动 {len(categories['debug_files'])} 个debug文件到 scripts/debug/")
            print(f"  2. 移动 {len(categories['test_files'])} 个测试文件到 tests/temp/")
            print(f"  3. 移动 {len(categories['verify_files'])} 个verify文件到 tests/verify/")
            print(f"  4. 处理 {len(categories['temp_files'])} 个临时文件")

            response = input("\n是否继续？(y/N): ").strip().lower()
            if response != "y":
                print("清理已取消")
                return False

        # 创建目录
        self.create_directories()

        # 执行移动操作
        self.stats["moved"] += self.move_debug_files(categories["debug_files"])
        self.stats["moved"] += self.move_test_files(categories["test_files"])
        self.stats["moved"] += self.move_verify_files(categories["verify_files"])
        self.stats["moved"] += self.cleanup_temp_files(categories["temp_files"])

        # 重组scripts目录
        print("\n" + "-" * 60)
        print("开始重组scripts目录结构...")
        scripts_stats = self.reorganize_scripts_directory()
        self.stats["moved"] += scripts_stats["moved"]
        self.stats["errors"] += scripts_stats["errors"]

        # 显示统计信息
        print("\n" + "=" * 60)
        print("清理完成！")
        print("=" * 60)
        print(f"移动文件: {self.stats['moved']}")
        print(f"删除文件: {self.stats['deleted']}")
        print(f"跳过文件: {self.stats['skipped']}")
        print(f"错误数量: {self.stats['errors']}")

        return True

    def generate_report(self) -> str:
        """生成清理报告"""
        categories = self.analyze_root_files()

        report = f"""# 项目清理报告

## 文件分析结果

### Debug文件 ({len(categories['debug_files'])}个)
{chr(10).join(f"- {Path(f).name}" for f in categories['debug_files'])}

### 测试文件 ({len(categories['test_files'])}个)
{chr(10).join(f"- {Path(f).name}" for f in categories['test_files'])}

### Verify文件 ({len(categories['verify_files'])}个)
{chr(10).join(f"- {Path(f).name}" for f in categories['verify_files'])}

### 临时文件 ({len(categories['temp_files'])}个)
{chr(10).join(f"- {Path(f).name}" for f in categories['temp_files'])}

### 重要文件（不会移动） ({len(categories['important_files'])}个)
{chr(10).join(f"- {Path(f).name}" for f in categories['important_files'])}

## 建议操作
1. 将debug_*.py文件移动到 `scripts/debug/` 目录
2. 将test_*.py文件移动到 `tests/temp/` 目录
3. 将verify_*.py文件移动到 `tests/verify/` 目录
4. 清理临时文件到 `temp_backup/` 目录
5. 重组scripts目录结构：
   - 部署脚本移动到 `scripts/deploy/`
   - 测试工具移动到 `scripts/test_utils/`
   - 验证脚本移动到 `scripts/verification/`
   - 工具脚本移动到 `scripts/tools/`
   - 设置脚本移动到 `scripts/setup/`

## 注意事项
- 数据库文件 `loom.db` 应保留在根目录
- 配置文件（.yaml, .yml）应保留在原位置
- 重要项目文件不应移动
"""
        return report


def main():
    import argparse

    parser = argparse.ArgumentParser(description="项目清理工具")
    parser.add_argument("--dry-run", action="store_true", help="模拟运行，显示将要执行的操作")
    parser.add_argument("--report", action="store_true", help="生成清理报告")
    parser.add_argument("--yes", "-y", action="store_true", help="自动确认，不提示")
    parser.add_argument("--root", default=".", help="项目根目录路径")

    args = parser.parse_args()

    cleaner = ProjectCleanup(args.root)

    if args.report:
        report = cleaner.generate_report()
        print(report)

        # 保存报告到文件
        report_path = Path(args.root) / "cleanup_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n报告已保存到: {report_path}")

    elif args.dry_run:
        cleaner.run_dry_run()
    else:
        cleaner.run_cleanup(confirm=not args.yes)


if __name__ == "__main__":
    main()
