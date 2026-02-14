# Python 客户端

LOOM 提供了功能完整的 Python 客户端库，支持异步和同步两种调用方式，便于与 LOOM 系统进行交互。

## 安装

Python 客户端库已包含在 LOOM 项目中，无需额外安装。确保已安装以下依赖：

```bash
pip install aiohttp
```

## 快速开始

### 异步客户端

```python
import asyncio
from src.loom.api.client import LoomClient

async def main():
    # 创建客户端实例
    async with LoomClient(base_url="http://localhost:8000") as client:
        # 创建新会话
        session = await client.create_session(
            world_name="奇幻世界",
            character_name="冒险者",
            scenario="你是一名勇敢的冒险者，正在探索古老的遗迹。",
            rules=["战斗规则", "魔法规则"]
        )

        print(f"创建会话: {session['id']}")

        # 处理回合
        response = await client.process_turn(
            session_id=session['id'],
            input_text="我检查一下这个房间"
        )

        print(f"响应: {response['response']}")

# 运行异步函数
asyncio.run(main())
```

### 同步客户端

```python
from src.loom.api.client import SyncLoomClient

# 创建同步客户端实例
with SyncLoomClient(base_url="http://localhost:8000") as client:
    # 创建新会话
    session = client.create_session(
        world_name="科幻世界",
        character_name="太空探险家",
        scenario="你是一名太空探险家，发现了未知的外星文明。",
        rules=["物理规则", "外交规则"]
    )

    print(f"创建会话: {session['id']}")

    # 处理回合
    response = client.process_turn(
        session_id=session['id'],
        input_text="扫描外星结构"
    )

    print(f"响应: {response['response']}")
```

## API 参考

### LoomClient 类

#### 构造函数

```python
def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None)
```

**参数：**
- `base_url` (str): LOOM API 服务器的基础URL，默认为 `http://localhost:8000`
- `api_key` (Optional[str]): API密钥，用于认证（可选）

#### 连接管理

```python
async def connect(self)
```
连接到服务器，创建内部会话。

```python
async def close(self)
```
关闭连接，释放资源。

#### 会话管理 API

##### `create_session`
```python
async def create_session(self, world_name: str, character_name: str,
                       scenario: str = "", rules: List[str] = None) -> Dict[str, Any]
```
创建新会话。

**参数：**
- `world_name` (str): 世界名称
- `character_name` (str): 角色名称
- `scenario` (str): 场景描述（可选）
- `rules` (List[str]): 规则列表（可选）

**返回：**
包含会话信息的字典，包括 `id`、`name`、`created_at` 等字段。

##### `get_session`
```python
async def get_session(self, session_id: str) -> Dict[str, Any]
```
获取指定会话的详细信息。

**参数：**
- `session_id` (str): 会话ID

**返回：**
会话详细信息字典。

##### `list_sessions`
```python
async def list_sessions(self, limit: int = 20, offset: int = 0) -> List[Dict[str, Any]]
```
列出所有会话。

**参数：**
- `limit` (int): 返回数量限制，默认为20
- `offset` (int): 偏移量，用于分页，默认为0

**返回：**
会话列表。

##### `process_turn`
```python
async def process_turn(self, session_id: str, input_text: str) -> Dict[str, Any]
```
处理一个回合（用户输入）。

**参数：**
- `session_id` (str): 会话ID
- `input_text` (str): 用户输入文本

**返回：**
包含响应信息的字典，包括 `response`、`turn_id`、`timestamp` 等字段。

##### `save_session`
```python
async def save_session(self, session_id: str, filepath: str = "") -> Dict[str, Any]
```
保存会话到文件。

**参数：**
- `session_id` (str): 会话ID
- `filepath` (str): 文件路径（可选，如不指定则使用默认路径）

**返回：**
保存结果字典。

#### 规则管理 API

##### `validate_rule`
```python
async def validate_rule(self, rule_text: str) -> Dict[str, Any]
```
验证规则文本的语法和结构。

