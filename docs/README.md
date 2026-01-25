# LOOM 文档

欢迎使用 LOOM（Language-Oriented Open Mythos）文档。LOOM 是一个基于 Markdown 规则的非承载式叙事引擎，采用五层架构设计。

## 文档目录

### 核心概念
- [架构概述](ARCHITECTURE.md) - 五层架构详细说明
- [API 参考](API_REFERENCE.md) - 各层接口和使用方法
- [快速开始](#快速开始) - 立即开始使用 LOOM

### 用户指南
- [规则编写指南](#规则编写指南) - 如何编写有效的 Markdown 规则
- [会话管理](#会话管理) - 创建和管理叙事会话
- [干预系统](#干预系统) - 使用玩家干预功能
- [记忆系统](#记忆系统) - 世界记忆的管理和使用

### 开发者文档
- [代码结构](#代码结构) - 项目目录结构说明
- [扩展开发](#扩展开发) - 如何扩展 LOOM 功能
- [测试指南](#测试指南) - 运行和编写测试

## 快速开始

### 安装
```bash
# 克隆仓库
git clone https://github.com/your-org/loom.git
cd loom

# 安装依赖
pip install -e .
```

### 创建第一个会话
```python
from loom import SessionManager, RuleLoader

# 加载规则
rule_loader = RuleLoader("./canon")
canon = rule_loader.load_canon("basic_world")

# 创建会话
session_manager = SessionManager()
session = await session_manager.create_session({
    "name": "我的第一个冒险",
    "canon": canon
})

# 进行回合
response = await session.process_turn("我走进森林，寻找隐藏的宝藏")
print(response)
```

### 编写规则
创建 `canon/my_world.md`：
```markdown
# 世界观
这是一个奇幻世界，有魔法和巨龙。

# 叙事基调
冒险风格，带有幽默元素。

# 权限边界
玩家可以探索世界，但不能无故伤害NPC。
```

## 规则编写指南

### 基本结构
LOOM 规则使用标准 Markdown 格式，建议包含以下章节：

1. **世界观 (World)** - 世界设定、物理法则、种族文化
2. **叙事基调 (Tone)** - 故事风格、情绪范围
3. **冲突解决 (Conflict)** - 如何解决游戏中的冲突
4. **权限边界 (Permissions)** - 玩家可以/不可以做什么
5. **因果关系 (Causality)** - 时间、死亡、因果规则
6. **元信息 (Meta)** - 版本、作者、使用说明

### 最佳实践
- 使用清晰的语言，避免歧义
- 提供具体示例帮助 LLM 理解
- 保持规则一致性
- 版本控制你的规则文件

## 会话管理

### 会话生命周期
1. **创建会话** - 基于规则集创建新会话
2. **加载会话** - 从存储加载现有会话
3. **处理回合** - 玩家输入 → LLM 处理 → 叙事输出
4. **保存会话** - 保存会话状态和记忆
5. **结束会话** - 清理资源，生成摘要

### 会话配置
```yaml
session_config:
  name: "史诗冒险"
  canon_path: "./canon/fantasy.md"
  llm_provider: "openai"
  memory_backend: "sqlite"
  auto_save: true
```

## 干预系统

### 干预类型
LOOM 支持多种玩家干预：

1. **OOC 注释** - `(OOC: 这是元评论)`
2. **世界编辑** - `[EDIT: 角色: 添加技能: 剑术]`
3. **Retcon** - `[RETCON: 事实: 修改内容 (理由)]`
4. **基调调整** - `[TONE: 更严肃一些]`
5. **意图声明** - `[INTENT: 我想探索山洞]`

### 干预处理流程
```
玩家输入 → 干预解析 → 权限验证 → 执行干预 → 更新状态 → 记录审计
```

## 记忆系统

### 记忆类型
- **角色记忆** - NPC 和玩家角色信息
- **地点记忆** - 场景和环境描述
- **事实记忆** - 世界事实和知识
- **事件记忆** - 发生的重要事件
- **关系记忆** - 实体间的关系

### 记忆检索
LOOM 使用混合检索系统：
1. **关键词检索** - 基于文本匹配
2. **语义检索** - 基于向量相似度（可选）
3. **时间检索** - 基于时间相关性
4. **关系检索** - 基于实体关系网络

## 代码结构

```
loom/
├── src/loom/                    # 主源代码
│   ├── core/                   # 运行时核心层
│   ├── rules/                  # 规则层
│   ├── interpretation/         # 解释层
│   ├── memory/                 # 世界记忆层
│   ├── intervention/           # 玩家干预层
│   └── utils/                  # 工具函数
├── tests/                      # 测试代码
├── examples/                   # 示例文件
├── config/                     # 配置文件
├── docs/                       # 文档
└── scripts/                    # 工具脚本
```

## 扩展开发

### 插件系统
LOOM 支持通过插件扩展功能：

1. **LLM 提供商插件** - 添加新的 LLM 后端
2. **记忆后端插件** - 添加新的存储后端
3. **规则验证插件** - 自定义规则验证逻辑
4. **干预类型插件** - 添加新的干预类型

### 创建插件
```python
from loom.plugins import LoomPlugin

class MyPlugin(LoomPlugin):
    def initialize(self, config):
        # 初始化插件
        pass
    
    def process(self, data):
        # 处理数据
        return processed_data
```

## 测试指南

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest tests/test_core/

# 带覆盖率报告
pytest --cov=loom --cov-report=html
```

### 编写测试
```python
import pytest
from loom.core import SessionManager

@pytest.mark.asyncio
async def test_session_creation():
    manager = SessionManager()
    session = await manager.create_session({"name": "测试会话"})
    assert session.id is not None
    assert session.name == "测试会话"
```

## 获取帮助

### 常见问题
1. **Q: LLM 响应不符合规则怎么办？**
   A: 检查规则是否明确，尝试添加更多示例，使用一致性检查功能。

2. **Q: 记忆检索不准确怎么办？**
   A: 调整检索参数，启用向量存储，优化记忆摘要。

3. **Q: 如何提高性能？**
   A: 启用缓存，调整并发设置，使用更高效的 LLM 模型。

### 社区支持
- [GitHub Issues](https://github.com/your-org/loom/issues) - 报告问题和功能请求
- [Discord 频道](https://discord.gg/loom) - 实时讨论和帮助
- [文档 Wiki](https://github.com/your-org/loom/wiki) - 社区维护的文档

## 许可证

LOOM 采用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。

## 贡献指南

我们欢迎贡献！请阅读 [CONTRIBUTING.md](../CONTRIBUTING.md) 了解如何参与项目开发。

---

*LOOM - 让每个故事都有生命*