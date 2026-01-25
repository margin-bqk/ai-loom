# LOOM v0.9.x 到 v0.10.0 迁移指南

## 概述

本文档提供了从 LOOM v0.9.x（或更早版本）升级到 v0.10.0 的详细迁移指南。v0.10.0 是**阶段1重构**的发布版本，包含了项目定位重构、架构标准化和发布准备工作的完成。

**目标读者**: 系统管理员、DevOps工程师、LOOM项目维护者  
**预计迁移时间**: 30-60分钟  
**风险等级**: 中等（主要变更在架构层面，API保持兼容）

## 迁移前准备

### 1. 系统要求检查

确保系统满足 v0.10.0 的要求：
- **Python**: 3.10 或更高版本（推荐 3.12）
- **内存**: 至少 2GB 可用内存
- **磁盘空间**: 至少 500MB 可用空间
- **网络**: 可访问 LLM API（如 OpenAI、Anthropic）

### 2. 数据备份

**重要**: 在开始迁移前，务必备份所有数据。

```bash
# 创建备份目录
mkdir -p /backup/loom-$(date +%Y%m%d)

# 备份数据库
if [ -f "data/loom.db" ]; then
    cp data/loom.db /backup/loom-$(date +%Y%m%d)/loom.db
fi

# 备份配置文件
cp .env /backup/loom-$(date +%Y%m%d)/env.backup
cp -r config/ /backup/loom-$(date +%Y%m%d)/config/

# 备份规则文件
tar -czf /backup/loom-$(date +%Y%m%d)/canon.tar.gz canon/

# 备份会话数据
if [ -d "sessions/" ]; then
    tar -czf /backup/loom-$(date +%Y%m%d)/sessions.tar.gz sessions/
fi

# 验证备份
ls -la /backup/loom-$(date +%Y%m%d)/
```

### 3. 当前环境检查

```bash
# 检查当前版本
loom --version

# 检查 Python 版本
python --version

# 检查依赖项
pip list | grep loom

# 检查运行状态
curl -s http://localhost:8000/health | jq . 2>/dev/null || echo "服务可能未运行"
```

## 迁移步骤

### 步骤 1: 停止服务

```bash
# 方法 A: Docker Compose
docker-compose down

# 方法 B: 系统服务
systemctl stop loom

# 方法 C: 手动停止
pkill -f "loom" || true
pkill -f "uvicorn" || true
```

### 步骤 2: 升级 LOOM

#### 选项 A: PyPI 安装（推荐）

```bash
# 卸载旧版本（可选）
pip uninstall loom -y

# 安装新版本
pip install loom==0.10.0

# 安装可选依赖
pip install "loom[api,cli,vector]"
```

#### 选项 B: Docker 部署

```bash
# 拉取新镜像
docker pull yourregistry/loom:0.10.0

# 或重新构建
docker build -t loom:0.10.0 .
```

#### 选项 C: 从源代码安装

```bash
# 获取代码
git clone https://github.com/your-org/loom.git
cd loom
git checkout v0.10.0

# 安装
pip install -e ".[api,cli,vector]"
```

### 步骤 3: 更新配置文件

v0.10.0 引入了新的环境变量。您需要更新 `.env` 文件：

```bash
# 创建新配置文件
cp .env.example .env.new

# 合并现有配置（手动步骤）
echo "=== 需要手动合并的配置项 ==="
echo "请将以下现有配置从 .env 复制到 .env.new:"
echo "1. LLM API 密钥 (OPENAI_API_KEY, ANTHROPIC_API_KEY 等)"
echo "2. 数据库连接字符串 (DATABASE_URL)"
echo "3. 自定义路径配置"
echo "4. 安全相关配置"
echo ""
echo "完成后执行:"
echo "mv .env .env.old && mv .env.new .env"
```

