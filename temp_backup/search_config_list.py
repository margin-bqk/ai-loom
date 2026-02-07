import os
import re


def search_in_files(directory, pattern):
    """在目录中搜索文件内容"""
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(".md"):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                        if re.search(pattern, content, re.IGNORECASE):
                            print(f"找到匹配: {filepath}")
                            # 显示匹配的上下文
                            lines = content.split("\n")
                            for i, line in enumerate(lines):
                                if re.search(pattern, line, re.IGNORECASE):
                                    start = max(0, i - 2)
                                    end = min(len(lines), i + 3)
                                    print(f"  行 {i+1}:")
                                    for j in range(start, end):
                                        prefix = ">>> " if j == i else "    "
                                        print(f"{prefix}{lines[j]}")
                                    print()
                except Exception as e:
                    print(f"读取文件 {filepath} 时出错: {e}")


if __name__ == "__main__":
    print("搜索 'config list' 模式...")
    search_in_files("docs", r"config\s+list")

    print("\n搜索 'loom config list' 模式...")
    search_in_files("docs", r"loom\s+config\s+list")
