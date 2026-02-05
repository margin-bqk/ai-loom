# 第一个示例

## 概述

本文档将引导您完成 LOOM 的第一个完整示例。我们将创建一个简单的奇幻世界会话，体验 LOOM 的核心功能。

## 示例目标

通过本示例，您将学习到：

1. 如何创建和加载规则文件
2. 如何启动交互式会话
3. 如何进行基本的玩家干预
4. 如何查看会话历史
5. 如何导出会话结果

## 准备工作

### 1. 确保 LOOM 已安装

```bash
# 检查安装
loom --version

# 预期输出：loom 0.10.0
```

### 2. 配置 LLM 提供商

确保至少配置了一个 LLM 提供商。如果您还没有配置，可以：

```bash
# 设置环境变量（临时）
export OPENAI_API_KEY="sk-your-openai-api-key"

# 或者编辑 .env 文件
echo "OPENAI_API_KEY=sk-your-openai-api-key" >> .env
```

### 3. 准备规则文件

我们将使用内置的奇幻世界模板：

```bash
# 查看可用规则模板
ls templates/rules/

# 预期输出：
# fantasy_basic.md
# sci_fi_basic.md
```

## 示例 1：基础交互式会话

### 步骤 1：启动会话

```bash
# 启动交互式会话
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --name "我的第一个奇幻世界" \
  --provider openai \
  --max-turns 5
```

### 步骤 2：交互过程

启动后，您将看到类似以下输出：

```
========================================
LOOM 交互式会话启动
========================================
会话名称: 我的第一个奇幻世界
规则文件: templates/rules/fantasy_basic.md
LLM 提供商: openai (gpt-3.5-turbo)
最大回合数: 5
========================================

世界已加载: 奇幻世界基础规则模板
时代背景: 中世纪
魔法系统: 元素魔法、奥术魔法、治疗魔法、召唤魔法
主要种族: 人类、精灵、矮人、兽人

请输入您的行动 (或输入 'help' 查看命令):
```

### 步骤 3：输入行动

尝试以下输入：

```
我是一名年轻的冒险者，刚刚来到这个小镇。我想了解这里有什么特别的地方。
```

### 步骤 4：查看响应

LOOM 将生成类似以下的响应：

```
欢迎来到风语镇，年轻的冒险者！这是一个位于艾瑟兰大陆边缘的小镇，以它的风车和古老的预言而闻名。

特别的地方包括：
1. **风车广场** - 镇中心，商贩聚集的地方
2. **预言者之塔** - 据说能预知未来的古老建筑
3. **铁匠铺** - 老铁匠格鲁姆的店铺，他打造的武器很有名
4. **旅店"沉睡巨龙"** - 旅行者和冒险者常去的地方

您想先去哪里看看？
```

### 步骤 5：继续对话

您可以继续输入：

```
我想先去预言者之塔看看。
```

### 步骤 6：结束会话

输入 `exit` 或 `quit` 结束会话：

```
exit
```

会话将自动保存，并显示摘要信息。

## 示例 2：使用玩家干预

### 步骤 1：启动带详细日志的会话

```bash
loom run interactive \
  --canon templates/rules/fantasy_basic.md \
  --name "干预示例" \
  --provider openai \
  --verbose
```

### 步骤 2：使用 OOC 注释

在输入中使用 `(( ))` 进行 Out-of-Character 注释：

```
我想去铁匠铺看看有什么好武器。((注意：我的角色对魔法武器特别感兴趣))
```

### 步骤 3：使用世界编辑

输入 `!edit` 命令修改世界状态：

```
!edit 添加一个新地点：魔法泉水，位于小镇北边的森林里，据说有治愈效果。
```

### 步骤 4：查看编辑结果

系统将确认编辑并更新世界状态。

### 步骤 5：使用 Retcon

如果需要修正之前的叙述：

```
!retcon 修正：铁匠铺的老铁匠名字应该是"格鲁姆·铁砧"，不是"格鲁姆"。
```

## 示例 3：批处理运行

### 步骤 1：准备输入文件

创建 `input.txt`：

```txt
我来到风语镇，想找一份工作。
我听说镇长的仓库需要守卫。
我决定去应聘仓库守卫。
我成功获得了这份工作。
第一天晚上，我听到仓库里有奇怪的声音。
```

### 步骤 2：运行批处理

```bash
loom run batch \
  --canon templates/rules/fantasy_basic.md \
  --input input.txt \
  --output output.txt \
  --name "批处理示例"
```

### 步骤 3：查看结果

