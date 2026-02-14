# Basic Narrative

## 概述

本文档提供 LOOM 基础叙事功能的完整示例，展示如何使用 LOOM 创建、管理和运行基本的叙事会话。通过本示例，您将学习如何：

1. 配置基础世界规则
2. 创建叙事会话
3. 与 AI 进行交互式叙事
4. 管理会话状态和记忆
5. 导出和分享叙事内容

## 快速开始

### 1. 准备环境

确保已安装 LOOM 并配置了 LLM 提供商：

```bash
# 安装 LOOM
pip install -e .

# 配置环境变量
export OPENAI_API_KEY="your-api-key"
# 或使用其他提供商
export ANTHROPIC_API_KEY="your-api-key"
```

### 2. 运行基础示例

LOOM 提供了完整的基础示例，位于 `examples/full_example/`：

```bash
# 进入示例目录
cd examples/full_example

# 运行完整示例
python run_example.py
```

## 基础世界配置

### 1. 世界配置文件

创建 `world_config.yaml` 定义基础世界规则：

```yaml
# examples/full_example/config/world_config.yaml
version: "1.0"
name: "基础奇幻世界"

world:
  name: "艾瑟利亚"
  description: |
    一个充满魔法和神秘的中世纪奇幻世界。
    世界由多个王国和城邦组成，魔法是自然力量的一部分。

  physical_laws:
    - "魔法是世界的自然力量，存在于所有生物和物体中"
    - "魔法分为元素魔法（火、水、风、土）和奥术魔法（时间、空间、生命）"
    - "魔法使用需要消耗精神力，过度使用会导致魔法衰竭"
    - "物理法则基本遵循现实世界，但允许魔法干预"

  major_races:
    - name: "人类"
      description: "适应性强，学习速度快，魔法天赋中等"

    - name: "精灵"
      description: "长寿，与自然和谐相处，擅长元素魔法"

    - name: "矮人"
      description: "擅长锻造和采矿，对魔法有天然抗性"

    - name: "兽人"
      description: "身体强壮，部落文化，有独特的萨满魔法传统"

tone:
  overall_style: "英雄史诗风格"
  mood_range:
    primary: ["冒险", "惊奇", "偶尔的幽默"]
    allowed: ["紧张", "悲伤（短暂）", "胜利的喜悦"]
    avoid: ["彻底的绝望", "无意义的残忍", "过度的恐怖"]

  narrative_pacing:
    opening: "中等节奏，建立世界观和角色"
    development: "节奏加快，增加冲突和挑战"
    climax: "快速节奏，紧张刺激"
    ending: "放慢节奏，提供情感满足和反思"

conflict:
  conflict_types:
    - type: "角色冲突"
      resolution: "通过对话、妥协或角色成长解决"

    - type: "物理冲突"
      resolution: "通过战斗、技能或魔法解决"

    - type: "道德冲突"
      resolution: "通过价值观讨论和艰难选择解决"

    - type: "环境冲突"
      resolution: "通过智慧、团队合作或特殊能力解决"

  combat_rules:
    - "战斗应该有叙事意义，避免无意义的暴力"
    - "角色可以受伤，但死亡应该是重要的叙事时刻"
    - "魔法战斗应该遵循'等价交换'原则（使用魔法需要代价）"
    - "允许战术性撤退和谈判"

permissions:
  player_can:
    - "创建和扮演自己的角色"
    - "探索世界的任何地区"
    - "学习魔法和技能（需要合理训练）"
    - "与其他角色建立关系"
    - "影响故事发展方向"

  player_cannot:
    - "直接控制其他玩家的角色（除非获得同意）"
    - "违反角色设定的行为（如精灵突然精通矮人锻造）"
    - "无理由的恶意行为（纯粹为了破坏）"
    - "创造全知全能的角色（角色应有弱点）"

causality:
  time_flow: "线性流动，不可逆转"
  death_and_resurrection:
    - "死亡通常是永久的"
    - "复活魔法极其罕见且代价巨大"
    - "角色死亡应该是重要的叙事事件"

  causality_principles:
    - "行动必有后果：角色的选择会影响世界"
    - "一致性原则：事件应该逻辑连贯"
    - "公平性原则：奖励和惩罚应该与行动相称"
    - "惊奇但合理：允许意外转折，但应有伏笔"

meta:
  version: "1.0.0"
  author: "LOOM示例团队"
  created_date: "2025-01-01"
  expected_duration: "3-10次会话"
  recommended_players: "3-6人"
```

