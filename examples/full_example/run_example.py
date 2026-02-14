#!/usr/bin/env python3
"""
完整示例项目 - 运行示例
展示如何使用 LOOM 系统运行一个完整的奇幻世界会话
"""

import asyncio
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.loom.core.config_manager import ConfigManager
from src.loom.core.session_manager import SessionManager
from src.loom.rules.rule_loader import RuleLoader


async def run_fantasy_example():
    """运行奇幻世界示例"""
    print("=" * 60)
    print("LOOM 完整示例 - 奇幻世界会话")
    print("=" * 60)

    # 1. 初始化配置
    print("\n1. 初始化配置...")
    config = ConfigManager()
    await config.load_config("examples/full_example/config/world_config.yaml")

    # 2. 加载规则
    print("2. 加载规则...")
    rule_loader = RuleLoader()
    rules = await rule_loader.load_rules_from_file("templates/rules/fantasy_basic.md")

    # 3. 创建会话管理器
    print("3. 创建会话管理器...")
    session_manager = SessionManager(config, rule_loader)

    # 4. 开始新会话
    print("4. 开始新会话...")
    session_id = await session_manager.create_session(
        world_name="艾瑟兰大陆", character_name="艾莉亚", scenario="法师塔的早晨"
    )

    print(f"会话 ID: {session_id}")

    # 5. 运行几个回合
    print("\n5. 运行会话回合...")

    # 第一回合
    print("\n--- 第一回合 ---")
    response1 = await session_manager.process_turn(
        session_id, "艾莉亚醒来，发现自己躺在法师塔的床上。窗外传来鸟鸣声。她应该做什么？"
    )
    print(f"AI 响应: {response1[:100]}...")

    # 第二回合
    print("\n--- 第二回合 ---")
    response2 = await session_manager.process_turn(
        session_id, "艾莉亚决定起床，穿上法师袍，然后去塔顶找导师雷纳德。"
    )
    print(f"AI 响应: {response2[:100]}...")

    # 第三回合
    print("\n--- 第三回合 ---")
    response3 = await session_manager.process_turn(
        session_id, "在塔顶，雷纳德告诉艾莉亚今天有一个重要的魔法测试。她感到既紧张又兴奋。"
    )
    print(f"AI 响应: {response3[:100]}...")

    # 6. 保存会话
    print("\n6. 保存会话...")
    await session_manager.save_session(
        session_id, "examples/full_example/sessions/fantasy_session.json"
    )

    # 7. 导出数据
    print("7. 导出数据...")
    export_data = await session_manager.export_session(session_id, format="json")
    with open("examples/full_example/sessions/export.json", "w", encoding="utf-8") as f:
        f.write(export_data)

    print("\n" + "=" * 60)
    print("示例运行完成！")
    print("生成的文件:")
    print("  - examples/full_example/sessions/fantasy_session.json")
    print("  - examples/full_example/sessions/export.json")
    print("=" * 60)

    return session_id


async def demonstrate_features():
    """演示其他功能"""
    print("\n" + "=" * 60)
    print("功能演示")
    print("=" * 60)

    # 初始化
    config = ConfigManager()
    await config.load_default()

    rule_loader = RuleLoader()
    session_manager = SessionManager(config, rule_loader)

    # 演示规则检查
    print("\n1. 规则检查演示...")
    rules_text = """
    rule: 魔法消耗
    description: 施展魔法需要消耗魔力
    condition: 当角色施展魔法时
    effect: 角色的魔力值减少
    """

    is_valid = await rule_loader.validate_rule(rules_text)
    print(f"规则有效性: {is_valid}")

    # 演示配置管理
    print("\n2. 配置管理演示...")
    world_config = config.get_world_config()
    print(f"世界名称: {world_config.get('name', '未设置')}")
    print(f"角色数量: {len(world_config.get('characters', []))}")

    # 演示会话管理
    print("\n3. 会话管理演示...")
    sessions = await session_manager.list_sessions()
    print(f"现有会话数量: {len(sessions)}")

    if sessions:
        print("最近会话:")
        for i, session in enumerate(sessions[:3], 1):
            print(
                f"  {i}. {session.get('id', '未知')} - {session.get('world_name', '未知世界')}"
            )


def main():
    """主函数"""
    try:
        # 运行主示例
        loop = asyncio.get_event_loop()
        session_id = loop.run_until_complete(run_fantasy_example())

        # 演示其他功能
        loop.run_until_complete(demonstrate_features())

        print("\n" + "=" * 60)
        print("示例项目使用说明:")
        print("=" * 60)
        print("1. 使用 CLI 运行:")
        print("   $ loom run --world examples/full_example/config/world_config.yaml")
        print()
        print("2. 使用 Python 脚本:")
        print("   $ python examples/full_example/run_example.py")
        print()
        print("3. 查看生成的会话文件:")
        print("   $ cat examples/full_example/sessions/fantasy_session.json | jq .")
        print()
        print("4. 使用 Web UI:")
        print("   $ loom web start")
        print("   然后在浏览器中访问 http://localhost:8000")

    except Exception as e:
        print(f"运行示例时出错: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
