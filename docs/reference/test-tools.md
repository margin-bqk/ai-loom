# LOOM 测试工具和脚本

## 目录

1. [测试工具概述](#测试工具概述)
2. [测试数据生成工具](#测试数据生成工具)
   - [规则生成器](#规则生成器)
   - [会话数据生成器](#会话数据生成器)
   - [记忆数据生成器](#记忆数据生成器)
3. [测试环境管理工具](#测试环境管理工具)
   - [环境设置脚本](#环境设置脚本)
   - [Docker测试环境](#docker测试环境)
   - [测试数据库管理](#测试数据库管理)
4. [测试执行工具](#测试执行工具)
   - [测试运行器](#测试运行器)
   - [测试报告生成器](#测试报告生成器)
   - [覆盖率分析工具](#覆盖率分析工具)
5. [性能测试工具](#性能测试工具)
   - [基准测试工具](#基准测试工具)
   - [负载测试工具](#负载测试工具)
   - [压力测试工具](#压力测试工具)
6. [监控和调试工具](#监控和调试工具)
   - [日志分析工具](#日志分析工具)
   - [性能分析工具](#性能分析工具)
   - [调试工具](#调试工具)
7. [持续集成工具](#持续集成工具)
   - [GitHub Actions配置](#github-actions配置)
   - [测试流水线](#测试流水线)
   - [质量门禁](#质量门禁)

## 测试工具概述

LOOM 提供了一套完整的测试工具和脚本，帮助开发者和测试人员高效地进行测试工作。

### 工具分类

| 工具类别 | 主要工具 | 用途 |
|----------|----------|------|
| 数据生成 | `generate_test_data.py` | 生成测试数据 |
| 环境管理 | `setup_test_env.sh` | 设置测试环境 |
| 测试执行 | `run_tests.py` | 运行测试套件 |
| 性能测试 | `run_performance_tests.py` | 执行性能测试 |
| 监控调试 | `analyze_logs.py` | 分析测试日志 |
| CI/CD | GitHub Actions | 自动化测试流水线 |

## 测试数据生成工具

### 规则生成器

#### 脚本位置
`scripts/generate_test_rules.py`

#### 功能
- 生成各种复杂度的测试规则文件
- 支持不同世界类型（奇幻、科幻、现实）
- 生成包含冲突的规则用于测试冲突检测
- 生成大规模规则文件用于性能测试

#### 使用方法
```bash
# 生成基础测试规则
python scripts/generate_test_rules.py \
  --type fantasy \
  --complexity medium \
  --output tests/fixtures/rules/fantasy_medium.md

# 生成包含冲突的规则
python scripts/generate_test_rules.py \
  --type scifi \
  --with-conflicts \
  --output tests/fixtures/rules/scifi_conflicts.md

# 生成大规模规则用于性能测试
python scripts/generate_test_rules.py \
  --type mixed \
  --size large \
  --entities 100 \
  --output tests/performance/rules/large_ruleset.md
```

#### 配置选项
```yaml
# config/test_data_generation.yaml
rule_generation:
  # 基础配置
  default_complexity: medium
  default_type: fantasy

  # 奇幻世界配置
  fantasy:
    races: [human, elf, dwarf, orc]
    magic_types: [elemental, divine, nature, arcane]
    locations: [forest, mountain, castle, dungeon]

  # 科幻世界配置
  scifi:
    factions: [federation, empire, rebels, aliens]
    tech_levels: [primitive, advanced, futuristic, transcendent]
    locations: [spaceship, planet, station, wormhole]

  # 现实世界配置
  modern:
    eras: [ancient, medieval, modern, future]
    cultures: [western, eastern, middle_eastern, african]
    locations: [city, countryside, coast, mountains]
```

### 会话数据生成器

#### 脚本位置
`scripts/generate_test_sessions.py`

#### 功能
- 生成测试会话数据
- 模拟不同用户行为模式
- 生成包含干预的会话历史
- 创建大规模会话数据集

#### 使用方法
```bash
# 生成单个测试会话
python scripts/generate_test_sessions.py \
  --count 1 \
  --turns 10 \
  --with-interventions \
  --output tests/fixtures/sessions/session_1.json

# 生成批量测试会话
python scripts/generate_test_sessions.py \
  --count 100 \
  --turns 5 \
  --output tests/performance/data/sessions_batch/

# 生成特定类型的会话
python scripts/generate_test_sessions.py \
  --type combat_heavy \
  --turns 20 \
  --output tests/fixtures/sessions/combat_session.json
```

#### 用户行为模式
```python
# 预定义的行为模式
BEHAVIOR_PATTERNS = {
    "explorer": {
        "actions": ["explore", "observe", "investigate"],
        "intervention_rate": 0.1,
        "turn_length": "medium"
    },
    "combat_focused": {
        "actions": ["attack", "defend", "use_item"],
        "intervention_rate": 0.05,
        "turn_length": "short"
    },
    "roleplayer": {
        "actions": ["talk", "emote", "develop_character"],
        "intervention_rate": 0.2,
        "turn_length": "long"
    },
    "power_gamer": {
        "actions": ["optimize", "exploit", "min_max"],
        "intervention_rate": 0.15,
        "turn_length": "medium"
    }
}
```

### 记忆数据生成器

#### 脚本位置
`scripts/generate_test_memories.py`

#### 功能
- 生成测试记忆实体
- 创建实体关系网络
- 生成不同重要级别的记忆
- 创建大规模记忆数据集

#### 使用方法
```bash
# 生成测试记忆实体
python scripts/generate_test_memories.py \
  --entities 50 \
  --relations 100 \
  --output tests/fixtures/memories/memory_network.json

# 生成特定类型的记忆
python scripts/generate_test_memories.py \
  --entity-types character location fact \
  --density high \
  --output tests/fixtures/memories/dense_memory.json

# 生成性能测试用的大规模记忆
python scripts/generate_test_memories.py \
  --entities 10000 \
  --relations 50000 \
  --output tests/performance/data/large_memory.db
```

#### 记忆实体类型
```python
MEMORY_ENTITY_TEMPLATES = {
    "character": {
        "fields": ["name", "description", "traits", "relationships"],
        "importance_range": [0.3, 0.9]
    },
    "location": {
        "fields": ["name", "description", "features", "connections"],
        "importance_range": [0.2, 0.8]
    },
    "fact": {
        "fields": ["content", "source", "certainty", "relevance"],
        "importance_range": [0.1, 0.7]
    },
    "plotline": {
        "fields": ["title", "summary", "characters", "progress"],
        "importance_range": [0.5, 1.0]
    }
}
```

## 测试环境管理工具

### 环境设置脚本

#### 脚本位置
`scripts/setup_test_env.sh`

#### 功能
- 一键设置测试环境
- 安装测试依赖
- 配置测试数据库
- 准备测试数据

#### 使用方法
```bash
# 设置完整测试环境
./scripts/setup_test_env.sh --full

# 设置最小测试环境
./scripts/setup_test_env.sh --minimal

# 设置特定组件的测试环境
./scripts/setup_test_env.sh --component memory
./scripts/setup_test_env.sh --component llm
./scripts/setup_test_env.sh --component rules

# 清理测试环境
./scripts/setup_test_env.sh --clean
```

#### 脚本内容示例
```bash
#!/bin/bash
# setup_test_env.sh

set -e

# 解析参数
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            SETUP_FULL=true
            shift
            ;;
        --minimal)
            SETUP_MINIMAL=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        *)
            echo "未知参数: $1"
            exit 1
            ;;
    esac
done

# 清理环境
if [ "$CLEAN" = true ]; then
    echo "清理测试环境..."
    rm -rf tests/data/
    rm -rf tests/fixtures/generated/
    docker-compose -f docker-compose.test.yml down -v
    echo "环境清理完成"
    exit 0
fi

# 设置环境
echo "设置测试环境..."

# 创建目录
mkdir -p tests/data
mkdir -p tests/fixtures/generated
mkdir -p tests/logs

# 安装测试依赖
pip install -r requirements-test.txt

# 启动测试数据库
if [ "$SETUP_FULL" = true ]; then
    docker-compose -f docker-compose.test.yml up -d
    sleep 10  # 等待数据库启动
fi

# 生成测试数据
python scripts/generate_test_data.py --all

echo "测试环境设置完成"
```

### Docker测试环境

#### 配置文件
`docker-compose.test.yml`

#### 功能
- 提供完整的测试环境
- 包含所有依赖服务
- 支持隔离测试
- 易于清理和重置

#### 配置内容
```yaml
version: '3.8'

services:
  # 测试数据库
  test-db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: loom_test
      POSTGRES_USER: test_user
      POSTGRES_PASSWORD: test_password
    ports:
      - "5432:5432"
    volumes:
      - test-postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U test_user"]
      interval: 5s
      timeout: 5s
      retries: 5

  # 测试缓存
  test-redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - test-redis-data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 5

  # 向量数据库（测试用）
  test-qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - test-qdrant-data:/qdrant/storage

  # 测试监控
  test-prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./config/prometheus.test.yml:/etc/prometheus/prometheus.yml
      - test-prometheus-data:/prometheus

  # 测试LLM模拟器
  test-llm-mock:
    build:
      context: .
      dockerfile: Dockerfile.llm-mock
    ports:
      - "8080:8080"
    environment:
      MOCK_RESPONSE_DELAY: 100
      MOCK_ERROR_RATE: 0.01

volumes:
  test-postgres-data:
  test-redis-data:
  test-qdrant-data:
  test-prometheus-data:
```

### 测试数据库管理

#### 脚本位置
`scripts/manage_test_db.py`

#### 功能
- 创建和初始化测试数据库
- 导入测试数据
- 执行数据库迁移
- 清理测试数据

#### 使用方法
```bash
# 初始化测试数据库
python scripts/manage_test_db.py --init

# 导入测试数据
python scripts/manage_test_db.py --import tests/fixtures/data/test_data.json

# 执行迁移
python scripts/manage_test_db.py --migrate

# 重置数据库
python scripts/manage_test_db.py --reset

# 导出测试数据
python scripts/manage_test_db.py --export tests/fixtures/data/export.json
```

## 测试执行工具

### 测试运行器

#### 脚本位置
`scripts/run_tests.py`

#### 功能
- 运行不同类型的测试
- 支持并行测试
- 生成测试报告
- 集成覆盖率检查

#### 使用方法
```bash
# 运行所有测试
python scripts/run_tests.py --all

# 运行特定类型的测试
python scripts/run_tests.py --unit
python scripts/run_tests.py --integration
python scripts/run_tests.py --e2e
python scripts/run_tests.py --performance

# 运行特定组件的测试
python scripts/run_tests.py --component core
python scripts/run_tests.py --component memory
python scripts/run_tests.py --component interpretation

# 并行运行测试
python scripts/run_tests.py --parallel --workers 4

# 生成详细报告
python scripts/run_tests.py --report --output reports/test_report.html
```

#### 配置选项
```python
# config/test_runner.yaml
test_runner:
  # 默认配置
  default:
    workers: 2
    timeout: 30
    verbose: true

  # 单元测试配置
  unit:
    pattern: "test_*.py"
    paths: ["tests/test_*"]
    coverage: true

  # 集成测试配置
  integration:
    pattern: "test_*integration*.py"
    paths: ["tests/test_integration", "tests/test_*integration*"]
    requires: ["test-db", "test-redis"]

  # 端到端测试配置
  e2e:
    pattern: "test_*e2e*.py"
    paths: ["tests/test_e2e"]
    requires: ["test-llm-mock"]
    timeout: 60

  # 性能测试配置
  performance:
    pattern: "test_*performance*.py"
    paths: ["tests/performance"]
    markers: ["performance", "benchmark"]
    timeout: 300
```

### 测试报告生成器

#### 脚本位置
`scripts/generate_test_report.py`

#### 功能
- 生成HTML测试报告
- 可视化测试结果
- 显示覆盖率信息
- 提供历史对比

#### 使用方法
```bash
# 生成测试报告
python scripts/generate_test_report.py \
  --input test_results.json \
  --output reports/test_report.html

# 生成带覆盖率的报告
python scripts/generate_test_report.py \
  --coverage coverage.xml \
  --output reports/full_report.html

# 生成历史对比报告
python scripts/generate_test_report.py \
  --history reports/history/ \
  --output reports/trend_report.html
```

#### 报告示例
```html
<!-- 生成的HTML报告包含 -->
1. 测试概览（通过率、总测试数、运行时间）
2. 测试分类统计（单元测试、集成测试等）
3. 失败测试详情
4. 覆盖率图表
5. 性能测试结果
6. 历史趋势图
7. 建议和改进点
```

### 覆盖率分析工具

#### 脚本位置
`scripts/analyze_coverage.py`

#### 功能
- 分析测试覆盖率
- 识别未覆盖的代码
- 生成覆盖率报告
- 提供改进建议

#### 使用方法
```bash
# 分析覆盖率
python scripts/analyze_coverage.py --analyze

# 生成详细报告
python scripts/analyze_coverage.py --report --html

# 识别低覆盖率文件
python scripts/analyze_coverage.py --identify --threshold 80

# 生成覆盖率趋势
python scripts/analyze_coverage.py --trend --days 30
```

## 性能测试工具

### 基准测试工具

#### 脚本位置
`scripts/run_benchmarks.py`

#### 功能
- 运行性能基准测试
- 比较不同版本的性能
- 检测性能回归
- 生成性能报告

#### 使用方法
```bash
# 运行所有基准测试
python scripts/run_benchmarks.py --all

# 运行特定基准测试
python scripts/run_benchmarks.py --benchmark turn_processing
python scripts/run_benchmarks.py --benchmark memory_operations

# 比较性能
python scripts/run_benchmarks.py --compare v1.0 v1.1

# 检测性能回归
python scripts/run_benchmarks.py --regression-check
```

### 负载测试工具

#### 脚本位置
`scripts/run_load_tests.py`

#### 功能
- 模拟多用户负载
- 测试系统容量
- 识别性能瓶颈
- 生成负载测试报告

#### 使用方法
```bash
# 运行负载测试
python scripts/run_load_tests.py \
  --users 100 \
  --duration 300 \
  --rate 10

# 运行特定场景的负载测试
python scripts/run_load_tests.py \
  --scenario heavy_writing \
  --users 50 \
  --duration 600

# 生成负载测试报告
python scripts/run_load_tests.py \
  --report \
  --output reports/load_test_report.html
```

### 压力测试工具

#### 脚本位置
`scripts/run_stress_tests.py`

#### 功能
- 测试系统极限
- 验证错误处理
- 测试恢复能力
- 生成压力测试报告

#### 使用方法
```bash
# 运行压力测试
python scripts/run_stress_tests.py \
  --intensity high \
  --duration 900

# 测试特定组件的压力
python scripts/run_stress_tests.py \
  --component database \
  --intensity extreme

# 测试故障恢复