**参数：**
- `rule_text` (str): 规则文本

**返回：**
验证结果字典，包含 `valid`、`errors`、`warnings` 等字段。

##### `check_consistency`
```python
async def check_consistency(self, rule_texts: List[str]) -> Dict[str, Any]
```
检查多个规则之间的一致性。

**参数：**
- `rule_texts` (List[str]): 规则文本列表

**返回：**
一致性检查结果字典，包含 `consistent`、`conflicts`、`suggestions` 等字段。

#### 世界管理 API

##### `get_world_config`
```python
async def get_world_config(self, world_name: str) -> Dict[str, Any]
```
获取指定世界的配置信息。

**参数：**
- `world_name` (str): 世界名称

**返回：**
世界配置字典。

##### `create_world`
```python
async def create_world(self, config: Dict[str, Any]) -> Dict[str, Any]
```
创建新世界。

**参数：**
- `config` (Dict[str, Any]): 世界配置字典

**返回：**
创建结果字典。

#### 记忆管理 API

##### `query_memory`
```python
async def query_memory(self, session_id: str, query: str, limit: int = 10) -> List[Dict[str, Any]]
```
查询会话记忆。

**参数：**
- `session_id` (str): 会话ID
- `query` (str): 查询文本
- `limit` (int): 返回数量限制，默认为10

**返回：**
记忆条目列表。

##### `summarize_memory`
```python
async def summarize_memory(self, session_id: str) -> Dict[str, Any]
```
总结会话记忆。

**参数：**
- `session_id` (str): 会话ID

**返回：**
记忆总结字典。

#### 导出 API

##### `export_session`
```python
async def export_session(self, session_id: str, format: str = "json") -> Dict[str, Any]
```
导出会话数据。

**参数：**
- `session_id` (str): 会话ID
- `format` (str): 导出格式，支持 `json`、`markdown`、`yaml`、`csv`，默认为 `json`

**返回：**
导出数据字典。

#### 系统状态 API

##### `health_check`
```python
async def health_check(self) -> Dict[str, Any]
```
检查系统健康状态。

**返回：**
健康状态字典，包含 `status`、`version`、`uptime` 等字段。

##### `get_system_info`
```python
async def get_system_info(self) -> Dict[str, Any]
```
获取系统信息。

**返回：**
系统信息字典，包含 `version`、`components`、`config` 等字段。

#### 插件管理 API

##### `list_plugins`
```python
async def list_plugins(self) -> List[Dict[str, Any]]
```
列出所有可用插件。

**返回：**
插件列表。

##### `get_plugin`
```python
async def get_plugin(self, plugin_name: str) -> Dict[str, Any]
```
获取指定插件的详细信息。

**参数：**
- `plugin_name` (str): 插件名称

**返回：**
插件信息字典。

#### 便捷方法

##### `run_conversation`
```python
async def run_conversation(self, session_id: str, messages: List[str]) -> List[Dict[str, Any]]
```
运行多轮对话。

**参数：**
- `session_id` (str): 会话ID
- `messages` (List[str]): 消息列表

**返回：**
响应列表，每个响应包含 `input`、`response`、`timestamp` 字段。

##### `batch_create_sessions`
```python
async def batch_create_sessions(self, sessions_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]
```
批量创建多个会话。

**参数：**
- `sessions_data` (List[Dict[str, Any]]): 会话数据列表，每个字典包含 `world_name`、`character_name`、`scenario`、`rules` 字段

**返回：**
创建结果列表。

### SyncLoomClient 类

`SyncLoomClient` 是 `LoomClient` 的同步包装器，提供相同的 API 但使用同步调用方式。

#### 构造函数

```python
def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None)
```

**参数：**
- `base_url` (str): LOOM API 服务器的基础URL，默认为 `http://localhost:8000`
- `api_key` (Optional[str]): API密钥，用于认证（可选）

#### 方法