### 2. 使用 Python 代码创建世界

```python
# examples/basic_world.py
from loom import WorldBuilder, SessionManager

# 创建世界构建器
world_builder = WorldBuilder()

# 定义基础世界
world = world_builder.create_world(
    name="基础奇幻世界",
    description="一个充满魔法和神秘的中世纪奇幻世界",
    genre="fantasy",
    tone="heroic_epic"
)

# 添加物理法则
world.add_physical_law("魔法是世界的自然力量")
world.add_physical_law("魔法使用消耗精神力")
world.add_physical_law("物理法则基本遵循现实世界")

# 添加种族
world.add_race("人类", "适应性强，学习速度快，魔法天赋中等")
world.add_race("精灵", "长寿，与自然和谐相处，擅长元素魔法")
world.add_race("矮人", "擅长锻造和采矿，对魔法有天然抗性")

# 设置叙事基调
world.set_tone(
    primary_moods=["冒险", "惊奇", "幽默"],
    pacing={
        "opening": "中等节奏",
        "development": "加快节奏",
        "climax": "快速节奏",
        "ending": "放慢节奏"
    }
)

# 保存世界配置
world.save("my_basic_world.yaml")
print(f"世界 '{world.name}' 创建成功!")
```

## 创建叙事会话

### 1. 初始化会话管理器

```python
# examples/session_example.py
import asyncio
from loom import SessionManager, SessionConfig
from loom.interpretation import LLMProviderFactory

async def create_basic_session():
    """创建基础叙事会话"""

    # 初始化会话管理器
    session_manager = SessionManager()

    # 配置 LLM 提供商
    llm_config = {
        "type": "openai",
        "api_key": "your-api-key",
        "model": "gpt-4",
        "temperature": 0.8,
        "max_tokens": 1000
    }

    # 创建会话配置
    session_config = SessionConfig(
        session_type="fantasy_adventure",
        world_config="examples/full_example/config/world_config.yaml",
        initial_prompt="""你是一位经验丰富的奇幻故事讲述者。
        我们将一起创作一个关于年轻魔法学徒的冒险故事。
        故事发生在艾瑟利亚世界，一个充满魔法和神秘的地方。""",
        llm_provider="openai",
        llm_model="gpt-4",
        max_turns=10,
        memory_enabled=True,
        memory_capacity=20
    )

    # 创建会话
    session = await session_manager.create_session(session_config)

    print(f"会话创建成功!")
    print(f"会话ID: {session.session_id}")
    print(f"会话类型: {session.session_type}")
    print(f"初始提示: {session.initial_prompt[:100]}...")

    return session

if __name__ == "__main__":
    asyncio.run(create_basic_session())
```

### 2. 交互式叙事示例

```python
# examples/interactive_story.py
import asyncio
from loom import SessionManager

async def interactive_storytelling():
    """交互式叙事示例"""

    # 创建会话
    session_manager = SessionManager()
    session = await session_manager.load_session("your_session_id")

    print("=== 奇幻冒险故事 ===")
    print("输入 'quit' 退出，'save' 保存会话")
    print("-" * 40)

    # 显示初始故事
    if session.turns:
        last_turn = session.turns[-1]
        print(f"[故事讲述者] {last_turn.response}")

    # 交互循环
    while True:
        # 获取用户输入
        user_input = input("\n[你] ")

        if user_input.lower() == 'quit':
            print("退出故事...")
            break

        if user_input.lower() == 'save':
            await session_manager.save_session(session)
            print("会话已保存!")
            continue

        # 添加回合
        try:
            turn = await session.add_turn(user_input)
            print(f"\n[故事讲述者] {turn.response}")

            # 显示统计信息
            print(f"\n[统计] 回合: {len(session.turns)}, "
                  f"令牌: {turn.usage.get('total_tokens', 0)}, "
                  f"成本: ${turn.cost:.6f}")

        except Exception as e:
            print(f"错误: {e}")

    # 保存最终会话
    await session_manager.save_session(session)
    print(f"\n故事结束! 会话已保存为: {session.session_id}")

if __name__ == "__main__":
    asyncio.run(interactive_storytelling())
```

