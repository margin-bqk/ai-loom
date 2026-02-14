#!/usr/bin/env python3
"""
验证结果分析脚本
"""

import json
import os


def analyze_verification_report():
    """分析验证报告"""
    with open("verification_report.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    summary = data["summary"]
    results = data["results"]

    total = summary["total"]
    passed = summary["passed"]
    failed = summary["failed"]
    warnings = summary["warnings"]

    success_rate = (passed / total) * 100

    print("=" * 80)
    print("LOOM 修复验证结果分析报告")
    print("=" * 80)
    print(f"\n[验证统计]:")
    print(f"  总计验证项: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")
    print(f"  警告: {warnings}")
    print(f"  修复成功率: {success_rate:.1f}%")

    print(f"\n[分类验证结果]:")
    categories = {}
    for result in results:
        category = result["category"]
        if category not in categories:
            categories[category] = {"total": 0, "passed": 0, "failed": 0, "warnings": 0}
        categories[category]["total"] += 1
        if result["status"] == "PASS":
            categories[category]["passed"] += 1
        elif result["status"] == "FAIL":
            categories[category]["failed"] += 1
        elif result["status"] == "WARNING":
            categories[category]["warnings"] += 1

    for category, stats in categories.items():
        rate = (stats["passed"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        print(f"  {category}: {stats['passed']}/{stats['total']} 通过 ({rate:.1f}%)")

    print(f"\n[失败项详细分析]:")
    fail_count = 0
    for result in results:
        if result["status"] == "FAIL":
            fail_count += 1
            print(f"\n  {fail_count}. {result['category']} - {result['check_name']}")
            print(f"     原因: {result['message']}")
            if "details" in result:
                details = result["details"]
                if "error" in details:
                    print(f"     错误: {details['error']}")
                elif "missing_implementations" in details:
                    print(f"     缺失实现: {len(details['missing_implementations'])} 个命令")

    print(f"\n[警告项分析]:")
    warning_count = 0
    for result in results:
        if result["status"] == "WARNING":
            warning_count += 1
            print(f"\n  {warning_count}. {result['category']} - {result['check_name']}")
            print(f"     问题: {result['message']}")

    print(f"\n[关键修复点验证状态]:")
    key_checks = [
        ("Docker配置", "Docker Compose结构"),
        ("Docker配置", "环境变量一致性"),
        ("CLI命令", "帮助命令"),
        ("快速开始指南", "安装命令完整性"),
        ("快速开始指南", "示例代码存在性"),
        ("文档代码一致性", "API文档存在性"),
    ]

    for category, check_name in key_checks:
        for result in results:
            if result["category"] == category and result["check_name"].startswith(
                check_name
            ):
                status_text = (
                    "[PASS]"
                    if result["status"] == "PASS"
                    else "[FAIL]"
                    if result["status"] == "FAIL"
                    else "[WARNING]"
                )
                print(f"  {status_text} {category}: {check_name}")

    print(f"\n[修复建议]:")
    print("  1. 脚本编码问题: 修复验证脚本中的Unicode字符编码问题（GBK环境）")
    print("  2. 依赖缺失: 安装aiosqlite依赖包")
    print("  3. CLI命令一致性: 更新文档以反映实际实现的命令")
    print("  4. CLI命令执行: 确保文档中的命令示例与实际命令一致")

    print(f"\n[总体评估]:")
    if success_rate >= 90:
        print("  [优秀] - 修复工作非常成功，大部分问题已解决")
    elif success_rate >= 75:
        print("  [良好] - 修复工作基本成功，但仍有改进空间")
    else:
        print("  [需要改进] - 修复工作尚未完成，需要进一步优化")

    print(f"\n[报告生成时间]: {data['generated_at']}")
    print("=" * 80)


if __name__ == "__main__":
    analyze_verification_report()