`SyncLoomClient` 提供了与 `LoomClient` 完全相同的所有方法，但都是同步版本。方法签名和功能与异步版本一致。

### 错误处理

#### LoomClientError

```python
class LoomClientError(Exception):
    """LOOM 客户端错误"""
    pass
```

当 API 调用失败时，会抛出 `LoomClientError` 异常。常见错误包括：
- 网络连接问题
- 服务器返回错误状态码
- JSON 解析失败

## 高级用法

### 使用 API 密钥

```python
async with LoomClient(
    base_url="https://api.your-loom-server.com",
    api_key="your-api-key-here"
) as client:
    # 使用认证的客户端
    sessions = await client.list_sessions()
```

### 错误处理示例

```python
from src.loom.api.client import LoomClient, LoomClientError

async def safe_api_call():
    try:
        async with LoomClient() as client:
            response = await client.health_check()
            print(f"系统状态: {response['status']}")
    except LoomClientError as e:
        print(f"客户端错误: {e}")
    except Exception as e:
        print(f"未知错误: {e}")
```

### 批量操作

```python
async def batch_operations():
    async with LoomClient() as client:
        # 批量创建会话
        sessions_data = [
            {
                "world_name": "奇幻世界",
                "character_name": "法师",
                "scenario": "你是一名强大的法师，正在研究古代魔法。"
            },
            {
                "world_name": "科幻世界",
                "character_name": "工程师",
                "scenario": "你是一名太空工程师，负责维护空间站。"
            }
        ]

        results = await client.batch_create_sessions(sessions_data)

        # 批量处理回合
        for session in results:
            response = await client.process_turn(
                session_id=session['id'],
                input_text="开始探索"
            )
            print(f"会话 {session['id']} 响应: {response['response'][:50]}...")
```

### 记忆查询示例

```python
async def memory_example():
    async with LoomClient() as client:
        # 创建会话
        session = await client.create_session(
            world_name="侦探世界",
            character_name="侦探",
            scenario="你是一名侦探，正在调查一桩谋杀案。"
        )

        # 进行几轮对话
        await client.process_turn(session['id'], "我到达犯罪现场")
        await client.process_turn(session['id'], "检查尸体")
        await client.process_turn(session['id'], "寻找线索")

        # 查询记忆
        memories = await client.query_memory(
            session_id=session['id'],
            query="犯罪现场",
            limit=5
        )

        print(f"找到 {len(memories)} 条相关记忆:")
        for memory in memories:
            print(f"- {memory['content'][:100]}...")

        # 获取记忆总结
        summary = await client.summarize_memory(session['id'])
        print(f"记忆总结: {summary['summary'][:200]}...")
```

## 最佳实践

1. **使用上下文管理器**：始终使用 `async with` 或 `with` 语句来确保资源正确释放。
2. **错误处理**：对 API 调用进行适当的错误处理。
3. **连接复用**：对于多个 API 调用，复用同一个客户端实例以提高性能。
4. **超时设置**：对于长时间运行的操作，考虑设置适当的超时。
5. **分页处理**：当处理大量数据时，使用 `limit` 和 `offset` 参数进行分页。

## 常见问题

### Q: 如何连接到远程服务器？
A: 在创建客户端时指定 `base_url` 参数：
```python
client = LoomClient(base_url="https://your-server.com:8000")
```

### Q: 如何处理认证？
A: 使用 `api_key` 参数：
```python
client = LoomClient(api_key="your-api-key")
```

### Q: 如何导出会话数据？
A: 使用 `export_session` 方法：
```python
export_data = await client.export_session(session_id, format="markdown")
```

### Q: 客户端支持哪些导出格式？
A: 支持 `json`、`markdown`、`yaml`、`csv` 四种格式。

### Q: 如何检查服务器是否正常运行？
A: 使用 `health_check` 方法：
```python
status = await client.health_check()
if status['status'] == 'healthy':
    print("服务器运行正常")