## 完整示例：魔法学徒的冒险

### 1. 示例脚本

```python
# examples/magic_apprentice.py
#!/usr/bin/env python3
"""
魔法学徒冒险示例
展示完整的 LOOM 叙事流程
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path

from loom import SessionManager, SessionConfig, WorldBuilder
from loom.export import NarrativeExporter

class MagicApprenticeAdventure:
    """魔法学徒冒险示例类"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session_manager = SessionManager()
        self.world_builder = WorldBuilder()

    async def setup_world(self):
        """设置奇幻世界"""
        print("1. 创建奇幻世界...")

        # 创建或加载世界
        world_config = Path("examples/full_example/config/world_config.yaml")
        if world_config.exists():
            world = self.world_builder.load_world(str(world_config))
        else:
            world = self.world_builder.create_world(
                name="艾瑟利亚",
                description="魔法与神秘的中世纪奇幻世界",
                genre="fantasy"
            )

        print(f"  世界: {world.name}")
        print(f"  描述: {world.description[:50]}...")

        return world

    async def create_characters(self):
        """创建角色"""
        print("\n2. 创建角色...")

        characters = [
            {
                "name": "艾莉亚",
                "role": "主角",
                "description": "16岁的魔法学徒，聪明但缺乏自信，拥有罕见的空间魔法天赋",
                "personality": "好奇、善良、有时过于谨慎",
                "goal": "掌握魔法，找到失踪的导师"
            },
            {
                "name": "导师阿尔德林",
                "role": "导师",
                "description": "经验丰富的老法师，艾莉亚的导师，最近神秘失踪",
                "personality": "智慧、神秘、有时严厉",
                "goal": "引导艾莉亚发现她的真正潜力"
            },
            {
                "name": "里奥",
                "role": "同伴",
                "description": "年轻的战士，艾莉亚的童年朋友，忠诚勇敢",
                "personality": "勇敢、忠诚、有点冲动",
                "goal": "保护艾莉亚，证明自己的价值"
            }
        ]

        for char in characters:
            print(f"  {char['name']} - {char['role']}: {char['description'][:30]}...")

        return characters

    async def start_adventure(self, world, characters):
        """开始冒险"""
        print("\n3. 开始冒险会话...")

        # 创建会话配置
        session_config = SessionConfig(
            session_type="magic_apprentice_adventure",
            world_config=world.config_path if hasattr(world, 'config_path') else None,
            initial_prompt=self._create_initial_prompt(world, characters),
            llm_provider="openai",
            llm_model="gpt-4",
            temperature=0.8,
            max_tokens=800,
            max_turns=15,
            memory_enabled=True,
            memory_capacity=25
        )

        # 创建会话
        session = await self.session_manager.create_session(session_config)

        print(f"  会话ID: {session.session_id}")
        print(f"  最大回合数: {session_config.max_turns}")

        return session

    def _create_initial_prompt(self, world, characters):
        """创建初始提示"""
        main_char = next(c for c in characters if c["role"] == "主角")
        mentor = next(c for c in characters if c["role"] == "导师")
        companion = next(c for c in characters if c["role"] == "同伴")

        prompt = f"""
        你是一位专业的奇幻故事讲述者，擅长创作成长和冒险故事。

        世界设定: {world.name}
        {world.description}

        主要角色:
        1. {main_char['name']} - {main_char['description']}
           性格: {main_char['personality']}
           目标: {main_char['goal']}

        2. {mentor['name']} - {mentor['description']}
           性格: {mentor['personality']}
           现状: 最近神秘失踪

        3. {companion['name']} - {companion['description']}
           性格: {companion['personality']}
           目标: {companion['goal']}

        故事开场:
        清晨，{main_char['name']}在魔法学院的图书馆里发现了一本奇怪的古书。
        书封面上有一个她从未见过的符号，书页中夹着一封{mentor['name']}留下的神秘信件。
        信件只有一句话："当月亮变成银色时，到遗忘之塔来找我。危险，但必须来。"

        请开始讲述这个故事，描述{main_char['name']}发现古书和信件时的场景，
        以及她决定寻找{mentor['name']}时的内心挣扎。
        保持奇幻冒险的基调，注重细节和氛围营造。
        """

        return prompt

    async def run_story(self, session):
        """运行故事"""
        print("\n4. 运行交互式故事...")
        print("=" * 60)

        # 显示初始故事
        if session.turns:
            last_turn = session.turns[-1]
            print(f"[故事讲述者]\n{last_turn.response}\n")

        # 预定义的玩家输入序列（模拟交互）
        player_inputs = [
            "艾莉亚仔细研究古书上的符号，试图辨认它的含义",
            "她决定去找里奥帮忙，毕竟里奥总是知道该怎么处理奇怪的事情",
            "在去找里奥的路上，艾莉亚注意到学院里的气氛有些不对劲",
            "艾莉亚向里奥展示古书和信件，询问他的意见",
            "他们决定今晚就出发去遗忘之塔，但需要准备一些魔法用品",
            "在魔法用品店，店主警告他们遗忘之塔的危险性",
            "夜幕降临，艾莉亚和里奥悄悄离开学院，踏上寻找导师的旅程"
        ]

        for i, input_text in enumerate(player_inputs, 1):
            print(f"\n[回合 {i}] 玩家: {input_text}")

            try:
                # 添加回合
                turn = await session.add_turn(input_text)

                print(f"[故事讲述者]\n{turn.response}\n")
                print(f"[统计] 令牌: {turn.usage.get('total_tokens', 0)}, "
                      f"成本: ${turn.cost:.6f}")

                # 暂停一下，让阅读更自然
                await asyncio.sleep(1)

            except Exception as e:
                print(f"错误: {e}")
                break

        return session

    async def export_story(self, session):
        """导出故事"""
        print("\n5. 导出故事...")

        exporter = NarrativeExporter()

        # 导出为多种格式
        export_formats = ["markdown", "html", "json"]

        for format in export_formats:
            try:
                output_path = f"magic_apprentice_adventure.{format}"
                await exporter.export_session(session, output_path, format)
                print(f"  ✓ 导出为 {format}: {output_path}")
            except Exception as e:
                print(f"  ✗ 导出 {format} 失败: {e}")

        # 生成统计报告
        stats = {
            "session_id": session.session_id,
            "total_turns": len(session.turns),
            "total_tokens": sum(t.usage.get("total_tokens", 0) for t in session.turns),
            "total_cost": sum(t.cost for t in session.turns),
            "average_turn_length": sum(len(t.response) for t in session.turns) / len(session.turns) if session.turns else 0,
            "start_time": session.created_at.isoformat() if hasattr(session, 'created_at') else datetime.now().isoformat(),
            "end_time": datetime.now().isoformat()
        }

        stats_file = "adventure_stats.json"
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)

        print(f"  ✓ 统计报告: {stats_file}")

        return stats

    async def run_full_example(self):
        """运行完整示例"""
        print("=" * 60)
        print("魔法学徒冒险示例")
        print("=" * 60)

        try:
            # 1. 设置世界
            world = await self.setup_world()

            # 2. 创建角色
            characters = await self.create_characters()

            # 3. 开始冒险
            session = await self.start_adventure(world, characters)

            # 4. 运行故事
            session = await self.run_story(session)

            # 5. 导出故事
            stats = await self.export_story(session)

            print("\n" + "=" * 60)
            print("示例完成!")
            print(f"总回合数: {stats['total_turns']}")
            print(f"总令牌数: {stats['total_tokens']}")
            print(f"总成本: ${stats['total_cost']:.6f}")
            print(f"平均回合长度: {stats['average_turn_length']:.0f} 字符")
            print("=" * 60)

            return session

        except Exception as e:
            print(f"示例运行失败: {e}")
            import traceback
            traceback.print_exc()
            return None

async def main():
    """主函数"""
    # 从环境变量获取API密钥
    import os
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        print("错误: 请设置 OPENAI_API_KEY 环境变量")
        print("示例: export OPENAI_API_KEY='your-api-key'")
        return

    # 创建并运行示例
    adventure = MagicApprenticeAdventure(api_key)
    await adventure.run_full_example()

if __name__ == "__main__":
    asyncio.run(main())

## 高级功能

### 1. 记忆系统

LOOM 的记忆系统允许 AI 记住之前的对话内容：

```python
# 启用记忆
session_config = SessionConfig(
    memory_enabled=True,
    memory_capacity=20,  # 记住最近20条消息
    memory_type="summarization"  # 使用摘要记忆
)

