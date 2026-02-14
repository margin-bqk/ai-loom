# LOOM 世界构建指南

## 简介
本指南将帮助您使用 LOOM 系统创建和管理互动叙事世界。无论您是游戏设计师、作家还是互动叙事爱好者，本指南都将为您提供构建丰富、一致且引人入胜的世界的工具和方法。

## 1. 世界构建基础

### 1.1 确定世界类型
- **奇幻世界**: 魔法、神话生物、中世纪技术
- **科幻世界**: 先进科技、太空旅行、外星文明
- **现实世界**: 历史、现代、近未来
- **混合世界**: 结合多种元素的独特设定

### 1.2 核心元素
每个世界都应包含以下核心元素：

1. **地理环境**: 地形、气候、自然资源
2. **社会结构**: 政府、经济、文化、宗教
3. **历史背景**: 重要事件、历史人物、文化演变
4. **科技/魔法系统**: 世界的特殊规则和能力
5. **主要冲突**: 驱动叙事的核心矛盾

## 2. 使用 LOOM 创建世界

### 2.1 初始化项目
```bash
# 使用 CLI 工具创建新世界
loom init my_fantasy_world --type fantasy

# 进入项目目录
cd my_fantasy_world
```

### 2.2 配置世界设置
编辑 `config/world_config.yaml` 文件：
```yaml
world:
  name: "艾瑟兰大陆"
  description: "一个充满魔法与冒险的奇幻世界"
  genre: "fantasy"

characters:
  - name: "艾莉亚"
    role: "主角"
    description: "年轻的法师学徒"

locations:
  - name: "法师塔"
    description: "位于山顶的古老建筑"
```

### 2.3 定义规则
创建规则文件 `rules/world_rules.md`：
```markdown
# 世界规则

## 魔法规则
- 魔法需要消耗魔力
- 强大魔法需要吟唱时间
- 魔法反噬可能发生

## 物理规则
- 重力与地球相似
- 存在四季变化
- 日夜循环为24小时
```

## 3. 角色创建与管理

### 3.1 角色设计原则
1. **背景故事**: 角色的过去经历和动机
2. **性格特质**: 核心性格特征和行为模式
3. **能力技能**: 角色擅长的领域和特殊能力
4. **人际关系**: 与其他角色的联系和情感

### 3.2 使用 LOOM 管理角色
```bash
# 查看所有角色
loom session list-characters

# 添加新角色
loom session add-character --name "雷纳德" --role "导师"

# 更新角色信息
loom session update-character --name "艾莉亚" --trait "勇敢"
```

## 4. 规则系统设计

### 4.1 规则类型
- **硬性规则**: 必须遵守的物理/魔法定律
- **软性规则**: 可以灵活解释的社会/文化规范
- **叙事规则**: 影响故事发展的创作原则

### 4.2 规则一致性检查
LOOM 提供自动一致性检查：
```bash
# 检查规则一致性
loom rules check --file rules/world_rules.md

# 验证规则冲突
loom rules validate --all
```

## 5. 会话管理

### 5.1 开始新会话
```bash
# 启动交互式会话
loom run --world my_fantasy_world --character "艾莉亚"

# 使用特定规则集
loom run --rules rules/fantasy_basic.md

# 批量运行会话
loom run --batch --scenario "quest_start"
```

### 5.2 会话控制
- **暂停/继续**: 按 Ctrl+C 暂停，输入 `continue` 继续
- **保存进度**: 自动保存到 `sessions/` 目录
- **导出会话**: 导出为 JSON、Markdown 或 PDF 格式

## 6. 玩家干预与编辑

### 6.1 玩家干预类型
1. **建议**: 提供叙事方向建议
2. **修正**: 纠正事实错误或不一致
3. **重述**: 要求重新描述场景或事件
4. **编辑**: 直接修改世界状态

### 6.2 使用干预工具
```bash
# 查看可用的干预选项
loom intervention list

# 应用玩家干预
loom intervention apply --type "retcon" --description "修正时间线错误"

# 查看干预历史
loom intervention history
```

## 7. 记忆与连续性

### 7.1 记忆系统
LOOM 自动跟踪：
- 角色对话和行动
- 重要事件和决定
- 世界状态变化
- 规则应用历史

### 7.2 记忆查询
```bash
# 查询特定事件的记忆
loom memory query --event "龙之袭击"

# 查看角色关系发展
loom memory relationships --character "艾莉亚"

# 导出记忆数据
loom memory export --format json
```

## 8. 高级功能

### 8.1 多世界管理
```bash
# 切换不同世界
loom config set-world another_world

# 比较世界差异
loom world compare world1 world2

# 合并世界元素
loom world merge --source world1 --target world2
```

### 8.2 插件扩展
LOOM 支持插件系统：
```python
# 示例插件：自定义规则检查器
from loom.plugins import RulePlugin

class CustomRuleChecker(RulePlugin):
    def check_consistency(self, rule_text):
        # 实现自定义检查逻辑
        pass
```

## 9. 最佳实践

### 9.1 世界构建技巧
1. **从小处开始**: 先构建核心区域，再扩展
2. **保持一致性**: 定期检查规则和事实一致性
3. **留有余地**: 为意外发展和玩家创意留出空间
4. **迭代改进**: 根据反馈不断优化世界设定

### 9.2 性能优化
1. **规则精简**: 避免过于复杂的规则系统
2. **记忆管理**: 定期清理不重要的记忆数据
3. **批量处理**: 使用批量模式处理大量数据
4. **缓存利用**: 启用缓存提高响应速度

## 10. 故障排除

### 常见问题
1. **规则冲突**: 使用 `loom rules validate` 检查
2. **记忆丢失**: 检查存储路径和权限
3. **性能下降**: 清理缓存和优化规则
4. **API错误**: 验证 LLM 提供商配置

### 获取帮助
```bash
# 查看帮助文档
loom --help

# 查看特定命令帮助
loom run --help

# 报告问题
loom dev report-issue --description "详细描述问题"
```

## 11. 下一步
- 查看 [示例项目](examples/full_example/) 获取完整示例
- 探索 [模板库](templates/) 获取预构建模板
- 阅读 [API文档](docs/API_REFERENCE.md) 了解高级功能
- 加入社区获取更多资源和帮助

---

*本指南将持续更新。如有问题或建议，请通过 GitHub Issues 提交反馈。*
