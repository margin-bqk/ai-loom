#!/usr/bin/env python3
"""
LOOM 部署回滚脚本

功能：
1. 回滚 Docker 部署
2. 回滚 Kubernetes 部署
3. 回滚云部署
4. 恢复备份

用法：
    python scripts/rollback.py --help
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).parent.parent


class RollbackManager:
    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def log(self, message: str):
        print(f"[{time.strftime('%H:%M:%S')}] {message}")

    def run_command(self, cmd: str, cwd: Optional[Path] = None) -> bool:
        """运行命令并返回成功状态"""
        try:
            if self.verbose:
                print(f"执行: {cmd}")
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=cwd or PROJECT_ROOT,
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode != 0:
                print(f"命令失败: {cmd}")
                print(f"错误: {result.stderr}")
                return False
            return True
        except subprocess.TimeoutExpired:
            print(f"命令超时: {cmd}")
            return False
        except Exception as e:
            print(f"命令异常: {cmd}")
            print(f"异常: {e}")
            return False

    def rollback_docker(
        self, previous_tag: str = "stable", current_tag: str = "latest"
    ):
        """回滚 Docker 部署"""
        self.log(f"回滚 Docker 部署: {current_tag} -> {previous_tag}")

        # 停止当前容器
        self.run_command("docker stop loom-app 2>/dev/null || true")
        self.run_command("docker rm loom-app 2>/dev/null || true")

        # 拉取上一个版本的镜像
        self.run_command(f"docker pull yourregistry/loom:{previous_tag}")

        # 运行上一个版本的容器
        cmd = f"docker run -d -p 8000:8000 --name loom-app yourregistry/loom:{previous_tag}"
        if self.run_command(cmd):
            self.log("Docker 回滚成功")
            return True
        else:
            self.log("Docker 回滚失败")
            return False

    def rollback_kubernetes(
        self, namespace: str = "loom", previous_version: str = "v0.1.0"
    ):
        """回滚 Kubernetes 部署"""
        self.log(f"回滚 Kubernetes 部署到版本 {previous_version}")

        # 检查 kubectl 是否可用
        if not self.run_command("kubectl version --client"):
            self.log("错误: kubectl 不可用")
            return False

        # 回滚 Deployment
        cmd = f"kubectl rollout undo deployment/loom -n {namespace}"
        if self.run_command(cmd):
            self.log("Kubernetes 回滚成功")

            # 等待回滚完成
            self.run_command(
                f"kubectl rollout status deployment/loom -n {namespace} --timeout=300s"
            )
            return True
        else:
            # 如果回滚失败，尝试使用之前的镜像标签
            self.log("尝试使用之前的镜像标签...")
            patch_cmd = f"kubectl set image deployment/loom loom=yourregistry/loom:{previous_version} -n {namespace}"
            if self.run_command(patch_cmd):
                self.log("镜像标签更新成功")
                return True

        self.log("Kubernetes 回滚失败")
        return False

    def rollback_cloudformation(self, stack_name: str = "loom-stack"):
        """回滚 CloudFormation 堆栈"""
        self.log(f"回滚 CloudFormation 堆栈 {stack_name}")

        # 检查 AWS CLI 是否可用
        if not self.run_command("aws --version"):
            self.log("错误: AWS CLI 不可用")
            return False

        # 获取上一个成功的堆栈版本
        cmd = f"aws cloudformation list-stack-resources --stack-name {stack_name}"
        if not self.run_command(cmd):
            self.log("无法获取堆栈信息")
            return False

        # 回滚到上一个版本（这里需要根据实际情况实现）
        self.log("CloudFormation 回滚需要手动操作")
        print("建议步骤:")
        print("1. 在 AWS 控制台中找到 CloudFormation 堆栈")
        print("2. 选择 '回滚到上一个成功的版本'")
        print("3. 或使用: aws cloudformation rollback-stack --stack-name loom-stack")

        return False

    def restore_backup(self, backup_file: str, target_dir: str = "/app/data"):
        """从备份恢复数据"""
        self.log(f"从备份恢复数据: {backup_file}")

        if not Path(backup_file).exists():
            self.log(f"错误: 备份文件不存在 {backup_file}")
            return False

        # 根据备份类型执行恢复
        if backup_file.endswith(".tar.gz"):
            cmd = f"tar -xzf {backup_file} -C {target_dir}"
        elif backup_file.endswith(".sql"):
            cmd = f"sqlite3 {target_dir}/loom.db < {backup_file}"
        else:
            self.log(f"错误: 不支持的备份格式 {backup_file}")
            return False

        if self.run_command(cmd):
            self.log("数据恢复成功")
            return True
        else:
            self.log("数据恢复失败")
            return False

    def create_emergency_plan(self):
        """创建紧急回滚计划文档"""
        self.log("创建紧急回滚计划...")

        plan = """# LOOM 紧急回滚计划

