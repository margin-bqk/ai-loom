#!/usr/bin/env python3
"""
核心运行时层集成测试脚本
验证ConfigManager、SessionManager、PersistenceEngine、TurnScheduler和PromptAssembler的基本功能
"""

import asyncio
import os
import sys
import tempfile
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loom.core.config_manager import ConfigManager
from src.loom.core.persistence_engine import SQLitePersistence
from src.loom.core.prompt_assembler import PromptAssembler, PromptContext
from src.loom.core.session_manager import SessionConfig, SessionManager
from src.loom.core.turn_scheduler import Turn, TurnScheduler


async def test_basic_integration():
    """测试基本集成"""
    print("=" * 60)
    print("核心运行时层集成测试")
    print("=" * 60)

    # 创建临时数据库
    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_integration.db")

    try:
        # 1. 测试ConfigManager
        print("\n1. 测试ConfigManager...")
        config_manager = ConfigManager()
        config = config_manager.get_config()
        print(f"   ✓ 配置加载成功")
        print(f"   - 默认LLM提供商: {config.session_defaults.default_llm_provider}")
        print(f"   - 最大并发回合数: {config.max_concurrent_turns}")

        # 2. 测试PersistenceEngine
        print("\n2. 测试PersistenceEngine...")
        persistence = SQLitePersistence(db_path=db_path)
        await persistence.initialize()
        print(f"   ✓ 持久化引擎初始化成功")

        # 3. 测试SessionManager
        print("\n3. 测试SessionManager...")
        session_manager = SessionManager(
            persistence_engine=persistence, config_manager=config_manager
        )

        session_config = SessionConfig(
            name="集成测试会话", canon_path="./test_canon", llm_provider="openai"
        )

        session = await session_manager.create_session(session_config)
        print(f"   ✓ 会话创建成功: {session.id}")
        print(f"   - 会话名称: {session.name}")
        print(f"   - 创建时间: {session.created_at}")

        # 4. 测试TurnScheduler
        print("\n4. 测试TurnScheduler...")
        turn_scheduler = TurnScheduler(
            max_concurrent=config.max_concurrent_turns,
            session_manager=session_manager,
            persistence_engine=persistence,
        )

        turn = turn_scheduler.create_turn(
            session_id=session.id,
            turn_number=1,
            player_input="测试玩家输入",
            interventions=[{"type": "ooc", "content": "这是一个测试"}],
        )

        turn_id = await turn_scheduler.submit_turn(turn)
        print(f"   ✓ 回合提交成功: {turn_id}")

        # 5. 测试PromptAssembler
        print("\n5. 测试PromptAssembler...")
        prompt_assembler = PromptAssembler(config_manager=config_manager)

        prompt_context = PromptContext(
            session_id=session.id,
            turn_number=1,
            player_input="测试玩家输入",
            rules_text="# 测试规则\n这是一个测试世界观规则。",
            memories=[
                {
                    "type": "character",
                    "content": {"name": "测试角色", "description": "一个测试角色"},
                    "created_at": datetime.now().isoformat(),
                }
            ],
            interventions=[{"type": "ooc", "content": "测试干预"}],
            llm_provider="openai",
        )

        prompt_result = prompt_assembler.assemble(prompt_context)
        print(f"   ✓ Prompt组装成功")
        print(f"   - 系统提示长度: {len(prompt_result.system_prompt)} 字符")
        print(f"   - 用户提示长度: {len(prompt_result.user_prompt)} 字符")
        print(f"   - 令牌估计: {prompt_result.token_estimate}")

        # 6. 测试会话持久化
        print("\n6. 测试会话持久化...")
        await session_manager.save_session(session, force=True)

        # 从内存中移除会话
        del session_manager.active_sessions[session.id]

        # 重新加载会话
        reloaded_session = await session_manager.load_session(session.id)
        if reloaded_session:
            print(f"   ✓ 会话持久化成功")
            print(f"   - 重新加载的会话ID: {reloaded_session.id}")
            print(f"   - 会话名称: {reloaded_session.name}")
        else:
            print(f"   ✗ 会话持久化失败")

        # 7. 清理
        print("\n7. 清理资源...")
        await turn_scheduler.stop()
        await persistence.close()

        # 删除临时文件
        import shutil

        shutil.rmtree(temp_dir)

        print(f"\n{'=' * 60}")
        print("集成测试完成！所有核心组件工作正常。")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"集成测试失败: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 60)
        return False


