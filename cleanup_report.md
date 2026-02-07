# 项目清理报告

## 文件分析结果

### Debug文件 (3个)
- debug_canon.py
- debug_canon_fixed.py
- debug_yaml_dump.py

### 测试文件 (11个)
- test_all_fixes.py
- test_config_reset.py
- test_config_reset_fixed.py
- test_config_reset_fixed_simple.py
- test_db.py
- test_field_issue.py
- test_rule_fix_verification.py
- test_rule_validation.py
- test_rule_validation_fixed.py
- test_session_db.py
- test_session_db_fixed.py

### Verify文件 (1个)
- verify_fixes_simple.py

### 临时文件 (2个)
- search_config_list.py
- test_input.txt

### 重要文件（不会移动） (13个)
- .env.example
- .flake8
- .gitignore
- .pre-commit-config.yaml
- CHANGELOG.md
- docker-compose.yml
- Dockerfile
- loom.db
- pyproject.toml
- README.md
- RELEASE_CHECKLIST.md
- RELEASE_CHECKLIST_v0.10.0.md
- requirements.txt

## 建议操作
1. 将debug_*.py文件移动到 `scripts/debug/` 目录
2. 将test_*.py文件移动到 `tests/temp/` 目录
3. 将verify_*.py文件移动到 `tests/verify/` 目录
4. 清理临时文件到 `temp_backup/` 目录

## 注意事项
- 数据库文件 `loom.db` 应保留在根目录
- 配置文件（.yaml, .yml）应保留在原位置
- 重要项目文件不应移动
