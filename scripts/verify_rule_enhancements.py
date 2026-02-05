#!/usr/bin/env python3
"""
规则层增强功能集成验证脚本

验证第二阶段规则层增强组件的集成兼容性：
1. AdvancedMarkdownCanon 向后兼容性
2. RuleValidator 与现有规则系统的集成
3. RuleHotLoader 与现有会话管理的集成
4. 整体功能验证
"""

import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.rules import (
    MarkdownCanon,
    AdvancedMarkdownCanon,
    RuleValidator,
    RuleHotLoader,
    RuleLoader,
)
from src.loom.rules.markdown_canon import CanonSectionType


def test_backward_compatibility():
    """测试向后兼容性"""
    print("=" * 60)
    print("测试向后兼容性")
    print("=" * 60)

    # 创建测试内容
    test_content = """---
version: 1.0.0
author: Test User
---

# 世界观 (World)

这是一个测试世界观。

# 叙事基调 (Tone)

严肃的奇幻风格。
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        # 测试基础MarkdownCanon
        print("1. 测试基础 MarkdownCanon...")
        base_canon = MarkdownCanon(temp_path, test_content)
        assert base_canon is not None
        assert len(base_canon.sections) == 2
        assert "世界观 (World)" in base_canon.sections
        print("   ✓ 基础MarkdownCanon工作正常")

        # 测试AdvancedMarkdownCanon继承
        print("2. 测试 AdvancedMarkdownCanon 继承...")
        advanced_canon = AdvancedMarkdownCanon(temp_path, test_content)
        assert advanced_canon is not None
        assert isinstance(advanced_canon, MarkdownCanon)  # 应该是子类
        print("   ✓ AdvancedMarkdownCanon正确继承MarkdownCanon")

        # 测试基础方法兼容性
        print("3. 测试基础方法兼容性...")
        assert hasattr(advanced_canon, "get_section")
        assert hasattr(advanced_canon, "validate")
        assert hasattr(advanced_canon, "search_content")
        assert hasattr(advanced_canon, "to_dict")

        # 调用基础方法
        section = advanced_canon.get_section("世界观 (World)")
        assert section is not None

        errors = advanced_canon.validate()
        assert isinstance(errors, list)

        search_results = advanced_canon.search_content("测试")
        assert isinstance(search_results, list)

        dict_repr = advanced_canon.to_dict()
        assert isinstance(dict_repr, dict)
        print("   ✓ 所有基础方法工作正常")

        # 测试增强功能
        print("4. 测试增强功能...")
        assert hasattr(advanced_canon, "get_validation_report")
        assert hasattr(advanced_canon, "to_enhanced_dict")
        assert hasattr(advanced_canon, "get_referenced_sections")

        report = advanced_canon.get_validation_report()
        assert isinstance(report, dict)
        assert "is_valid" in report

        enhanced_dict = advanced_canon.to_enhanced_dict()
        assert "advanced_features" in enhanced_dict
        print("   ✓ 增强功能工作正常")

        print("\n✅ 向后兼容性测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 向后兼容性测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_rule_validator_integration():
    """测试规则验证器集成"""
    print("\n" + "=" * 60)
    print("测试规则验证器集成")
    print("=" * 60)

    # 创建测试内容
    test_content = """---
version: 1.0.0
author: Test User
created: 2025-01-01
updated: 2025-01-02
---

# 世界观 (World)

这是一个包含潜在冲突的测试世界观。
不能同时做两件事。

# 叙事基调 (Tone)

