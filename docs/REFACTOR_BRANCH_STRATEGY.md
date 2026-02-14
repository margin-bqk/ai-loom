# LOOM 重构分支策略

## 概述

本文档定义了 LOOM 项目重构期间的分支管理策略，确保重构过程有序、可控，并支持并行开发。

## 分支命名规范

### 主分支
- `main`: 稳定版本分支，仅接受经过完整测试的代码
- `develop`: 开发主分支，集成各功能分支

### 重构分支
- `refactor/phase0-prep`: 阶段0准备分支（当前分支）
- `refactor/phase1-positioning`: 阶段1定位重构分支
- `refactor/phase2-core`: 阶段2核心层重构分支
- `refactor/phase3-interpretation`: 阶段3解释层重构分支
- `refactor/phase4-memory`: 阶段4记忆层重构分支
- `refactor/phase5-intervention`: 阶段5干预层重构分支
- `refactor/phase6-integration`: 阶段6集成测试分支

### 功能分支
- `feature/*`: 新功能开发
- `bugfix/*`: 缺陷修复
- `hotfix/*`: 紧急修复

### 发布分支
- `release/v*.*.*`: 版本发布分支

## 重构阶段分支策略

### 阶段0：准备阶段（当前）
**分支**: `refactor/phase0-prep`
**目标**: 完成架构分析、环境准备、迁移策略制定
**产出**:
1. 架构差距分析报告
2. 开发环境配置
3. 测试环境验证
4. 代码质量标准
5. 阶段1详细实施计划

**合并策略**: 完成后合并到 `develop` 分支

### 阶段1：定位重构
**分支**: `refactor/phase1-positioning`
**目标**: 重新定位五层架构边界，确保严格解耦
**关键任务**:
1. 定义清晰的层间接口
2. 移除层间硬编码依赖
3. 建立依赖注入机制
4. 实现配置驱动架构

### 阶段2-5：各层重构
**策略**: 每个阶段独立分支，并行开发
**要求**: 保持向后兼容性，通过接口适配器支持现有代码

### 阶段6：集成测试
**分支**: `refactor/phase6-integration`
**目标**: 集成所有重构层，进行全面测试
**关键任务**:
1. 端到端测试
2. 性能基准测试
3. 向后兼容性验证
4. 文档更新

## 工作流程

### 1. 分支创建
```bash
# 从 develop 分支创建重构分支
git checkout develop
git pull origin develop
git checkout -b refactor/phase1-positioning
```

### 2. 开发提交
- 使用语义化提交消息
- 频繁提交，小步前进
- 每个提交对应一个逻辑变更

### 3. 代码审查
- 所有重构分支必须通过代码审查
- 审查重点：架构符合性、测试覆盖率、向后兼容性
- 使用 Pull Request 进行合并

### 4. 合并策略
```bash
# 定期同步 develop 分支
git checkout refactor/phase1-positioning
git fetch origin
git merge origin/develop

# 完成阶段后合并到 develop
git checkout develop
git merge --no-ff refactor/phase1-positioning
git push origin develop
```

### 5. 冲突解决
- 优先在重构分支解决冲突
- 保持重构分支与 develop 同步
- 复杂冲突使用 rebase 策略

## 版本控制最佳实践

### 1. 提交规范
```
<type>(<scope>): <subject>

<body>

<footer>
```

**类型**:
- `feat`: 新功能
- `fix`: 缺陷修复
- `refactor`: 重构（不改变外部行为）
- `perf`: 性能优化
- `test`: 测试相关
- `docs`: 文档更新
- `chore`: 构建过程或辅助工具变更

### 2. 分支保护规则
- `main` 分支: 强制代码审查，禁止直接推送
- `develop` 分支: 强制通过 CI/CD 流水线
- 重构分支: 要求 80% 以上测试覆盖率

### 3. 标签策略
- 每个阶段完成创建里程碑标签: `refactor-phase0`, `refactor-phase1`
- 版本发布标签: `v0.2.0`, `v0.3.0`

## 回滚策略

### 1. 快速回滚
```bash
# 回滚到上一个稳定提交
git revert <commit-hash>

# 或使用标签回滚
git checkout refactor-phase0
```

### 2. 功能开关
- 使用配置开关控制新功能
- 支持运行时切换重构代码路径
- 保持向后兼容性至少 2 个版本

### 3. 紧急修复
- 从 `main` 分支创建 `hotfix/*` 分支
- 修复后同时合并到 `main` 和 `develop`
- 确保重构分支同步修复

## 工具支持

### 1. Git Hooks
- 预提交钩子: 代码格式化、静态检查
- 预推送钩子: 运行单元测试
- 提交消息钩子: 验证提交格式

### 2. CI/CD 集成
- 每个推送触发构建和测试
- 合并前要求通过所有检查
- 自动生成变更日志

### 3. 代码审查工具
- GitHub Pull Requests
- 强制至少 1 人审查
- 要求所有检查通过

## 沟通与协调

### 1. 进度跟踪
- 每周同步会议
- 使用项目看板跟踪任务
- 定期更新重构状态文档

### 2. 冲突预防
- 提前沟通接口变更
- 共享架构决策记录
- 及时同步分支状态

### 3. 文档更新
- 每个阶段更新架构文档
- 维护 API 变更日志
- 更新开发者指南

## 风险评估与缓解

### 1. 技术风险
- **风险**: 重构导致现有功能破坏
- **缓解**: 全面测试覆盖，功能开关，渐进式迁移

### 2. 进度风险
- **风险**: 重构时间超出预期
- **缓解**: 分阶段实施，定期评估，设置里程碑

### 3. 质量风险
- **风险**: 新架构引入缺陷
- **缓解**: 代码审查，自动化测试，性能监控

## 附录

### 常用命令参考

```bash
# 查看分支状态
git branch -avv

# 清理已合并分支
git branch --merged develop | grep -v "^\*" | xargs -n 1 git branch -d

# 查看提交历史
git log --oneline --graph --all -20

# 同步远程分支
git fetch --prune

# 重命名分支
git branch -m old-name new-name
git push origin :old-name new-name
git push origin -u new-name
```

### 联系人
- 架构负责人: [负责人姓名]
- 开发协调: [协调人姓名]
- 质量保证: [QA负责人]

---

**最后更新**: 2026-01-12
**版本**: 1.0
**状态**: 实施中
