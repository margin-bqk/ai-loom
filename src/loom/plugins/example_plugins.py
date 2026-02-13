"""
示例插件
展示如何创建和使用 LOOM 插件
"""

import json
from typing import Any, Dict, List

import yaml

from . import ExportPlugin, MemoryPlugin, RulePlugin


class MarkdownRuleFormatter(RulePlugin):
    """Markdown规则格式化插件"""

    def __init__(self):
        super().__init__()
        self.name = "MarkdownRuleFormatter"
        self.version = "1.1.0"
        self.description = "增强Markdown规则解析和格式化"

    def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化插件: {self.name}")
        return True

    def cleanup(self):
        """清理插件资源"""
        print(f"清理插件: {self.name}")

    def preprocess_rule(self, rule_text: str) -> str:
        """预处理规则文本 - 清理和标准化"""
        # 移除多余的空行
        lines = [line.strip() for line in rule_text.split("\n") if line.strip()]
        return "\n".join(lines)

    def postprocess_rule(
        self, rule_text: str, parsed_rule: Dict[str, Any]
    ) -> Dict[str, Any]:
        """后处理解析后的规则 - 添加元数据"""
        parsed_rule["formatted_by"] = self.name
        parsed_rule["formatted_version"] = self.version

        # 计算规则复杂度
        word_count = len(rule_text.split())
        line_count = len(rule_text.split("\n"))
        parsed_rule["complexity"] = {
            "word_count": word_count,
            "line_count": line_count,
            "estimated_read_time": f"{word_count/200:.1f}分钟",
        }

        return parsed_rule

    def validate_rule(self, rule_text: str) -> bool:
        """验证规则有效性 - 检查基本结构"""
        required_sections = ["rule:", "description:", "condition:", "effect:"]
        rule_lower = rule_text.lower()

        for section in required_sections:
            if section not in rule_lower:
                return False

        return True


class JSONMemoryStore(MemoryPlugin):
    """JSON内存存储插件"""

    def __init__(self):
        super().__init__()
        self.name = "JSONMemoryStore"
        self.version = "1.0.0"
        self.description = "将记忆存储为JSON文件"
        self.memories: List[Dict[str, Any]] = []

    def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化插件: {self.name}")
        # 可以在这里加载现有的记忆文件
        return True

    def cleanup(self):
        """清理插件资源"""
        print(f"清理插件: {self.name}")
        # 保存记忆到文件
        self._save_memories()

    def store_memory(self, memory_data: Dict[str, Any]) -> str:
        """存储记忆"""
        memory_id = f"memory_{len(self.memories) + 1}"
        memory_data["id"] = memory_id
        memory_data["timestamp"] = "2024-01-01T00:00:00Z"  # 实际应使用当前时间

        self.memories.append(memory_data)
        print(f"存储记忆: {memory_id} - {memory_data.get('summary', '无摘要')[:50]}...")
        return memory_id

    def retrieve_memory(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """检索记忆 - 简单关键词匹配"""
        results = []
        query_lower = query.lower()

        for memory in self.memories:
            # 简单文本匹配
            memory_text = json.dumps(memory, ensure_ascii=False).lower()
            if query_lower in memory_text:
                results.append(memory)

            if len(results) >= limit:
                break

        return results

    def summarize_memories(self, memories: List[Dict[str, Any]]) -> str:
        """总结记忆"""
        if not memories:
            return "无记忆可总结"

        total = len(memories)
        # 提取关键信息
        summaries = []
        for memory in memories[:5]:  # 只总结前5个
            summary = memory.get("summary", "无摘要")
            summaries.append(f"- {summary}")

        result = f"共 {total} 条记忆:\n" + "\n".join(summaries)
        if total > 5:
            result += f"\n... 还有 {total - 5} 条记忆"

        return result

    def _save_memories(self):
        """保存记忆到文件（示例）"""
        if self.memories:
            # 实际实现中应该保存到文件
            pass


class YAMLExportPlugin(ExportPlugin):
    """YAML导出插件"""

    def __init__(self):
        super().__init__()
        self.name = "YAMLExportPlugin"
        self.version = "1.0.0"
        self.description = "导出数据为YAML格式"

    def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化插件: {self.name}")
        return True

    def cleanup(self):
        """清理插件资源"""
        print(f"清理插件: {self.name}")

    def export(self, data: Dict[str, Any], **kwargs) -> str:
        """导出数据为YAML格式"""
        try:
            # 添加导出元数据
            export_data = {
                "exported_by": self.name,
                "export_version": self.version,
                "timestamp": "2024-01-01T00:00:00Z",
                "data": data,
            }

            yaml_str = yaml.dump(export_data, allow_unicode=True, sort_keys=False)
            return yaml_str

        except Exception as e:
            return f"导出失败: {e}"

    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        return ["yaml", "yml"]


class CSVExportPlugin(ExportPlugin):
    """CSV导出插件"""

    def __init__(self):
        super().__init__()
        self.name = "CSVExportPlugin"
        self.version = "1.0.0"
        self.description = "导出数据为CSV格式"

    def initialize(self) -> bool:
        """初始化插件"""
        print(f"初始化插件: {self.name}")
        return True

    def cleanup(self):
        """清理插件资源"""
        print(f"清理插件: {self.name}")

    def export(self, data: Dict[str, Any], **kwargs) -> str:
        """导出数据为CSV格式"""
        try:
            # 简单实现 - 实际应根据数据结构生成CSV
            csv_lines = []

            # 添加标题
            if "headers" in kwargs:
                csv_lines.append(",".join(kwargs["headers"]))
            else:
                csv_lines.append("key,value")

            # 添加数据
            for key, value in data.items():
                if isinstance(value, (str, int, float, bool)):
                    csv_lines.append(f'{key},"{value}"')
                else:
                    csv_lines.append(f'{key},"{str(value)}"')

            return "\n".join(csv_lines)

        except Exception as e:
            return f"导出失败: {e}"

    def get_supported_formats(self) -> List[str]:
        """获取支持的格式"""
        return ["csv"]


# 插件注册函数
def register_example_plugins():
    """注册所有示例插件"""
    from . import register_plugin

    plugins = [
        MarkdownRuleFormatter(),
        JSONMemoryStore(),
        YAMLExportPlugin(),
        CSVExportPlugin(),
    ]

    registered = []
    for plugin in plugins:
        if register_plugin(plugin):
            registered.append(plugin.name)

    return registered