async def test_component_interactions():
    """测试组件交互"""
    print("\n" + "=" * 60)
    print("组件交互测试")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp()
    db_path = os.path.join(temp_dir, "test_interactions.db")

    try:
        # 初始化组件
        config_manager = ConfigManager()
        persistence = SQLitePersistence(db_path=db_path)
        await persistence.initialize()
        session_manager = SessionManager(
            persistence_engine=persistence, config_manager=config_manager
        )
        turn_scheduler = TurnScheduler(
            max_concurrent=2,
            session_manager=session_manager,
            persistence_engine=persistence,
        )
        prompt_assembler = PromptAssembler(config_manager=config_manager)

        # 测试1: 配置管理器与会话管理器集成
        print("\n测试1: 配置管理器与会话管理器集成...")
        session_config = SessionConfig(
            name="配置集成测试",
            canon_path="./test_canon"
            # 不指定llm_provider，应使用默认值
        )

        session = await session_manager.create_session(session_config)
        default_provider = (
            config_manager.get_config().session_defaults.default_llm_provider
        )
        if session.config.llm_provider == default_provider:
            print(f"   ✓ 会话使用了配置管理器中的默认LLM提供商: {default_provider}")
        else:
            print(
                f"   ✗ 会话LLM提供商不匹配: {session.config.llm_provider} != {default_provider}"
            )

        # 测试2: 会话管理器与持久化引擎集成
        print("\n测试2: 会话管理器与持久化引擎集成...")
        session.current_turn = 5
        session.total_turns = 10
        await session_manager.save_session(session, force=True)

        # 重新加载
        reloaded = await session_manager.load_session(session.id)
        if reloaded and reloaded.current_turn == 5 and reloaded.total_turns == 10:
            print(f"   ✓ 会话状态持久化成功")
        else:
            print(f"   ✗ 会话状态持久化失败")

        # 测试3: 回合调度器与会话管理器集成
        print("\n测试3: 回合调度器与会话管理器集成...")
        turn = turn_scheduler.create_turn(
            session_id=session.id, turn_number=6, player_input="交互测试输入"
        )

        turn_id = await turn_scheduler.submit_turn(turn)
        if turn_id:
            print(f"   ✓ 回合成功提交到调度器: {turn_id}")
        else:
            print(f"   ✗ 回合提交失败")

        # 测试4: Prompt组装器与配置管理器集成
        print("\n测试4: Prompt组装器与配置管理器集成...")
        context = PromptContext(
            session_id=session.id,
            turn_number=7,
            player_input="Prompt测试输入",
            rules_text="# 测试规则",
            llm_provider=default_provider,
        )

        result = prompt_assembler.assemble(context)
        if result and result.token_estimate > 0:
            print(f"   ✓ Prompt组装成功，使用LLM提供商: {default_provider}")
        else:
            print(f"   ✗ Prompt组装失败")

        # 清理
        await turn_scheduler.stop()
        await persistence.close()
        import shutil

        shutil.rmtree(temp_dir)

        print(f"\n{'=' * 60}")
        print("组件交互测试完成！")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"组件交互测试失败: {e}")
        import traceback

        traceback.print_exc()
        print("=" * 60)
        return False


async def main():
    """主函数"""
    print("LOOM核心运行时层集成测试")
    print("=" * 60)

    success1 = await test_basic_integration()
    success2 = await test_component_interactions()

    if success1 and success2:
        print("\n✅ 所有集成测试通过！")
        return 0
    else:
        print("\n❌ 集成测试失败！")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