```bash
# 查看输出
cat output.txt

# 或者查看格式化输出
loom session show --name "批处理示例" --format json
```

## 示例 4：完整示例项目

LOOM 包含一个完整的示例项目，展示了更复杂的使用场景。

### 步骤 1：进入示例目录

```bash
cd examples/full_example
```

### 步骤 2：查看项目结构

```bash
tree .
# 预期结构：
# .
# ├── config
# │   └── world_config.yaml
# ├── rules
# │   └── fantasy_world.md
# └── run_example.py
```

### 步骤 3：运行示例

```bash
python run_example.py
```

### 步骤 4：查看示例输出

示例将展示：
1. 世界配置加载
2. 角色创建和初始化
3. 多回合交互
4. 记忆系统使用
5. 会话导出

## 常用命令参考

### 会话管理命令

```bash
# 列出所有会话
loom session list

# 查看特定会话
loom session show --name "我的第一个奇幻世界"

# 继续现有会话
loom run continue --session-id <session_id>

# 删除会话
loom session delete --name "测试会话"
```

### 导出和导入

```bash
# 导出会话为 Markdown
loom export markdown --session-name "我的第一个奇幻世界" --output session.md

# 导出会话为 JSON
loom export json --session-name "我的第一个奇幻世界" --output session.json

# 导入会话
loom import --file session.json --name "恢复的会话"
```

### 调试命令

```bash
# 查看详细日志
loom run interactive --verbose

# 查看推理过程
loom run interactive --debug-reasoning

# 查看性能指标
loom run interactive --monitor-performance
```

## 故障排除

### 1. 会话启动失败

```bash
# 检查规则文件
cat templates/rules/fantasy_basic.md | head -20

# 检查提供商连接
loom config test --provider openai

# 查看日志
tail -f logs/loom.log
```

### 2. 响应质量不佳

```bash
# 尝试不同模型
loom run interactive --provider openai --model gpt-4

# 调整温度参数
loom config set llm.openai.temperature 0.5

# 使用更详细的规则文件
cp examples/full_example/rules/fantasy_world.md my_rules.md
loom run interactive --canon my_rules.md
```

### 3. 性能问题

```bash
# 启用缓存
loom config set llm.openai.enable_caching true

# 减少最大令牌数
loom config set llm.openai.max_tokens 500

# 使用本地模型
loom run interactive --provider ollama --model llama2
```

## 下一步学习

完成第一个示例后，您可以：

1. **创建自定义规则**: 查看 [规则编写指南](../reference/world-building-guide.md)
2. **学习高级功能**: 查看 [用户指南](../user-guide/getting-started.md)
3. **探索 API 使用**: 查看 [API 使用指南](../user-guide/api-usage/quick-api-start.md)
4. **了解开发扩展**: 查看 [开发指南](../development/setup-development.md)

## 示例代码片段

### Python API 使用示例

```python
import asyncio
from loom.core.session_manager import SessionManager
from loom.core.config_manager import ConfigManager

async def run_example():
    # 初始化配置
    config = ConfigManager()
    
    # 创建会话管理器
    session_manager = SessionManager(config)
    
    # 创建新会话
    session = await session_manager.create_session(
        name="Python API 示例",
        canon_path="templates/rules/fantasy_basic.md"
    )
    
    # 执行行动
    response = await session.execute_action(
        "我来到风语镇，想找一份冒险者工作。"
    )
    
    print(f"响应: {response}")
    
    # 保存会话
    await session.save()

# 运行示例
asyncio.run(run_example())
```

### 规则文件示例

创建自定义规则文件 `my_world.md`：

```markdown
# 我的自定义世界

## 世界设定
- **世界名称**: 星尘王国
- **时代背景**: 蒸汽朋克奇幻
- **魔法系统**: 蒸汽魔法 - 魔法通过蒸汽机械释放
- **主要种族**: 人类、机械侏儒、蒸汽精灵

## 核心规则
1. 魔法需要蒸汽能量驱动
2. 科技与魔法可以结合
3. 每个角色都有独特的蒸汽核心
4. 世界中有漂浮的蒸汽岛屿

## 角色创建
- 选择种族和职业
- 分配蒸汽核心属性
- 定义背景故事
- 设置初始装备
```

使用自定义规则运行：

```bash
loom run interactive --canon my_world.md --name "蒸汽朋克冒险"
```

---

> 提示：尝试修改规则文件，观察对会话行为的影响。这是理解 LOOM "叙事失明" 架构的好方法。
