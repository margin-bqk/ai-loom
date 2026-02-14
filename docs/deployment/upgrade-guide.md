# LOOM 升级指南

本文档提供了 LOOM 版本升级的详细步骤和注意事项，确保升级过程平滑、安全。

## 升级策略

### 升级类型

1. **补丁版本升级** (X.Y.Z → X.Y.Z+1)
   - 向后兼容的 bug 修复
   - 低风险，通常可以直接升级

2. **次版本升级** (X.Y.Z → X.Y+1.0)
   - 向后兼容的新功能
   - 中等风险，需要测试新功能

3. **主版本升级** (X.Y.Z → X+1.0.0)
   - 不兼容的 API 变更
   - 高风险，需要仔细规划和测试

### 升级方法

- **原地升级**: 直接更新到新版本
- **蓝绿部署**: 并行运行新旧版本，逐步切换流量
- **金丝雀发布**: 先向小部分用户发布新版本

## 升级前准备

### 1. 阅读发布说明

仔细阅读目标版本的发布说明，特别关注：
- 破坏性变更
- 弃用警告
- 新配置要求
- 迁移步骤

### 2. 备份数据

```bash
# 备份数据库
sqlite3 data/loom.db ".backup backup/loom-pre-upgrade-$(date +%Y%m%d).db"

# 备份配置文件
cp -r config/ backup/config-$(date +%Y%m%d)/
cp .env backup/env-$(date +%Y%m%d)

# 备份规则文件
tar -czf backup/canon-$(date +%Y%m%d).tar.gz canon/
```

### 3. 检查系统要求

```bash
# 检查 Python 版本
python --version

# 检查依赖项
pip list | grep loom

# 检查磁盘空间
df -h

# 检查内存
free -h
```

### 4. 测试环境验证

在测试环境中先进行升级，验证：
- 所有功能正常工作
- 性能符合预期
- 数据迁移成功

## 升级步骤

### 通用升级流程

#### 步骤 1: 停止服务

```bash
# Docker
docker-compose down

# Kubernetes
kubectl scale deployment/loom --replicas=0 -n loom

# 系统服务
systemctl stop loom
```

#### 步骤 2: 升级应用

```bash
# 方法 A: PyPI 安装
pip install --upgrade loom==X.Y.Z

# 方法 B: Docker
docker pull yourregistry/loom:X.Y.Z

# 方法 C: 源代码
git checkout vX.Y.Z
pip install -e .
```

#### 步骤 3: 应用数据迁移（如果需要）

```bash
# 运行迁移脚本
loom db migrate

# 或手动迁移
python scripts/migrate_data.py
```

#### 步骤 4: 启动服务

```bash
# Docker
docker-compose up -d

# Kubernetes
kubectl scale deployment/loom --replicas=3 -n loom

# 系统服务
systemctl start loom
```

#### 步骤 5: 验证升级

```bash
# 检查版本
loom --version

# 检查健康状态
curl http://localhost:8000/health

# 运行冒烟测试
python scripts/smoke_test.py
```

## 版本特定升级说明

### 从 0.1.0 升级到 0.2.0

#### 破坏性变更
1. **配置格式变更**: `config.yaml` 格式更新
2. **数据库模式变更**: 新增索引和表
3. **API 端点变更**: 部分 REST 端点路径修改

#### 迁移步骤

```bash
# 1. 备份当前配置
cp config/default_config.yaml config/default_config.yaml.backup

# 2. 运行配置迁移工具
python scripts/migrate_config.py --from 0.1.0 --to 0.2.0

# 3. 更新数据库模式
loom db upgrade

# 4. 验证迁移
loom config validate
loom db check
```

#### 配置变更示例

**0.1.0 配置**:
```yaml
llm:
  provider: openai
  model: gpt-4
```

**0.2.0 配置**:
```yaml
llm_providers:
  default: openai
  openai:
    model: gpt-4-turbo
    temperature: 0.7
```

### 从 0.9.x 升级到 0.10.0（阶段1重构）

#### 重要变更
1. **项目定位重构**: 从"游戏引擎"改为"叙事解释器"相关术语
2. **架构标准化**: 五层架构（核心、规则、解释、记忆、干预）接口标准化
3. **配置更新**: 新增环境变量和配置选项
4. **接口兼容性**: 保持主要API向后兼容，但部分内部接口有调整

#### 迁移步骤

