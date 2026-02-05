#!/usr/bin/env python3
"""
规则组件核心功能测试

直接测试新实现的三个核心组件的核心功能，避免复杂的依赖。
"""

import sys
import tempfile
from pathlib import Path

# 直接导入需要的模块，避免导入整个项目
sys.path.insert(0, str(Path(__file__).parent.parent))


# 模拟缺失的依赖
class MockObserver:
    pass


class MockFileSystemEventHandler:
    pass


sys.modules["watchdog.observers"] = type(sys)("watchdog.observers")
sys.modules["watchdog.observers"].Observer = MockObserver
sys.modules["watchdog.events"] = type(sys)("watchdog.events")
sys.modules["watchdog.events"].FileSystemEventHandler = MockFileSystemEventHandler

# 现在导入我们的模块
try:
    from src.loom.rules.advanced_markdown_canon import AdvancedMarkdownCanon
    from src.loom.rules.rule_validator import RuleValidator
    from src.loom.rules.markdown_canon import MarkdownCanon

    print("模块导入成功")
except ImportError as e:
    print(f"模块导入失败: {e}")
    # 尝试直接导入文件
    import importlib.util
    import os

    # 直接加载模块
    base_path = Path(__file__).parent.parent / "src" / "loom" / "rules"

    # 加载markdown_canon
    spec = importlib.util.spec_from_file_location(
        "markdown_canon", base_path / "markdown_canon.py"
    )
    markdown_canon = importlib.util.module_from_spec(spec)
    sys.modules["markdown_canon"] = markdown_canon
    spec.loader.exec_module(markdown_canon)

    # 加载advanced_markdown_canon
    spec = importlib.util.spec_from_file_location(
        "advanced_markdown_canon", base_path / "advanced_markdown_canon.py"
    )
    advanced_markdown_canon = importlib.util.module_from_spec(spec)
    sys.modules["advanced_markdown_canon"] = advanced_markdown_canon
    spec.loader.exec_module(advanced_markdown_canon)

    # 加载rule_validator
    spec = importlib.util.spec_from_file_location(
        "rule_validator", base_path / "rule_validator.py"
    )
    rule_validator = importlib.util.module_from_spec(spec)
    sys.modules["rule_validator"] = rule_validator
    spec.loader.exec_module(rule_validator)

    from advanced_markdown_canon import AdvancedMarkdownCanon
    from rule_validator import RuleValidator
    from markdown_canon import MarkdownCanon

    print("直接模块加载成功")


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("测试基本功能")
    print("=" * 60)

    # 创建测试内容
    test_content = """---
version: 1.0.0
author: Test User
---

# 世界观 (World)

这是一个测试世界观。

# 叙事基调 (Tone)

测试叙事基调。
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        # 测试1: AdvancedMarkdownCanon 创建
        print("1. 测试 AdvancedMarkdownCanon 创建...")
        canon = AdvancedMarkdownCanon(temp_path, test_content)
        assert canon is not None
        print("   ✓ 创建成功")

        # 测试2: 基础方法
        print("2. 测试基础方法...")
        section = canon.get_section("世界观 (World)")
        assert section is not None
        print("   ✓ get_section 正常")

        errors = canon.validate()
        assert isinstance(errors, list)
        print("   ✓ validate 正常")

        # 测试3: 增强功能
        print("3. 测试增强功能...")
        report = canon.get_validation_report()
        assert isinstance(report, dict)
        assert "is_valid" in report
        print("   ✓ get_validation_report 正常")

        enhanced_dict = canon.to_enhanced_dict()
        assert "advanced_features" in enhanced_dict
        print("   ✓ to_enhanced_dict 正常")

        # 测试4: RuleValidator
        print("4. 测试 RuleValidator...")
        validator = RuleValidator()
        validation_report = validator.validate_sync(canon)
        assert validation_report is not None
        assert hasattr(validation_report, "validation_score")
        print(f"   ✓ 验证完成，分数: {validation_report.validation_score:.2%}")

        print("\n✅ 基本功能测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 基本功能测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_advanced_features():
    """测试高级功能"""
    print("\n" + "=" * 60)
    print("测试高级功能")
    print("=" * 60)

    # 创建包含高级功能的测试内容
    test_content = """---
version: 2.0.0
author: Advanced Test
requires: ["base_rules"]
---

# 世界观 (World)

这是一个包含引用的测试世界观。
引用[@角色设定]和[@地点描述]。

