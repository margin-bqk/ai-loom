#!/usr/bin/env python3
"""
DeepSeek API 使用示例

本示例展示如何在 LOOM 中使用 DeepSeek 作为 LLM 提供商，
包括中文内容生成、推理模式、成本计算等功能。

使用方法:
1. 设置环境变量: export DEEPSEEK_API_KEY="your-api-key"
2. 运行: python deepseek_example.py
"""

import asyncio
import os
import sys
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from loom.interpretation import LLMProviderFactory
    from loom import SessionManager, SessionConfig
except ImportError:
    print("错误: 无法导入 LOOM 模块。请确保在项目根目录运行此脚本。")
    print("尝试: cd /path/to/ai-loom && python examples/deepseek_example.py")
    sys.exit(1)


class DeepSeekExample:
    """DeepSeek 使用示例类"""

    def __init__(self, api_key: str = None):
        """
        初始化示例

        Args:
            api_key: DeepSeek API 密钥，如果为 None 则从环境变量读取
        """
        self.api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            print("错误: 未找到 DeepSeek API 密钥")
            print("请设置环境变量: export DEEPSEEK_API_KEY='your-api-key'")
            print("或在代码中直接提供 API 密钥")
            sys.exit(1)

    def create_deepseek_config(self, thinking_enabled: bool = False) -> Dict[str, Any]:
        """
        创建 DeepSeek 配置

        Args:
            thinking_enabled: 是否启用推理模式

        Returns:
            DeepSeek 配置字典
        """
        model = "deepseek-reasoner" if thinking_enabled else "deepseek-chat"
        max_tokens = 32000 if thinking_enabled else 4096

        return {
            "type": "deepseek",
            "api_key": self.api_key,
            "base_url": "https://api.deepseek.com",
            "model": model,
            "thinking_enabled": thinking_enabled,
            "temperature": 1.0,
            "max_tokens": max_tokens,
            "timeout": 60,
            "max_retries": 3,
            "retry_delay": 2.0,
            "enable_caching": True,
            "cache_ttl": 300,
            "connection_pool_size": 5,
        }

    async def test_connection(self):
        """测试 DeepSeek 连接"""
        print("=" * 60)
        print("测试 DeepSeek 连接")
        print("=" * 60)

        config = self.create_deepseek_config()
        provider = LLMProviderFactory.create_provider(config)

        try:
            # 简单测试请求
            response = await provider.generate("请回复'连接测试成功'")

            print(f"✓ 连接测试成功")
            print(f"  模型: {response.model}")
            print(f"  响应: {response.content}")
            print(f"  令牌使用: {response.usage}")
            print(f"  成本: ${response.cost:.6f}")

            return True

        except Exception as e:
            print(f"✗ 连接测试失败: {e}")
            return False

    async def chinese_content_generation(self):
        """中文内容生成示例"""
        print("\n" + "=" * 60)
        print("中文内容生成示例")
        print("=" * 60)

        config = self.create_deepseek_config()
        provider = LLMProviderFactory.create_provider(config)

        # 中文内容生成任务
        tasks = [
            {"name": "诗歌创作", "prompt": "创作一首关于中秋节的七言绝句"},
            {
                "name": "故事创作",
                "prompt": "写一个关于人工智能助手的科幻微小说，不超过200字",
            },
            {
                "name": "文章摘要",
                "prompt": """请为以下文章写一个中文摘要：
                人工智能正在改变我们的生活方式。从智能手机助手到自动驾驶汽车，
                从医疗诊断到金融分析，AI技术已经渗透到各个领域。
                未来，随着技术的进步，人工智能将在教育、娱乐、工作等方面发挥更大作用。
                然而，这也带来了伦理、隐私和就业等挑战。我们需要在享受技术带来的便利的同时，
                认真思考如何应对这些挑战。""",
            },
        ]

        results = []
        total_cost = 0

        for task in tasks:
            print(f"\n▶ {task['name']}")
            print(f"  提示: {task['prompt'][:50]}...")

            try:
                response = await provider.generate(
                    task["prompt"], temperature=0.8, max_tokens=500
                )

                print(f"  ✓ 生成成功")
                print(f"    响应: {response.content[:80]}...")
                print(f"    长度: {len(response.content)} 字符")
                print(f"    令牌: {response.usage.get('total_tokens', 0)}")
                print(f"    成本: ${response.cost:.6f}")

                results.append(
                    {
                        "task": task["name"],
                        "content": response.content,
                        "tokens": response.usage.get("total_tokens", 0),
                        "cost": response.cost,
                    }
                )

                total_cost += response.cost

            except Exception as e:
                print(f"  ✗ 生成失败: {e}")
                results.append({"task": task["name"], "error": str(e)})

        print(f"\n📊 中文内容生成统计:")
        print(f"  总任务数: {len(tasks)}")
        print(f"  成功数: {len([r for r in results if 'content' in r])}")
        print(f"  总成本: ${total_cost:.6f}")

        return results

    async def reasoning_mode_demo(self):
        """推理模式演示"""
        print("\n" + "=" * 60)
        print("推理模式演示")
        print("=" * 60)

        config = self.create_deepseek_config(thinking_enabled=True)
        provider = LLMProviderFactory.create_provider(config)

        # 推理问题
        reasoning_problems = [
            {
                "category": "逻辑推理",
                "problem": "如果所有猫都怕水，而汤姆是一只猫，那么汤姆怕水吗？请展示完整的推理过程。",
            },
            {
                "category": "数学问题",
                "problem": """一个水池有进水管和出水管。进水管单独注满水池需要3小时，
                出水管单独排空水池需要4小时。如果同时打开进水管和出水管，需要多少小时才能注满水池？
                请展示计算步骤。""",
            },
            {
                "category": "科学推理",
                "problem": "解释为什么冰会浮在水面上，而大多数固体都会下沉。请从物理原理角度解释。",
            },
        ]

        results = []

        for problem in reasoning_problems:
            print(f"\n▶ {problem['category']}")
            print(f"  问题: {problem['problem']}")

            try:
                response = await provider.generate(
                    problem["problem"],
                    temperature=0.3,  # 降低温度以获得更确定的推理
                    max_tokens=1000,
                )

                print(f"  ✓ 推理完成")
                print(f"    响应摘要: {response.content[:100]}...")
                print(f"    模型: {response.model}")
                print(
                    f"    推理模式: {response.metadata.get('thinking_enabled', False)}"
                )
                print(f"    令牌: {response.usage.get('total_tokens', 0)}")
                print(f"    成本: ${response.cost:.6f}")

                # 保存完整响应到文件
                filename = f"reasoning_{problem['category']}.txt"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"问题: {problem['problem']}\n\n")
                    f.write(f"回答:\n{response.content}\n\n")
                    f.write(f"元数据: {response.metadata}\n")
                    f.write(f"令牌使用: {response.usage}\n")
                    f.write(f"成本: ${response.cost:.6f}\n")

                print(f"    完整响应已保存到: {filename}")

                results.append(
                    {
                        "category": problem["category"],
                        "response": response.content,
                        "tokens": response.usage.get("total_tokens", 0),
                        "cost": response.cost,
                        "file": filename,
                    }
                )

            except Exception as e:
                print(f"  ✗ 推理失败: {e}")
                results.append({"category": problem["category"], "error": str(e)})

        return results

    async def session_with_deepseek(self):
        """使用 DeepSeek 的完整会话示例"""
        print("\n" + "=" * 60)
        print("完整会话示例")
        print("=" * 60)

        # 创建会话管理器
        session_manager = SessionManager()

        # 配置使用 DeepSeek
        session_config = SessionConfig(
            session_type="chinese_content",
            initial_prompt="我们来讨论中国传统文化",
            llm_provider="deepseek",
            llm_model="deepseek-chat",
            max_turns=3,
            memory_enabled=True,
        )

        print("创建会话...")
        session = await session_manager.create_session(session_config)
        print(f"会话ID: {session.session_id}")

        # 对话流程
        conversation = [
            "首先，请介绍一下中国传统节日",
            "那么在这些节日中，食物有什么特别的含义吗？",
            "最后，现代社会中这些传统节日有什么新的变化？",
        ]

        print("\n开始对话:")

        for i, user_input in enumerate(conversation, 1):
            print(f"\n[用户] 第{i}轮: {user_input}")

            try:
                # 发送用户输入
                turn = await session.add_turn(user_input)

                print(f"[AI] 响应: {turn.response[:150]}...")
                print(f"    模型: {turn.model}")
                print(f"    令牌: {turn.usage.get('total_tokens', 0)}")
                print(f"    成本: ${turn.cost:.6f}")

                # 模拟用户思考时间
                await asyncio.sleep(1)

            except Exception as e:
                print(f"  ✗ 对话失败: {e}")
                break

        print(f"\n📊 会话统计:")
        print(f"  总回合数: {len(session.turns)}")
        print(f"  总成本: ${sum(t.cost for t in session.turns):.6f}")

        # 保存会话记录
        filename = f"session_{session.session_id}.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"会话ID: {session.session_id}\n")
            f.write(f"创建时间: {datetime.now().isoformat()}\n")
            f.write(f"会话类型: {session_config.session_type}\n")
            f.write(f"LLM提供商: {session_config.llm_provider}\n")
            f.write(f"LLM模型: {session_config.llm_model}\n")
            f.write("\n" + "=" * 50 + "\n\n")

            for i, turn in enumerate(session.turns, 1):
                f.write(f"回合 {i}:\n")
                f.write(f"用户: {turn.prompt}\n")
                f.write(f"AI: {turn.response}\n")
                f.write(f"模型: {turn.model}\n")
                f.write(f"令牌: {turn.usage}\n")
                f.write(f"成本: ${turn.cost:.6f}\n")
                f.write("\n" + "-" * 30 + "\n\n")

        print(f"会话记录已保存到: {filename}")

        return session

    async def cost_comparison(self):
        """成本比较示例"""
        print("\n" + "=" * 60)
        print("成本比较示例")
        print("=" * 60)

        # 测试文本
        test_prompts = [
            "写一句简单的问候语",
            "写一段产品描述，大约100字",
            "写一篇关于人工智能的短文，不少于300字",
        ]

        # 配置不同提供商
        providers_config = {
            "deepseek": self.create_deepseek_config(),
            "openai": {
                "type": "openai",
                "api_key": os.getenv("OPENAI_API_KEY", "test-key"),
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 1000,
            },
        }

        results = {}

        for provider_name, config in providers_config.items():
            print(f"\n测试 {provider_name}...")

            # 跳过没有API密钥的提供商
            if provider_name == "openai" and not os.getenv("OPENAI_API_KEY"):
                print("  跳过: 未设置 OPENAI_API_KEY 环境变量")
                continue

            provider_results = []
            total_cost = 0

            for prompt in test_prompts:
                try:
                    provider = LLMProviderFactory.create_provider(config)
                    response = await provider.generate(prompt)

                    provider_results.append(
                        {
                            "prompt": prompt[:30] + "...",
                            "tokens": response.usage.get("total_tokens", 0),
                            "cost": response.cost,
                        }
                    )

                    total_cost += response.cost

                except Exception as e:
                    print(f"  ✗ 测试失败: {e}")
                    provider_results.append(
                        {"prompt": prompt[:30] + "...", "error": str(e)}
                    )

            results[provider_name] = {
                "results": provider_results,
                "total_cost": total_cost,
            }

        # 输出比较结果
        print("\n📊 成本比较结果:")
        for provider_name, data in results.items():
            print(f"\n{provider_name}:")
            if "results" in data:
                for result in data["results"]:
                    if "cost" in result:
                        print(f"  {result['prompt']}")
                        print(f"    令牌: {result['tokens']}")
                        print(f"    成本: ${result['cost']:.6f}")
                print(f"  总成本: ${data['total_cost']:.6f}")

        return results

    async def run_all_examples(self):
        """运行所有示例"""
        print("DeepSeek API 使用示例")
        print("=" * 60)
        print(f"开始时间: {datetime.now().isoformat()}")
        print(
            f"API密钥: {self.api_key[:10]}...{self.api_key[-4:] if len(self.api_key) > 14 else ''}"
        )
        print()

        # 运行各个示例
        await self.test_connection()
        await self.chinese_content_generation()
        await self.reasoning_mode_demo()
        await self.session_with_deepseek()
        await self.cost_comparison()

        print("\n" + "=" * 60)
        print("所有示例完成!")
        print(f"结束时间: {datetime.now().isoformat()}")
        print("=" * 60)


async def main():
    """主函数"""
    # 从环境变量或命令行参数获取API密钥
    api_key = None
    if len(sys.argv) > 1:
        api_key = sys.argv[1]

    example = DeepSeekExample(api_key)

    try:
        await example.run_all_examples()
    except KeyboardInterrupt:
        print("\n\n用户中断")
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback

        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    # 运行异步主函数
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