```bash
# 1. 备份当前安装
cp -r /path/to/loom /path/to/loom-backup-$(date +%Y%m%d)

# 2. 检查当前版本
loom --version

# 3. 升级到 v0.10.0
pip install --upgrade loom==0.10.0

# 4. 验证安装
loom --version  # 应该显示 0.10.0

# 5. 更新配置文件（如果需要）
cp .env.example .env.new
# 手动合并现有配置到新文件
mv .env .env.old
mv .env.new .env

# 6. 运行兼容性检查
loom check --compatibility

# 7. 测试基本功能
loom run --test --canon examples/basic_world.md
```

#### 配置变更

**新增环境变量**:
```bash
# 叙事解释器模式
NARRATIVE_INTERPRETER_MODE=advanced

# 一致性检查强度
CONSISTENCY_CHECK_LEVEL=medium

# 记忆存储类型
MEMORY_STORAGE_TYPE=sqlite

# 干预处理模式
INTERVENTION_HANDLING_MODE=adaptive

# 性能监控
ENABLE_PERFORMANCE_MONITORING=true
METRICS_EXPORT_PORT=8001
```

#### 向后兼容性说明
- **CLI命令**: 所有现有CLI命令保持兼容
- **API端点**: Web API端点保持兼容
- **数据格式**: 会话数据格式保持兼容
- **规则文件**: Markdown规则文件格式保持兼容

#### 已知迁移问题
1. **测试失败**: 部分集成测试可能因接口调整而失败
2. **插件兼容性**: 自定义插件可能需要更新以匹配新接口
3. **性能差异**: 新版本可能有不同的性能特征

### 从 0.2.0 升级到 1.0.0

#### 重大变更
1. **插件系统重构**: 插件接口完全重写
2. **存储后端抽象**: 支持多种数据库
3. **认证系统**: 新增用户认证和授权

#### 迁移步骤

```bash
# 1. 导出所有数据
loom export --format json --output backup/loom-data-export.json

# 2. 卸载旧版本
pip uninstall loom

# 3. 安装新版本
pip install loom==1.0.0

# 4. 初始化新数据库
loom init --force

# 5. 导入数据
loom import --file backup/loom-data-export.json

# 6. 迁移插件
python scripts/migrate_plugins.py
```

## 云环境升级

### AWS ECS 升级

```bash
# 1. 更新任务定义
aws ecs register-task-definition \
  --family loom-task \
  --cli-input-json file://task-definition-vX.Y.Z.json

# 2. 更新服务
aws ecs update-service \
  --cluster loom-cluster \
  --service loom-service \
  --task-definition loom-task:X.Y.Z \
  --desired-count 3
```

### Kubernetes 升级

```bash
# 1. 更新镜像标签
kubectl set image deployment/loom loom=yourregistry/loom:X.Y.Z -n loom

# 2. 监控滚动更新
kubectl rollout status deployment/loom -n loom --timeout=300s

# 3. 如有问题，回滚
kubectl rollout undo deployment/loom -n loom
```

### Azure AKS 升级

```bash
# 1. 更新 Deployment
kubectl apply -f deployment-vX.Y.Z.yaml

# 2. 使用蓝绿部署
# 创建新 Deployment
kubectl apply -f deployment-green.yaml

# 更新 Service 指向新 Deployment
kubectl patch svc loom-service -n loom -p '{"spec":{"selector":{"version":"green"}}}'
```

## 数据迁移

### 数据库迁移

```python
# 迁移脚本示例
import sqlite3
import json

def migrate_0_1_to_0_2():
    """从 0.1.0 迁移到 0.2.0"""
    conn = sqlite3.connect('data/loom.db')

    # 添加新表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS metrics (
            id INTEGER PRIMARY KEY,
            timestamp DATETIME,
            metric_name TEXT,
            value REAL
        )
    ''')

    # 添加索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON metrics(timestamp)')

    conn.commit()
    conn.close()
```

### 配置迁移

```yaml
# 自动迁移配置
migrations:
  - version: "0.1.0"
    steps:
      - rename_key: "llm.provider -> llm_providers.default"
      - add_key: "llm_providers.openai.temperature"
      - default_value: 0.7
```

### 规则文件迁移

```bash
# 批量更新规则文件
find canon/ -name "*.md" -exec sed -i 's/old_pattern/new_pattern/g' {} \;
```

## 升级后验证

### 功能测试