测试基调。
"""

    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".md", delete=False, encoding="utf-8"
    ) as f:
        f.write(test_content)
        temp_path = Path(f.name)

    try:
        # 创建规则集
        print("1. 创建规则集...")
        canon = MarkdownCanon(temp_path, test_content)
        assert canon is not None
        print("   ✓ 规则集创建成功")

        # 创建验证器
        print("2. 创建 RuleValidator...")
        validator = RuleValidator()
        assert validator is not None
        print("   ✓ 验证器创建成功")

        # 同步验证
        print("3. 执行同步验证...")
        report = validator.validate_sync(canon)
        assert report is not None
        assert hasattr(report, "is_valid")
        assert hasattr(report, "validation_score")
        assert hasattr(report, "to_dict")
        print(f"   ✓ 验证完成，分数: {report.validation_score:.2%}")

        # 测试报告方法
        print("4. 测试验证报告...")
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "canon_path" in report_dict
        assert "validation_score" in report_dict

        summary = report.get_summary()
        assert isinstance(summary, str)
        assert "Validation Report" in summary
        print("   ✓ 验证报告功能正常")

        # 测试高级规则集验证
        print("5. 测试高级规则集验证...")
        advanced_canon = AdvancedMarkdownCanon(temp_path, test_content)
        advanced_report = validator.validate_sync(advanced_canon)
        assert advanced_report is not None
        print("   ✓ 高级规则集验证成功")

        print("\n✅ 规则验证器集成测试通过！")
        return True

    except Exception as e:
        print(f"\n❌ 规则验证器集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        return False

    finally:
        if temp_path.exists():
            temp_path.unlink()


def test_rule_hot_loader_integration():
    """测试规则热加载器集成"""
    print("\n" + "=" * 60)
    print("测试规则热加载器集成")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        try:
            # 创建测试文件
            test_file = temp_dir_path / "test_rules.md"
            test_content = """---
version: 1.0.0
author: Hot Loader Test
---

# 世界观 (World)

热加载测试世界观。
"""

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            print("1. 创建 RuleHotLoader...")
            hot_loader = RuleHotLoader(
                {"use_advanced_parser": True, "max_version_history": 3}
            )
            assert hot_loader is not None
            print("   ✓ 热加载器创建成功")

            # 测试规则加载
            print("2. 测试规则加载...")
            canon = hot_loader.get_canon(test_file)
            assert canon is not None
            assert isinstance(canon, AdvancedMarkdownCanon)
            print("   ✓ 规则加载成功")

            # 测试会话管理
            print("3. 测试会话管理...")
            session_id = "test_session_123"
            success = hot_loader.create_session(session_id, test_file)
            assert success == True
            assert session_id in hot_loader.sessions
            print("   ✓ 会话创建成功")

            # 测试获取会话规则
            session_canon = hot_loader.get_session_canon(session_id)
            assert session_canon is not None
            print("   ✓ 会话规则获取成功")

            # 测试版本历史
            print("4. 测试版本历史...")
            history = hot_loader.get_version_history(test_file)
            assert isinstance(history, list)
            assert len(history) >= 1
            print(f"   ✓ 版本历史记录: {len(history)} 个版本")

            # 测试统计信息
            print("5. 测试统计信息...")
            stats = hot_loader.get_stats()
            assert isinstance(stats, dict)
            assert "total_loads" in stats
            assert stats["total_loads"] >= 1
            print(f"   ✓ 统计信息: {stats['total_loads']} 次加载")

            # 测试规则验证集成
            print("6. 测试规则验证集成...")
            canon_with_validation, validation_report = (
                hot_loader.get_canon_with_validation(test_file)
            )
            assert canon_with_validation is not None
            assert validation_report is not None
            print("   ✓ 规则验证集成成功")

            print("\n✅ 规则热加载器集成测试通过！")
            return True

        except Exception as e:
            print(f"\n❌ 规则热加载器集成测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_rule_loader_integration():
    """测试与现有RuleLoader的集成"""
    print("\n" + "=" * 60)
    print("测试与现有RuleLoader的集成")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        try:
            # 创建测试文件
            test_file = temp_dir_path / "integration_test.md"
            test_content = """---
version: 2.0.0
author: Integration Test
---

# 世界观 (World)

集成测试世界观。

# 叙事基调 (Tone)

