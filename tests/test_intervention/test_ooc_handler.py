"""
OOCHandler单元测试
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.loom.intervention.ooc_handler import OOCHandler, OOCComment, OOCResult


class TestOOCHandler:
    """OOCHandler测试类"""

    def setup_method(self):
        """测试设置"""
        self.handler = OOCHandler()

    def test_extract_ooc_bracket_format(self):
        """测试括号格式解析"""
        text = "叙事文本(OOC: 这是一个OOC注释)"
        result = self.handler.extract_ooc(text)

        assert len(result.ooc_comments) == 1
        comment = result.ooc_comments[0]
        assert comment.content == "这是一个OOC注释"
        assert comment.position > 0
        assert "叙事文本" in result.narrative_text

    def test_extract_ooc_slash_format(self):
        """测试斜杠格式解析"""
        text = "叙事文本 /ooc 这是一个OOC注释"
        result = self.handler.extract_ooc(text)

        assert len(result.ooc_comments) == 1
        comment = result.ooc_comments[0]
        assert comment.content == "这是一个OOC注释"

    def test_extract_ooc_meta_format(self):
        """测试meta格式解析"""
        text = "叙事文本[meta] 这是一个meta注释"
        result = self.handler.extract_ooc(text)

        assert len(result.ooc_comments) == 1
        comment = result.ooc_comments[0]
        assert comment.content == "这是一个meta注释"

    def test_extract_ooc_multiple_formats(self):
        """测试多种格式混合解析"""
        text = "叙事文本(OOC: 注释1) /ooc 注释2 [meta] 注释3"
        result = self.handler.extract_ooc(text)

        assert len(result.ooc_comments) == 3
        contents = [c.content for c in result.ooc_comments]
        assert "注释1" in contents
        assert "注释2" in contents
        assert "注释3" in contents

    def test_extract_ooc_nested_brackets(self):
        """测试嵌套括号解析"""
        text = "叙事文本(OOC: 这是一个(嵌套)的注释)"
        result = self.handler.extract_ooc(text)

        assert len(result.ooc_comments) == 1
        comment = result.ooc_comments[0]
        assert comment.content == "这是一个(嵌套)的注释"

    def test_extract_ooc_no_ooc(self):
        """测试无OOC的文本解析"""
        text = "这是一个纯粹的叙事文本，没有任何OOC注释。"
        result = self.handler.extract_ooc(text)

        assert len(result.ooc_comments) == 0
        assert "叙事文本" in result.narrative_text

    def test_categorize_ooc(self):
        """测试OOC分类"""
        comments = [
            OOCComment(content="我觉得这个角色应该更勇敢", position=0),
            OOCComment(content="城堡里有什么？", position=10),
            OOCComment(content="请改变天气", position=20),
            OOCComment(content="剧情发展太快了", position=30),
        ]

        categories = self.handler.categorize_ooc(comments)

        assert len(categories["intent"]) > 0
        assert len(categories["question"]) > 0
        assert len(categories["feedback"]) > 0

    def test_should_respond_to_ooc_with_question(self):
        """测试判断是否应该回应OOC（包含问题）"""
        comments = [
            OOCComment(content="这是什么地方？", position=0),
        ]

        should_respond = self.handler.should_respond_to_ooc(comments)

        assert should_respond == True

    def test_should_respond_to_ooc_without_question(self):
        """测试判断是否应该回应OOC（不包含问题）"""
        comments = [
            OOCComment(content="我觉得很好", position=0),
        ]

        should_respond = self.handler.should_respond_to_ooc(comments)

        assert should_respond == False

    def test_generate_ooc_response(self):
        """测试生成OOC回应"""
        comments = [
            OOCComment(content="这是什么地方？", position=0),
            OOCComment(content="谢谢", position=10),
        ]

        response = self.handler.generate_ooc_response(comments)

        assert "已收到" in response
        assert "不客气" in response

    def test_merge_ooc_back_footnote_style(self):
        """测试将OOC合并回文本（脚注风格）"""
        narrative_text = "叙事文本"
        comments = [
            OOCComment(content="注释1", position=0),
            OOCComment(content="注释2", position=10),
        ]

        merged = self.handler.merge_ooc_back(narrative_text, comments, style="footnote")

        assert "叙事文本" in merged
        assert "OOC注释" in merged
        assert "[1]" in merged
        assert "[2]" in merged

    def test_extract_intents_for_prompt(self):
        """测试为Prompt提取意图"""
        comments = [
            OOCComment(content="我觉得这个角色应该更勇敢", position=0),
            OOCComment(content="城堡里有什么？", position=10),
        ]

        intents_info = self.handler.extract_intents_for_prompt(comments)

        assert "intents" in intents_info
        assert "feedbacks" in intents_info
        assert "questions" in intents_info
        assert "summary" in intents_info

    def test_prepare_ooc_for_prompt_assembler(self):
        """测试为PromptAssembler准备OOC干预信息"""
        comments = [
            OOCComment(content="角色应该更勇敢", position=0),
        ]

        interventions = self.handler.prepare_ooc_for_prompt_assembler(comments)

        assert len(interventions) == 1
        assert interventions[0]["type"] == "ooc_intent"
        assert "角色应该更勇敢" in interventions[0]["content"]

    @pytest.mark.asyncio
    async def test_process_ooc_for_session(self):
        """测试为会话处理OOC注释"""
        comments = [
            OOCComment(content="测试注释1", position=0),
            OOCComment(content="测试注释2", position=10),
        ]

        result = await self.handler.process_ooc_for_session("test_session", comments)

        assert result["session_id"] == "test_session"
        assert result["total_ooc_comments"] == 2
        assert "categories" in result
        assert "extracted_intents" in result

    @pytest.mark.asyncio
    async def test_integrate_with_prompt_assembler(self):
        """测试与PromptAssembler集成"""
        mock_prompt_assembler = Mock()
        mock_context = Mock()
        mock_context.interventions = []
        mock_context.additional_context = {}

        comments = [
            OOCComment(content="角色应该更勇敢", position=0),
        ]

        result = await self.handler.integrate_with_prompt_assembler(
            mock_prompt_assembler, mock_context, comments
        )

        assert result["success"] == True
        assert result["ooc_interventions_added"] == 1
        assert result["intents_extracted"] >= 0

    def test_analyze_sentiment_positive(self):
        """测试情感分析（正面）"""
        content = "我喜欢这个故事"
        sentiment = self.handler._analyze_sentiment(content)

        assert sentiment == "positive"

    def test_analyze_sentiment_negative(self):
        """测试情感分析（负面）"""
        content = "我不喜欢这个角色"
        sentiment = self.handler._analyze_sentiment(content)

        assert sentiment == "negative"

    def test_analyze_sentiment_neutral(self):
        """测试情感分析（中性）"""
        content = "这是一个注释"
        sentiment = self.handler._analyze_sentiment(content)

        assert sentiment == "neutral"

    def test_classify_question_type_why(self):
        """测试问题类型分类（为什么）"""
        content = "为什么会这样？"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "why"

    def test_classify_question_type_how(self):
        """测试问题类型分类（如何）"""
        content = "如何解决？"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "how"

    def test_classify_question_type_when(self):
        """测试问题类型分类（何时）"""
        content = "什么时候开始？"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "when"

    def test_classify_question_type_where(self):
        """测试问题类型分类（哪里）"""
        content = "在哪里？"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "where"

    def test_classify_question_type_who(self):
        """测试问题类型分类（谁）"""
        content = "谁做的？"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "who"

    def test_classify_question_type_what(self):
        """测试问题类型分类（什么）"""
        content = "这是什么？"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "what"

    def test_classify_question_type_general(self):
        """测试问题类型分类（一般）"""
        content = "注释"
        qtype = self.handler._classify_question_type(content)

        assert qtype == "general"

    def test_extract_subject(self):
        """测试提取主题"""
        content = "关于角色性格的澄清说明"
        subject = self.handler._extract_subject(content)

        assert len(subject) > 0

    def test_generate_ooc_summary(self):
        """测试生成OOC摘要"""
        comments = [
            OOCComment(content="测试1", position=0),
            OOCComment(content="测试2", position=10),
        ]

        categories = self.handler.categorize_ooc(comments)
        summary = self.handler._generate_ooc_summary(categories)

        assert "OOC注释分类" in summary


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
