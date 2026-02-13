"""
版本控制集成

集成Git进行规则版本管理，支持分支、提交、回滚等操作。
与RuleLoader集成，管理规则演化。
"""

import subprocess
import shutil
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime

from ..utils.logging_config import get_logger
from .rule_loader import RuleLoader

logger = get_logger(__name__)


class VersionControl:
    """版本控制管理器"""

    def __init__(self, repo_path: str = "./canon"):
        self.repo_path = Path(repo_path)
        self.git_path = shutil.which("git")

        if not self.git_path:
            logger.warning("Git not found in PATH, version control disabled")
            self.enabled = False
        else:
            self.enabled = True
            self._ensure_git_repo()

        logger.info(
            f"VersionControl initialized for {repo_path} (enabled={self.enabled})"
        )

    def _ensure_git_repo(self):
        """确保目录是Git仓库"""
        if not (self.repo_path / ".git").exists():
            try:
                self._run_git_command(["init"])
                self._run_git_command(["config", "user.email", "loom@example.com"])
                self._run_git_command(["config", "user.name", "LOOM System"])

                # 创建.gitignore
                gitignore = self.repo_path / ".gitignore"
                if not gitignore.exists():
                    gitignore.write_text("*.bak\n*.tmp\n*.log\n")

                logger.info(f"Initialized Git repository at {self.repo_path}")
            except Exception as e:
                logger.error(f"Failed to initialize Git repository: {e}")
                self.enabled = False

    def _run_git_command(
        self, args: List[str], capture_output: bool = True
    ) -> Tuple[bool, str]:
        """运行Git命令"""
        if not self.enabled:
            return False, "Version control disabled"

        try:
            cmd = [self.git_path] + args
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=capture_output,
                text=True,
                encoding="utf-8",
            )

            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                logger.error(f"Git command failed: {' '.join(args)} - {error_msg}")
                return False, error_msg

            output = result.stdout.strip() if result.stdout else ""
            return True, output

        except Exception as e:
            logger.error(f"Exception running Git command: {e}")
            return False, str(e)

    def commit_changes(self, message: str = None) -> bool:
        """提交更改"""
        if not message:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"LOOM auto-commit: {timestamp}"

        # 添加所有文件
        success, _ = self._run_git_command(["add", "."])
        if not success:
            return False

        # 提交
        success, _ = self._run_git_command(["commit", "-m", message])
        if success:
            logger.info(f"Committed changes: {message}")

        return success

    def get_status(self) -> Dict[str, Any]:
        """获取仓库状态"""
        if not self.enabled:
            return {"enabled": False}

        status = {"enabled": True}

        # 获取当前分支
        success, branch = self._run_git_command(["branch", "--show-current"])
        if success:
            status["current_branch"] = branch

        # 获取未提交的更改
        success, changes = self._run_git_command(["status", "--porcelain"])
        if success:
            changed_files = [line[3:] for line in changes.split("\n") if line]
            status["changed_files"] = changed_files
            status["has_changes"] = len(changed_files) > 0

        # 获取最新提交
        success, log = self._run_git_command(["log", "-1", "--oneline"])
        if success:
            status["latest_commit"] = log

        return status

    def get_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """获取提交历史"""
        if not self.enabled:
            return []

        success, log = self._run_git_command(
            ["log", f"-{limit}", "--pretty=format:%H|%an|%ad|%s", "--date=iso"]
        )

        if not success:
            return []

        history = []
        for line in log.split("\n"):
            if not line:
                continue

            parts = line.split("|", 3)
            if len(parts) == 4:
                history.append(
                    {
                        "hash": parts[0][:8],
                        "full_hash": parts[0],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    }
                )

        return history

    def create_branch(self, branch_name: str) -> bool:
        """创建分支"""
        if not self.enabled:
            return False

        success, _ = self._run_git_command(["checkout", "-b", branch_name])
        if success:
            logger.info(f"Created and switched to branch '{branch_name}'")

        return success

    def switch_branch(self, branch_name: str) -> bool:
        """切换分支"""
        if not self.enabled:
            return False

        success, _ = self._run_git_command(["checkout", branch_name])
        if success:
            logger.info(f"Switched to branch '{branch_name}'")

        return success

    def list_branches(self) -> List[str]:
        """列出所有分支"""
        if not self.enabled:
            return []

        success, output = self._run_git_command(["branch", "--list"])
        if not success:
            return []

        branches = []
        for line in output.split("\n"):
            if line:
                # 移除前导空格和星号
                branch = line.strip()
                if branch.startswith("* "):
                    branch = branch[2:]
                branches.append(branch)

        return branches

    def rollback_to_commit(self, commit_hash: str) -> bool:
        """回滚到指定提交"""
        if not self.enabled:
            return False

        logger.warning(f"Rolling back to commit {commit_hash}")

        # 使用reset --hard（危险操作）
        success, _ = self._run_git_command(["reset", "--hard", commit_hash])
        if success:
            logger.info(f"Rolled back to commit {commit_hash}")
        else:
            logger.error(f"Failed to rollback to commit {commit_hash}")

        return success

    def get_diff(self, commit1: str = "HEAD", commit2: str = None) -> Optional[str]:
        """获取差异"""
        if not self.enabled:
            return None

        args = ["diff", commit1]
        if commit2:
            args.append(commit2)

        success, diff = self._run_git_command(args)
        if success:
            return diff

        return None

    def tag_version(self, version: str, message: str = None) -> bool:
        """创建版本标签"""
        if not self.enabled:
            return False

        if not message:
            message = f"Version {version}"

        success, _ = self._run_git_command(["tag", "-a", version, "-m", message])
        if success:
            logger.info(f"Created tag '{version}': {message}")

        return success

    def get_tags(self) -> List[Dict[str, str]]:
        """获取所有标签"""
        if not self.enabled:
            return []

        success, output = self._run_git_command(["tag", "--list", "-n"])
        if not success:
            return []

        tags = []
        for line in output.split("\n"):
            if line:
                parts = line.split(" ", 1)
                if len(parts) == 2:
                    tags.append({"name": parts[0], "message": parts[1].strip()})
                else:
                    tags.append({"name": parts[0], "message": ""})

        return tags

    def backup(self, backup_dir: str = "./backups") -> bool:
        """创建备份"""
        if not self.enabled:
            return False

        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"canon_backup_{timestamp}.tar.gz"
        backup_file = backup_path / backup_name

        try:
            # 使用Git归档创建备份
            success, _ = self._run_git_command(
                ["archive", "--format=tar.gz", f"--output={backup_file}", "HEAD"]
            )

            if success:
                logger.info(f"Created backup at {backup_file}")
                return True
            else:
                return False

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False

    def integrate_with_rule_loader(self, rule_loader: RuleLoader) -> Dict[str, Any]:
        """与RuleLoader集成

        Args:
            rule_loader: RuleLoader实例

        Returns:
            集成状态信息
        """
        if not self.enabled:
            return {"enabled": False, "error": "Version control disabled"}

        # 获取规则统计信息
        stats = rule_loader.get_canon_stats()

        # 检查是否有未提交的更改
        status = self.get_status()

        # 自动提交更改（如果有）
        if status.get("has_changes", False):
            logger.info(
                f"Auto-committing {len(status.get('changed_files', []))} changed files"
            )
            self.commit_changes(f"LOOM auto-commit before integration")

        # 获取当前版本信息
        history = self.get_history(limit=1)
        current_version = history[0] if history else None

        return {
            "enabled": True,
            "rule_loader_stats": stats,
            "git_status": status,
            "current_version": current_version,
            "integration_time": datetime.now().isoformat(),
        }

    def get_canon_diff(
        self, canon_name: str, commit1: str = "HEAD~1", commit2: str = "HEAD"
    ) -> Optional[Dict[str, Any]]:
        """获取规则文件的差异

        Args:
            canon_name: 规则名
            commit1: 第一个提交
            commit2: 第二个提交

        Returns:
            差异信息
        """
        if not self.enabled:
            return None

        file_path = f"{canon_name}.md"

        # 获取文件在两个提交中的内容
        success1, content1 = self._run_git_command(["show", f"{commit1}:{file_path}"])
        success2, content2 = self._run_git_command(["show", f"{commit2}:{file_path}"])

        if not success1 or not success2:
            return None

        # 获取差异
        success, diff = self._run_git_command(
            ["diff", commit1, commit2, "--", file_path]
        )
        if not success:
            return None

        # 解析差异
        diff_lines = diff.split("\n")
        added = []
        removed = []

        for line in diff_lines:
            if line.startswith("+") and not line.startswith("+++"):
                added.append(line[1:])
            elif line.startswith("-") and not line.startswith("---"):
                removed.append(line[1:])

        return {
            "canon_name": canon_name,
            "commit1": commit1,
            "commit2": commit2,
            "content1_length": len(content1),
            "content2_length": len(content2),
            "diff": diff,
            "added_lines": added,
            "removed_lines": removed,
            "change_summary": f"Added {len(added)} lines, removed {len(removed)} lines",
        }

    def create_version_snapshot(
        self, version_name: str, rule_loader: RuleLoader
    ) -> bool:
        """创建版本快照

        Args:
            version_name: 版本名
            rule_loader: RuleLoader实例

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        # 确保所有更改已提交
        status = self.get_status()
        if status.get("has_changes", False):
            logger.warning(f"Uncommitted changes found, committing before snapshot")
            self.commit_changes(f"Pre-snapshot commit for {version_name}")

        # 创建标签
        success = self.tag_version(
            version_name, f"LOOM version snapshot: {version_name}"
        )

        if success:
            # 导出规则信息
            stats = rule_loader.get_canon_stats()
            cache_info = rule_loader.export_cache_info()

            # 保存版本元数据
            metadata = {
                "version": version_name,
                "created": datetime.now().isoformat(),
                "stats": stats,
                "cache_info": cache_info,
            }

            metadata_file = self.repo_path / f".loom_versions/{version_name}.json"
            metadata_file.parent.mkdir(parents=True, exist_ok=True)

            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)

            logger.info(f"Created version snapshot '{version_name}' with metadata")

        return success

    def compare_versions(self, version1: str, version2: str) -> Dict[str, Any]:
        """比较两个版本

        Args:
            version1: 第一个版本（标签或提交）
            version2: 第二个版本（标签或提交）

        Returns:
            比较结果
        """
        if not self.enabled:
            return {"error": "Version control disabled"}

        # 获取差异统计
        success, diff_stat = self._run_git_command(
            ["diff", "--stat", version1, version2]
        )
        if not success:
            return {"error": f"Failed to compare {version1} and {version2}"}

        # 获取更改的文件列表
        success, name_status = self._run_git_command(
            ["diff", "--name-status", version1, version2]
        )
        changed_files = []

        if success:
            for line in name_status.split("\n"):
                if line:
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        changed_files.append(
                            {
                                "status": parts[0],  # A=添加, M=修改, D=删除
                                "file": parts[1],
                            }
                        )

        return {
            "version1": version1,
            "version2": version2,
            "diff_stat": diff_stat,
            "changed_files": changed_files,
            "total_changes": len(changed_files),
        }

    def restore_version(self, version: str, rule_loader: RuleLoader) -> bool:
        """恢复到指定版本

        Args:
            version: 版本标签或提交哈希
            rule_loader: RuleLoader实例

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        logger.warning(f"Restoring to version {version}")

        # 检查版本是否存在
        success, _ = self._run_git_command(["rev-parse", f"{version}^{{commit}}"])
        if not success:
            logger.error(f"Version {version} not found")
            return False

        # 使用checkout恢复文件
        success, _ = self._run_git_command(["checkout", version, "--", "."])
        if not success:
            logger.error(f"Failed to checkout version {version}")
            return False

        # 清空RuleLoader缓存
        rule_loader.clear_cache()

        logger.info(f"Restored to version {version}, cleared rule loader cache")
        return True
