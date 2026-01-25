"""
Prompt组装器

动态组装Prompt，注入规则、记忆、玩家输入等上下文。
支持模板系统、记忆摘要、干预处理和LLM格式适配。
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
import json
import re

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class PromptContext:
    """Prompt上下文"""
    session_id: str
    turn_number: int
    player_input: str
    rules_text: str  # 完整的规则Markdown
    memories: List[Dict[str, Any]]  # 相关记忆
    interventions: List[Dict[str, Any]]  # 干预信息
    system_prompt_template: str = "default"
    additional_context: Dict[str, Any] = field(default_factory=dict)
    llm_provider: str = "openai"  # LLM提供商，用于格式适配
    max_tokens: Optional[int] = None  # 最大令牌数限制
    
    def __post_init__(self):
        if self.additional_context is None:
            self.additional_context = {}


@dataclass
class PromptResult:
    """Prompt组装结果"""
    system_prompt: str
    user_prompt: str
    messages: List[Dict[str, str]]  # 适用于Chat API的消息列表
    metadata: Dict[str, Any]
    token_estimate: int  # 令牌数估计


class PromptAssembler:
    """Prompt组装器"""
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self.templates = self._load_default_templates()
        self.template_variables = self._load_template_variables()
        logger.info("PromptAssembler initialized")
    
    def _load_default_templates(self) -> Dict[str, Dict[str, str]]:
        """加载默认模板（支持多部分模板）"""
        return {
            "default": {
                "system": """你是一个叙事引擎，负责根据给定的世界观规则和记忆来推进故事。

# 核心原则
1. 严格遵守世界观规则
2. 保持叙事一致性
3. 尊重角色设定和故事逻辑
4. 自然地推进故事发展
5. 适当处理玩家干预

# 世界观规则
{rules_summary}

# 记忆使用指南
{memory_guidance}""",
                
                "user": """# 当前会话信息
- 会话ID：{session_id}
- 当前回合：第{turn_number}回合
- 当前时间：{current_time}

# 相关历史记忆
{memories_formatted}

# 玩家输入与干预
{player_input_with_interventions}

请根据以上信息，生成符合世界观规则的叙事响应。"""
            },
            
            "minimal": {
                "system": "你是一个叙事引擎。根据规则和记忆推进故事。",
                "user": "规则：{rules_summary}\n记忆：{memories_formatted}\n输入：{player_input}\n响应："
            },
            
            "detailed": {
                "system": """# 叙事解释器 - 详细模式

## 角色定义
你是一个专业的叙事引擎，负责在给定的世界观约束下生成连贯、有趣的故事发展。

## 核心职责
1. **规则遵守**：严格遵守所有世界观规则，不得违反
2. **一致性维护**：保持角色、设定、情节的一致性
3. **故事推进**：基于当前状态自然地推进故事
4. **干预处理**：适当处理玩家干预，保持叙事流畅
5. **记忆整合**：有效利用历史记忆，避免矛盾

## 世界观规则摘要
{rules_summary}

## 记忆使用策略
{memory_guidance}""",
                
                "user": """# 会话上下文
- **会话标识**：{session_id}
- **回合编号**：{turn_number}
- **时间戳**：{current_time}
- **LLM提供商**：{llm_provider}

# 详细历史记忆
{memories_detailed}

# 玩家输入解析
## 原始输入
{player_input}

## 干预信息
{interventions_formatted}

## 上下文摘要
{context_summary}

# 输出要求
请生成符合以下要求的叙事响应：
1. 严格遵守世界观规则
2. 保持叙事一致性
3. 自然地推进故事
4. 适当处理干预
5. 输出纯叙事文本（不要添加元注释）

