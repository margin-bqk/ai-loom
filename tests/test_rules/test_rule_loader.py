"""
RuleLoader单元测试
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from src.loom.rules.rule_loader import RuleLoader
from src.loom.rules.markdown_canon import MarkdownCanon


class TestRuleLoader:
    """RuleLoader测试类"""

    def setup_method(self):
        """测试设置"""
        self.temp_dir = tempfile.mkdtemp()
        self.canon_dir = Path(self.temp_dir) / "canon"
        self.canon_dir.mkdir(parents=True, exist_ok=True)

        # 创建测试规则文件
        self.test_canon_content = """---
version: 1.0.0
author: Test Author
---

# 世界观
这是一个测试世界。

# 叙事基调
测试基调。

# 冲突解决
现实主义。

# 权限边界
玩家可以探索世界。
玩家不能杀死关键NPC。

# 因果关系
时间只能向前流动。

# 元信息
created: 2025-01-01
"""

        self.test_file = self.canon_dir / "test_world.md"
        self.test_file.write_text(self.test_canon_content, encoding="utf-8")

        # 创建第二个测试文件
        self.test_file2 = self.canon_dir / "another_world.md"
        self.test_file2.write_text(
            """# 世界观
另一个世界。
""",
            encoding="utf-8",
        )

        # 创建子目录测试文件（用于递归加载）
        self.sub_dir = self.canon_dir / "subdir"
        self.sub_dir.mkdir(parents=True, exist_ok=True)
        self.sub_file = self.sub_dir / "sub_world.md"
        self.sub_file.write_text(
            """# 世界观
子目录世界。
""",
            encoding="utf-8",
        )

    def teardown_method(self):
        """测试清理"""
        shutil.rmtree(self.temp_dir)

    def test_load_canon(self):
        """测试加载规则集"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 加载现有规则集
        canon = loader.load_canon("test_world")
        assert canon is not None
        assert canon.path == self.test_file
        assert len(canon.sections) >= 5  # 至少有5个章节

        # 检查元数据
        assert canon.metadata["version"] == "1.0.0"
        assert canon.metadata["author"] == "Test Author"

        # 加载不存在的规则集
        nonexistent = loader.load_canon("nonexistent")
        assert nonexistent is None

    def test_cache_mechanism(self):
        """测试缓存机制"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 第一次加载
        canon1 = loader.load_canon("test_world")
        assert canon1 is not None

        # 第二次加载应该使用缓存
        canon2 = loader.load_canon("test_world")
        assert canon2 is canon1  # 应该是同一个对象（缓存）

        # 修改文件后缓存应该失效
        self.test_file.write_text("# 世界观\n修改后的世界。", encoding="utf-8")
        canon3 = loader.load_canon("test_world")
        assert canon3 is not canon1  # 应该是新对象

        # 检查缓存统计
        stats = loader.get_canon_stats()
        assert stats["cached_canons"] >= 1

    def test_get_all_canons(self):
        """测试获取所有规则集"""
        loader = RuleLoader(canon_dir=str(self.canon_dir), recursive=False)

        canons = loader.get_all_canons()
        assert len(canons) == 2  # test_world 和 another_world
        assert "test_world" in canons
        assert "another_world" in canons

        # 测试递归加载
        loader_recursive = RuleLoader(canon_dir=str(self.canon_dir), recursive=True)
        canons_recursive = loader_recursive.get_all_canons()
        assert len(canons_recursive) == 3  # 包括子目录文件

    def test_load_all_canons(self):
        """测试加载所有规则集（新方法）"""
        loader = RuleLoader(canon_dir=str(self.canon_dir), recursive=True)

        canons = loader.load_all_canons()
        assert len(canons) == 3

        # 检查子目录文件
        subdir_canon_name = "subdir/sub_world"
        assert subdir_canon_name in canons

        # 检查文件路径
        for name, canon in canons.items():
            assert isinstance(canon, MarkdownCanon)
            assert canon.path.exists()

    def test_dependency_management(self):
        """测试依赖关系管理"""
        # 创建有依赖关系的规则文件
        dependent_content = """---
version: 1.0.0
depends_on: test_world
---

# 世界观
依赖test_world的世界。
参见：test_world的设定。
"""

        dependent_file = self.canon_dir / "dependent_world.md"
        dependent_file.write_text(dependent_content, encoding="utf-8")

        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 加载依赖文件以提取依赖关系
        loader.load_canon("dependent_world")

        # 检查依赖树
        dep_tree = loader.get_dependency_tree("dependent_world")
        assert dep_tree["canon"] == "dependent_world"
        assert "test_world" in dep_tree["dependencies"]

        # 检查所有依赖
        all_deps = loader.get_dependency_tree()
        assert "dependencies" in all_deps

    def test_validate_all(self):
        """测试验证所有规则集"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        validation_results = loader.validate_all()

        # 检查验证结果
        for canon_name, errors in validation_results.items():
            assert isinstance(canon_name, str)
            assert isinstance(errors, list)

    def test_create_default_canon(self):
        """测试创建默认规则集"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 创建默认规则集
        success = loader.create_default_canon("default_world")
        assert success is True

        # 检查文件是否存在
        default_file = self.canon_dir / "default_world.md"
        assert default_file.exists()

        # 内容应该包含标准章节
        content = default_file.read_text(encoding="utf-8")
        assert "# 世界观" in content
        assert "# 叙事基调" in content

        # 尝试创建已存在的文件
        success_again = loader.create_default_canon("default_world")
        assert success_again is False  # 应该失败

    def test_file_watching(self):
        """测试文件监控"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 记录回调调用
        callback_called = []

        def test_callback(file_path):
            callback_called.append(file_path)

        # 注册回调
        loader.register_change_callback(test_callback)

        # 开始监控（在实际测试中可能跳过，因为需要运行观察者）
        # loader.start_watching()

        # 这里我们只测试回调注册，不实际测试文件系统事件

    def test_clear_cache(self):
        """测试清空缓存"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 加载一些规则集
        loader.load_canon("test_world")
        loader.load_canon("another_world")

        stats_before = loader.get_canon_stats()
        assert stats_before["cached_canons"] == 2

        # 清空特定缓存
        loader.clear_cache("test_world")
        stats_after = loader.get_canon_stats()
        assert stats_after["cached_canons"] == 1

        # 清空所有缓存
        loader.clear_cache()
        stats_all_cleared = loader.get_canon_stats()
        assert stats_all_cleared["cached_canons"] == 0

    def test_export_cache_info(self):
        """测试导出缓存信息"""
        loader = RuleLoader(canon_dir=str(self.canon_dir))

        # 加载规则集
        loader.load_canon("test_world")

        cache_info = loader.export_cache_info()

        assert "cached_files" in cache_info
        assert "cache_keys" in cache_info
        assert "file_hashes" in cache_info
        assert "dependencies" in cache_info

        assert cache_info["cached_files"] >= 1
        assert len(cache_info["cache_keys"]) >= 1

    def test_get_canon_stats(self):
        """测试获取规则集统计信息"""
        loader = RuleLoader(canon_dir=str(self.canon_dir), recursive=True)

        stats = loader.get_canon_stats()

        assert "canon_dir" in stats
        assert "recursive" in stats
        assert stats["recursive"] is True
        assert "cached_canons" in stats
        assert "available_files" in stats
        assert "dependency_graph_size" in stats

        # 检查文件列表
        assert len(stats["available_files"]) == 3

        for file_info in stats["available_files"]:
            assert "name" in file_info
            assert "path" in file_info
            assert "size" in file_info
            assert "cached" in file_info


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
