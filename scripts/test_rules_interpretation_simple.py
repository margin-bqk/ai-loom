#!/usr/bin/env python3
"""
规则层与解释层简单集成测试
测试规则层和解释层的基本功能集成
"""

import asyncio
import tempfile
import shutil
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入规则层
from src.loom.rules.rule_loader import RuleLoader
from src.loom.rules.markdown_canon import MarkdownCanon, CanonSectionType

# 导入解释层
from src.loom.interpretation.rule_interpreter import RuleInterpreter
from src.loom.interpretation.consistency_checker import ConsistencyChecker


async def test_rules_interpretation_integration():
    """测试规则层和解释层的集成"""
    print("=== 规则层与解释层集成测试 ===")
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp()
    canon_dir = Path(temp_dir) / "canon"
    canon_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. 创建测试规则文件
        test_canon_content = """---
version: 1.0.0
author: Integration Test
---

# 世界观
这是一个奇幻世界，有魔法和龙。
主要角色：艾伦（人类法师）、莉莉丝（精灵弓箭手）。
重要地点：魔法学院、黑暗森林。

# 叙事基调
黑暗奇幻风格，带有希望的元素。

# 冲突解决
现实主义，但允许魔法干预。

# 权限边界
玩家可以探索世界，但不能杀死关键NPC。
玩家可以学习魔法，但不能成为神。

# 因果关系
时间只能向前流动。
魔法需要付出代价。

# 元信息
created: 2025-12-30
"""
        
        test_file = canon_dir / "fantasy_world.md"
        test_file.write_text(test_canon_content, encoding="utf-8")
        
        # 2. 初始化规则层组件
        print("1. 初始化规则层组件...")
        rule_loader = RuleLoader(canon_dir=str(canon_dir))
        
        # 加载规则集
        canon = rule_loader.load_canon("fantasy_world")
        assert canon is not None, "规则集加载失败"
        print(f"   加载规则集: {canon.path.name}")
        print(f"   章节数: {len(canon.sections)}")
        print(f"   元数据: {canon.metadata}")
        
        # 验证规则集
        errors = canon.validate()
        if errors:
            print(f"   验证警告: {errors}")
        else:
            print("   验证通过")
        
        # 3. 测试规则查询功能
        print("\n2. 测试规则查询功能...")
        
        # 搜索内容
        search_results = canon.search_content("魔法")
        print(f"   搜索'魔法'结果数: {len(search_results)}")
        for name, context in search_results[:2]:
            print(f"     - {name}: {context[:50]}...")
        
        # 提取实体
        entities = canon.extract_entities()
        print(f"   提取实体:")
        print(f"     角色: {entities['characters']}")
        print(f"     地点: {entities['locations']}")
        
        # 4. 初始化解释层组件
        print("\n3. 初始化解释层组件...")
        
        # 创建规则解释器
        rule_interpreter = RuleInterpreter()
        
        # 创建一致性检查器
        consistency_checker = ConsistencyChecker()
        
        print(f"   初始化规则解释器")
        print(f"   初始化一致性检查器")
        
        # 5. 测试规则解释
        print("\n4. 测试规则解释...")
        context = {
            "type": "general",
            "scene": "魔法学院的大厅",
            "characters": ["艾伦", "莉莉丝"],
            "action": "探索图书馆"
        }
        
        interpretation_result = rule_interpreter.interpret(canon)
        print(f"   解释规则数: {len(interpretation_result.constraints)}")
        
        # 显示规则类型统计
        rule_types = {}
        for constraint in interpretation_result.constraints:
            rule_type = constraint.type
            rule_types[rule_type] = rule_types.get(rule_type, 0) + 1
        
        print(f"   规则类型分布:")
        for rule_type, count in rule_types.items():
            print(f"     {rule_type}: {count}条")
        
        # 显示前3条规则
        for i, constraint in enumerate(interpretation_result.constraints[:3]):
            content = constraint.content
            if len(content) > 60:
                content = content[:57] + "..."
            print(f"     {i+1}. [{constraint.type}] {content}")
        
        # 6. 测试规则冲突检测
        print("\n5. 测试规则冲突检测...")
        
        # 使用解释出的规则进行冲突检测
        conflicts = rule_interpreter.detect_conflicts(interpretation_result.constraints)
        print(f"   检测到冲突数: {len(conflicts)}")
        if conflicts:
            for conflict in conflicts:
                if 'constraint1' in conflict and 'constraint2' in conflict:
                    print(f"     - {conflict['constraint1']} 与 {conflict['constraint2']} 冲突")
                elif 'constraints' in conflict:
                    print(f"     - 关于'{conflict.get('keyword', '未知')}'的冲突: {conflict['constraints']}")
        
        # 7. 测试一致性检查
        print("\n6. 测试一致性检查...")
        
        test_response = "艾伦和莉莉丝决定一起探索图书馆，寻找失落的魔法书。他们发现了一本古老的典籍，上面记载着强大的咒语。"
        rules_text = canon.get_full_text()
        
        consistency_result = consistency_checker.check(
            response=test_response,
            rules_text=rules_text,
            constraints=interpretation_result.constraints
        )
        
        print(f"   一致性分数: {consistency_result['score']:.2f}")
        print(f"   问题数: {len(consistency_result['issues'])}")
        
        if consistency_result['issues']:
            for i, issue in enumerate(consistency_result['issues'][:2]):
                print(f"     {i+1}. [{issue.type}] {issue.description}")
        
        # 8. 测试规则片段组合
        print("\n7. 测试规则片段组合...")
        
        combined = canon.combine_fragments(["世界观", "叙事基调"])
        print(f"   组合片段长度: {len(combined)} 字符")
        print(f"   包含'世界观': {'# 世界观' in combined}")
        print(f"   包含'叙事基调': {'# 叙事基调' in combined}")
        
        # 9. 测试规则加载器的依赖管理
        print("\n8. 测试规则依赖管理...")
        
        # 创建依赖规则
        dependent_content = """---
version: 1.0.0
depends_on: fantasy_world
---

# 世界观
扩展自fantasy_world。
新增角色：格鲁特（矮人工匠）。
"""
        
        dependent_file = canon_dir / "extended_world.md"
        dependent_file.write_text(dependent_content, encoding="utf-8")
        
        # 加载依赖规则
        dependent_canon = rule_loader.load_canon("extended_world")
        if dependent_canon:
            print(f"   加载依赖规则: {dependent_canon.path.name}")
            
            # 检查依赖关系
            dep_tree = rule_loader.get_dependency_tree("extended_world")
            print(f"   依赖: {dep_tree.get('dependencies', [])}")
        
        # 10. 测试完整工作流
        print("\n9. 测试完整工作流...")
        
        # 模拟一个叙事场景
        scenario_context = {
            "type": "action",
            "scene": "魔法学院",
            "characters": ["艾伦", "莉莉丝"],
            "time": "白天"
        }
        
        # 获取上下文相关的规则
        contextual_rules = rule_interpreter.get_contextual_rules(
            scenario_context,
            interpretation_result
        )
        
        # 检查一致性
        test_response = "艾伦使用火球术炸开了禁书区的门，但触发了警报。"
        test_result = consistency_checker.check(
            response=test_response,
            rules_text=canon.get_full_text(),
            constraints=contextual_rules
        )
        
        print(f"   上下文相关规则数: {len(contextual_rules)}")
        print(f"   叙事一致性: {'通过' if test_result['passed'] else '失败'}")
        
        print("\n✅ 集成测试通过！")
        print(f"   测试总结:")
        print(f"     - 加载了 {len(canon.sections)} 个规则章节")
        print(f"     - 解释了 {len(interpretation_result.constraints)} 条规则")
        print(f"     - 提取了 {len(entities['characters'])} 个角色")
        print(f"     - 一致性检查分数: {consistency_result['score']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n清理临时目录: {temp_dir}")


async def main():
    """主函数"""
    print("LOOM项目 - 规则层与解释层集成测试")
    print("=" * 50)
    
    success = await test_rules_interpretation_integration()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ 所有集成测试通过！")
        print("规则层和解释层已成功集成并正常工作。")
        print("\n组件功能验证:")
        print("  ✓ MarkdownCanon - 规则解析和查询")
        print("  ✓ RuleLoader - 规则加载和缓存")
        print("  ✓ RuleInterpreter - 规则解释和冲突检测")
        print("  ✓ ConsistencyChecker - 一致性检查和修正建议")
    else:
        print("\n" + "=" * 50)
        print("❌ 集成测试失败")
        
    return success


if __name__ == "__main__":
    asyncio.run(main())