## 情况评估
1. 确定问题范围（全部/部分功能不可用）
2. 评估影响（用户影响、数据丢失风险）
3. 确定回滚目标版本

## 回滚步骤

### 1. 停止当前部署
- Docker: `docker stop loom-app`
- Kubernetes: `kubectl scale deployment/loom --replicas=0 -n loom`
- 云服务: 根据提供商控制台停止服务

### 2. 数据备份
- 备份当前数据: `tar -czf backup-$(date +%Y%m%d-%H%M%S).tar.gz /app/data`
- 导出数据库: `sqlite3 /app/data/loom.db .dump > backup-$(date +%Y%m%d-%H%M%S).sql`

### 3. 执行回滚
根据部署方式选择：

#### Docker 回滚
```bash
docker pull yourregistry/loom:stable
docker run -d -p 8000:8000 -v ./data:/app/data --name loom-app yourregistry/loom:stable
```

#### Kubernetes 回滚
```bash
kubectl rollout undo deployment/loom -n loom
kubectl rollout status deployment/loom -n loom --timeout=300s
```

#### 云服务回滚
- AWS ECS: 更新任务定义到上一个版本
- Azure AKS: 更新 Deployment 镜像标签
- GCP GKE: 类似 Kubernetes 回滚

### 4. 验证回滚
- 检查服务状态: `curl http://localhost:8000/health`
- 验证核心功能
- 检查数据完整性

### 5. 通知和沟通
- 通知团队回滚已完成
- 更新状态页面
- 记录根本原因分析

## 联系人
- 运维负责人: [姓名]
- 开发负责人: [姓名]
- 产品负责人: [姓名]

## 附录
- 备份位置: /backups/
- 监控仪表板: http://monitoring.example.com
- 文档: https://docs.loom.dev/emergency
"""

        with open("EMERGENCY_ROLLBACK_PLAN.md", "w", encoding="utf-8") as f:
            f.write(plan)

        self.log("紧急回滚计划已保存到 EMERGENCY_ROLLBACK_PLAN.md")
        return True


def main():
    parser = argparse.ArgumentParser(description="LOOM 部署回滚脚本")
    parser.add_argument("--docker", action="store_true", help="回滚 Docker 部署")
    parser.add_argument("--k8s", action="store_true", help="回滚 Kubernetes 部署")
    parser.add_argument("--aws", action="store_true", help="回滚 AWS 部署")
    parser.add_argument("--backup", help="从备份文件恢复数据")
    parser.add_argument("--plan", action="store_true", help="创建紧急回滚计划")
    parser.add_argument("--all", action="store_true", help="执行完整回滚流程")
    parser.add_argument("--verbose", "-v", action="store_true", help="详细输出")

    args = parser.parse_args()

    if not any([args.docker, args.k8s, args.aws, args.backup, args.plan, args.all]):
        parser.print_help()
        sys.exit(1)

    manager = RollbackManager(verbose=args.verbose)

    success = True

    if args.all or args.docker:
        if not manager.rollback_docker():
            success = False

    if args.all or args.k8s:
        if not manager.rollback_kubernetes():
            success = False

    if args.all or args.aws:
        if not manager.rollback_cloudformation():
            success = False

    if args.backup:
        if not manager.restore_backup(args.backup):
            success = False

    if args.plan:
        manager.create_emergency_plan()

    if success:
        print("\n回滚操作完成")
        sys.exit(0)
    else:
        print("\n回滚操作失败")
        sys.exit(1)


if __name__ == "__main__":
    main()