# 自定义记忆权重
memory_weights = {
    "character_details": 1.0,    # 角色细节高权重
    "plot_points": 0.8,          # 情节点中等权重
    "world_facts": 0.6,          # 世界事实中等权重
    "conversation_flow": 0.4     # 对话流程低权重
}

session.set_memory_weights(memory_weights)
```

### 2. 角色一致性

确保角色行为一致：

```python
# 定义角色一致性规则
character_consistency = {
    "艾莉亚": {
        "traits": ["好奇", "善良", "谨慎"],
        "speech_pattern": "使用正式但友好的语气，偶尔表现出不自信",
        "knowledge_limits": ["战斗经验有限", "高级魔法知识不足"],
        "growth_arc": "从缺乏自信到勇敢面对挑战"
    },
    "里奥": {
        "traits": ["勇敢", "忠诚", "冲动"],
        "speech_pattern": "直接、热情、有时鲁莽",
        "knowledge_limits": ["魔法知识有限", "战略思考需要改进"],
        "growth_arc": "学会思考后果，成为可靠的保护者"
    }
}

session.set_character_consistency(character_consistency)
```

### 3. 情节管理

管理故事情节发展：

```python
# 定义情节结构
plot_structure = {
    "act_1": {
        "name": "发现与决定",
        "scenes": [
            "发现古书和信件",
            "寻求朋友帮助",
            "决定出发冒险"
        ],
        "tone": "神秘、犹豫、决心"
    },
    "act_2": {
        "name": "旅程与挑战",
        "scenes": [
            "准备旅程",
            "面对第一个挑战",
            "发现新线索"
        ],
        "tone": "冒险、紧张、成长"
    },
    "act_3": {
        "name": "高潮与解决",
        "scenes": [
            "面对最终挑战",
            "导师的真相",
            "角色成长时刻"
        ],
        "tone": "紧张、情感、解决"
    }
}

