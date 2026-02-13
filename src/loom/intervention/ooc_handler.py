"""
OOC注释处理

专门处理Out-of-Character注释，分离叙事和元对话。
"""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class OOCComment:
    """OOC注释"""

    content: str
    position: int  # 在原始文本中的位置
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OOCResult:
    """OOC处理结果"""

    narrative_text: str  # 清理后的叙事文本
    ooc_comments: List[OOCComment]  # 提取的OOC注释
    metadata: Dict[str, Any] = field(default_factory=dict)


class OOCHandler:
    """OOC注释处理器"""

    def __init__(self):
        self.ooc_patterns = [
            # 括号格式 - 处理嵌套括号
            re.compile(r"\(OOC:\s*((?:[^()]|\([^()]*\))*)\)", re.IGNORECASE),
            re.compile(r"\[OOC:\s*((?:[^\[\]]|\[[^\[\]]*\])*)\]", re.IGNORECASE),
            re.compile(r"\{OOC:\s*((?:[^{}]|\{[^{}]*\})*)\}", re.IGNORECASE),
            # 斜杠格式 - 修改为在遇到其他OOC模式时停止
            re.compile(
                r"\/ooc\s+(.*?)(?=\s*(?:\(OOC:|\[OOC:|\{OOC:|\/ooc|\[meta\]|\[comment\]|\[note\]|<!--|\(\(|\[\[|\n|$))",
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(r"\/\/\s*(.*?)(?=\n|$)", re.MULTILINE),  # 单行注释
            re.compile(r"\/\*\s*(.*?)\s*\*\/", re.DOTALL),  # 多行注释
            # 特殊标记
            re.compile(
                r"\[meta\]\s*(.*?)(?=\s*(?:\(OOC:|\[OOC:|\{OOC:|\/ooc|\[meta\]|\[comment\]|\[note\]|<!--|\(\(|\[\[|\n|$))",
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r"\[comment\]\s*(.*?)(?=\s*(?:\(OOC:|\[OOC:|\{OOC:|\/ooc|\[meta\]|\[comment\]|\[note\]|<!--|\(\(|\[\[|\n|$))",
                re.IGNORECASE | re.DOTALL,
            ),
            re.compile(
                r"\[note\]\s*(.*?)(?=\s*(?:\(OOC:|\[OOC:|\{OOC:|\/ooc|\[meta\]|\[comment\]|\[note\]|<!--|\(\(|\[\[|\n|$))",
                re.IGNORECASE | re.DOTALL,
            ),
            # HTML风格
            re.compile(r"<!--\s*(.*?)\s*-->", re.DOTALL),
            # 简写
            re.compile(r"\(\((.*?)\)\)", re.DOTALL),  # ((注释))
            re.compile(r"\[\[(.*?)\]\]", re.DOTALL),  # [[注释]]
        ]
        self.intent_keywords = {
            "clarification": ["意思是", "解释", "说明", "澄清", "什么意思", "意味着"],
            "intent": ["想要", "希望", "意图", "打算", "计划", "目标", "目的", "应该"],
            "feedback": [
                "喜欢",
                "不喜欢",
                "建议",
                "反馈",
                "评价",
                "批评",
                "表扬",
                "太快",
                "太慢",
            ],
            "meta": ["注释", "备注", "注意", "提醒", "记录", "标记"],
            "question": ["?", "？", "为什么", "如何", "怎么", "何时", "哪里"],
            "correction": ["错误", "不对", "更正", "修改", "纠正", "应该是"],
        }
        logger.info("OOCHandler initialized")

    def extract_ooc(self, text: str) -> OOCResult:
        """从文本中提取OOC注释"""
        ooc_comments = []
        clean_text = text

        for pattern in self.ooc_patterns:
            matches = list(pattern.finditer(text))
            for match in matches:
                content = match.group(1).strip()

                ooc_comment = OOCComment(
                    content=content,
                    position=match.start(),
                    metadata={
                        "pattern": pattern.pattern[:50],
                        "raw_match": match.group(0),
                    },
                )

                ooc_comments.append(ooc_comment)

                # 从clean_text中移除OOC注释
                clean_text = clean_text.replace(match.group(0), "")

        # 清理多余的空格和换行
        clean_text = self._clean_text(clean_text)

        result = OOCResult(
            narrative_text=clean_text,
            ooc_comments=sorted(ooc_comments, key=lambda x: x.position),
        )

        logger.debug(f"Extracted {len(ooc_comments)} OOC comments from text")

        return result

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 移除多余的空格
        lines = text.split("\n")
        cleaned_lines = []

        for line in lines:
            line = line.strip()
            if line:  # 保留非空行
                cleaned_lines.append(line)

        # 重新组合，段落间保留一个空行
        cleaned_text = "\n".join(cleaned_lines)

        # 合并多个连续空格
        cleaned_text = re.sub(r"\s+", " ", cleaned_text)

        return cleaned_text

    def categorize_ooc(
        self, ooc_comments: List[OOCComment]
    ) -> Dict[str, List[OOCComment]]:
        """对OOC注释进行分类"""
        categories = {
            "clarification": [],  # 澄清说明
            "intent": [],  # 意图声明
            "feedback": [],  # 反馈
            "meta": [],  # 元注释
            "question": [],  # 问题
            "correction": [],  # 更正
            "other": [],  # 其他
        }

        for comment in ooc_comments:
            content_lower = comment.content.lower()
            categorized = False

            for category, keywords in self.intent_keywords.items():
                if any(keyword in content_lower for keyword in keywords):
                    categories[category].append(comment)
                    categorized = True
                    break

            if not categorized:
                categories["other"].append(comment)

        return categories

    async def process_ooc_for_session(
        self, session_id: str, ooc_comments: List[OOCComment]
    ) -> Dict[str, Any]:
        """为会话处理OOC注释"""
        # 分类OOC注释
        categories = self.categorize_ooc(ooc_comments)

        # 提取关键信息
        intents = []
        feedbacks = []

        for comment in categories["intent"]:
            intents.append(comment.content)

        for comment in categories["feedback"]:
            feedbacks.append(comment.content)

        result = {
            "session_id": session_id,
            "total_ooc_comments": len(ooc_comments),
            "categories": {k: len(v) for k, v in categories.items()},
            "extracted_intents": intents,
            "extracted_feedback": feedbacks,
            "timestamp": __import__("datetime").datetime.now().isoformat(),
        }

        logger.info(
            f"Processed {len(ooc_comments)} OOC comments for session {session_id}"
        )

        return result

    def merge_ooc_back(
        self,
        narrative_text: str,
        ooc_comments: List[OOCComment],
        style: str = "footnote",
    ) -> str:
        """将OOC注释合并回文本"""
        if not ooc_comments:
            return narrative_text

        if style == "footnote":
            # 脚注风格
            footnotes = []
            for i, comment in enumerate(ooc_comments, 1):
                footnotes.append(f"[{i}] {comment.content}")

            footnote_text = "\n".join(footnotes)
            return f"{narrative_text}\n\n---\nOOC注释:\n{footnote_text}"

        elif style == "inline":
            # 行内风格（在括号中）
            # 这里简化实现
            return narrative_text

        else:
            # 默认：附加在末尾
            ooc_text = "\n".join([f"(OOC: {c.content})" for c in ooc_comments])
            return f"{narrative_text}\n\n{ooc_text}"

    def should_respond_to_ooc(self, ooc_comments: List[OOCComment]) -> bool:
        """判断是否应该回应OOC注释"""
        if not ooc_comments:
            return False

        # 检查是否有需要回应的OOC
        for comment in ooc_comments:
            content_lower = comment.content.lower()

            # 如果包含问号或明确请求回应
            if (
                "?" in comment.content
                or "？" in comment.content
                or any(word in content_lower for word in ["回答", "回应", "请回复"])
            ):
                return True

        return False

    def generate_ooc_response(self, ooc_comments: List[OOCComment]) -> str:
        """生成OOC回应"""
        if not ooc_comments:
            return ""

        responses = []

        for comment in ooc_comments:
            content_lower = comment.content.lower()

            if "?" in comment.content or "？" in comment.content:
                # 对于问题，生成简单回应
                responses.append(f"关于'{comment.content}'：已收到，将在叙事中考虑。")
            elif any(word in content_lower for word in ["谢谢", "感谢"]):
                responses.append("不客气！")
            elif any(word in content_lower for word in ["喜欢", "好评"]):
                responses.append("感谢反馈！")
            elif any(word in content_lower for word in ["不喜欢", "批评"]):
                responses.append("收到反馈，会注意改进。")

        if responses:
            return "\n".join(responses)
        else:
            return "OOC注释已记录。"

    # 与PromptAssembler集成的方法

    def extract_intents_for_prompt(
        self, ooc_comments: List[OOCComment]
    ) -> Dict[str, Any]:
        """提取OOC中的意图信息，用于Prompt组装"""
        categories = self.categorize_ooc(ooc_comments)

        intents = []
        feedbacks = []
        questions = []
        clarifications = []

        for comment in categories["intent"]:
            intents.append(
                {
                    "content": comment.content,
                    "position": comment.position,
                    "metadata": comment.metadata,
                }
            )

        for comment in categories["feedback"]:
            feedbacks.append(
                {
                    "content": comment.content,
                    "sentiment": self._analyze_sentiment(comment.content),
                    "metadata": comment.metadata,
                }
            )

        for comment in categories["question"]:
            questions.append(
                {
                    "content": comment.content,
                    "type": self._classify_question_type(comment.content),
                    "metadata": comment.metadata,
                }
            )

        for comment in categories["clarification"]:
            clarifications.append(
                {
                    "content": comment.content,
                    "subject": self._extract_subject(comment.content),
                    "metadata": comment.metadata,
                }
            )

        return {
            "intents": intents,
            "feedbacks": feedbacks,
            "questions": questions,
            "clarifications": clarifications,
            "summary": self._generate_ooc_summary(categories),
        }

    def _analyze_sentiment(self, content: str) -> str:
        """分析情感倾向"""
        positive_words = ["喜欢", "好", "棒", "优秀", "精彩", "有趣", "满意"]
        negative_words = ["不喜欢", "差", "糟糕", "无聊", "失望", "不满意", "批评"]

        content_lower = content.lower()

        # 首先检查负面词（优先级更高）
        for word in negative_words:
            if word in content_lower:
                return "negative"

        # 然后检查正面词
        for word in positive_words:
            if word in content_lower:
                return "positive"

        return "neutral"

    def _classify_question_type(self, content: str) -> str:
        """分类问题类型"""
        content_lower = content.lower()

        if any(word in content_lower for word in ["为什么", "为何", "原因"]):
            return "why"
        elif any(word in content_lower for word in ["如何", "怎么", "怎样"]):
            return "how"
        elif any(word in content_lower for word in ["何时", "什么时候"]):
            return "when"
        elif any(word in content_lower for word in ["哪里", "何处"]):
            return "where"
        elif any(word in content_lower for word in ["谁", "什么人"]):
            return "who"
        elif any(word in content_lower for word in ["什么", "哪个"]):
            return "what"
        else:
            return "general"

    def _extract_subject(self, content: str) -> str:
        """提取澄清主题"""
        # 简单实现：提取前几个词作为主题
        words = content.split()
        if len(words) > 3:
            return " ".join(words[:3]) + "..."
        return content[:20]

    def _generate_ooc_summary(self, categories: Dict[str, List[OOCComment]]) -> str:
        """生成OOC摘要"""
        summary_parts = []

        for category, comments in categories.items():
            if comments:
                summary_parts.append(f"{category}: {len(comments)}条")

        if summary_parts:
            return "OOC注释分类: " + ", ".join(summary_parts)
        else:
            return "无OOC注释"

    def prepare_ooc_for_prompt_assembler(
        self, ooc_comments: List[OOCComment]
    ) -> List[Dict[str, Any]]:
        """为PromptAssembler准备OOC干预信息"""
        interventions = []

        for comment in ooc_comments:
            # 确定干预类型
            categories = self.categorize_ooc([comment])
            primary_category = next(
                (cat for cat, comments in categories.items() if comments), "other"
            )

            intervention = {
                "type": f"ooc_{primary_category}",
                "content": comment.content,
                "position": comment.position,
                "metadata": {
                    **comment.metadata,
                    "category": primary_category,
                    "processed_by": "OOCHandler",
                },
            }

            # 添加特定字段
            if primary_category == "intent":
                intervention["intent"] = "玩家意图声明"
            elif primary_category == "feedback":
                intervention["sentiment"] = self._analyze_sentiment(comment.content)
            elif primary_category == "question":
                intervention["question_type"] = self._classify_question_type(
                    comment.content
                )

            interventions.append(intervention)

        return interventions

    async def integrate_with_prompt_assembler(
        self, prompt_assembler, context, ooc_comments: List[OOCComment]
    ) -> Dict[str, Any]:
        """与PromptAssembler集成"""
        if not prompt_assembler:
            return {"success": False, "error": "PromptAssembler not provided"}

        # 准备OOC干预信息
        ooc_interventions = self.prepare_ooc_for_prompt_assembler(ooc_comments)

        # 添加到上下文中
        if hasattr(context, "interventions"):
            context.interventions.extend(ooc_interventions)
        else:
            context.interventions = ooc_interventions

        # 提取意图信息
        intents_info = self.extract_intents_for_prompt(ooc_comments)

        # 添加到额外上下文
        if hasattr(context, "additional_context"):
            context.additional_context["ooc_intents"] = intents_info
        else:
            context.additional_context = {"ooc_intents": intents_info}

        return {
            "success": True,
            "ooc_interventions_added": len(ooc_interventions),
            "intents_extracted": len(intents_info["intents"]),
            "feedbacks_extracted": len(intents_info["feedbacks"]),
            "questions_extracted": len(intents_info["questions"]),
        }
