"""交互式需求文档规划服务

通过多轮问答方式引导用户选择，逐步构建完整的需求文档提示词。
问题由 AI 根据上下文动态生成。
"""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ============================================================
# 自定义异常
# ============================================================

class OptionsGenerationError(Exception):
    """选项生成失败异常"""
    pass


class QuestionGenerationError(Exception):
    """问题生成失败异常"""
    pass


# ============================================================
# AI 动态生成问题的提示词模板
# ============================================================

SECTION_CONTEXT = """
需求文档章节分类：
1. 背景与目标（Why）- 需求产生的原因和期望达成的目标
2. 范围（Scope）- 项目的功能范围和边界
3. 用户与使用场景（Use Case）- 目标用户和使用场景
4. 功能需求（Functional Requirements）- 具体的功能点
5. 非功能需求（Non-Functional Requirements）- 性能、安全、兼容性等
6. 输入与输出（I/O）- 数据流转
7. 边界情况（Edge Cases）- 异常处理
8. 技术方案（How）- 技术选型和实现思路
9. 验收标准（Acceptance Criteria）- 成功标准和测试要求
"""

NEXT_QUESTION_PROMPT = """你是一个专业的需求分析师。根据用户的初始需求和对话历史，生成下一个要问的问题。

用户初始需求：{goal}

对话历史（最近的问答）：
{conversation_history}

当前已覆盖的章节：
{covered_sections}

请根据以上信息，判断还需要了解用户的哪些信息来完善需求文档。注意：
1. 每次只问一个问题
2. 问题要具体、明确
3. 选项要简洁（不超过30字），涵盖常见选项
4. 根据章节分类补充尚未覆盖的内容
5. 已收集的信息足够时，可以直接生成最终需求文档

请以JSON格式返回：
{{
  "need_more_info": true/false,  // 是否还需要更多信息
  "next_question": {{
    "section_id": "章节ID",
    "section_name": "章节名称",
    "question_id": "问题ID（唯一标识）",
    "question": "问题文本",
    "allow_multi_select": true/false,  // 是否多选
    "hint": "提示信息",
    "options_prompt": "选项生成提示"
  }},
  "final_doc_content": "...",  // 当 need_more_info=false 时，填写生成的需求文档内容
  "covered_sections": ["1", "2", ...]  // 更新后的已覆盖章节
}}

当 need_more_info=false 时，final_doc_content 应该是一份完整的Markdown格式需求文档，包含所有章节内容。
"""


# ============================================================
# 对话消息结构
# ============================================================

class ConversationMessage:
    """对话消息"""

    def __init__(
        self,
        role: str,  # "user" | "assistant"
        content: str,
        question_id: Optional[str] = None,
        selected_options: Optional[List[Dict]] = None,
    ):
        self.role = role
        self.content = content
        self.question_id = question_id
        self.selected_options = selected_options or []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "question_id": self.question_id,
            "selected_options": self.selected_options,
        }


# ============================================================
# 核心服务类
# ============================================================