集成测试基调。
"""

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            print("1. 创建 RuleLoader...")
            rule_loader = RuleLoader(str(temp_dir_path))
            assert rule_loader is not None
            print("   ✓ RuleLoader创建成功")

            # 测试规则加载
            print("2. 测试规则加载...")
            canon = rule_loader.load_canon_from_path(test_file)
            assert canon is not None
            assert isinstance(canon, MarkdownCanon)
            print("   ✓ 规则加载成功")

            # 测试与AdvancedMarkdownCanon的兼容性
            print("3. 测试与AdvancedMarkdownCanon的兼容性...")
            # RuleLoader返回基础MarkdownCanon，但我们可以手动创建Advanced版本
            advanced_canon = AdvancedMarkdownCanon(test_file, test_content)
            assert advanced_canon is not None
            print("   ✓ AdvancedMarkdownCanon兼容性测试通过")

            # 测试与RuleValidator的集成
            print("4. 测试与RuleValidator的集成...")
            validator = RuleValidator()
            report = validator.validate_sync(canon)
            assert report is not None
            print(
                f"   ✓ RuleValidator集成测试通过，验证分数: {report.validation_score:.2%}"
            )

            print("\n✅ RuleLoader集成测试通过！")
            return True

        except Exception as e:
            print(f"\n❌ RuleLoader集成测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def test_comprehensive_workflow():
    """测试完整工作流程"""
    print("\n" + "=" * 60)
    print("测试完整工作流程")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)

        try:
            # 创建测试文件
            test_file = temp_dir_path / "workflow_test.md"
            test_content = """---
version: 3.0.0
author: Workflow Test
requires: ["base_rules"]
---

# 世界观 (World)

完整工作流程测试。
引用[@角色设定]。

# 角色设定 (Characters)

主要角色描述。

# 冲突解决 (Conflict)

不能违反物理法则。
"""

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_content)

            print("1. 初始化所有组件...")
            hot_loader = RuleHotLoader({"use_advanced_parser": True})
            validator = RuleValidator()

            print("   ✓ 组件初始化成功")

            # 工作流程步骤1: 加载规则
            print("2. 工作流程步骤1: 加载规则...")
            canon = hot_loader.get_canon(test_file, "workflow_session")
            assert canon is not None
            print("   ✓ 规则加载成功")

            # 工作流程步骤2: 验证规则
            print("3. 工作流程步骤2: 验证规则...")
            report = validator.validate_sync(canon)
            assert report is not None
            print(f"   ✓ 规则验证完成，状态: {'有效' if report.is_valid() else '无效'}")

            # 工作流程步骤3: 获取增强信息
            print("4. 工作流程步骤3: 获取增强信息...")
            if isinstance(canon, AdvancedMarkdownCanon):
                enhanced_info = canon.to_enhanced_dict()
                assert "advanced_features" in enhanced_info
                print(
                    f"   ✓ 获取增强信息成功，功能: {enhanced_info['advanced_features']}"
                )
            else:
                print("   ⚠ 使用基础规则集，跳过增强功能测试")

            # 工作流程步骤4: 模拟规则更新
            print("5. 工作流程步骤4: 模拟规则更新...")
            # 修改文件内容
            updated_content = test_content + "\n# 新增章节\n新增内容。\n"
            with open(test_file, "w", encoding="utf-8") as f:
                f.write(updated_content)

            # 重新加载
            updated_canon = hot_loader._reload_canon(test_file)
            assert updated_canon is not None
            print("   ✓ 规则更新成功")

            # 检查版本历史
            history = hot_loader.get_version_history(test_file)
            assert len(history) >= 2
            print(f"   ✓ 版本历史更新，当前版本数: {len(history)}")

            print("\n✅ 完整工作流程测试通过！")
            return True

        except Exception as e:
            print(f"\n❌ 完整工作流程测试失败: {e}")
            import traceback

            traceback.print_exc()
            return False


def main():
    """主函数"""
    print("AI-LOOM 规则层增强功能集成验证")
    print("=" * 60)

    tests = [
        ("向后兼容性", test_backward_compatibility),
        ("规则验证器集成", test_rule_validator_integration),
        ("规则热加载器集成", test_rule_hot_loader_integration),
        ("RuleLoader集成", test_rule_loader_integration),
        ("完整工作流程", test_comprehensive_workflow),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常: {e}")
            results.append((test_name, False))

    # 输出总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)

    passed = 0
    failed = 0

    for test_name, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{test_name:20} {status}")

        if success:
            passed += 1
        else:
            failed += 1

    print("\n" + "=" * 60)
    print(f"总计: {len(tests)} 个测试")
    print(f"通过: {passed}")
    print(f"失败: {failed}")

    if failed == 0:
        print("\n🎉 所有集成测试通过！规则层增强功能已成功实现。")
        return 0
    else:
        print(f"\n⚠  {failed} 个测试失败，请检查实现。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
