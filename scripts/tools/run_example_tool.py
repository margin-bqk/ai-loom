#!/usr/bin/env python3
"""
LOOM 示例运行脚本
演示如何使用 LOOM 创建会话、处理回合和使用干预
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.loom.core.session_manager import SessionConfig, SessionManager
from src.loom.interpretation.llm_provider import LLMProviderFactory
from src.loom.intervention.player_intervention import PlayerIntervention
from src.loom.rules.rule_loader import RuleLoader


async def run_basic_example():
    """运行基础示例"""
    print("=== LOOM 基础示例 ===")
    print("演示创建会话、加载规则、处理回合")

    try:
        # 1. 加载规则
        print("\n1. 加载规则...")
        rule_loader = RuleLoader("./canon")
        canon = rule_loader.load_canon("default")

        if not canon:
            print("警告: 未找到默认规则，创建示例规则...")
            rule_loader.create_default_canon("default")
            canon = rule_loader.load_canon("default")

        print(f"✓ 规则加载成功: {canon.metadata.get('version', '未知版本')}")
        print(f"  章节: {list(canon.sections.keys())}")

        # 2. 创建 LLM 提供者（使用模拟提供者）
        print("\n2. 创建 LLM 提供者...")
        llm_config = {
            "name": "example",
            "type": "openai",
            "model": "gpt-3.5-turbo",
            "api_key": "sk-example",  # 示例密钥
            "base_url": "https://api.openai.com/v1",
        }

        # 在实际使用中，您应该使用真实的 API 密钥
        # 这里使用模拟模式
        llm_config["simulate"] = True

        llm_provider = LLMProviderFactory.create_provider(llm_config)
        print(f"✓ LLM 提供者创建成功: {llm_provider.name}")

        # 3. 创建会话
        print("\n3. 创建会话...")
        session_config = SessionConfig(
            name="示例冒险",
            canon_path="./canon/default.md",
            memory_backend="memory",  # 使用内存后端
            llm_provider="example",
            metadata={"example": True},
        )

        session_manager = SessionManager()
        session = await session_manager.create_session(session_config)
        print(f"✓ 会话创建成功: {session.name} (ID: {session.id[:8]}...)")

        # 4. 处理回合（模拟）
        print("\n4. 处理回合...")
        player_inputs = [
            "我走进森林，寻找隐藏的宝藏。",
            "(OOC: 我想让故事更紧张一些)",
            "突然，我听到树丛中有动静。",
            "[INTENT: 我想小心地调查声音来源]",
        ]

        intervention_parser = PlayerIntervention()

        for i, input_text in enumerate(player_inputs, 1):
            print(f"\n  回合 {i}: {input_text}")

            # 解析干预
            parsed = intervention_parser.parse_input(input_text)

            if parsed["has_interventions"]:
                print(f"    检测到干预: {len(parsed['interventions'])} 个")
                for interv in parsed["interventions"]:
                    print(f"      - {interv.type.value}: {interv.content[:30]}...")

            print(f"    清理后的输入: {parsed['clean_input']}")

            # 模拟处理延迟
            await asyncio.sleep(0.5)

        # 5. 演示干预处理
        print("\n5. 演示干预处理...")
        complex_input = "我攻击兽人 [EDIT: 兽人: 添加属性: 盔甲=厚重] (OOC: 这样战斗更有挑战性)"

        print(f"  复杂输入: {complex_input}")
        parsed = intervention_parser.parse_input(complex_input)

        print(f"  解析结果:")
        print(f"    - 清理输入: {parsed['clean_input']}")
        print(f"    - 干预数量: {len(parsed['interventions'])}")

        for interv in parsed["interventions"]:
            print(f"    - {interv.type.value.upper()}: {interv.content}")

        # 6. 显示会话信息
        print("\n6. 会话信息:")
        print(f"   会话ID: {session.id}")
        print(f"   会话名称: {session.name}")
        print(f"   创建时间: {session.created_at}")
        print(f"   当前回合: {session.current_turn}")

        print("\n✓ 示例运行完成!")
        print("\n下一步建议:")
        print("  1. 在 .env 文件中设置真实的 API 密钥")
        print("  2. 修改 canon/default.md 创建自己的世界规则")
        print("  3. 查看 examples/ 目录中的更多示例")
        print("  4. 阅读 docs/ 目录中的文档")

        return True

    except Exception as e:
        print(f"\n✗ 示例运行失败: {e}")
        import traceback

        traceback.print_exc()
        return False


async def run_advanced_example():
    """运行高级示例（需要真实 API 密钥）"""
    print("\n\n=== LOOM 高级示例 ===")
    print("注意: 此示例需要真实的 API 密钥")

    try:
        # 检查环境变量
        import os

        api_key = os.environ.get("OPENAI_API_KEY")

        if not api_key or api_key.startswith("sk-example"):
            print("警告: 未找到有效的 OpenAI API 密钥")
            print("请设置 OPENAI_API_KEY 环境变量")
            print("跳过高级示例...")
            return False

        print("检测到 API 密钥，运行高级示例...")

        # 这里可以添加更复杂的示例代码
        # 例如：实际调用 LLM、使用记忆系统等

        print("高级示例代码待实现...")
        print("请参考文档和测试用例了解高级用法")

        return True

    except Exception as e:
        print(f"高级示例失败: {e}")
        return False


def main():
    """主函数"""
    print("LOOM 示例运行脚本")
    print("=" * 50)

    # 检查必要文件
    required_dirs = ["canon", "config", "src"]
    for dir_name in required_dirs:
        if not (project_root / dir_name).exists():
            print(f"错误: 目录 '{dir_name}' 不存在")
            print("请确保在项目根目录运行此脚本")
            return 1

    # 运行异步主函数
    try:
        success = asyncio.run(run_basic_example())

        if success and len(sys.argv) > 1 and sys.argv[1] == "--advanced":
            asyncio.run(run_advanced_example())

        return 0 if success else 1

    except KeyboardInterrupt:
        print("\n\n示例被用户中断")
        return 130
    except Exception as e:
        print(f"\n未处理的错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
