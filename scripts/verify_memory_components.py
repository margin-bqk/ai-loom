#!/usr/bin/env python3
"""
验证第二阶段世界记忆系统组件

这个脚本直接验证新组件的导入和基本功能，避免复杂的依赖问题。
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试所有新组件的导入"""
    print("=" * 60)
    print("测试第二阶段世界记忆系统组件导入")
    print("=" * 60)

    imports_to_test = [
        ("VectorMemoryStore", "src.loom.memory.vector_memory_store"),
        ("MemorySummarizer", "src.loom.memory.memory_summarizer"),
        ("EnhancedWorldMemory", "src.loom.memory.enhanced_world_memory"),
        ("MemoryConsistencyChecker", "src.loom.memory.memory_consistency_checker"),
    ]

    all_passed = True

    for class_name, module_path in imports_to_test:
        try:
            module = __import__(module_path, fromlist=[class_name])
            cls = getattr(module, class_name)
            print(f"✓ 成功导入 {class_name}")

            # 测试类的基本属性
            if hasattr(cls, "__init__"):
                print(f"  - 有构造函数")
            if hasattr(cls, "__doc__") and cls.__doc__:
                print(f"  - 有文档字符串")

        except ImportError as e:
            print(f"✗ 导入 {class_name} 失败: {e}")
            all_passed = False
        except AttributeError as e:
            print(f"✗ 在模块 {module_path} 中找不到 {class_name}: {e}")
            all_passed = False
        except Exception as e:
            print(f"✗ 导入 {class_name} 时发生错误: {e}")
            all_passed = False

    return all_passed


def test_module_exports():
    """测试__init__.py的导出"""
    print("\n" + "=" * 60)
    print("测试模块导出")
    print("=" * 60)

    try:
        from src.loom.memory import (
            VectorMemoryStore,
            MemorySummarizer as EnhancedMemorySummarizer,
            EnhancedWorldMemory,
            MemoryConsistencyChecker,
        )

        print("✓ 成功从src.loom.memory导入所有组件")

        # 验证导出列表
        from src.loom.memory import __all__

        expected_exports = [
            "VectorMemoryStore",
            "MemorySummarizer",
            "EnhancedWorldMemory",
            "MemoryConsistencyChecker",
        ]

        for export in expected_exports:
            if export in __all__:
                print(f"✓ {export} 在__all__列表中")
            else:
                print(f"✗ {export} 不在__all__列表中")

    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False

    return True