**关键新增配置**:
```bash
# 叙事解释器模式
NARRATIVE_INTERPRETER_MODE=advanced  # basic, advanced, creative

# 一致性检查强度
CONSISTENCY_CHECK_LEVEL=medium  # low, medium, high

# 记忆存储类型
MEMORY_STORAGE_TYPE=sqlite  # sqlite, postgres, memory

# 干预处理模式
INTERVENTION_HANDLING_MODE=adaptive  # strict, lenient, adaptive

# 性能监控
ENABLE_PERFORMANCE_MONITORING=true
METRICS_EXPORT_PORT=8001
```

### 步骤 4: 运行数据迁移（如果需要）

v0.10.0 的数据模式与 v0.9.x 兼容，但建议运行兼容性检查：

```bash
# 检查数据兼容性
loom db check --compatibility

# 如果有迁移脚本，运行它
if [ -f "scripts/migrate_v0.9_to_v0.10.py" ]; then
    python scripts/migrate_v0.9_to_v0.10.py
fi
```

### 步骤 5: 启动服务

```bash
# 方法 A: Docker Compose
docker-compose up -d

# 方法 B: 系统服务
systemctl start loom

# 方法 C: 直接运行
uvicorn loom.web.app:app --host 0.0.0.0 --port 8000 &
```

### 步骤 6: 验证迁移

```bash
# 检查版本
loom --version  # 应该显示 0.10.0

# 检查健康状态
curl -s http://localhost:8000/health | jq .status  # 应该返回 "healthy"

# 检查就绪状态
curl -s http://localhost:8000/ready | jq .ready  # 应该返回 true

# 运行冒烟测试
loom run --test --canon examples/basic_world.md --session test-migration
```

## 架构变更说明

### 五层架构标准化

v0.10.0 明确了五层架构，各层职责更清晰：

1. **核心运行时层** (`loom.core`)
   - 会话管理、回合调度、持久化引擎
   - 接口更标准化，错误处理更完善

2. **规则层** (`loom.rules`)
   - Markdown规则解析、版本控制、规则加载
   - 支持更复杂的规则结构和依赖管理

3. **解释层** (`loom.interpretation`)
   - LLM推理流水线、一致性检查、规则解释
   - 新增性能优化和错误恢复机制

4. **记忆层** (`loom.memory`)
   - 结构化存储、向量存储、摘要生成
   - 支持多种存储后端和查询优化

5. **干预层** (`loom.intervention`)
   - OOC处理、世界编辑、Retcon处理
   - 更灵活的干预策略和冲突解决

### 接口变更

#### 向后兼容的变更
- **CLI命令**: 所有现有命令保持兼容
- **Web API**: REST API 端点保持兼容
- **数据格式**: 会话和规则数据格式保持兼容

#### 新增接口
- **组件集成接口**: 各层之间更清晰的集成点
- **监控接口**: 性能指标和健康检查端点
- **扩展接口**: 插件系统预留接口

#### 废弃的接口（警告）
- 部分内部辅助函数已重命名
- 实验性API可能已移除
- 查看详细变更请参考 `CHANGELOG.md`

## 迁移后验证

### 功能测试

```bash
# 1. 基本叙事解释测试
loom run --canon examples/basic_world.md --session test-narrative --max-turns 3

# 2. 规则解释测试
loom rules validate --file canon/default.md

# 3. 记忆操作测试
loom memory stats --session test-narrative

# 4. 干预处理测试
echo "测试文本 [OOC: 这是一个测试注释]" | loom process --session test-narrative
```

### 性能基准

```bash
# 运行性能测试
python scripts/performance_benchmark.py --baseline v0.9.x

# 监控资源使用
docker stats loom-app  # 或使用系统监控工具

# 检查响应时间
time curl -s http://localhost:8000/health > /dev/null
```

### 数据完整性检查

```bash
# 检查数据库完整性
if [ -f "data/loom.db" ]; then
    sqlite3 data/loom.db "PRAGMA integrity_check;"
fi

# 检查会话数据
loom session list --all

# 验证规则加载
loom rules list --detailed
```

## 故障排除

### 常见问题

#### 问题 1: 升级后服务无法启动

**可能原因**:
- 缺少新依赖项
- 配置文件格式错误
- 端口冲突

