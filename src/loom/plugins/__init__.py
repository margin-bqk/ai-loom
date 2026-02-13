"""
LOOM 插件系统
提供可扩展的插件架构，允许开发者扩展系统功能
"""

import importlib
import inspect
import logging
import pkgutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

logger = logging.getLogger(__name__)


class PluginBase(ABC):
    """插件基类"""

    def __init__(self):
        self.name = self.__class__.__name__
        self.version = "1.0.0"
        self.enabled = True

    @abstractmethod
    def initialize(self) -> bool:
        """初始化插件"""
        pass

    @abstractmethod
    def cleanup(self):
        """清理插件资源"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """获取插件信息"""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "description": self.__doc__ or "无描述",
        }


class RulePlugin(PluginBase):
    """规则插件 - 扩展规则系统"""

    @abstractmethod
    def preprocess_rule(self, rule_text: str) -> str:
        """预处理规则文本"""
        pass

    @abstractmethod
    def postprocess_rule(
        self, rule_text: str, parsed_rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """后处理解析后的规则"""
        pass

    @abstractmethod
    def validate_rule(self, rule_text: str) -> bool:
        """验证规则有效性"""
        pass


class MemoryPlugin(PluginBase):
    """记忆插件 - 扩展记忆系统"""

    @abstractmethod
    def store_memory(self, memory_data: Dict[str, Any]) -> str:
        """存储记忆"""
        pass

    @abstractmethod
    def retrieve_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """检索记忆"""
        pass

    @abstractmethod
    def summarize_memories(self, memories: List[Dict[str, Any]]) -> str:
        """总结记忆"""
        pass


class LLMPlugin(PluginBase):
    """LLM插件 - 扩展LLM提供商"""

    @abstractmethod
    def generate_response(self, prompt: str, **kwargs) -> str:
        """生成响应"""
        pass

    @abstractmethod
    def get_models(self) -> List[str]:
        """获取支持的模型列表"""
        pass

    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """获取能力信息"""
        pass


class ExportPlugin(PluginBase):
    """导出插件 - 扩展导出格式"""

    @abstractmethod
    def export(self, data: Dict[str, Any], **kwargs) -> str:
        """导出数据"""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        pass


class PluginManager:
    """插件管理器"""

    def __init__(self):
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_types: Dict[str, Type[PluginBase]] = {
            "rule": RulePlugin,
            "memory": MemoryPlugin,
            "llm": LLMPlugin,
            "export": ExportPlugin,
        }

    def register_plugin(self, plugin: PluginBase) -> bool:
        """注册插件"""
        if plugin.name in self.plugins:
            logger.warning(f"插件 {plugin.name} 已注册")
            return False

        self.plugins[plugin.name] = plugin
        logger.info(f"注册插件: {plugin.name}")
        return True

    def unregister_plugin(self, plugin_name: str) -> bool:
        """注销插件"""
        if plugin_name not in self.plugins:
            return False

        plugin = self.plugins[plugin_name]
        plugin.cleanup()
        del self.plugins[plugin_name]
        logger.info(f"注销插件: {plugin_name}")
        return True

    def get_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """获取插件"""
        return self.plugins.get(plugin_name)

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """按类型获取插件"""
        plugin_class = self.plugin_types.get(plugin_type)
        if not plugin_class:
            return []

        return [
            plugin
            for plugin in self.plugins.values()
            if isinstance(plugin, plugin_class)
        ]

    def load_plugins_from_path(self, path: str) -> List[str]:
        """从路径加载插件"""
        loaded = []
        plugin_path = Path(path)

        if not plugin_path.exists():
            logger.warning(f"插件路径不存在: {path}")
            return loaded

        # 查找Python模块
        for module_info in pkgutil.iter_modules([str(plugin_path)]):
            try:
                module = importlib.import_module(
                    f"{plugin_path.name}.{module_info.name}"
                )

                # 查找插件类
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, PluginBase)
                        and obj != PluginBase
                    ):

                        # 实例化并注册插件
                        plugin_instance = obj()
                        if self.register_plugin(plugin_instance):
                            loaded.append(plugin_instance.name)

            except Exception as e:
                logger.error(f"加载插件模块 {module_info.name} 失败: {e}")

        return loaded

    def initialize_all(self) -> Dict[str, bool]:
        """初始化所有插件"""
        results = {}
        for name, plugin in self.plugins.items():
            try:
                success = plugin.initialize()
                results[name] = success
                logger.info(f"初始化插件 {name}: {'成功' if success else '失败'}")
            except Exception as e:
                results[name] = False
                logger.error(f"初始化插件 {name} 时出错: {e}")

        return results

    def cleanup_all(self):
        """清理所有插件"""
        for name, plugin in self.plugins.items():
            try:
                plugin.cleanup()
                logger.info(f"清理插件: {name}")
            except Exception as e:
                logger.error(f"清理插件 {name} 时出错: {e}")

    def list_plugins(self) -> List[Dict[str, Any]]:
        """列出所有插件信息"""
        return [plugin.get_info() for plugin in self.plugins.values()]


# 全局插件管理器实例
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """获取全局插件管理器"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def register_plugin(plugin: PluginBase) -> bool:
    """注册插件（便捷函数）"""
    return get_plugin_manager().register_plugin(plugin)


def get_plugin(plugin_name: str) -> Optional[PluginBase]:
    """获取插件（便捷函数）"""
    return get_plugin_manager().get_plugin(plugin_name)