{{macro:power_level}}
力量等级系统
{{endmacro}}

# 角色设定 (Characters)

主要角色描述。

# 地点描述 (Locations)

重要地点。
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        # 创建AdvancedMarkdownCanon
        canon = AdvancedMarkdownCanon(temp_path, test_content)

        # 测试引用提取
        print("1. 测试引用提取...")
        referenced = canon.get_referenced_sections("世界观 (World)")
        assert "角色设定 (Characters)" in referenced
        assert "地点描述 (Locations)" in referenced
        print("   ✓ 引用提取正常")

        # 测试宏提取
        print("2. 测试宏提取...")
        assert hasattr(canon, "macros")
        assert "power_level" in canon.macros
        print("   ✓ 宏提取正常")

        # 测试依赖分析
        print("3. 测试依赖分析...")
        assert hasattr(canon, "dependencies")
        assert len(canon.dependencies) > 0
        print(f"   ✓ 发现 {len(canon.dependencies)} 个依赖")

        # 测试验证
        print("4. 测试验证...")
        report = canon.get_validation_report()
        assert report["is_valid"] in [True, False]
        print(f"   ✓ 验证完成，状态: {'有效' if report['is_valid'] else '无效'}")

        # 测试规则模式提取
        print("5. 测试规则模式提取...")
        patterns = canon.extract_rule_patterns()
        assert isinstance(patterns, dict)
        assert "constraints" in patterns
        print("   ✓ 规则模式提取正常")

        print("\n✅ 高级功能测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 高级功能测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n" + "=" * 60)
    print("测试向后兼容性")
    print("=" * 60)

    # 创建简单测试内容
    test_content = """---
version: 1.0.0
author: Compatibility Test
---

# 世界观 (World)

兼容性测试内容。

# 叙事基调 (Tone)

测试基调。
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        # 创建基础MarkdownCanon
        print("1. 创建基础 MarkdownCanon...")
        base_canon = MarkdownCanon(temp_path, test_content)
        assert base_canon is not None
        print("   ✓ 基础版本创建成功")

        # 创建AdvancedMarkdownCanon
        print("2. 创建 AdvancedMarkdownCanon...")
        advanced_canon = AdvancedMarkdownCanon(temp_path, test_content)
        assert advanced_canon is not None
        print("   ✓ 高级版本创建成功")

        # 测试继承关系
        print("3. 测试继承关系...")
        assert isinstance(advanced_canon, MarkdownCanon)
        print("   ✓ 正确继承MarkdownCanon")

        # 测试方法兼容性
        print("4. 测试方法兼容性...")
        methods_to_test = [
            ("get_section", "世界观 (World)"),
            ("validate", None),
            ("search_content", "测试"),
            ("to_dict", None),
        ]

        for method_name, arg in methods_to_test:
            base_method = getattr(base_canon, method_name)
            advanced_method = getattr(advanced_canon, method_name)

            # 调用方法
            if arg:
                base_result = base_method(arg) if arg else base_method()
                advanced_result = advanced_method(arg) if arg else advanced_method()
            else:
                base_result = base_method()
                advanced_result = advanced_method()

            # 检查返回类型
            assert type(base_result) == type(advanced_result)
            print(f"   ✓ {method_name} 方法兼容")

        # 测试增强方法
        print("5. 测试增强方法...")
        enhanced_methods = [
            "get_validation_report",
            "to_enhanced_dict",
            "get_referenced_sections",
        ]
        for method in enhanced_methods:
            assert hasattr(advanced_canon, method)
            # 确保基础版本没有这些方法
            assert not hasattr(base_canon, method)

        print("   ✓ 增强方法正确添加")

        print("\n✅ 向后兼容性测试通过")
        return True

    except Exception as e:
        print(f"\n❌ 向后兼容性测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if temp_path.exists():
            temp_path.unlink()


def main():
    """主函数"""
    print("AI-LOOM 规则层增强组件测试")
    print("=" * 60)

    tests = [
        ("基本功能", test_basic_functionality),
        ("高级功能", test_advanced_features),
        ("向后兼容性", test_backward_compatibility),
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"测试异常: {e}")
            import traceback

            traceback.print_exc()
            results.append((test_name, False))

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, success in results:
        status = "通过" if success else "失败"
        print(f"{test_name:15} {status}")

        if success:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"总计: {len(tests)} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed == 0:
        print("\n所有测试通过！规则层增强功能已成功实现。")
        return 0
    else:
        print(f"\n{failed} 个测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