class InteractivePlannerService:
    """交互式规划服务"""

    def __init__(self):
        self.question_flow = []  # 不再使用预定义问题
        self._options_cache: Dict[str, List[Dict[str, str]]] = {}

    def get_question_by_index(self, index: int) -> Optional[Dict[str, Any]]:
        """根据索引获取问题（不再支持，按索引获取已废弃）"""
        return None

    def get_question_with_options(
        self,
        index: int,
        goal: str,
        previous_answers: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> Optional[Dict[str, Any]]:
        """获取问题及其由 LLM 生成的问题和选项

        Args:
            index: 问题索引（已废弃，仅保留兼容性）
            goal: 用户目标
            previous_answers: 之前的回答（对话历史）

        Returns:
            问题字典（包含 AI 生成的问题和选项）
        """
        try:
            from config.ai_config import get_api_key, get_default_provider

            api_key = get_api_key(get_default_provider())
            if not api_key:
                logger.warning("[InteractivePlanner] 未配置AI API Key")
                raise OptionsGenerationError("未配置AI API Key")

            try:
                from zhipuai import ZhipuAI
                client = ZhipuAI(api_key=api_key)
            except ImportError:
                logger.warning("[InteractivePlanner] 未安装 zhipuai")
                raise OptionsGenerationError("未安装 zhipuai 库")

            # 构建对话历史
            conversation_history = self._build_conversation_history(previous_answers)
            covered_sections = self._get_covered_sections(previous_answers)

            prompt = NEXT_QUESTION_PROMPT.format(
                goal=goal,
                conversation_history=conversation_history or "（暂无，用户刚提交需求）",
                covered_sections=covered_sections or "（暂无，尚未开始问答）"
            )

            messages = [{"role": "user", "content": prompt}]
            logger.info(f"[InteractivePlanner] 调用AI生成下一个问题 | goal={goal[:50]}...")

            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=messages,
                max_tokens=2048,
                temperature=0.7
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"[InteractivePlanner] AI响应: {content[:200]}...")

            # 解析JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            data = json.loads(content.strip())

            # 检查是否需要更多信息
            if not data.get("need_more_info", True):
                # AI 认为信息足够，返回文档生成信号
                return {
                    "section_id": "doc",
                    "section_name": "需求文档",
                    "question_id": "final_doc",
                    "question": "已收集足够信息，正在生成需求文档...",
                    "allow_multi_select": False,
                    "hint": "",
                    "options": [],
                    "is_final_doc": True,
                    "final_doc_content": data.get("final_doc_content", ""),
                    "covered_sections": data.get("covered_sections", []),
                }

            # 返回 AI 生成的问题
            next_q = data.get("next_question", {})
            if not next_q:
                raise QuestionGenerationError("AI 未返回有效的问题")

            # 生成该问题的选项
            question_id = next_q.get("question_id", f"q_{index}")
            options = self._generate_options_via_llm(
                goal, next_q, previous_answers, conversation_history
            )

            return {
                "section_id": next_q.get("section_id", ""),
                "section_name": next_q.get("section_name", ""),
                "question_id": question_id,
                "question": next_q.get("question", ""),
                "allow_multi_select": True,
                "hint": next_q.get("hint", ""),
                "options": options,
                "is_final_doc": False,
            }

        except QuestionGenerationError:
            raise
        except OptionsGenerationError:
            raise
        except Exception as e:
            logger.error(f"[InteractivePlanner] 生成问题失败: {str(e)}")
            raise QuestionGenerationError(f"LLM生成问题失败: {str(e)}")

    def _build_conversation_history(
        self,
        previous_answers: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> str:
        """构建对话历史文本"""
        if not previous_answers:
            return ""

        lines = []
        for _section_id, answers in previous_answers.items():
            for answer in answers:
                q_text = answer.get("question_text", "") or answer.get("question", "")
                selected = answer.get("selected_options", [])
                if selected:
                    selected_texts = [opt.get("text", "") for opt in selected if isinstance(opt, dict)]
                    if selected_texts:
                        lines.append(f"问：{q_text}")
                        lines.append(f"答：{'; '.join(selected_texts)}")
                        lines.append("---")

        return "\n".join(lines) if lines else ""

    def _get_covered_sections(
        self,
        previous_answers: Optional[Dict[str, List[Dict[str, Any]]]] = None
    ) -> List[str]:
        """获取已覆盖的章节列表"""
        if not previous_answers:
            return []

        covered = set()
        for section_id, answers in previous_answers.items():
            if answers:  # 该章节有回答
                covered.add(section_id)

        return sorted(list(covered))

    def _generate_options_via_llm(
        self,
        goal: str,
        question: Dict[str, Any],
        previous_answers: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        conversation_history: str = "",
    ) -> List[Dict[str, str]]:
        """调用 LLM 生成选项

        Args:
            goal: 用户目标
            question: 问题定义
            previous_answers: 之前的回答
            conversation_history: 对话历史文本

        Returns:
            选项列表
        """
        try:
            from config.ai_config import get_api_key, get_default_provider

            api_key = get_api_key(get_default_provider())
            if not api_key:
                raise OptionsGenerationError("未配置AI API Key")

            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=api_key)

            # 构建上下文
            context = ""
            if conversation_history:
                context = f"\n\n已有对话历史：\n{conversation_history}"

            options_prompt = question.get("options_prompt", "请生成4-6个简洁选项")

            prompt = f"""根据用户需求生成选项。

用户需求：{goal}

当前问题：{question.get('question', '')}

{options_prompt}

请生成4-8个简洁选项（不超过30字）。

请以JSON格式返回：
{{
  "options": [
    {{"id": "选项1的简短ID", "text": "选项1的文本"}},
    {{"id": "选项2的简短ID", "text": "选项2的文本"}}
  ]
}}
{context}"""

            messages = [{"role": "user", "content": prompt}]
            logger.info(f"[InteractivePlanner] 生成选项 | question_id={question.get('question_id', 'unknown')}")

            response = client.chat.completions.create(
                model="glm-4-flash",
                messages=messages,
                max_tokens=1024,
                temperature=0.8
            )

            content = response.choices[0].message.content.strip()
            logger.info(f"[InteractivePlanner] 选项响应: {content[:100]}...")

            # 解析JSON
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]

            data = json.loads(content.strip())
            options = data.get('options', [])

            if not options:
                raise OptionsGenerationError("LLM返回了空选项")

            return options

        except Exception as e:
            logger.error(f"[InteractivePlanner] 生成选项失败: {str(e)}")
            raise OptionsGenerationError(f"LLM生成选项失败: {str(e)}")

    def get_total_questions(self) -> int:
        """获取问题总数（动态模式返回-1表示不固定）"""
        return -1

    def get_current_section_questions(self, section_id: str) -> List[Dict[str, Any]]:
        """获取指定章节的所有问题（动态模式暂不支持）"""
        return []

    def parse_answer(
        self,
        question_id: str,
        question_text: str,
        selected_ids: List[str],
        options: List[Dict[str, str]],
        custom_input: Optional[str] = None
    ) -> Dict[str, Any]:
        """解析用户答案，并保存选项的完整信息"""
        options_map = {opt["id"]: opt["text"] for opt in options}

        selected_options = []
        for sid in selected_ids:
            selected_options.append({
                "id": sid,
                "text": options_map.get(sid, sid)
            })

        return {
            "question_id": question_id,
            "question_text": question_text,
            "selected_ids": selected_ids,
            "selected_options": selected_options,
            "custom_input": custom_input,
        }

    def explain_question(self, question_text: str, user_question: str = "") -> str:
        """解释当前问题的含义

        Args:
            question_text: 问题的文本
            user_question: 用户针对该问题的提问

        Returns:
            AI 解释的文本
        """
        from config.ai_config import get_api_key, get_default_provider

        api_key = get_api_key(get_default_provider())
        if not api_key:
            return "未配置AI API Key，无法解释问题"

        try:
            from zhipuai import ZhipuAI
            client = ZhipuAI(api_key=api_key)
        except ImportError:
            return "未安装 zhipuai SDK，无法解释问题"

        prompt = f"""你是一个专业的需求分析师。当前需要回答的问题是：

问题：「{question_text}」

用户提问：「{user_question if user_question else '这个题目是什么意思？'}」

请用简洁易懂的语言解释这个问题的含义，帮助用户理解如何回答。如果用户没有提问，请简要说明这个问题的目的和回答方向。

回答："""

        try:
            response = client.chat.completions.create(
                model="glm-4",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
            )
            explanation = response.choices[0].message.content.strip()
            return explanation
        except Exception as e:
            logger.error(f"[InteractivePlanner] 解释问题失败: {str(e)}")
            return f"解释问题失败: {str(e)}"

    def build_requirement_doc_prompt(
        self,
        goal: str,
        answers: Dict[str, List[Dict[str, Any]]]
    ) -> Dict[str, Any]:
        """根据用户回答构建需求文档提示词（动态模式下由AI直接生成）"""
        return {
            "goal": goal,
            "answers": answers,
            "document_type": "requirement",
        }


# 全局服务实例
_interactive_planner_service = None


def get_interactive_planner_service() -> InteractivePlannerService:
    """获取交互式规划服务单例"""
    global _interactive_planner_service
    if _interactive_planner_service is None:
        _interactive_planner_service = InteractivePlannerService()
    return _interactive_planner_service