# LOOM 发布检查清单

本文档描述了发布 LOOM 新版本时需要完成的步骤。请按顺序执行所有检查项。

## 发布前准备

### 1. 代码质量检查
- [ ] 运行所有测试：`pytest`
- [ ] 确保测试覆盖率 >= 85%：`pytest --cov=src.loom --cov-report=html`
- [ ] 代码格式化：`black src/ tests/`
- [ ] 类型检查：`mypy src/`
- [ ] 代码风格检查：`flake8 src/`
- [ ] 安全检查：`bandit -r src/`
- [ ] 依赖安全检查：`safety check`

### 2. 文档更新
- [ ] 更新 `CHANGELOG.md`，包含新版本的所有变更
- [ ] 更新 `README.md` 中的版本号和功能描述
- [ ] 更新 `docs/` 目录下的所有相关文档
- [ ] 确保所有示例代码都能正常运行
- [ ] 更新 API 文档（如有）

### 3. 版本管理
- [ ] 更新 `pyproject.toml` 中的版本号
- [ ] 更新 `src/loom/__init__.py` 中的 `__version__`
- [ ] 创建 Git 标签：`git tag vX.Y.Z`
- [ ] 确保标签已签名（可选）

### 4. 打包验证
- [ ] 构建源代码包：`python -m build`
- [ ] 验证包结构：`twine check dist/*`
- [ ] 测试安装：`pip install dist/loom-X.Y.Z-py3-none-any.whl`
- [ ] 验证 CLI 命令可用：`loom --help`
- [ ] 运行基础示例确保功能正常

## 发布流程

### 5. PyPI 发布
- [ ] 配置 PyPI 令牌（环境变量 `TWINE_USERNAME` 和 `TWINE_PASSWORD`）
- [ ] 上传到 PyPI：`twine upload dist/*`
- [ ] 验证 PyPI 页面显示正确

### 6. Docker 发布
- [ ] 构建 Docker 镜像：`docker build -t loom:latest .`
- [ ] 使用版本标签：`docker tag loom:latest loom:X.Y.Z`
- [ ] 推送到 Docker Hub：`docker push yourusername/loom:X.Y.Z`
- [ ] 更新 `docker-compose.yml` 中的镜像标签（如有需要）

### 7. GitHub 发布
- [ ] 在 GitHub 创建 Release
- [ ] 上传构建产物（wheel 和 tar.gz）
- [ ] 添加发布说明（从 CHANGELOG 复制）
- [ ] 标记为预发布或正式发布

### 8. 文档发布
- [ ] 构建文档网站：`mkdocs build`（如果使用 MkDocs）
- [ ] 部署到 GitHub Pages：`mkdocs gh-deploy`
- [ ] 验证文档网站可访问

## 发布后验证

### 9. 安装验证
- [ ] 从 PyPI 安装：`pip install loom==X.Y.Z`
- [ ] 验证版本号：`loom --version`
- [ ] 运行基础测试：`python -m pytest tests/test_core/ -v`

### 10. 集成测试
- [ ] 使用 Docker 运行完整示例：`docker-compose up -d`
- [ ] 验证 Web 界面可访问：`http://localhost:8000`
- [ ] 验证监控仪表板：`http://localhost:3000`
- [ ] 运行端到端测试脚本

### 11. 通知和沟通
- [ ] 更新项目状态页面
- [ ] 发送发布公告（邮件列表、Discord、Twitter等）
- [ ] 更新相关依赖项目

## 回滚计划

如果发布出现问题，按以下步骤回滚：

1. **PyPI 回滚**
   - 标记有问题的版本为 "yanked"
   - 发布修复版本或回退到上一个稳定版本

2. **Docker 回滚**
   - 推送上一个版本的镜像标签
   - 更新 `docker-compose.yml` 使用旧版本

3. **GitHub 回滚**
   - 删除有问题的 Release
   - 删除 Git 标签（如果需要）

4. **文档回滚**
   - 回退文档网站到上一个版本

## 版本策略

- **主版本号 (X)**：不兼容的 API 变更
- **次版本号 (Y)**：向后兼容的功能性新增
- **修订号 (Z)**：向后兼容的问题修复

## 维护计划

- 每个版本发布后，创建维护分支（如 `maintenance/vX.Y`）
- 关键安全问题需要发布补丁版本
- 定期更新依赖项（每月一次）

---

**最后更新**: 2025-12-31  
**维护者**: LOOM 团队