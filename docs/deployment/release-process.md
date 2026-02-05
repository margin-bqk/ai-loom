# LOOM 发布流程

本文档描述了 LOOM 项目的标准发布流程，确保每次发布都可靠、可重复且符合质量要求。

## 发布周期

LOOM 采用语义化版本控制（SemVer）：
- **主版本号 (X)**：不兼容的 API 变更
- **次版本号 (Y)**：向后兼容的功能性新增
- **修订号 (Z)**：向后兼容的问题修复

发布频率：
- **修订版本**：根据需要发布，通常用于紧急修复
- **次版本**：每 1-2 个月发布一次
- **主版本**：当有重大架构变更时发布

## 发布角色

| 角色 | 职责 |
|------|------|
| **发布经理** | 协调发布流程，确保所有步骤完成 |
| **开发团队** | 完成功能开发，编写测试，更新文档 |
| **质量保证** | 执行测试，验证发布候选版本 |
| **运维团队** | 部署到生产环境，监控发布过程 |

## 发布前准备（开发阶段）

### 1. 功能冻结
- 在预定发布日期前 3 天进入功能冻结期
- 只允许修复关键 bug，不允许新增功能
- 更新 `CHANGELOG.md`，记录所有变更

### 2. 代码质量检查
```bash
# 运行所有测试
pytest

# 检查测试覆盖率（要求 >= 85%）
pytest --cov=src.loom --cov-report=html

# 代码格式化
black src/ tests/

# 类型检查
mypy src/

# 代码风格检查
flake8 src/

# 安全检查
bandit -r src/
safety check
```

### 3. 文档更新
- 更新 `README.md` 中的版本号和功能描述
- 更新 `docs/` 目录下的所有相关文档
- 确保所有示例代码都能正常运行
- 更新 API 文档（如有）

## 发布流程

### 阶段 1：版本准备

1. **确定版本号**
   - 根据变更类型确定版本号增量
   - 更新 `pyproject.toml` 中的版本号
   - 更新 `src/loom/__init__.py` 中的 `__version__`

2. **更新变更日志**
   - 将 `CHANGELOG.md` 中的 "[未发布]" 部分重命名为新版本
   - 添加发布日期
   - 确保所有变更项都已记录

3. **创建发布分支**
   ```bash
   git checkout -b release/vX.Y.Z
   git add .
   git commit -m "准备发布 vX.Y.Z"
   git push origin release/vX.Y.Z
   ```

### 阶段 2：构建和测试

1. **构建发布包**
   ```bash
   # 安装构建工具
   pip install build twine
   
   # 构建包
   python -m build
   
   # 验证包
   twine check dist/*
   ```

2. **测试安装**
   ```bash
   # 创建虚拟环境测试
   python -m venv test-venv
   source test-venv/bin/activate  # Linux/Mac
   # 或 test-venv\Scripts\activate  # Windows
   
   # 安装构建的包
   pip install dist/loom-X.Y.Z-py3-none-any.whl
   
   # 验证安装
   loom --version
   loom --help
   
   # 运行基础测试
   python -m pytest tests/test_core/ -v
   ```

3. **Docker 构建测试**
   ```bash
   docker build -t loom:X.Y.Z .
   docker run -d -p 8000:8000 --name loom-test loom:X.Y.Z
   # 验证容器运行
   curl http://localhost:8000/health
   docker stop loom-test
   docker rm loom-test
   ```

### 阶段 3：预发布验证

1. **端到端测试**
   - 运行完整的示例项目
   - 测试所有 CLI 命令
   - 验证 Web 界面功能

2. **性能测试**
   - 运行性能测试套件
   - 检查内存使用情况
   - 验证响应时间

3. **安全扫描**
   - 运行漏洞扫描
   - 检查依赖项安全公告
   - 验证配置安全性

### 阶段 4：发布

1. **创建 Git 标签**
   ```bash
   git tag -a vX.Y.Z -m "Release vX.Y.Z"
   git push origin vX.Y.Z
   ```

2. **合并到主分支**
   ```bash
   git checkout main
   git merge --no-ff release/vX.Y.Z
   git push origin main
   ```

3. **发布到 PyPI**
   ```bash
   twine upload dist/*
   ```

4. **发布 Docker 镜像**
   ```bash
   docker tag loom:X.Y.Z yourregistry/loom:X.Y.Z
   docker tag loom:X.Y.Z yourregistry/loom:latest
   docker push yourregistry/loom:X.Y.Z
   docker push yourregistry/loom:latest
   ```

5. **创建 GitHub Release**
   - 在 GitHub 上创建 Release
   - 上传构建产物（wheel 和 tar.gz）
   - 添加发布说明（从 CHANGELOG 复制）
   - 标记为预发布或正式发布

### 阶段 5：部署

1. **部署到测试环境**
   - 使用新版本更新测试环境
   - 运行冒烟测试
   - 验证所有功能正常

2. **部署到生产环境**
   - 使用蓝绿部署或金丝雀发布
   - 监控关键指标
   - 准备回滚计划

3. **验证生产环境**
   - 检查健康端点
   - 验证核心功能
   - 监控错误率

### 阶段 6：发布后

1. **更新文档网站**
   ```bash
   mkdocs build
   mkdocs gh-deploy
   ```

2. **发送发布公告**
   - 更新项目状态页面
   - 发送邮件通知
   - 在社区渠道发布公告

3. **清理**
   - 删除发布分支
   - 更新项目路线图
   - 安排下一次发布计划

## 紧急发布流程

对于紧急修复，使用简化流程：

1. **创建热修复分支**
   ```bash
   git checkout -b hotfix/vX.Y.Z
   ```

2. **应用修复并测试**
   - 只修复关键问题
   - 运行最小测试集

3. **快速发布**
   - 跳过部分非关键检查
   - 直接发布到生产环境
   - 事后补充完整测试

4. **合并回开发分支**
   - 将热修复合并到 main 和 develop 分支

## 自动化发布

使用发布脚本简化流程：

```bash
# 运行完整发布流程
python scripts/release.py release

# 仅构建
python scripts/release.py build

# 仅创建标签
python scripts/release.py tag
```

## 质量门禁

发布必须满足以下条件：

| 检查项 | 要求 |
|--------|------|
| 测试通过率 | 100% |
| 测试覆盖率 | ≥ 85% |
| 代码风格 | 通过 black、flake8 检查 |
| 类型检查 | 通过 mypy 检查 |
| 安全扫描 | 无高危漏洞 |
| 文档完整性 | 所有公共 API 有文档 |
| 性能基准 | 符合性能要求 |

## 故障处理

如果发布过程中出现问题：

1. **立即停止发布流程**
2. **分析问题原因**
3. **执行回滚（如果需要）**
4. **修复问题后重新发布**
5. **记录事故报告**

## 发布检查清单

详细检查清单请参阅 [RELEASE_CHECKLIST.md](../RELEASE_CHECKLIST.md)。

## 联系信息

- **发布经理**: [姓名]
- **紧急联系人**: [姓名]
- **发布日历**: [链接]

---

*最后更新: 2025-12-31*  
*版本: 1.0*