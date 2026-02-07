#!/usr/bin/env python3
"""
阶段1重构测试运行脚本
运行所有阶段1测试套件并生成报告
"""

import subprocess
import sys
import os
from datetime import datetime
from pathlib import Path

def run_tests():
    """运行所有阶段1测试"""
    print("=" * 80)
    print("LOOM项目重构 - 阶段1测试套件")
    print("=" * 80)
    
    # 测试目录
    test_dir = "tests/test_phase1"
    
    # 检查测试目录是否存在
    if not os.path.exists(test_dir):
        print(f"错误: 测试目录不存在: {test_dir}")
        return False
    
    print(f"测试目录: {test_dir}")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 运行测试
    cmd = [sys.executable, "-m", "pytest", test_dir, "-v", "--tb=short"]
    
    print(f"执行命令: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 输出测试结果
        print("测试输出:")
        print("-" * 80)
        print(result.stdout)
        
        if result.stderr:
            print("错误输出:")
            print("-" * 80)
            print(result.stderr)
        
        print("-" * 80)
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"退出代码: {result.returncode}")
        
        # 解析测试结果
        if "passed" in result.stdout:
            lines = result.stdout.split('\n')
            for line in lines:
                if "passed in" in line:
                    print(f"测试结果: {line.strip()}")
                    break
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"运行测试时出错: {e}")
        return False

def run_performance_tests():
    """运行性能基准测试"""
    print("\n" + "=" * 80)
    print("性能基准测试")
    print("=" * 80)
    
    cmd = [sys.executable, "-m", "pytest", 
           "tests/test_phase1/test_performance_benchmark.py", 
           "-v", "--tb=no"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        
        if result.stderr:
            print("错误:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"运行性能测试时出错: {e}")
        return False

def generate_coverage_report():
    """生成测试覆盖率报告"""
    print("\n" + "=" * 80)
    print("测试覆盖率报告")
    print("=" * 80)
    
    # 检查是否安装了pytest-cov
    try:
        import pytest_cov
    except ImportError:
        print("警告: 未安装pytest-cov，跳过覆盖率报告")
        return True
    
    cmd = [sys.executable, "-m", "pytest", 
           "tests/test_phase1/", 
           "--cov=src/loom",
           "--cov-report=term-missing",
           "--cov-report=html:coverage_html"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 输出覆盖率摘要
        lines = result.stdout.split('\n')
        coverage_section = False
        for line in lines:
            if "coverage" in line.lower() or "TOTAL" in line:
                print(line)
                coverage_section = True
            elif coverage_section and line.strip() and not line.startswith('---'):
                print(line)
        
        if os.path.exists("coverage_html/index.html"):
            print(f"\n详细覆盖率报告已生成: coverage_html/index.html")
        
        return True
    except Exception as e:
        print(f"生成覆盖率报告时出错: {e}")
        return False

def main():
    """主函数"""
    print("LOOM项目重构 - 阶段1测试验证脚本")
    print("版本: 1.0")
    print()
    
    # 运行所有测试
    all_passed = True
    
    # 1. 运行功能测试
    if not run_tests():
        all_passed = False
        print("\n❌ 功能测试失败")
    else:
        print("\n✅ 功能测试通过")
    
    # 2. 运行性能测试
    if not run_performance_tests():
        all_passed = False
        print("\n❌ 性能测试失败")
    else:
        print("\n✅ 性能测试通过")
    
    # 3. 生成覆盖率报告（可选）
    generate_coverage_report()
    
    # 总结
    print("\n" + "=" * 80)
    print("测试总结")
    print("=" * 80)
    
    if all_passed:
        print("✅ 所有测试通过！阶段1重构验证成功。")
        print("\n建议下一步:")
        print("1. 查看详细测试报告: docs/TEST_REPORT_PHASE1.md")
        print("2. 将阶段1代码合并到主分支")
        print("3. 开始阶段2（核心引擎重构）的规划")
        return 0
    else:
        print("❌ 测试失败！请检查失败原因。")
        print("\n建议:")
        print("1. 查看上面的错误输出")
        print("2. 修复失败的测试")
        print("3. 重新运行测试脚本")
        return 1

if __name__ == "__main__":
    sys.exit(main())