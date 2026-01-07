#!/usr/bin/env python3
"""
规则层与解释层集成测试
测试规则层和解释层与核心运行时层的集成
"""

import asyncio
import tempfile
import shutil
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心运行时层
from src.loom.core.config_manager import ConfigManager
from src.loom.core.session_manager import SessionManager
from src.loom.core.prompt_assembler import PromptAssembler
from src.loom.core.turn_scheduler import TurnScheduler

# 导入规则层
from src.loom.rules.rule_loader import RuleLoader
from src.loom.rules.markdown_canon import MarkdownCanon

# 导入解释层
from src.loom.interpretation.rule_interpreter import RuleInterpreter
from src.loom.interpretation.llm_provider import LLMProvider
from src.loom.interpretation.reasoning_pipeline import ReasoningPipeline
from src.loom.interpretation.consistency_checker import ConsistencyChecker


async def test_integration():
    """测试规则层和解释层与核心运行时层的集成"""
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
depends_on: base_world
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
        
        # 3. 初始化解释层组件
        print("\n2. 初始化解释层组件...")
        
        # 创建配置管理器
        config = ConfigManager()
        await config.load_defaults()
        
        # 创建LLM提供者（使用模拟模式）
        llm_provider = LLMProvider(config)
        
        # 创建规则解释器
        rule_interpreter = RuleInterpreter()
        
        # 创建一致性检查器
        consistency_checker = ConsistencyChecker()
        
        # 创建推理流水线
        reasoning_pipeline = ReasoningPipeline(
            rule_interpreter=rule_interpreter,
            llm_provider=llm_provider,
            consistency_checker=consistency_checker
        )
        
        print(f"   初始化LLM提供者: {llm_provider.provider_name}")
        print(f"   初始化规则解释器")
        print(f"   初始化推理流水线")
        
        # 4. 初始化核心运行时层组件
        print("\n3. 初始化核心运行时层组件...")
        
        # 创建会话管理器
        session_manager = SessionManager(config)
        
        # 创建Prompt组装器
        prompt_assembler = PromptAssembler(config)
        
        # 创建回合调度器
        turn_scheduler = TurnScheduler(config)
        
        print(f"   初始化会话管理器")
        print(f"   初始化Prompt组装器")
        print(f"   初始化回合调度器")
        
        # 5. 测试规则解释
        print("\n4. 测试规则解释...")
        context = {
            "current_scene": "魔法学院的大厅",
            "characters": ["艾伦", "莉莉丝"],
            "action": "探索图书馆"
        }
        
        interpreted_rules = rule_interpreter.interpret(canon, context)
        print(f"   解释规则数: {len(interpreted_rules)}")
        for rule in interpreted_rules[:3]:  # 显示前3条规则
            print(f"     - {rule['type']}: {rule['constraint'][:50]}...")
        
        # 6. 测试Prompt组装
        print("\n5. 测试Prompt组装...")
        prompt_context = {
            "rules": interpreted_rules,
            "history": [],
            "current_state": "艾伦和莉莉丝在魔法学院相遇",
            "user_input": "接下来会发生什么？"
        }
        
        prompt = prompt_assembler.assemble(prompt_context)
        print(f"   组装Prompt长度: {len(prompt)} 字符")
        print(f"   Prompt预览: {prompt[:100]}...")
        
        # 7. 测试推理流水线（使用模拟LLM）
        print("\n6. 测试推理流水线（模拟）...")
        
        # 设置模拟响应
        mock_response = "艾伦和莉莉丝决定一起探索图书馆，寻找失落的魔法书。他们发现了一本古老的典籍，上面记载着强大的咒语。"
        
        # 创建模拟LLM提供者
        class MockLLMProvider:
            async def generate(self, prompt, **kwargs):
                return mock_response
        
        reasoning_pipeline.llm_provider = MockLLMProvider()
        
        # 运行推理
        result = await reasoning_pipeline.run(
            canon=canon,
            context=context,
            user_input="接下来会发生什么？"
        )
        
        print(f"   推理结果: {result['result'][:80]}...")
        print(f"   一致性检查: {'通过' if result['consistency_check']['passed'] else '失败'}")
        
        # 8. 测试一致性检查
        print("\n7. 测试一致性检查...")
        history = [
            {"turn": 1, "content": "艾伦在魔法学院学习火球术"},
            {"turn": 2, "content": "莉莉丝从精灵森林来到学院"}
        ]
        
        consistency_result = consistency_checker.check(
            current_narrative=result['result'],
            history=history,
            rules=interpreted_rules
        )
        
        print(f"   一致性分数: {consistency_result['score']:.2f}")
        print(f"   违反规则数: {len(consistency_result['violations'])}")
        if consistency_result['suggestions']:
            print(f"   建议: {consistency_result['suggestions'][0]}")
        
        # 9. 测试与SessionManager的集成
        print("\n8. 测试与SessionManager的集成...")
        
        # 创建会话
        session = await session_manager.create_session(
            session_id="test_integration",
            config=config.get_config()
        )
        
        # 设置会话的规则集
        session.rules = canon
        session.rule_interpreter = rule_interpreter
        
        print(f"   创建会话: {session.session_id}")
        print(f"   会话状态: {session.state}")
        
        # 10. 测试完整工作流
        print("\n9. 测试完整工作流...")
        
        # 模拟一个回合
        turn_context = {
            "session": session,
            "user_input": "艾伦尝试施展火球术",
            "rules": canon,
            "history": history
        }
        
        # 使用规则解释器
        turn_rules = rule_interpreter.interpret(canon, turn_context)
        
        # 组装Prompt
        turn_prompt = prompt_assembler.assemble({
            "rules": turn_rules,
            "history": history,
            "current_state": "在魔法学院的训练场",
            "user_input": "艾伦尝试施展火球术"
        })
        
        print(f"   回合规则数: {len(turn_rules)}")
        print(f"   回合Prompt长度: {len(turn_prompt)} 字符")
        
        print("\n✅ 集成测试通过！")
        print(f"   测试了 {len(canon.sections)} 个规则章节")
        print(f"   解释了 {len(interpreted_rules)} 条规则")
        print(f"   生成了 {len(result['result'])} 字符的叙事")
        
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
    
    success = await test_integration()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ 所有集成测试通过！")
        print("规则层和解释层已成功与核心运行时层集成。")
    else:
        print("\n" + "=" * 50)
        print("❌ 集成测试失败")
        
    return success


if __name__ == "__main__":
    asyncio.run(main())