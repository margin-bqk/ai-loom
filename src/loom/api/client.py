"""
LOOM API 客户端库
提供与 LOOM 系统交互的 Python 客户端
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import aiohttp


class LoomClient:
    """LOOM API 客户端"""

    def __init__(
        self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None
    ):
        """
        初始化客户端

        Args:
            base_url: API 基础URL
            api_key: API密钥（可选）
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        await self.close()

    async def connect(self):
        """连接服务器"""
        if self.session is None:
            self.session = aiohttp.ClientSession(
                headers=self._get_headers(), timeout=aiohttp.ClientTimeout(total=30)
            )

    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.close()
            self.session = None

    def _get_headers(self) -> Dict[str, str]:
        """获取请求头"""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "LOOM-Python-Client/1.0.0",
        }

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        return headers

    async def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """发送HTTP请求"""
        if self.session is None:
            await self.connect()

        url = f"{self.base_url}/api/v1{endpoint}"

        try:
            async with self.session.request(method, url, **kwargs) as response:
                response.raise_for_status()
                return await response.json()

        except aiohttp.ClientError as e:
            raise LoomClientError(f"HTTP请求失败: {e}")
        except json.JSONDecodeError as e:
            raise LoomClientError(f"JSON解析失败: {e}")

    # 会话管理 API

    async def create_session(
        self,
        world_name: str,
        character_name: str,
        scenario: str = "",
        rules: List[str] = None,
    ) -> Dict[str, Any]:
        """
        创建新会话

        Args:
            world_name: 世界名称
            character_name: 角色名称
            scenario: 场景描述
            rules: 规则列表

        Returns:
            会话信息
        """
        data = {
            "world_name": world_name,
            "character_name": character_name,
            "scenario": scenario,
            "rules": rules or [],
        }

        return await self._request("POST", "/sessions", json=data)

    async def get_session(self, session_id: str) -> Dict[str, Any]:
        """
        获取会话信息

        Args:
            session_id: 会话ID

        Returns:
            会话信息
        """
        return await self._request("GET", f"/sessions/{session_id}")

    async def list_sessions(
        self, limit: int = 20, offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        列出所有会话

        Args:
            limit: 返回数量限制
            offset: 偏移量

        Returns:
            会话列表
        """
        params = {"limit": limit, "offset": offset}
        response = await self._request("GET", "/sessions", params=params)
        return response.get("sessions", [])

    async def process_turn(self, session_id: str, input_text: str) -> Dict[str, Any]:
        """
        处理回合

        Args:
            session_id: 会话ID
            input_text: 输入文本

        Returns:
            响应信息
        """
        data = {"input": input_text}
        return await self._request("POST", f"/sessions/{session_id}/turn", json=data)

    async def save_session(self, session_id: str, filepath: str = "") -> Dict[str, Any]:
        """
        保存会话

        Args:
            session_id: 会话ID
            filepath: 文件路径（可选）

        Returns:
            保存结果
        """
        data = {"filepath": filepath} if filepath else {}
        return await self._request("POST", f"/sessions/{session_id}/save", json=data)

    # 规则管理 API

    async def validate_rule(self, rule_text: str) -> Dict[str, Any]:
        """
        验证规则

        Args:
            rule_text: 规则文本

        Returns:
            验证结果
        """
        data = {"rule_text": rule_text}
        return await self._request("POST", "/rules/validate", json=data)

    async def check_consistency(self, rule_texts: List[str]) -> Dict[str, Any]:
        """
        检查规则一致性

        Args:
            rule_texts: 规则文本列表

        Returns:
            一致性检查结果
        """
        data = {"rules": rule_texts}
        return await self._request("POST", "/rules/consistency", json=data)

    # 世界管理 API

    async def get_world_config(self, world_name: str) -> Dict[str, Any]:
        """
        获取世界配置

        Args:
            world_name: 世界名称

        Returns:
            世界配置
        """
        return await self._request("GET", f"/worlds/{world_name}")

    async def create_world(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建新世界

        Args:
            config: 世界配置

        Returns:
            创建结果
        """
        return await self._request("POST", "/worlds", json=config)

    # 记忆管理 API

    async def query_memory(
        self, session_id: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        查询记忆

        Args:
            session_id: 会话ID
            query: 查询文本
            limit: 返回数量限制

        Returns:
            记忆列表
        """
        params = {"query": query, "limit": limit}
        response = await self._request(
            "GET", f"/sessions/{session_id}/memory", params=params
        )
        return response.get("memories", [])

    async def summarize_memory(self, session_id: str) -> Dict[str, Any]:
        """
        总结记忆

        Args:
            session_id: 会话ID

        Returns:
            记忆总结
        """
        return await self._request("GET", f"/sessions/{session_id}/memory/summary")

    # 导出 API

    async def export_session(
        self, session_id: str, format: str = "json"
    ) -> Dict[str, Any]:
        """
        导出会话

        Args:
            session_id: 会话ID
            format: 导出格式（json, markdown, yaml, csv）

        Returns:
            导出数据
        """
        params = {"format": format}
        return await self._request(
            "GET", f"/sessions/{session_id}/export", params=params
        )

    # 系统状态 API

    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查

        Returns:
            系统状态
        """
        return await self._request("GET", "/health")

    async def get_system_info(self) -> Dict[str, Any]:
        """
        获取系统信息

        Returns:
            系统信息
        """
        return await self._request("GET", "/system/info")

    # 插件管理 API

    async def list_plugins(self) -> List[Dict[str, Any]]:
        """
        列出所有插件

        Returns:
            插件列表
        """
        response = await self._request("GET", "/plugins")
        return response.get("plugins", [])

    async def get_plugin(self, plugin_name: str) -> Dict[str, Any]:
        """
        获取插件信息

        Args:
            plugin_name: 插件名称

        Returns:
            插件信息
        """
        return await self._request("GET", f"/plugins/{plugin_name}")

    # 便捷方法

    async def run_conversation(
        self, session_id: str, messages: List[str]
    ) -> List[Dict[str, Any]]:
        """
        运行对话

        Args:
            session_id: 会话ID
            messages: 消息列表

        Returns:
            响应列表
        """
        responses = []

        for message in messages:
            response = await self.process_turn(session_id, message)
            responses.append(
                {
                    "input": message,
                    "response": response.get("response", ""),
                    "timestamp": datetime.now().isoformat(),
                }
            )

        return responses

    async def batch_create_sessions(
        self, sessions_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量创建会话

        Args:
            sessions_data: 会话数据列表

        Returns:
            创建结果列表
        """
        tasks = []
        for data in sessions_data:
            task = self.create_session(
                data["world_name"],
                data["character_name"],
                data.get("scenario", ""),
                data.get("rules", []),
            )
            tasks.append(task)

        return await asyncio.gather(*tasks)


class LoomClientError(Exception):
    """LOOM 客户端错误"""

    pass


# 同步客户端（简化版）
class SyncLoomClient:
    """同步 LOOM 客户端（使用 asyncio 包装）"""

    def __init__(
        self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None
    ):
        self.client = LoomClient(base_url, api_key)
        self.loop = asyncio.new_event_loop()

    def __enter__(self):
        """同步上下文管理器入口"""
        self.loop.run_until_complete(self.client.connect())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """同步上下文管理器出口"""
        self.loop.run_until_complete(self.client.close())
        self.loop.close()

    def _run_async(self, coro):
        """运行异步协程"""
        return self.loop.run_until_complete(coro)

    # 包装所有异步方法
    def create_session(self, *args, **kwargs):
        return self._run_async(self.client.create_session(*args, **kwargs))

    def get_session(self, *args, **kwargs):
        return self._run_async(self.client.get_session(*args, **kwargs))

    def list_sessions(self, *args, **kwargs):
        return self._run_async(self.client.list_sessions(*args, **kwargs))

    def process_turn(self, *args, **kwargs):
        return self._run_async(self.client.process_turn(*args, **kwargs))

    def save_session(self, *args, **kwargs):
        return self._run_async(self.client.save_session(*args, **kwargs))

    def validate_rule(self, *args, **kwargs):
        return self._run_async(self.client.validate_rule(*args, **kwargs))

    def check_consistency(self, *args, **kwargs):
        return self._run_async(self.client.check_consistency(*args, **kwargs))

    def get_world_config(self, *args, **kwargs):
        return self._run_async(self.client.get_world_config(*args, **kwargs))

    def create_world(self, *args, **kwargs):
        return self._run_async(self.client.create_world(*args, **kwargs))

    def query_memory(self, *args, **kwargs):
        return self._run_async(self.client.query_memory(*args, **kwargs))

    def summarize_memory(self, *args, **kwargs):
        return self._run_async(self.client.summarize_memory(*args, **kwargs))

    def export_session(self, *args, **kwargs):
        return self._run_async(self.client.export_session(*args, **kwargs))

    def health_check(self, *args, **kwargs):
        return self._run_async(self.client.health_check(*args, **kwargs))

    def get_system_info(self, *args, **kwargs):
        return self._run_async(self.client.get_system_info(*args, **kwargs))

    def list_plugins(self, *args, **kwargs):
        return self._run_async(self.client.list_plugins(*args, **kwargs))

    def get_plugin(self, *args, **kwargs):
        return self._run_async(self.client.get_plugin(*args, **kwargs))

    def run_conversation(self, *args, **kwargs):
        return self._run_async(self.client.run_conversation(*args, **kwargs))

    def batch_create_sessions(self, *args, **kwargs):
        return self._run_async(self.client.batch_create_sessions(*args, **kwargs))