**解决方案**:
```bash
# 检查错误日志
docker logs loom-app  # 或查看应用日志

# 验证依赖
pip install -r requirements.txt

# 检查端口
netstat -tlnp | grep :8000

# 以调试模式启动
LOOM_LOG_LEVEL=DEBUG uvicorn loom.web.app:app --host 0.0.0.0 --port 8000
```

#### 问题 2: 数据访问错误

**可能原因**:
- 数据库模式不兼容
- 文件权限问题
- 数据损坏

**解决方案**:
```bash
# 从备份恢复数据
cp /backup/loom-*/loom.db data/loom.db

# 修复权限
chmod -R 755 data/
chown -R $USER:$USER data/

# 运行数据修复
loom db repair --backup-first
```

#### 问题 3: 性能下降

**可能原因**:
- 新功能增加了开销
- 配置未优化
- 资源不足

**解决方案**:
```bash
# 调整配置
export LOOM_CACHE_ENABLED=true
export LOOM_BATCH_SIZE=5

# 监控性能
loom metrics --live

# 优化资源分配
# 编辑 docker-compose.yml 或系统服务配置
```

### 回滚步骤

如果迁移遇到无法解决的问题，可以回滚到之前版本：

```bash
# 1. 停止服务
docker-compose down

# 2. 恢复备份
tar -xzf /backup/loom-*/canon.tar.gz
cp /backup/loom-*/loom.db data/loom.db
cp /backup/loom-*/env.backup .env

# 3. 安装旧版本
pip install loom==0.9.0  # 或您之前的版本

# 4. 启动服务
docker-compose up -d

# 5. 验证回滚
loom --version
curl http://localhost:8000/health
```

## 最佳实践

### 生产环境迁移

1. **使用蓝绿部署**: 并行运行新旧版本，逐步切换流量
2. **金丝雀发布**: 先向小部分用户发布新版本
3. **全面监控**: 迁移后密切监控 24-48 小时
4. **A/B测试**: 比较新旧版本的性能和功能

### 测试环境验证

在迁移生产环境前，务必在测试环境验证：
- 功能完整性
- 性能表现
- 数据迁移正确性
- 回滚流程

### 文档更新

迁移完成后：
1. 更新运行文档
2. 记录迁移经验
3. 更新故障排除指南
4. 通知相关团队

## 获取帮助

如果遇到本文档未覆盖的问题：

1. **查看详细日志**: 启用 `LOOM_LOG_LEVEL=DEBUG`
2. **检查 GitHub Issues**: https://github.com/your-org/loom/issues
3. **查阅文档**: https://loom.dev/docs
4. **社区支持**: https://github.com/your-org/loom/discussions
5. **联系维护者**: support@loom.dev

## 附录

### A. 版本对比

| 特性 | v0.9.x | v0.10.0 | 变更类型 |
|------|--------|---------|----------|
| 项目定位 | 游戏引擎 | 叙事解释器 | 术语更新 |
| 架构 | 模块化 | 五层标准化 | 架构优化 |
| API兼容性 | N/A | 完全兼容 | 新增 |
| 配置选项 | 基础 | 扩展 | 新增 |
| 性能监控 | 有限 | 增强 | 改进 |

### B. 检查清单

- [ ] 备份所有数据
- [ ] 验证系统要求
- [ ] 停止运行的服务
- [ ] 安装 v0.10.0
- [ ] 更新配置文件
- [ ] 运行数据迁移
- [ ] 启动服务
- [ ] 验证基本功能
- [ ] 运行完整测试
- [ ] 监控性能
- [ ] 更新文档

### C. 有用的命令

```bash
# 快速健康检查
./scripts/health_check.sh

# 性能基准
./scripts/run_benchmarks.sh

# 数据完整性验证
./scripts/validate_data.sh

# 自动化迁移
./scripts/migrate_to_v0.10.0.sh
```

---

**最后更新**: 2026-01-12  
**文档版本**: 1.0  
**对应 LOOM 版本**: v0.10.0

*注意: 本文档基于实际测试编写，但您的环境可能有所不同。建议在生产环境迁移前进行充分测试。*