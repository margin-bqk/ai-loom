# LOOM 修复验证工具

`verify_fixes.py` 是一个统一的修复验证工具，用于检查修复后的文档与代码一致性、Docker配置、CLI命令等。

## 功能特性

1. **集成现有验证功能**：整合 `scripts/verification/` 目录下的现有验证脚本
2. **检查文档与代码一致性**：验证修复后的文档与代码是否一致
3. **验证Docker Compose配置**：检查多环境Docker配置的正确性
4. **验证CLI命令一致性**：检查CLI文档与实际实现的一致性
5. **验证快速开始指南**：检查安装命令和示例的正确性
6. **生成详细报告**：提供修复验证的详细结果报告

## 安装要求

- Python 3.8+
- 依赖包：PyYAML

## 使用方法

### 基本使用

```bash
# 查看帮助
python verify_fixes.py --help

# 运行所有验证
python verify_fixes.py

# 只验证文档一致性
python verify_fixes.py --category docs

# 验证Docker配置
python verify_fixes.py --category docker

# 验证CLI命令
python verify_fixes.py --category cli

# 验证快速开始指南
python verify_fixes.py --category quickstart

# 集成现有验证脚本
python verify_fixes.py --category scripts
```

### 输出选项

```bash
# 控制台输出（默认）
python verify_fixes.py --output console

# JSON输出
python verify_fixes.py --output json --output-file report.json

# 同时输出到控制台和JSON文件
python verify_fixes.py --output both --output-file verification_results.json
```

### 详细模式

```bash
# 启用详细输出
python verify_fixes.py --verbose
```

## 验证类别说明

### 1. 现有脚本验证 (scripts)
- 检查 `scripts/verification/` 目录下的验证脚本
- 验证脚本的可导入性和基本结构

### 2. 文档代码一致性验证 (docs)
- CLI命令文档与实现的一致性
- 配置文档与配置文件的一致性
- API文档与实现的一致性

### 3. Docker配置验证 (docker)
- Docker Compose文件结构验证
- 多环境配置文件验证
- Dockerfile完整性检查

### 4. CLI命令验证 (cli)
- CLI命令可执行性验证
- 帮助系统完整性检查

### 5. 快速开始指南验证 (quickstart)
- 快速开始文档完整性检查
- 安装命令正确性验证
- 示例代码语法检查

## 报告格式

### 控制台报告
```
开始验证修复...
============================================================

执行验证: DocCodeConsistencyVerifier
----------------------------------------

============================================================
验证结果汇总
============================================================
总计: 4
通过: 2
失败: 1
警告: 1
跳过: 0

[WARNING] 文档代码一致性 - CLI命令文档完整性
  消息: 有1个实现的CLI命令未在文档中提及
  详情: {
  "missing_commands": [
    "init"
  ]
}
```

### JSON报告格式
```json
{
  "summary": {
    "total": 4,
    "passed": 2,
    "failed": 1,
    "warnings": 1,
    "skipped": 0
  },
  "results": [
    {
      "category": "文档代码一致性",
      "check_name": "CLI命令文档完整性",
      "status": "WARNING",
      "message": "有1个实现的CLI命令未在文档中提及",
      "details": {
        "missing_commands": ["init"]
      },
      "timestamp": "2026-02-13T10:59:30.123456"
    }
  ],
  "generated_at": "2026-02-13T10:59:30.123456"
}
```

## 集成到CI/CD

### GitHub Actions 示例
```yaml
name: Verify Fixes

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  verify:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pyyaml
    
    - name: Run verification
      run: |
        python verify_fixes.py --output both --output-file verification_report.json
    
    - name: Upload verification report
      uses: actions/upload-artifact@v3
      with:
        name: verification-report
        path: verification_report.json
```

### 预提交钩子示例
在 `.pre-commit-config.yaml` 中添加：
```yaml
repos:
  - repo: local
    hooks:
      - id: verify-fixes
        name: Verify fixes
        entry: python verify_fixes.py --category docs
        language: system
        pass_filenames: false
        always_run: true
```

## 扩展验证器

要添加新的验证器，请继承 `BaseVerifier` 类：

```python
class CustomVerifier(BaseVerifier):
    """自定义验证器"""
    
    def verify(self):
        # 实现验证逻辑
        self.report.add_result(VerificationResult(
            category="自定义",
            check_name="示例检查",
            status=VerificationStatus.PASS,
            message="验证通过",
            details={},
            timestamp=datetime.now().isoformat()
        ))
```

然后在 `main()` 函数中添加新的验证器。

## 故障排除

### 常见问题

1. **ImportError: No module named 'yaml'**
   ```bash
   pip install pyyaml
   ```

2. **CLI命令未找到**
   - 确保已安装LOOM：`pip install -e .`

3. **文件编码问题**
   - 脚本使用UTF-8编码，确保文件保存为UTF-8格式

### 调试模式
```bash
# 启用详细输出
python verify_fixes.py --verbose

# 使用Python调试
python -m pdb verify_fixes.py --category docs
```

## 贡献指南

1. 遵循现有代码风格
2. 添加适当的错误处理
3. 更新文档
4. 添加测试用例

## 许可证

本项目使用MIT许可证。
```

## 脚本结构

```
verify_fixes.py
├── VerificationStatus (状态枚举)
├── VerificationResult (验证结果数据类)
├── VerificationReport (报告生成器)
├── BaseVerifier (验证器基类)
├── ExistingScriptsVerifier (现有脚本验证)
├── DocCodeConsistencyVerifier (文档代码一致性验证)
├── DockerConfigVerifier (Docker配置验证)
├── CLICommandVerifier (CLI命令验证)
├── QuickStartVerifier (快速开始指南验证)
└── main() (主函数)
```

## 下一步计划

1. 添加更多验证类型（API测试、性能测试等）
2. 支持配置文件
3. 添加HTML报告生成
4. 集成到项目构建系统
5. 添加自动化修复建议