# 响应："""
            },
            
            "openai_chat": {
                "system": "你是一个叙事引擎，根据给定的世界观规则和记忆推进故事。",
                "user": "规则：{rules_summary}\n记忆：{memories_formatted}\n输入：{player_input}\n请生成叙事响应："
            },
            
            "anthropic": {
                "system": """你是一个叙事引擎。

世界观规则：
{rules_summary}

记忆指南：
{memory_guidance}

请根据玩家的输入和以上上下文，生成符合规则的叙事响应。""",
                "user": "记忆：{memories_formatted}\n输入：{player_input_with_interventions}\n响应："
            }
        }
    
    def _load_template_variables(self) -> Dict[str, Any]:
        """加载模板变量配置"""
        return {
            "max_memories_per_prompt": 10,
            "max_rules_length": 4000,
            "max_memory_length": 2000,
            "default_llm_provider": "openai",
            "token_estimation_ratio": 1.3  # 字符到令牌的估计比率
        }
    
    def assemble(self, context: PromptContext) -> PromptResult:
        """组装Prompt"""
        # 选择模板
        template_name = context.system_prompt_template
        if template_name not in self.templates:
            template_name = "default"
            logger.warning(f"Template '{context.system_prompt_template}' not found, using 'default'")
        
        template = self.templates[template_name]
        
        # 准备所有变量
        variables = self._prepare_variables(context, template_name)
        
        # 应用模板
        system_prompt = template["system"].format(**variables)
        user_prompt = template["user"].format(**variables)
        
        # 构建消息列表（适用于Chat API）
        messages = self._build_messages(system_prompt, user_prompt, context.llm_provider)
        
        # 估计令牌数
        token_estimate = self._estimate_tokens(system_prompt + user_prompt)
        
        # 检查令牌限制
        if context.max_tokens and token_estimate > context.max_tokens:
            logger.warning(f"Prompt token estimate ({token_estimate}) exceeds limit ({context.max_tokens})")
            # 可以在这里实现截断逻辑
        
        result = PromptResult(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            messages=messages,
            metadata={
                "template": template_name,
                "llm_provider": context.llm_provider,
                "session_id": context.session_id,
                "turn_number": context.turn_number,
                "memories_count": len(context.memories),
                "interventions_count": len(context.interventions),
                "rules_length": len(context.rules_text),
                "assembled_at": datetime.now().isoformat()
            },
            token_estimate=token_estimate
        )
        
        logger.debug(f"Assembled prompt for session {context.session_id}, turn {context.turn_number}")
        logger.debug(f"Template: {template_name}, Tokens: {token_estimate}, Memories: {len(context.memories)}")
        
        return result
    
    def _prepare_variables(self, context: PromptContext, template_name: str) -> Dict[str, str]:
        """准备模板变量"""
        from datetime import datetime
        
        # 处理规则文本
        rules_summary = self._summarize_rules(context.rules_text)
        
        # 处理记忆
        memories_formatted = self._format_memories(context.memories, "brief")
        memories_detailed = self._format_memories(context.memories, "detailed")
        
        # 处理干预
        interventions_formatted = self._format_interventions(context.interventions)
        
        # 构建变量字典
        variables = {
            "session_id": context.session_id,
            "turn_number": context.turn_number,
            "player_input": context.player_input,
            "rules_text": context.rules_text,
            "rules_summary": rules_summary,
            "memories_formatted": memories_formatted,
            "memories_detailed": memories_detailed,
            "interventions_formatted": interventions_formatted,
            "player_input_with_interventions": self._combine_input_and_interventions(
                context.player_input, context.interventions
            ),
            "current_time": datetime.now().isoformat(),
            "llm_provider": context.llm_provider,
            "memory_guidance": self._get_memory_guidance(context.memories),
            "context_summary": self._generate_context_summary(context)
        }
        
        # 添加额外上下文
        variables.update(context.additional_context)
        
        return variables
    
    def _summarize_rules(self, rules_text: str) -> str:
        """摘要规则文本"""
        if len(rules_text) <= self.template_variables["max_rules_length"]:
            return rules_text
        
        # 简单截断，可以改进为智能摘要
        summary = rules_text[:self.template_variables["max_rules_length"]] + "...\n\n（规则过长，已截断）"
        
        # 尝试保留重要部分（如标题）
        lines = rules_text.split('\n')
        important_lines = []
        for line in lines:
            if line.startswith('#') or line.startswith('##') or '重要' in line or '必须' in line:
                important_lines.append(line)
        
        if important_lines:
            summary = "\n".join(important_lines[:10]) + "\n\n" + summary
        
        return summary
    
    def _format_memories(self, memories: List[Dict[str, Any]], format_type: str = "brief") -> str:
        """格式化记忆"""
        if not memories:
            return "（无相关记忆）"
        
        # 限制记忆数量
        max_memories = self.template_variables["max_memories_per_prompt"]
        memories = memories[:max_memories]
        
        if format_type == "brief":
            return self._format_memories_brief(memories)
        elif format_type == "detailed":
            return self._format_memories_detailed(memories)
        else:
            return self._format_memories_brief(memories)
    
    def _format_memories_brief(self, memories: List[Dict[str, Any]]) -> str:
        """简要格式化记忆"""
        formatted = []
        for i, memory in enumerate(memories):
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})
            
            # 提取摘要或关键信息
            summary = content.get("summary", "")
            if not summary and isinstance(content, dict):
                # 尝试从内容中提取关键信息
                keys = list(content.keys())
                if keys:
                    summary = f"{keys[0]}: {str(content[keys[0]])[:50]}..."
                else:
                    summary = str(content)[:100]
            elif not summary:
                summary = str(content)[:100]
            
            formatted.append(f"{i+1}. [{mem_type}] {summary}")
        
        return "\n".join(formatted)
    
    def _format_memories_detailed(self, memories: List[Dict[str, Any]]) -> str:
        """详细格式化记忆"""
        formatted = []
        for i, memory in enumerate(memories):
            mem_type = memory.get("type", "unknown")
            content = memory.get("content", {})
            created_at = memory.get("created_at", "")
            metadata = memory.get("metadata", {})
            
            memory_text = f"## 记忆 #{i+1}: {mem_type}\n"
            
            if created_at:
                memory_text += f"**时间**: {created_at}\n"
            
            if isinstance(content, dict):
                for key, value in content.items():
                    if isinstance(value, (str, int, float, bool)):
                        memory_text += f"- **{key}**: {value}\n"
                    elif isinstance(value, list):
                        memory_text += f"- **{key}**: {', '.join(str(v) for v in value[:5])}"
                        if len(value) > 5:
                            memory_text += f" ...（共{len(value)}项）"
                        memory_text += "\n"
            else:
                memory_text += f"**内容**: {content}\n"
            
            if metadata:
                memory_text += f"**元数据**: {json.dumps(metadata, ensure_ascii=False, indent=2)}\n"
            
            formatted.append(memory_text.strip())
        
        return "\n\n".join(formatted)
    
    def _format_interventions(self, interventions: List[Dict[str, Any]]) -> str:
        """格式化干预信息"""
        if not interventions:
            return "（无干预）"
        
        formatted = []
        for i, interv in enumerate(interventions):
            interv_type = interv.get("type", "unknown")
            content = interv.get("content", "")
            intent = interv.get("intent", "")
            
            interv_text = f"### 干预 #{i+1}: {interv_type}\n"
            
            if intent:
                interv_text += f"**意图**: {intent}\n"
            
            interv_text += f"**内容**: {content}"
            
            formatted.append(interv_text)
        
        return "\n\n".join(formatted)
    
    def _combine_input_and_interventions(self, player_input: str, interventions: List[Dict[str, Any]]) -> str:
        """合并玩家输入和干预信息"""
        if not interventions:
            return player_input
        
        result = f"## 玩家输入\n{player_input}\n\n## 干预信息"
        
        for i, interv in enumerate(interventions):
            interv_type = interv.get("type", "unknown")
            content = interv.get("content", "")
            result += f"\n{i+1}. **[{interv_type}]** {content}"
        
        return result
    
    def _get_memory_guidance(self, memories: List[Dict[str, Any]]) -> str:
        """生成记忆使用指南"""
        if not memories:
            return "当前没有相关历史记忆。请基于世界观规则和当前输入进行叙事。"
        
        memory_types = {}
        for memory in memories:
            mem_type = memory.get("type", "unknown")
            memory_types[mem_type] = memory_types.get(mem_type, 0) + 1
        
        type_summary = ", ".join([f"{k}({v})" for k, v in memory_types.items()])
        
        return f"""当前有 {len(memories)} 条相关历史记忆，类型分布：{type_summary}。

记忆使用建议：
1. 参考历史记忆保持叙事一致性
2. 避免与已有记忆矛盾
3. 可以引用重要历史事件
4. 新信息应与已有记忆协调"""
    
    def _generate_context_summary(self, context: PromptContext) -> str:
        """生成上下文摘要"""
        summary = f"会话 {context.session_id} 的第 {context.turn_number} 回合\n"
        summary += f"玩家输入长度: {len(context.player_input)} 字符\n"
        summary += f"规则长度: {len(context.rules_text)} 字符\n"
        summary += f"相关记忆: {len(context.memories)} 条\n"
        summary += f"干预数量: {len(context.interventions)} 个"
        
        return summary
    
    def _build_messages(self, system_prompt: str, user_prompt: str, llm_provider: str) -> List[Dict[str, str]]:
        """构建消息列表（适用于Chat API）"""
        messages = []
        
        if llm_provider == "openai":
            # OpenAI格式
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})
        elif llm_provider == "anthropic":
            # Anthropic格式（简化）
            messages.append({"role": "user", "content": f"{system_prompt}\n\n{user_prompt}"})
        else:
            # 默认格式
            messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def _estimate_tokens(self, text: str) -> int:
        """估计文本的令牌数"""
        # 简单估计：中文字符和英文字符的混合
        # 实际实现应该使用tiktoken或其他令牌化库
        chinese_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        english_chars = len(text) - chinese_chars
        
        # 粗略估计：中文字符≈2令牌，英文字符≈0.25令牌
        estimated_tokens = chinese_chars * 2 + english_chars * 0.25
        
        return int(estimated_tokens * self.template_variables["token_estimation_ratio"])
    
    def register_template(self, name: str, template: Dict[str, str]):
        """注册自定义模板"""
        if "system" not in template or "user" not in template:
            raise ValueError("Template must contain 'system' and 'user' keys")
        
        self.templates[name] = template
        logger.info(f"Registered template '{name}'")
    
    def list_templates(self) -> List[str]:
        """列出所有可用模板"""
        return list(self.templates.keys())
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """获取模板信息"""
        if template_name not in self.templates:
            return None
        
        template = self.templates[template_name]
        return {
            "name": template_name,
            "system_length": len(template.get("system", "")),
            "user_length": len(template.get("user", "")),
            "variables": self._extract_template_variables(template),
            "llm_providers": ["openai", "anthropic", "ollama"]
        }
    
    def _extract_template_variables(self, template: Dict[str, str]) -> List[str]:
        """提取模板中的变量名"""
        import re
        variables = set()
        
        for text in template.values():
            matches = re.findall(r'\{(\w+)\}', text)
            variables.update(matches)
        
        return sorted(list(variables))
    
    def validate_context(self, context: PromptContext) -> List[str]:
        """验证上下文是否有效"""
        errors = []
        
        if not context.session_id:
            errors.append("session_id不能为空")
        
        if context.turn_number < 0:
            errors.append("turn_number必须大于等于0")
        
        if not context.player_input:
            errors.append("player_input不能为空")
        
        if not context.rules_text:
            errors.append("rules_text不能为空")
        
        # 检查记忆格式
        for i, memory in enumerate(context.memories):
            if not isinstance(memory, dict):
                errors.append(f"记忆 #{i+1} 必须是字典类型")
            elif "type" not in memory:
                errors.append(f"记忆 #{i+1} 缺少type字段")
        
        # 检查干预格式
        for i, intervention in enumerate(context.interventions):
            if not isinstance(intervention, dict):
                errors.append(f"干预 #{i+1} 必须是字典类型")
        
        return errors
    
    def truncate_to_fit_tokens(self, context: PromptContext, max_tokens: int) -> PromptContext:
        """截断内容以适应令牌限制"""
        # 创建副本以避免修改原始上下文
        truncated_context = PromptContext(
            session_id=context.session_id,
            turn_number=context.turn_number,
            player_input=context.player_input,
            rules_text=context.rules_text,
            memories=context.memories.copy(),
            interventions=context.interventions.copy(),
            system_prompt_template=context.system_prompt_template,
            additional_context=context.additional_context.copy(),
            llm_provider=context.llm_provider,
            max_tokens=max_tokens
        )
        
        # 估计当前令牌数
        result = self.assemble(truncated_context)
        current_tokens = result.token_estimate
        
        if current_tokens <= max_tokens:
            return truncated_context
        
        # 需要截断
        excess_tokens = current_tokens - max_tokens
        logger.info(f"需要截断 {excess_tokens} 令牌以适应限制 {max_tokens}")
        
        # 策略：按优先级截断
        # 1. 首先截断记忆
        if truncated_context.memories:
            # 减少记忆数量
            target_memory_count = max(1, len(truncated_context.memories) - (excess_tokens // 50))
            truncated_context.memories = truncated_context.memories[:target_memory_count]
        
        # 重新估计
        result = self.assemble(truncated_context)
        if result.token_estimate <= max_tokens:
            return truncated_context
        
        # 2. 截断规则文本
        if len(truncated_context.rules_text) > 1000:
            truncated_context.rules_text = truncated_context.rules_text[:1000] + "...\n（规则已截断）"
        
        # 3. 截断玩家输入（最后手段）
        if len(truncated_context.player_input) > 500:
            truncated_context.player_input = truncated_context.player_input[:500] + "..."
        
        return truncated_context
    
    def create_context_from_session(self, session, player_input: str, memories: List[Dict[str, Any]] = None,
                                   interventions: List[Dict[str, Any]] = None) -> PromptContext:
        """从会话创建上下文"""
        # 这里需要集成规则加载和记忆检索
        # 简化实现
        return PromptContext(
            session_id=session.id,
            turn_number=session.current_turn + 1,
            player_input=player_input,
            rules_text="[需要从规则层加载]",  # 实际应从规则层加载
            memories=memories or [],
            interventions=interventions or [],
            additional_context={
                "session_name": session.name,
                "session_config": session.config.__dict__ if hasattr(session.config, '__dict__') else session.config
            }
        )