session.set_plot_structure(plot_structure)
```

## 故障排除

### 常见问题

#### 1. API 连接问题

```python
# 检查 API 配置
try:
    # 测试连接
    await session.test_connection()
    print("API 连接正常")
except Exception as e:
    print(f"API 连接失败: {e}")
    # 检查环境变量
    import os
    print(f"API_KEY 存在: {bool(os.getenv('OPENAI_API_KEY'))}")
```

#### 2. 记忆丢失问题

```python
# 检查记忆状态
memory_status = session.get_memory_status()
print(f"记忆容量: {memory_status['capacity']}")
print(f"当前记忆数: {memory_status['current_count']}")
print(f"记忆类型: {memory_status['type']}")

# 手动添加重要记忆
await session.add_to_memory(
    content="艾莉亚发现了导师的古老魔法书",
    importance=0.9,  # 高重要性
    category="plot_points"
)
```

#### 3. 角色不一致问题

```python
# 检查角色一致性
inconsistencies = session.check_character_inconsistencies()
if inconsistencies:
    print("发现角色不一致:")
    for inc in inconsistencies:
        print(f"  - {inc['character']}: {inc['issue']}")

    # 修复不一致
    await session.fix_character_inconsistency(
        character="艾莉亚",
        issue="使用了过于自信的语气",
        correction="应使用犹豫但坚定的语气"
    )
