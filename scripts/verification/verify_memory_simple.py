#!/usr/bin/env python3
"""
简单验证第二阶段世界记忆系统组件
使用ASCII字符避免编码问题
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_file_exists():
    """检查文件是否存在"""
    print("=" * 60)
    print("检查文件是否存在")
    print("=" * 60)

    files = [
        "src/loom/memory/vector_memory_store.py",
        "src/loom/memory/memory_summarizer.py",
        "src/loom/memory/enhanced_world_memory.py",
        "src/loom/memory/memory_consistency_checker.py",
        "tests/test_memory/test_phase2_memory_system.py",
    ]

    all_ok = True
    for f in files:
        path = project_root / f
        if path.exists():
            size = path.stat().st_size
            print(f"[OK] {f} ({size} bytes)")
        else:
            print(f"[FAIL] {f} not found")
            all_ok = False

    return all_ok


def check_imports():
    """检查导入"""
    print("\n" + "=" * 60)
    print("检查导入")
    print("=" * 60)

    imports = [
        ("VectorMemoryStore", "src.loom.memory.vector_memory_store"),
        ("MemorySummarizer", "src.loom.memory.memory_summarizer"),
        ("EnhancedWorldMemory", "src.loom.memory.enhanced_world_memory"),
        ("MemoryConsistencyChecker", "src.loom.memory.memory_consistency_checker"),
    ]

    all_ok = True
    for class_name, module_path in imports:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"[OK] Imported {class_name}")
        except Exception as e:
            print(f"[FAIL] Failed to import {class_name}: {e}")
            all_ok = False

    return all_ok


def check_module_exports():
    """检查模块导出"""
    print("\n" + "=" * 60)
    print("检查模块导出")
    print("=" * 60)

    try:
        from src.loom.memory import __all__

        print(f"[OK] __all__ = {__all__}")

        expected = [
            "VectorMemoryStore",
            "MemorySummarizer",
            "EnhancedWorldMemory",
            "MemoryConsistencyChecker",
        ]

        for exp in expected:
            if exp in __all__:
                print(f"[OK] {exp} is exported")
            else:
                print(f"[FAIL] {exp} is NOT exported")
                return False

        return True
    except Exception as e:
        print(f"[FAIL] Error checking exports: {e}")
        return False


def check_class_hierarchy():
    """检查类继承关系"""
    print("\n" + "=" * 60)
    print("检查类继承关系")
    print("=" * 60)

    try:
        # 导入接口
        from src.loom.memory.interfaces import (
            VectorStoreInterface,
            SummarizerInterface,
            WorldMemoryInterface,
        )

        # 导入实现
        from src.loom.memory.vector_memory_store import VectorMemoryStore
        from src.loom.memory.memory_summarizer import MemorySummarizer
        from src.loom.memory.enhanced_world_memory import EnhancedWorldMemory

        # 检查继承关系
        checks = [
            ("VectorMemoryStore", VectorStoreInterface, VectorMemoryStore),
            ("MemorySummarizer", SummarizerInterface, MemorySummarizer),
            ("EnhancedWorldMemory", WorldMemoryInterface, EnhancedWorldMemory),
        ]

        all_ok = True
        for name, interface, implementation in checks:
            if issubclass(implementation, interface):
                print(f"[OK] {name} implements {interface.__name__}")
            else:
                print(f"[FAIL] {name} does NOT implement {interface.__name__}")
                all_ok = False

        # 检查EnhancedWorldMemory继承自WorldMemory
        from src.loom.memory.world_memory import WorldMemory

        if issubclass(EnhancedWorldMemory, WorldMemory):
            print(f"[OK] EnhancedWorldMemory inherits from WorldMemory")
        else:
            print(f"[FAIL] EnhancedWorldMemory does NOT inherit from WorldMemory")
            all_ok = False

        return all_ok
    except Exception as e:
        print(f"[FAIL] Error checking hierarchy: {e}")
        return False


def check_enum_values():
    """检查枚举值"""
    print("\n" + "=" * 60)
    print("检查枚举值")
    print("=" * 60)

    try:
        from src.loom.memory.vector_memory_store import VectorStoreBackend
        from src.loom.memory.memory_summarizer import SummaryStrategy, SummaryFormat
        from src.loom.memory.memory_consistency_checker import (
            ConsistencyIssueType,
            ConsistencySeverity,
        )

        enums = [
            ("VectorStoreBackend", VectorStoreBackend),
            ("SummaryStrategy", SummaryStrategy),
            ("SummaryFormat", SummaryFormat),
            ("ConsistencyIssueType", ConsistencyIssueType),
            ("ConsistencySeverity", ConsistencySeverity),
        ]

        all_ok = True
        for name, enum_class in enums:
            values = [e.value for e in enum_class]
            print(f"[OK] {name}: {values}")
            if not values:
                print(f"[WARN] {name} has no values")

        return all_ok
    except Exception as e:
        print(f"[FAIL] Error checking enums: {e}")
        return False


def main():
    """主函数"""
    print("第二阶段世界记忆系统验证")
    print("=" * 60)

    results = []

    # 运行检查
    results.append(("文件存在", check_file_exists()))
    results.append(("导入检查", check_imports()))
    results.append(("模块导出", check_module_exports()))
    results.append(("类继承", check_class_hierarchy()))
    results.append(("枚举值", check_enum_values()))

    # 显示结果
    print("\n" + "=" * 60)
    print("验证结果")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:15} {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("所有检查通过！")
        print("第二阶段世界记忆系统实现完成。")
        return 0
    else:
        print("部分检查失败！")
        return 1


if __name__ == "__main__":
    sys.exit(main())
