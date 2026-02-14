#!/usr/bin/env python3
"""
LOOM 部署验证脚本

功能：
1. 验证本地部署
2. 验证 Docker 部署
3. 验证 Kubernetes 部署
4. 验证云部署端点
5. 生成验证报告

用法：
    python scripts/deploy_verify.py --help
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import requests

PROJECT_ROOT = Path(__file__).parent.parent


class DeploymentVerifier:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []

    def log(self, message: str):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def record_result(self, test_name: str, success: bool, details: str = ""):
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time(),
        }
        self.results.append(result)
        status = "✓" if success else "✗"
        print(f"  {status} {test_name}")
        if details and not success:
            print(f"    {details}")

    def run_command(self, cmd: str, cwd: Optional[Path] = None) -> Tuple[bool, str]:
        """运行命令并返回成功状态和输出"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=30,
            )
            if self.verbose:
                print(f"命令: {cmd}")
                if result.stdout:
                    print(f"输出: {result.stdout}")
                if result.stderr:
                    print(f"错误: {result.stderr}")
            return result.returncode == 0, result.stdout.strip()
        except subprocess.TimeoutExpired:
            return False, "命令超时"
        except Exception as e:
            return False, str(e)

    def check_http_endpoint(self, url: str, timeout: int = 10) -> Tuple[bool, str]:
        """检查 HTTP 端点"""
        try:
            response = requests.get(url, timeout=timeout)
            if response.status_code == 200:
                return True, f"状态码: {response.status_code}"
            else:
                return False, f"状态码: {response.status_code}"
        except requests.exceptions.RequestException as e:
            return False, str(e)

    def verify_local_installation(self) -> bool:
        """验证本地安装"""
        self.log("验证本地安装...")

        # 检查 Python 包
        success, output = self.run_command(
            'python -c "import loom; print(loom.__version__)"'
        )
        self.record_result("导入 loom 模块", success, output)

        # 检查 CLI 命令
        success, output = self.run_command("loom --help")
        self.record_result("CLI 命令可用", success, output)

        # 检查 Web 服务器
        success, output = self.run_command(
            "python -c \"from loom.web.app import app; print('Web app loaded')\""
        )
        self.record_result("Web 应用加载", success, output)

        return all(r["success"] for r in self.results[-3:])

    def verify_docker_deployment(self) -> bool:
        """验证 Docker 部署"""
        self.log("验证 Docker 部署...")

        # 检查 Docker 是否运行
        success, output = self.run_command("docker --version")
        self.record_result("Docker 可用", success, output)

        # 检查 Docker 镜像构建
        success, output = self.run_command("docker build -t loom-test .")
        self.record_result("Docker 镜像构建", success, output)

        # 运行容器并检查健康状态
        success, output = self.run_command(
            "docker run -d -p 8000:8000 --name loom-test loom-test"
        )
        if success:
            time.sleep(5)  # 等待容器启动
            success, output = self.check_http_endpoint("http://localhost:8000/health")
            self.record_result("Docker 容器健康检查", success, output)

            # 停止并清理容器
            self.run_command("docker stop loom-test")
            self.run_command("docker rm loom-test")
        else:
            self.record_result("Docker 容器健康检查", False, "容器启动失败")

        # 清理镜像
        self.run_command("docker rmi loom-test")

        return all(r["success"] for r in self.results[-3:])

    def verify_kubernetes_deployment(self) -> bool:
        """验证 Kubernetes 部署"""
        self.log("验证 Kubernetes 部署...")

        # 检查 kubectl
        success, output = self.run_command("kubectl version --client")
        self.record_result("kubectl 可用", success, output)

        # 检查 Kubernetes 配置文件
        config_path = PROJECT_ROOT / "kubernetes"
        if config_path.exists():
            self.record_result("Kubernetes 配置存在", True, str(config_path))

            # 检查配置文件语法
            files = [
                "namespace.yaml",
                "configmap.yaml",
                "deployment.yaml",
                "service.yaml",
            ]
            for file in files:
                file_path = config_path / file
                if file_path.exists():
                    success, output = self.run_command(
                        f"kubectl apply --dry-run=client -f {file_path}"
                    )
                    self.record_result(f"Kubernetes {file} 语法检查", success, output)
                else:
                    self.record_result(f"Kubernetes {file} 语法检查", False, "文件不存在")
        else:
            self.record_result("Kubernetes 配置存在", False, "kubernetes 目录不存在")

        return all(r["success"] for r in self.results[-5:])

    def verify_cloud_endpoints(self, endpoints: List[str]) -> bool:
        """验证云部署端点"""
        self.log("验证云部署端点...")

        all_success = True
        for endpoint in endpoints:
            success, details = self.check_http_endpoint(endpoint)
            self.record_result(f"端点 {endpoint}", success, details)
            if not success:
                all_success = False

        return all_success

    def verify_monitoring(self) -> bool:
        """验证监控配置"""
        self.log("验证监控配置...")

        # 检查 Prometheus metrics 端点（如果运行）
        success, details = self.check_http_endpoint("http://localhost:8001/metrics")
        self.record_result("Prometheus metrics 端点", success, details)

        # 检查健康端点
        success, details = self.check_http_endpoint("http://localhost:8000/health")
        self.record_result("健康检查端点", success, details)

        # 检查就绪端点
        success, details = self.check_http_endpoint("http://localhost:8000/ready")
        self.record_result("就绪检查端点", success, details)

        return all(r["success"] for r in self.results[-3:])

    def generate_report(self, output_file: Optional[Path] = None) -> Dict:
        """生成验证报告"""
        report = {
            "timestamp": time.time(),
            "total_tests": len(self.results),
            "passed_tests": sum(1 for r in self.results if r["success"]),
            "failed_tests": sum(1 for r in self.results if not r["success"]),
            "results": self.results,
            "summary": "所有测试通过"
            if all(r["success"] for r in self.results)
            else "部分测试失败",
        }

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            self.log(f"报告已保存到 {output_file}")

        return report

    def print_summary(self):
        """打印验证摘要"""
        print("\n" + "=" * 60)
        print("部署验证摘要")
        print("=" * 60)

        passed = sum(1 for r in self.results if r["success"])
        total = len(self.results)

        print(f"总测试数: {total}")
        print(f"通过: {passed}")
        print(f"失败: {total - passed}")
        print(f"通过率: {passed/total*100:.1f}%")

        if total - passed > 0:
            print("\n失败测试:")
            for result in self.results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="LOOM 部署验证脚本")
    parser.add_argument("--local", action="store_true", help="验证本地安装")
    parser.add_argument("--docker", action="store_true", help="验证 Docker 部署")
    parser.add_argument("--kubernetes", action="store_true", help="验证 Kubernetes 配置")
    parser.add_argument("--monitoring", action="store_true", help="验证监控配置")
    parser.add_argument("--cloud-endpoints", nargs="+", help="验证云部署端点")
    parser.add_argument("--all", action="store_true", help="运行所有验证")
    parser.add_argument("--report", help="生成 JSON 报告文件")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    if not any(
        [
            args.local,
            args.docker,
            args.kubernetes,
            args.monitoring,
            args.cloud_endpoints,
            args.all,
        ]
    ):
        parser.print_help()
        sys.exit(1)

    verifier = DeploymentVerifier(verbose=args.verbose)

    if args.all or args.local:
        verifier.verify_local_installation()

    if args.all or args.docker:
        verifier.verify_docker_deployment()

    if args.all or args.kubernetes:
        verifier.verify_kubernetes_deployment()

    if args.all or args.monitoring:
        verifier.verify_monitoring()

    if args.cloud_endpoints:
        verifier.verify_cloud_endpoints(args.cloud_endpoints)

    # 生成报告
    report_file = Path(args.report) if args.report else None
    report = verifier.generate_report(report_file)

    # 打印摘要
    verifier.print_summary()

    # 返回退出码
    if report["failed_tests"] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()
