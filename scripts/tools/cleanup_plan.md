# 项目清理计划

## 概述
本计划旨在整理 `ai-loom` 项目的目录结构，将临时文件、测试文件和调试文件移动到合适的位置，保持根目录整洁。

## 当前问题分析
根据项目分析，根目录中存在以下类型的文件需要整理：

### 1. Debug文件 (`debug_*.py`)
- `debug_canon_fixed.py`
- `debug_canon.py`
- `debug_yaml_dump.py`

**问题**: 这些调试文件应该放在专门的调试目录中，而不是根目录。

### 2. 临时测试文件 (`test_*.py`)
- `test_all_fixes.py`
- `test_config_reset_fixed_simple.py`
- `test_config_reset_fixed.py`
- `test_config_reset.py`
- `test_db.py`
- `test_field_issue.py`
- `test_rule_fix_verification.py`
- `test_rule_validation_fixed.py`
- `test_rule_validation.py`
- `test_session_db_fixed.py`
- `test_session_db.py`

**问题**: 这些测试文件应该放在 `tests/` 目录下的相应子目录中。

### 3. Verify文件 (`verify_*.py`)
- `verify_fixes_simple.py`

**问题**: 验证文件应该整合到测试套件中。

### 4. 其他临时文件
- `search_config_list.py` - 配置搜索工具
- `test_input.txt` - 测试输入文件
- `loom.db` - 数据库文件（应保留）

## 清理策略

### 第一阶段：目录结构调整
1. **创建必要的目录**
   - `scripts/debug/` - 存放调试脚本
   - `tests/temp/` - 存放临时测试文件
   - `tests/verify/` - 存放验证脚本
   - `temp_backup/` - 临时备份目录

2. **文件移动规则**
   - `debug_*.py` → `scripts/debug/`
   - `test_*.py` → `tests/temp/`（临时位置，后续可进一步分类）
   - `verify_*.py` → `tests/verify/`
   - 临时文本文件 → `temp_backup/`

3. **保留的重要文件**
   - 配置文件：`.env.example`, `.flake8`, `.gitignore`, `.pre-commit-config.yaml`
   - 项目文档：`CHANGELOG.md`, `README.md`, `RELEASE_CHECKLIST*.md`
   - 构建文件：`docker-compose.yml`, `Dockerfile`, `pyproject.toml`, `requirements.txt`
   - 数据库文件：`loom.db`

### 第二阶段：文件分类整理
1. **测试文件进一步分类**
   - 单元测试 → `tests/test_core/`
   - 集成测试 → `tests/test_integration/`
   - 规则测试 → `tests/test_rules/`
   - 临时测试 → `tests/temp/`（保留）

2. **脚本文件整理**
   - 部署脚本 → `scripts/`（已存在）
   - 调试脚本 → `scripts/debug/`
   - 工具脚本 → `scripts/tools/`（可创建）

### 第三阶段：清理验证
1. **验证移动结果**
   - 检查文件是否完整移动
   - 更新相关导入路径（如果需要）
   - 验证脚本功能

2. **生成清理报告**
   - 统计移动的文件数量
   - 记录遇到的问题
   - 提供回滚方案

## 实施步骤

### 步骤1：分析当前状态
```bash
python scripts/cleanup_project.py --dry-run
```

### 步骤2：生成清理报告
```bash
python scripts/cleanup_project.py --report
```

### 步骤3：执行清理（需要确认）
```bash
python scripts/cleanup_project.py
```

### 步骤4：自动执行清理（无需确认）
```bash
python scripts/cleanup_project.py --yes
```

## 安全措施

### 1. 备份机制
- 所有移动操作都会检查目标文件是否存在
- 如果目标文件已存在，会自动添加数字后缀
- 不会删除任何文件，只会移动

### 2. 重要文件保护
- 重要文件列表已硬编码在脚本中
- 这些文件不会被移动
- 数据库文件 `loom.db` 会被特别保护

### 3. 错误处理
- 每个文件移动操作都有异常处理
- 错误会被记录并继续处理其他文件
- 最终会显示错误统计

## 预期结果

### 清理后的目录结构
```
ai-loom/
├── scripts/
│   ├── debug/
│   │   ├── debug_canon_fixed.py
│   │   ├── debug_canon.py
│   │   └── debug_yaml_dump.py
│   └── cleanup_project.py
├── tests/
│   ├── temp/
│   │   ├── test_all_fixes.py
│   │   ├── test_config_reset_fixed_simple.py
│   │   └── ...（其他测试文件）
│   └── verify/
│       └── verify_fixes_simple.py
├── temp_backup/
│   ├── search_config_list.py
│   └── test_input.txt
└── （干净的根目录）
```

### 根目录保留的文件
- `.env.example`
- `.flake8`
- `.gitignore`
- `.pre-commit-config.yaml`
- `CHANGELOG.md`
- `docker-compose.yml`
- `Dockerfile`
- `loom.db`
- `pyproject.toml`
- `README.md`
- `RELEASE_CHECKLIST_v0.10.0.md`
- `RELEASE_CHECKLIST.md`
- `requirements.txt`

## 风险与缓解

### 风险1：文件依赖关系破坏
- **风险**: 移动文件可能破坏其他脚本的导入路径
- **缓解**:
  - 只移动独立的调试和测试文件
  - 不移动被其他文件引用的文件
  - 提供回滚方案

### 风险2：重要文件误移动
- **风险**: 意外移动重要配置文件
- **缓解**:
  - 使用白名单保护重要文件
  - 在移动前显示将要操作的文件列表
  - 提供确认步骤

### 风险3：文件名冲突
- **风险**: 目标目录中已存在同名文件
- **缓解**:
  - 自动添加数字后缀避免覆盖
  - 显示重命名信息

## 后续改进建议

### 1. 自动化集成
- 将清理脚本集成到 CI/CD 流程
- 在发布前自动运行清理
- 添加预提交钩子检查

### 2. 智能分类
- 根据文件内容自动分类测试文件
- 识别重复或过时的文件
- 建议删除不必要的文件

### 3. 定期维护
- 每月运行一次清理脚本
- 清理 `temp_backup/` 目录中的旧文件
- 更新重要文件白名单

## 执行时间表
- **立即执行**: 第一阶段目录结构调整
- **一周内**: 第二阶段文件分类整理
- **一个月内**: 评估清理效果，进行优化

## 联系方式
如有问题或建议，请参考项目文档或联系维护团队。

---
*最后更新: 2026-02-07*
*清理脚本版本: 1.0.0*