```bash
# 1. 基本功能测试
loom run --canon canon/default.md --test

# 2. API 测试
python -m pytest tests/api/ -v

# 3. 集成测试
python -m pytest tests/integration/ -v

# 4. 性能测试
python scripts/performance_test.py --baseline 0.1.0
```

### 数据完整性检查

```bash
# 检查数据库完整性
sqlite3 data/loom.db "PRAGMA integrity_check;"

# 检查数据计数
loom stats --detailed

# 验证外键约束
sqlite3 data/loom.db "PRAGMA foreign_key_check;"
```

### 性能监控

```bash
# 监控关键指标
watch -n 5 'curl -s http://localhost:8000/metrics | grep loom_requests_total'

# 检查错误率
curl -s http://localhost:8000/metrics | grep loom_errors_total

# 监控资源使用
docker stats loom-app
kubectl top pod -n loom
```

## 回滚计划

### 何时回滚

出现以下情况时考虑回滚：
1. 关键功能无法使用
2. 性能下降超过 50%
3. 数据丢失或损坏
4. 安全漏洞

### 回滚步骤

```bash
# 1. 停止新版本
docker-compose down

# 2. 恢复备份
tar -xzf backup/loom-pre-upgrade-*.tar.gz

# 3. 启动旧版本
git checkout v0.1.0
docker-compose up -d

# 4. 验证回滚
curl http://localhost:8000/health
```

### 自动化回滚

```bash
# 使用回滚脚本
python scripts/rollback.py --docker --backup backup/loom-latest.tar.gz
```

## 常见问题

### 升级失败

**症状**: 升级过程中出现错误，服务无法启动

**解决方案**:
1. 检查日志获取详细错误信息
2. 验证系统要求是否满足
3. 检查依赖项兼容性
4. 回滚到上一个版本

### 数据不一致

**症状**: 升级后数据丢失或格式错误

**解决方案**:
1. 从备份恢复数据
2. 运行数据修复工具
3. 手动修复损坏的数据

### 性能下降

**症状**: 升级后响应时间变慢

**解决方案**:
1. 检查新版本的性能配置
2. 优化数据库查询
3. 调整资源分配
4. 启用性能监控

## 最佳实践

### 升级前
1. **充分测试**: 在测试环境验证升级
2. **备份数据**: 确保有完整备份
3. **阅读文档**: 了解变更和迁移步骤
4. **通知用户**: 提前通知维护窗口

### 升级中
1. **监控进度**: 实时监控升级过程
2. **逐步升级**: 使用蓝绿或金丝雀部署
3. **验证每一步**: 确保每个步骤成功

### 升级后
1. **监控运行状况**: 密切监控 24-48 小时
2. **收集反馈**: 收集用户反馈
3. **更新文档**: 记录升级经验和问题

## 自动化升级

### 使用 CI/CD 流水线

```yaml
# GitHub Actions 示例
name: Upgrade LOOM
on:
  release:
    types: [published]

jobs:
  upgrade:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run upgrade tests
        run: python scripts/upgrade_test.py
      - name: Deploy to staging
        run: ./scripts/deploy.sh --env staging
      - name: Run smoke tests
        run: python scripts/smoke_test.py --env staging
      - name: Deploy to production
        if: success()
        run: ./scripts/deploy.sh --env production
```

### 使用配置管理工具

```bash
# Ansible 示例
- name: Upgrade LOOM
  hosts: loom_servers
  tasks:
    - name: Backup current installation
      command: ./scripts/backup.sh

    - name: Install new version
      pip:
        name: loom
        version: "{{ target_version }}"

    - name: Run migrations
      command: loom db migrate

    - name: Restart service
      systemd:
        name: loom
        state: restarted
```

## 支持资源

- [发布说明](https://github.com/your-org/loom/releases)
- [变更日志](../CHANGELOG.md)
- [故障排除指南](DEPLOYMENT_TROUBLESHOOTING.md)
- [社区论坛](https://github.com/your-org/loom/discussions)

## 紧急联系

如果升级遇到无法解决的问题：

1. **查看文档**: 重新阅读本文档和相关资源
2. **搜索问题**: 在 GitHub Issues 中搜索类似问题
3. **寻求帮助**: 在 Discord 或论坛提问
4. **联系支持**: 发送邮件到 support@loom.dev

---

*最后更新: 2025-12-31*
*版本: 1.0*
