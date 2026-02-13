"""
Markdown规则解析

解析Markdown格式的规则文件，提取结构化规则信息。
支持YAML frontmatter元数据，提取世界观设定、角色定义、冲突规则等。
提供规则查询和检索接口，支持规则片段组合。
"""

import re
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


class CanonSectionType(Enum):
    """规则章节类型"""

    WORLD = "world"  # 世界观
    TONE = "tone"  # 叙事基调
    CONFLICT = "conflict"  # 冲突解决
    PERMISSIONS = "permissions"  # 权限边界
    CAUSALITY = "causality"  # 因果关系
    META = "meta"  # 元信息
    CUSTOM = "custom"  # 自定义章节


@dataclass
class CanonSection:
    """规则章节"""

    name: str
    section_type: CanonSectionType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    line_start: int = 0
    line_end: int = 0


@dataclass
class MarkdownCanon:
    """Markdown规则集"""

    path: Path
    sections: Dict[str, CanonSection] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    raw_content: str = ""

    def __post_init__(self):
        if self.raw_content and not self.sections:
            self._parse_content()

    def _parse_content(self):
        """解析Markdown内容，支持YAML frontmatter"""
        lines = self.raw_content.split("\n")

        # 提取YAML frontmatter（如果存在）
        frontmatter_end = self._extract_frontmatter(lines)

        current_section = None
        section_content = []
        section_start = frontmatter_end

        for i in range(frontmatter_end, len(lines)):
            line = lines[i]

            # 检测标题（# 开头）
            if line.startswith("# "):
                # 保存前一个章节
                if current_section:
                    self._add_section(
                        current_section, section_content, section_start, i - 1
                    )

                # 开始新章节
                current_section = line[2:].strip()
                section_content = []
                section_start = i

            elif current_section is not None:
                section_content.append(line)

        # 保存最后一个章节
        if current_section:
            self._add_section(
                current_section, section_content, section_start, len(lines) - 1
            )

        # 提取元数据（从frontmatter和meta章节）
        self._extract_metadata()

    def _extract_frontmatter(self, lines: List[str]) -> int:
        """提取YAML frontmatter，返回frontmatter结束的行索引"""
        if not lines or not lines[0].strip() == "---":
            return 0

        frontmatter_lines = []
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                # 解析YAML frontmatter
                try:
                    frontmatter_text = "\n".join(frontmatter_lines)
                    if frontmatter_text.strip():
                        frontmatter_data = yaml.safe_load(frontmatter_text)
                        if frontmatter_data and isinstance(frontmatter_data, dict):
                            self.metadata.update(frontmatter_data)
                            logger.debug(
                                f"Extracted frontmatter metadata: {list(frontmatter_data.keys())}"
                            )
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML frontmatter: {e}")

                return i + 1  # 跳过结束的'---'

            frontmatter_lines.append(lines[i])

        # 如果没有找到结束的'---'，则没有有效的frontmatter
        return 0

    def _add_section(self, name: str, content_lines: List[str], start: int, end: int):
        """添加章节"""
        content = "\n".join(content_lines).strip()

        # 确定章节类型
        section_type = self._infer_section_type(name)

        section = CanonSection(
            name=name,
            section_type=section_type,
            content=content,
            line_start=start,
            line_end=end,
        )

        self.sections[name] = section
        logger.debug(f"Parsed section '{name}' ({section_type.value})")

    def _infer_section_type(self, name: str) -> CanonSectionType:
        """推断章节类型"""
        name_lower = name.lower()

        type_mapping = {
            "world": CanonSectionType.WORLD,
            "世界观": CanonSectionType.WORLD,
            "世界设定": CanonSectionType.WORLD,
            "tone": CanonSectionType.TONE,
            "基调": CanonSectionType.TONE,
            "风格": CanonSectionType.TONE,
            "style": CanonSectionType.TONE,
            "conflict": CanonSectionType.CONFLICT,
            "冲突": CanonSectionType.CONFLICT,
            "permissions": CanonSectionType.PERMISSIONS,
            "权限": CanonSectionType.PERMISSIONS,
            "causality": CanonSectionType.CAUSALITY,
            "因果": CanonSectionType.CAUSALITY,
            "meta": CanonSectionType.META,
            "元信息": CanonSectionType.META,
        }

        for key, section_type in type_mapping.items():
            if key in name_lower:
                return section_type

        return CanonSectionType.CUSTOM

    def _extract_metadata(self):
        """提取元数据（从frontmatter和meta章节）"""
        # 从meta章节提取（如果存在）
        meta_section = self.get_section_by_type(CanonSectionType.META)
        if meta_section:
            content = meta_section.content
            # 解析键值对
            for line in content.split("\n"):
                if ":" in line:
                    key, value = line.split(":", 1)
                    self.metadata[key.strip()] = value.strip()

        # 设置默认元数据（如果未提供）
        if "version" not in self.metadata:
            self.metadata["version"] = "1.0.0"
        if "author" not in self.metadata:
            self.metadata["author"] = "Unknown"
        if "created" not in self.metadata:
            from datetime import datetime

            self.metadata["created"] = datetime.now().isoformat()

    def get_section(self, name: str) -> Optional[CanonSection]:
        """获取指定章节"""
        return self.sections.get(name)

    def get_section_by_type(
        self, section_type: CanonSectionType
    ) -> Optional[CanonSection]:
        """按类型获取章节"""
        for section in self.sections.values():
            if section.section_type == section_type:
                return section
        return None

    def get_all_sections(self) -> List[CanonSection]:
        """获取所有章节"""
        return list(self.sections.values())

    def get_full_text(self) -> str:
        """获取完整规则文本"""
        if self.raw_content:
            return self.raw_content

        # 重新组装
        sections_text = []
        for section in self.sections.values():
            sections_text.append(f"# {section.name}")
            sections_text.append(section.content)

        return "\n\n".join(sections_text)

    def validate(self) -> List[str]:
        """验证规则完整性"""
        errors = []

        # 检查必需章节
        required_types = [CanonSectionType.WORLD, CanonSectionType.TONE]
        for req_type in required_types:
            if not self.get_section_by_type(req_type):
                errors.append(f"Missing required section: {req_type.value}")

        # 检查内容非空
        for name, section in self.sections.items():
            if not section.content.strip():
                errors.append(f"Section '{name}' is empty")

        # 检查元数据
        if "version" not in self.metadata:
            errors.append("Missing version metadata")

        return errors

    def search_content(
        self, query: str, section_type: Optional[CanonSectionType] = None
    ) -> List[Tuple[str, str]]:
        """搜索规则内容

        Args:
            query: 搜索关键词
            section_type: 可选，限制搜索的章节类型

        Returns:
            列表，每个元素为(章节名, 匹配内容)
        """
        results = []
        query_lower = query.lower()

        for name, section in self.sections.items():
            if section_type and section.section_type != section_type:
                continue

            if query_lower in section.content.lower():
                # 提取包含关键词的上下文
                lines = section.content.split("\n")
                for i, line in enumerate(lines):
                    if query_lower in line.lower():
                        # 获取前后两行作为上下文
                        start = max(0, i - 2)
                        end = min(len(lines), i + 3)
                        context = "\n".join(lines[start:end])
                        results.append((name, context))
                        break

        return results

    def get_rules_by_type(self, section_type: CanonSectionType) -> List[str]:
        """按类型获取规则内容"""
        rules = []
        for section in self.sections.values():
            if section.section_type == section_type:
                rules.append(section.content)
        return rules

    def combine_fragments(self, fragment_names: List[str]) -> str:
        """组合规则片段

        Args:
            fragment_names: 要组合的章节名列表

        Returns:
            组合后的规则文本
        """
        fragments = []
        for name in fragment_names:
            section = self.get_section(name)
            if section:
                fragments.append(f"# {name}\n\n{section.content}")

        return "\n\n".join(fragments)

    def extract_entities(self) -> Dict[str, List[str]]:
        """提取实体（角色、地点、物品等）"""
        entities = {"characters": [], "locations": [], "items": [], "concepts": []}

        # 从世界观章节提取实体
        world_section = self.get_section_by_type(CanonSectionType.WORLD)
        if world_section:
            content = world_section.content

            # 简单模式匹配（实际实现可以使用更复杂的NLP）
            character_patterns = [
                r"角色[:：]\s*(.+)",
                r"人物[:：]\s*(.+)",
                r"主要角色[:：]\s*(.+)",
                r"(.+)是.*角色",
                r"角色包括[:：]\s*(.+)",
            ]
            location_patterns = [
                r"地点[:：]\s*(.+)",
                r"位置[:：]\s*(.+)",
                r"重要地点[:：]\s*(.+)",
                r"在(.+)地方",
            ]

            for pattern in character_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, str):
                        # 处理逗号分隔的列表
                        entities_list = self._split_entity_list(match.strip())
                        entities["characters"].extend(entities_list)

            for pattern in location_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    if isinstance(match, str):
                        # 处理逗号分隔的列表
                        entities_list = self._split_entity_list(match.strip())
                        entities["locations"].extend(entities_list)

        # 去重
        for key in entities:
            entities[key] = list(set(entities[key]))

        return entities

    def _split_entity_list(self, text: str) -> List[str]:
        """分割实体列表（处理逗号、顿号等分隔符）"""
        # 分割逗号、顿号、和、等
        separators = r"[,、，和及与]"
        parts = re.split(separators, text)

        # 清理每个部分
        cleaned = []
        for part in parts:
            part = part.strip()
            # 移除句号、冒号等标点
            part = re.sub(r"[。：:;；]", "", part)
            if part:
                cleaned.append(part)

        return cleaned

    def validate_with_schema(
        self, schema: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """使用模式验证规则完整性

        Args:
            schema: 验证模式，定义必需章节和字段

        Returns:
            错误消息列表
        """
        errors = self.validate()  # 基础验证

        if schema:
            # 检查必需章节
            required_sections = schema.get("required_sections", [])
            for section_name in required_sections:
                if section_name not in self.sections:
                    errors.append(f"Missing required section: {section_name}")

            # 检查必需元数据字段
            required_metadata = schema.get("required_metadata", [])
            for field in required_metadata:
                if field not in self.metadata:
                    errors.append(f"Missing required metadata field: {field}")

        return errors

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "path": str(self.path),
            "metadata": self.metadata,
            "sections": {
                name: {
                    "type": section.section_type.value,
                    "content": section.content,
                    "metadata": section.metadata,
                    "line_start": section.line_start,
                    "line_end": section.line_end,
                }
                for name, section in self.sections.items()
            },
            "entities": self.extract_entities(),
        }