def test_class_structures():
    """测试类结构"""
    print("\n" + "=" * 60)
    print("测试类结构")
    print("=" * 60)

    try:
        from src.loom.memory.vector_memory_store import (
            VectorMemoryStore,
            VectorStoreBackend,
        )
        from src.loom.memory.memory_summarizer import (
            MemorySummarizer,
            SummaryStrategy,
            SummaryFormat,
        )
        from src.loom.memory.enhanced_world_memory import (
            EnhancedWorldMemory,
            EnhancedMemoryConfig,
        )
        from src.loom.memory.memory_consistency_checker import (
            MemoryConsistencyChecker,
            ConsistencyIssueType,
            ConsistencySeverity,
        )

        print("✓ 成功导入所有类和枚举")

        # 测试VectorMemoryStore
        print("\n1. VectorMemoryStore:")
        print(f"   - 后端枚举: {[e.value for e in VectorStoreBackend]}")

        # 测试MemorySummarizer
        print("\n2. MemorySummarizer:")
        print(f"   - 摘要策略: {[s.value for s in SummaryStrategy]}")
        print(f"   - 摘要格式: {[f.value for f in SummaryFormat]}")

        # 测试EnhancedWorldMemory
        print("\n3. EnhancedWorldMemory:")
        print(f"   - 继承自WorldMemory: {EnhancedWorldMemory.__bases__}")

        # 测试MemoryConsistencyChecker
        print("\n4. MemoryConsistencyChecker:")
        print(f"   - 问题类型: {[t.value for t in ConsistencyIssueType]}")
        print(f"   - 严重程度: {[s.value for s in ConsistencySeverity]}")

    except Exception as e:
        print(f"✗ 测试类结构时出错: {e}")
        return False

    return True


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 60)
    print("测试向后兼容性")
    print("=" * 60)

    try:
        # 导入现有接口
        from src.loom.memory.interfaces import (
            VectorStoreInterface,
            SummarizerInterface,
            WorldMemoryInterface,
        )

        # 导入新组件
        from src.loom.memory.vector_memory_store import VectorMemoryStore
        from src.loom.memory.memory_summarizer import MemorySummarizer
        from src.loom.memory.enhanced_world_memory import EnhancedWorldMemory

        print("✓ 成功导入所有接口")

        # 验证继承关系
        print("\n验证继承关系:")

        # VectorMemoryStore 应该实现 VectorStoreInterface
        if issubclass(VectorMemoryStore, VectorStoreInterface):
            print("✓ VectorMemoryStore 实现 VectorStoreInterface")
        else:
            print("✗ VectorMemoryStore 未实现 VectorStoreInterface")

        # MemorySummarizer 应该实现 SummarizerInterface
        if issubclass(MemorySummarizer, SummarizerInterface):
            print("✓ MemorySummarizer 实现 SummarizerInterface")
        else:
            print("✗ MemorySummarizer 未实现 SummarizerInterface")

        # EnhancedWorldMemory 应该继承自 WorldMemoryInterface
        if issubclass(EnhancedWorldMemory, WorldMemoryInterface):
            print("✓ EnhancedWorldMemory 实现 WorldMemoryInterface")
        else:
            print("✗ EnhancedWorldMemory 未实现 WorldMemoryInterface")

        # EnhancedWorldMemory 应该继承自现有的 WorldMemory
        from src.loom.memory.world_memory import WorldMemory

        if issubclass(EnhancedWorldMemory, WorldMemory):
            print("✓ EnhancedWorldMemory 继承自 WorldMemory")
        else:
            print("✗ EnhancedWorldMemory 未继承自 WorldMemory")

    except Exception as e:
        print(f"✗ 测试向后兼容性时出错: {e}")
        return False

    return True


def test_file_existence():
    """测试文件存在性"""
    print("\n" + "=" * 60)
    print("测试文件存在性")
    print("=" * 60)

    files_to_check = [
        "src/loom/memory/vector_memory_store.py",
        "src/loom/memory/memory_summarizer.py",
        "src/loom/memory/enhanced_world_memory.py",
        "src/loom/memory/memory_consistency_checker.py",
        "tests/test_memory/test_phase2_memory_system.py",
        "scripts/test_memory_integration.py",
        "scripts/verify_memory_components.py",
    ]

    all_exist = True

    for file_path in files_to_check:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"[OK] {file_path} 存在")
            # 检查文件大小
            size = full_path.stat().st_size
            if size > 100:  # 至少100字节
                print(f"  大小: {size} 字节")
            else:
                print(f"  警告: 文件可能过小 ({size} 字节)")
                all_exist = False
        else:
            print(f"[FAIL] {file_path} 不存在")
            all_exist = False

    return all_exist


def main():
    """主验证函数"""
    print("第二阶段世界记忆系统组件验证")
    print("=" * 60)

    results = []

    # 运行所有测试
    results.append(("文件存在性", test_file_existence()))
    results.append(("组件导入", test_imports()))
    results.append(("模块导出", test_module_exports()))
    results.append(("类结构", test_class_structures()))
    results.append(("向后兼容性", test_backward_compatibility()))

    # 显示总结
    print("\n" + "=" * 60)
    print("验证总结")
    print("=" * 60)

    all_passed = True
    for test_name, passed in results:
        status = "✓ 通过" if passed else "✗ 失败"
        print(f"{test_name}: {status}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("所有验证测试通过！ ✓")
        print("第二阶段世界记忆系统组件实现完成。")
        return 0
    else:
        print("部分验证测试失败！ ✗")
        print("请检查上述错误并修复。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
