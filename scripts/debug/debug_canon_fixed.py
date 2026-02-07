#!/usr/bin/env python3
"""调试MarkdownCanon（修复版）"""

import sys
from pathlib import Path

# 添加src目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from loom.rules.markdown_canon import MarkdownCanon


def test_canon_creation():
    """测试Canon创建"""
    print("=== 测试MarkdownCanon创建 ===")

    # 创建一个简单的规则内容
    content = """# 世界设定
这是一个测试世界。

# 叙事基调
严肃的奇幻风格。
"""

    print(f"1. 正确创建MarkdownCanon实例...")
    # 正确的方式：传递path和raw_content，让sections使用默认值
    canon = MarkdownCanon(Path("test.md"), raw_content=content)

    print(f"2. 检查canon类型: {type(canon)}")
    print(f"3. 检查sections类型: {type(canon.sections)}")
    print(f"4. 检查sections值: {canon.sections}")

    if isinstance(canon.sections, dict):
        print(f"5. sections是字典，键: {list(canon.sections.keys())}")
        for key, value in canon.sections.items():
            print(f"   - {key}: {type(value)}")
            if hasattr(value, "name"):
                print(f"     名称: {value.name}, 类型: {value.section_type}")
    else:
        print(f"5. sections不是字典，实际类型: {type(canon.sections)}")
        print(f"   值: {canon.sections}")


def test_template_canon():
    """测试模板Canon"""
    print("\n=== 测试模板Canon ===")

    template_path = Path("templates/rules/fantasy_basic.md")
    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()

    print(f"1. 读取模板文件: {template_path}")
    print(f"2. 文件大小: {len(content)} 字符")

    # 正确创建Canon
    canon = MarkdownCanon(template_path, raw_content=content)

    print(f"3. 检查sections类型: {type(canon.sections)}")

    if isinstance(canon.sections, dict):
        print(f"4. 找到的章节:")
        for section_name, section in canon.sections.items():
            print(f"   - {section_name} (类型: {section.section_type.value})")
            print(f"     内容前50字符: {section.content[:50]}...")
    else:
        print(f"4. sections不是字典: {type(canon.sections)}")


def test_wrong_way():
    """测试错误的方式"""
    print("\n=== 测试错误创建方式 ===")

    content = "测试内容"

    print("1. 错误方式: MarkdownCanon(Path('test.md'), content)")
    try:
        canon = MarkdownCanon(Path("test.md"), content)
        print(f"   sections类型: {type(canon.sections)}")
        print(f"   sections值: {canon.sections}")
    except Exception as e:
        print(f"   错误: {e}")

    print("\n2. 正确方式: MarkdownCanon(Path('test.md'), raw_content=content)")
    try:
        canon = MarkdownCanon(Path("test.md"), raw_content=content)
        print(f"   sections类型: {type(canon.sections)}")
        print(f"   sections值: {canon.sections}")
    except Exception as e:
        print(f"   错误: {e}")


if __name__ == "__main__":
    test_wrong_way()
    test_canon_creation()
    test_template_canon()