```

#### 4. 成本控制

```python
# 监控成本
cost_tracker = session.get_cost_tracker()
print(f"当前成本: ${cost_tracker['current_cost']:.6f}")
print(f"令牌使用: {cost_tracker['tokens_used']}")
print(f"平均每回合成本: ${cost_tracker['average_cost_per_turn']:.6f}")

# 设置成本限制
session.set_cost_limit(max_cost=0.10)  # 最大$0.10
session.set_token_limit(max_tokens=5000)  # 最大5000令牌
```

## 最佳实践

### 1. 提示工程

```python
# 有效的提示结构
good_prompt = """
角色: {角色描述}
目标: {角色目标}
情境: {当前情境}
约束: {叙事约束}
风格: {写作风格}
示例: {示例输出}
"""

# 应用到会话
session_config = SessionConfig(
    initial_prompt=good_prompt.format(
        角色描述="年轻的魔法学徒，聪明但缺乏自信",
        角色目标="找到失踪的导师，掌握空间魔法",
        当前情境="在图书馆发现神秘古书",
        叙事约束="保持奇幻基调，注重角色成长",
        写作风格="描述性、情感丰富、节奏适中",
        示例输出="艾莉亚的手指轻轻拂过古书的皮革封面..."
    )
)
```

### 2. 会话管理

```python
# 定期保存会话
import asyncio

async def auto_save_session(session, interval_minutes=5):
    """自动保存会话"""
    while True:
        await asyncio.sleep(interval_minutes * 60)
        await session_manager.save_session(session)
        print(f"会话已自动保存: {datetime.now().isoformat()}")

# 会话版本控制
session.create_checkpoint("before_climax")
# 如果需要回滚
session.restore_checkpoint("before_climax")
```

### 3. 性能优化

```python
# 批量处理
async def batch_process_turns(session, inputs):
    """批量处理多个回合"""
    tasks = []
    for input_text in inputs:
        task = session.add_turn(input_text)
        tasks.append(task)

    # 并行处理
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # 处理结果
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(f"回合 {i} 失败: {result}")
        else:
            print(f"回合 {i} 成功: {result.usage['total_tokens']} 令牌")

# 缓存优化
session.enable_caching(
    cache_ttl=300,  # 5分钟缓存
    cache_size=100  # 最多缓存100条
)
```

## 扩展学习

### 1. 学习资源

- [LOOM 官方文档](../index.md): 完整的功能文档
- [API 使用指南](../api-usage/api-examples.md): API 详细示例
- [配置指南](../configuration/config-files.md): 配置文件详解
- [CLI 参考](../cli-reference/basic-commands.md): 命令行工具使用

### 2. 进阶主题

- **多角色对话**: 管理多个 AI 角色的复杂对话
- **动态世界生成**: 根据玩家选择动态生成世界内容
- **情感分析集成**: 分析玩家情感并调整叙事
- **语音合成**: 将文本叙事转换为语音

### 3. 社区示例

访问 LOOM 社区获取更多示例：
- GitHub: https://github.com/your-org/loom/examples
- Discord: #examples 频道
- 论坛: "实践示例"板块

## 下一步

完成基础叙事学习后，您可以：

1. **尝试奇幻示例**: 学习更复杂的奇幻世界构建
2. **探索科幻示例**: 了解科幻叙事的特殊要求
3. **学习交互式示例**: 掌握玩家干预和动态叙事
4. **创建自定义示例**: 基于您的需求构建专属叙事系统

祝您在 LOOM 的叙事之旅中创作出精彩的故事！
