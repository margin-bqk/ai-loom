#!/usr/bin/env python3
"""
批量更新LOOM项目文档中的术语
将"叙事解释器"相关术语改为"叙事解释器"相关术语
"""

import os
import re
from pathlib import Path
from typing import List, Tuple

# 定义术语映射
TERM_MAPPINGS = [
    # 主要术语映射
    ("叙事解释器", "叙事解释器"),
    ("叙事解释器", "叙事解释器"),
    ("解释器", "解释器"),
    ("Language-Oriented Open Mythos", "Language-Oriented Open Mythos"),
    ("语言驱动的开放叙事解释器运行时", "语言驱动的开放叙事解释器运行时"),
    ("非承载式架构", "非承载式架构"),
    ("叙事失明", "叙事失明"),
    ("运行时核心层", "运行时核心层"),
    ("规则层", "规则层"),
    ("解释层", "解释层"),
    ("世界记忆层", "世界记忆层"),
    ("玩家干预层", "玩家干预层"),
    ("Markdown规则", "Markdown规则"),
    ("LLM推理", "LLM推理"),
    ("世界记忆", "世界记忆"),
    ("玩家干预", "玩家干预"),
    # 次要术语映射
    ("解释器本身", "解释器本身"),
    ("解释器不解析", "解释器不解析"),
    ("解释器只负责", "解释器只负责"),
    ("解释器采用", "解释器采用"),
    ("解释器提供", "解释器提供"),
    ("解释器核心", "解释器核心"),
    ("解释器架构", "解释器架构"),
    ("解释器设计", "解释器设计"),
    ("解释器实现", "解释器实现"),
    ("解释器功能", "解释器功能"),
    ("解释器特性", "解释器特性"),
    ("解释器性能", "解释器性能"),
    ("解释器配置", "解释器配置"),
    ("解释器部署", "解释器部署"),
    ("解释器监控", "解释器监控"),
    ("解释器扩展", "解释器扩展"),
    ("解释器插件", "解释器插件"),
    ("解释器接口", "解释器接口"),
    ("解释器测试", "解释器测试"),
    ("解释器文档", "解释器文档"),
    ("解释器社区", "解释器社区"),
    ("解释器贡献", "解释器贡献"),
    ("解释器许可证", "解释器许可证"),
    ("解释器状态", "解释器状态"),
    ("解释器更新", "解释器更新"),
    ("解释器版本", "解释器版本"),
    ("解释器发布", "解释器发布"),
    ("解释器安装", "解释器安装"),
    ("解释器使用", "解释器使用"),
    ("解释器教程", "解释器教程"),
    ("解释器示例", "解释器示例"),
    ("解释器模板", "解释器模板"),
    ("解释器工具", "解释器工具"),
    ("解释器命令", "解释器命令"),
    ("解释器界面", "解释器界面"),
    ("解释器API", "解释器API"),
    ("解释器SDK", "解释器SDK"),
    ("解释器CLI", "解释器CLI"),
    ("解释器Web", "解释器Web"),
    ("解释器Docker", "解释器Docker"),
    ("解释器Kubernetes", "解释器Kubernetes"),
    ("解释器部署", "解释器部署"),
    ("解释器监控", "解释器监控"),
    ("解释器日志", "解释器日志"),
    ("解释器指标", "解释器指标"),
    ("解释器追踪", "解释器追踪"),
    ("解释器安全", "解释器安全"),
    ("解释器性能", "解释器性能"),
    ("解释器优化", "解释器优化"),
    ("解释器测试", "解释器测试"),
    ("解释器质量", "解释器质量"),
    ("解释器代码", "解释器代码"),
    ("解释器开发", "解释器开发"),
    ("解释器贡献", "解释器贡献"),
    ("解释器社区", "解释器社区"),
    ("解释器许可证", "解释器许可证"),
    ("解释器状态", "解释器状态"),
    ("解释器更新", "解释器更新"),
    ("解释器版本", "解释器版本"),
    ("解释器发布", "解释器发布"),
]

# 需要处理的文件扩展名
TEXT_EXTENSIONS = {'.md', '.txt', '.rst', '.py', '.yaml', '.yml', '.json', '.toml'}

# 需要处理的目录
TARGET_DIRS = [
    'docs/',
    'examples/',
    'templates/',
    'src/loom/',
    'scripts/',
    'config/',
]

# 排除的文件和目录
EXCLUDE_PATTERNS = [
    '__pycache__',
    '.git',
    '.venv',
    'venv',
    'node_modules',
    'dist',
    'build',
    '*.pyc',
    '*.pyo',
    '*.so',
    '*.dll',
    '*.exe',
    '*.bin',
]

def should_process_file(filepath: Path) -> bool:
    """判断是否应该处理该文件"""
    # 检查扩展名
    if filepath.suffix.lower() not in TEXT_EXTENSIONS:
        return False
    
    # 检查排除模式
    filepath_str = str(filepath)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in filepath_str:
            return False
    
    return True

def update_file_content(content: str) -> Tuple[str, int]:
    """更新文件内容中的术语"""
    changes = 0
    for old_term, new_term in TERM_MAPPINGS:
        # 使用正则表达式进行单词边界匹配
        pattern = r'\b' + re.escape(old_term) + r'\b'
        new_content, count = re.subn(pattern, new_term, content)
        if count > 0:
            content = new_content
            changes += count
    
    return content, changes

def process_file(filepath: Path) -> int:
    """处理单个文件"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        new_content, changes = update_file_content(content)
        
        if changes > 0:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✓ {filepath}: 更新了 {changes} 处术语")
            return changes
        else:
            print(f"  - {filepath}: 无需更新")
            return 0
    except Exception as e:
        print(f"  ✗ {filepath}: 错误 - {e}")
        return 0

def process_directory(directory: Path) -> Tuple[int, int]:
    """处理目录中的所有文件"""
    total_files = 0
    total_changes = 0
    
    for root, dirs, files in os.walk(directory):
        # 过滤排除的目录
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in EXCLUDE_PATTERNS)]
        
        for file in files:
            filepath = Path(root) / file
            if should_process_file(filepath):
                total_files += 1
                changes = process_file(filepath)
                total_changes += changes
    
    return total_files, total_changes

def main():
    """主函数"""
    print("LOOM项目术语更新工具")
    print("=" * 50)
    
    base_dir = Path.cwd()
    print(f"工作目录: {base_dir}")
    
    total_processed_files = 0
    total_changes_made = 0
    
    for target_dir in TARGET_DIRS:
        target_path = base_dir / target_dir
        if target_path.exists():
            print(f"\n处理目录: {target_dir}")
            files, changes = process_directory(target_path)
            total_processed_files += files
            total_changes_made += changes
        else:
            print(f"\n跳过不存在的目录: {target_dir}")
    
    # 处理根目录下的文件
    print(f"\n处理根目录文件")
    for file in base_dir.iterdir():
        if file.is_file() and should_process_file(file):
            total_processed_files += 1
            changes = process_file(file)
            total_changes_made += changes
    
    print("\n" + "=" * 50)
    print(f"处理完成!")
    print(f"处理文件数: {total_processed_files}")
    print(f"总术语更新数: {total_changes_made}")
    
    # 显示术语映射摘要
    print(f"\n术语映射摘要:")
    for old_term, new_term in TERM_MAPPINGS[:10]:  # 只显示前10个
        print(f"  {old_term} → {new_term}")
    if len(TERM_MAPPINGS) > 10:
        print(f"  ... 还有 {len(TERM_MAPPINGS) - 10} 个映射")

if __name__ == "__main__":
    main()