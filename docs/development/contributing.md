# LOOM 贡献指南

感谢您对 LOOM 项目的关注！我们欢迎各种形式的贡献，包括但不限于代码、文档、测试、示例和反馈。

## 1. 开始之前

### 1.1 行为准则
请阅读并遵守我们的 [行为准则](CODE_OF_CONDUCT.md)。我们致力于提供一个友好、包容的社区环境。

### 1.2 获取帮助
- **问题讨论**: 使用 [GitHub Discussions](https://github.com/loom-project/loom/discussions)
- **错误报告**: 使用 [GitHub Issues](https://github.com/loom-project/loom/issues)
- **实时交流**: 加入我们的 [Discord 社区](https://discord.gg/loom)

## 2. 开发环境设置

### 2.1 克隆仓库
```bash
git clone https://github.com/loom-project/loom.git
cd loom
```

### 2.2 安装依赖
```bash
# 使用 pip
pip install -e ".[dev]"

# 或使用 poetry
poetry install
```

### 2.3 环境配置
```bash
# 复制环境变量示例
cp .env.example .env

# 编辑 .env 文件，添加您的 API 密钥
# OPENAI_API_KEY=your_key_here
# ANTHROPIC_API_KEY=your_key_here
```

### 2.4 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_core/test_session_manager.py

# 运行测试并生成覆盖率报告
pytest --cov=src.loom --cov-report=html
```

## 3. 贡献流程

### 3.1 创建分支
```bash
# 从 main 分支创建新分支
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# 或修复 bug
git checkout -b fix/issue-number-description
```

### 3.2 分支命名规范
- `feature/`: 新功能
- `fix/`: bug 修复
- `docs/`: 文档更新
- `test/`: 测试相关
- `refactor/`: 代码重构
- `style/`: 代码风格调整

### 3.3 开发指南

#### 代码风格
- 遵循 PEP 8 规范
- 使用 Black 格式化代码
- 使用 isort 排序导入
- 使用 mypy 进行类型检查

```bash
# 格式化代码
black src/ tests/

# 排序导入
isort src/ tests/

# 类型检查
mypy src/
```

#### 提交信息规范
使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

```
<类型>[可选 范围]: <描述>

[可选 正文]

[可选 脚注]
```

类型包括：
- `feat`: 新功能
- `fix`: bug 修复
- `docs`: 文档更新
- `style`: 代码风格调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建过程或辅助工具变动

示例：
```
feat(cli): 添加会话导出功能

- 支持 JSON、Markdown、YAML 格式导出
- 添加导出进度显示
- 优化导出性能

Closes #123
```

### 3.4 测试要求
- 新功能必须包含单元测试
- bug 修复必须包含回归测试
- 测试覆盖率不应降低
- 使用 pytest 和 pytest-asyncio

### 3.5 文档更新
- 更新相关文档
- 添加代码注释和文档字符串
- 更新示例代码
- 考虑向后兼容性

## 4. 提交 Pull Request

### 4.1 准备工作
1. 确保代码通过所有测试
2. 更新 CHANGELOG.md（如果适用）
3. 更新文档
4. 确保提交信息规范

### 4.2 创建 PR
1. 推送分支到远程仓库
2. 在 GitHub 上创建 Pull Request
3. 填写 PR 模板
4. 关联相关 Issue

### 4.3 PR 模板
```markdown
## 描述
简要描述此 PR 的更改内容。

## 相关 Issue
关联的 Issue 编号，例如：Closes #123

## 更改类型
- [ ] Bug 修复
- [ ] 新功能
- [ ] 文档更新
- [ ] 代码重构
- [ ] 测试更新
- [ ] 其他（请说明）

## 测试
- [ ] 已添加单元测试
- [ ] 已通过所有现有测试
- [ ] 已手动测试

## 检查清单
- [ ] 代码遵循项目风格指南
- [ ] 已更新相关文档
- [ ] 已添加或更新测试
- [ ] 提交信息遵循规范
```

### 4.4 代码审查
- 至少需要一名维护者批准
- 解决所有审查意见
- 确保 CI 通过
- 保持友好的讨论氛围

## 5. 贡献类型

### 5.1 代码贡献
- 实现新功能
- 修复 bug
- 性能优化
- 代码重构

### 5.2 文档贡献
- 修复拼写错误
- 改进文档结构
- 添加使用示例
- 翻译文档

### 5.3 测试贡献
- 添加单元测试
- 添加集成测试
- 提高测试覆盖率
- 改进测试工具

### 5.4 示例贡献
- 创建新的示例项目
- 改进现有示例
- 添加模板
- 创建教程

### 5.5 插件贡献
- 开发新插件
- 改进插件系统
- 创建插件示例
- 编写插件文档

## 6. 项目结构

### 6.1 目录结构
```
loom/
├── src/loom/                    # 源代码
│   ├── core/                   # 核心模块
│   ├── interpretation/         # 规则解释
│   ├── intervention/           # 玩家干预
│   ├── memory/                # 记忆系统
│   ├── rules/                 # 规则管理
│   ├── plugins/               # 插件系统
│   ├── api/                   # API 客户端
│   └── cli/                   # CLI 工具
├── tests/                     # 测试代码
├── examples/                  # 示例项目
├── docs/                      # 文档
├── scripts/                   # 工具脚本
└── config/                    # 配置文件
```

### 6.2 代码组织原则
- 单一职责原则
- 依赖注入
- 异步优先
- 类型安全
- 可测试性

## 7. 开发工具

### 7.1 预提交钩子
项目配置了 pre-commit 钩子，自动检查代码质量：

```bash
# 安装 pre-commit
pre-commit install

# 手动运行所有钩子
pre-commit run --all-files
```

### 7.2 CI/CD 流程
GitHub Actions 自动运行：
- 单元测试
- 代码风格检查
- 类型检查
- 安全扫描
- 文档构建

### 7.3 调试工具
```python
# 使用内置调试工具
from src.loom.utils.logging_config import setup_logging
setup_logging(level="DEBUG")

# 使用 CLI 调试模式
loom dev debug --session session_id
```

## 8. 发布流程

### 8.1 版本管理
使用语义化版本控制：
- `MAJOR`: 不兼容的 API 变更
- `MINOR`: 向后兼容的功能性新增
- `PATCH`: 向后兼容的 bug 修复

### 8.2 发布检查清单
- [ ] 更新版本号
- [ ] 更新 CHANGELOG.md
- [ ] 运行完整测试套件
- [ ] 构建文档
- [ ] 创建发布标签
- [ ] 发布到 PyPI

## 9. 社区角色

### 9.1 贡献者
- 提交代码、文档或测试
- 报告 bug 或提出建议
- 帮助其他用户

### 9.2 维护者
- 审查和合并 PR
- 管理 Issue 和项目
- 发布新版本
- 指导新贡献者

### 9.3 核心团队
- 制定项目方向
- 管理社区
- 确保项目可持续发展

## 10. 获取帮助

### 10.1 学习资源
- [官方文档](https://docs.loom.dev)
- [API 参考](docs/API_REFERENCE.md)
- [示例项目](examples/)
- [开发博客](https://blog.loom.dev)

### 10.2 支持渠道
- **GitHub Issues**: 技术问题和 bug 报告
- **GitHub Discussions**: 功能讨论和问题解答
- **Discord**: 实时交流和社区支持
- **Stack Overflow**: 使用问题和技术问答

### 10.3  mentorship 计划
我们为新的贡献者提供 mentorship：
- 一对一指导
- 代码审查帮助
- 项目导航
- 职业发展建议

联系维护者了解更多信息。

## 11. 致谢

感谢所有贡献者的付出！您的贡献使 LOOM 变得更好。

### 11.1 贡献者名单
查看 [CONTRIBUTORS.md](CONTRIBUTORS.md) 了解所有贡献者。

### 11.2 特别感谢
- 项目创始人和核心团队
- 早期采用者和测试者
- 文档翻译志愿者
- 社区管理者

---

## 附录

### A. 开发环境故障排除

#### 常见问题
1. **依赖安装失败**
   ```bash
   # 清理缓存
   pip cache purge
   # 使用虚拟环境
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

2. **测试失败**
   ```bash
   # 检查环境变量
   echo $OPENAI_API_KEY
   # 运行单个测试调试
   pytest tests/test_core/test_session_manager.py::TestSessionManager::test_create_session -v
   ```

3. **代码风格检查失败**
   ```bash
   # 自动修复
   black src/loom/
   isort src/loom/
   ```

### B. 贡献者协议
通过向本项目提交贡献，您同意：
1. 您的贡献将在 MIT 许可证下发布
2. 您拥有提交代码的合法权利
3. 您已阅读并同意行为准则

### C. 许可证
LOOM 使用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

---

*本指南将持续更新。如有问题或建议，请通过 GitHub Issues 提交反馈。*
