"""
LOOM Web 应用主入口

基于 FastAPI 的 Web 界面，提供 REST API 和前端界面。
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..core.config_manager import ConfigManager
from ..core.persistence_engine import SQLitePersistenceEngine
from ..core.session_manager import SessionConfig, SessionManager
from ..rules.rule_loader import RuleLoader
from ..utils.logging_config import setup_logging

# 设置日志
setup_logging("INFO")

# 创建 FastAPI 应用
app = FastAPI(
    title="LOOM Web UI",
    description="Language-Oriented Open Mythos - Web 界面",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局变量
config_manager: Optional[ConfigManager] = None
session_manager: Optional[SessionManager] = None
rule_loader: Optional[RuleLoader] = None


# WebSocket 连接管理器
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass


manager = ConnectionManager()

# 模板目录
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"

# 确保目录存在
templates_dir.mkdir(parents=True, exist_ok=True)
static_dir.mkdir(parents=True, exist_ok=True)

# 挂载静态文件
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# 模板引擎
templates = Jinja2Templates(directory=templates_dir)


# 启动时初始化
@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global config_manager, session_manager, rule_loader

    try:
        # 初始化配置管理器
        config_manager = ConfigManager()
        config = config_manager.get_config()

        # 初始化持久化引擎
        persistence = SQLitePersistenceEngine(config.data_dir)
        await persistence.initialize()

        # 初始化会话管理器
        session_manager = SessionManager(persistence, config_manager)

        # 初始化规则加载器
        rule_loader = RuleLoader()

        print("✅ LOOM Web UI 初始化完成")
        print(f"   数据目录: {config.data_dir}")
        print(f"   API 文档: /api/docs")
        print(f"   前端界面: /")

    except Exception as e:
        print(f"❌ LOOM Web UI 初始化失败: {e}")
        import traceback

        traceback.print_exc()


# 首页
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """渲染首页"""
    return templates.TemplateResponse(
        "index.html", {"request": request, "title": "LOOM Web UI"}
    )


# API 路由
@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {"status": "healthy", "service": "loom-web-ui"}


@app.get("/api/config")
async def get_config():
    """获取配置信息"""
    if not config_manager:
        return JSONResponse(status_code=503, content={"error": "配置管理器未初始化"})

    config_snapshot = config_manager.get_config_snapshot()
    return {"config": config_snapshot}


@app.get("/api/sessions")
async def list_sessions(include_inactive: bool = False):
    """列出所有会话"""
    if not session_manager:
        return JSONResponse(status_code=503, content={"error": "会话管理器未初始化"})

    try:
        sessions = await session_manager.list_sessions(
            include_inactive=include_inactive
        )
        sessions_list = []

        for session_id, session in sessions.items():
            sessions_list.append(
                {
                    "id": session_id,
                    "name": session.name,
                    "status": session.status.value,
                    "current_turn": session.current_turn,
                    "total_turns": session.total_turns,
                    "created_at": session.created_at.isoformat(),
                    "llm_provider": session.config.llm_provider,
                }
            )

        return {"sessions": sessions_list, "count": len(sessions_list)}

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"获取会话列表失败: {str(e)}"}
        )


@app.post("/api/sessions")
async def create_session(session_data: dict):
    """创建新会话"""
    if not session_manager:
        return JSONResponse(status_code=503, content={"error": "会话管理器未初始化"})

    try:
        # 从请求数据创建会话配置
        session_config = SessionConfig(
            name=session_data.get("name", "新会话"),
            canon_path=session_data.get("canon_path", "./canon/default.md"),
            llm_provider=session_data.get("llm_provider", "openai"),
            max_turns=session_data.get("max_turns"),
            metadata=session_data.get("metadata", {}),
        )

        # 创建会话
        session = await session_manager.create_session(session_config)

        # 广播新会话创建
        await manager.broadcast(
            json.dumps(
                {
                    "type": "session_created",
                    "session_id": session.id,
                    "session_name": session.name,
                }
            )
        )

        return {
            "session": {
                "id": session.id,
                "name": session.name,
                "status": session.status.value,
                "config": {
                    "canon_path": session.config.canon_path,
                    "llm_provider": session.config.llm_provider,
                },
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"创建会话失败: {str(e)}"}
        )


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取会话详情"""
    if not session_manager:
        return JSONResponse(status_code=503, content={"error": "会话管理器未初始化"})

    try:
        session = await session_manager.load_session(session_id)
        if not session:
            return JSONResponse(
                status_code=404, content={"error": f"会话 {session_id} 不存在"}
            )

        # 获取会话统计
        stats = await session_manager.get_session_stats(session_id)

        return {"session": session.to_dict(), "stats": stats}

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"获取会话失败: {str(e)}"}
        )


@app.delete("/api/sessions/{session_id}")
async def delete_session(session_id: str, permanent: bool = False):
    """删除会话"""
    if not session_manager:
        return JSONResponse(status_code=503, content={"error": "会话管理器未初始化"})

    try:
        success = await session_manager.delete_session(session_id, permanent)

        if success:
            # 广播会话删除
            await manager.broadcast(
                json.dumps(
                    {
                        "type": "session_deleted",
                        "session_id": session_id,
                        "permanent": permanent,
                    }
                )
            )

            return {"success": True, "message": "会话已删除"}
        else:
            return JSONResponse(status_code=500, content={"error": "删除会话失败"})

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"删除会话失败: {str(e)}"}
        )


@app.get("/api/rules")
async def list_rules():
    """列出所有规则集"""
    if not rule_loader:
        return JSONResponse(status_code=503, content={"error": "规则加载器未初始化"})

    try:
        canons = rule_loader.load_all_canons()
        rules_list = []

        for name, canon in canons.items():
            rules_list.append(
                {
                    "name": name,
                    "path": str(canon.path),
                    "sections": list(canon.sections.keys()),
                    "metadata": canon.metadata,
                }
            )

        return {"rules": rules_list, "count": len(rules_list)}

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"获取规则列表失败: {str(e)}"}
        )


@app.get("/api/rules/{canon_name}")
async def get_rule(canon_name: str):
    """获取规则集详情"""
    if not rule_loader:
        return JSONResponse(status_code=503, content={"error": "规则加载器未初始化"})

    try:
        canon = rule_loader.load_canon(canon_name)
        if not canon:
            return JSONResponse(
                status_code=404, content={"error": f"规则集 {canon_name} 不存在"}
            )

        return {
            "canon": {
                "name": canon_name,
                "path": str(canon.path),
                "sections": canon.sections,
                "metadata": canon.metadata,
                "validation_errors": canon.validate(),
            }
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"获取规则集失败: {str(e)}"}
        )


@app.post("/api/turns/{session_id}")
async def process_turn(session_id: str, turn_data: dict):
    """处理回合"""
    if not session_manager:
        return JSONResponse(status_code=503, content={"error": "会话管理器未初始化"})

    try:
        # 这里需要实现实际的回合处理逻辑
        # 暂时返回模拟响应

        user_input = turn_data.get("input", "")
        intervention_type = turn_data.get("intervention_type", "player_input")

        # 模拟处理延迟
        await asyncio.sleep(1)

        # 广播回合处理
        await manager.broadcast(
            json.dumps(
                {
                    "type": "turn_processed",
                    "session_id": session_id,
                    "input": user_input,
                    "intervention_type": intervention_type,
                }
            )
        )

        return {
            "success": True,
            "response": f"已处理输入: {user_input}",
            "turn_completed": True,
            "session_id": session_id,
        }

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"error": f"处理回合失败: {str(e)}"}
        )


# WebSocket 端点
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket 连接"""
    await manager.connect(websocket)
    try:
        while True:
            # 接收客户端消息
            data = await websocket.receive_text()
            message = json.loads(data)

            # 处理不同类型的消息
            message_type = message.get("type")

            if message_type == "ping":
                await manager.send_personal_message(
                    json.dumps({"type": "pong", "timestamp": message.get("timestamp")}),
                    websocket,
                )
            elif message_type == "subscribe":
                # 客户端订阅特定会话
                session_id = message.get("session_id")
                await manager.send_personal_message(
                    json.dumps(
                        {
                            "type": "subscribed",
                            "session_id": session_id,
                            "message": f"已订阅会话 {session_id}",
                        }
                    ),
                    websocket,
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket 错误: {e}")
        manager.disconnect(websocket)


# 错误处理
@app.exception_handler(404)
async def not_found_exception_handler(request: Request, exc):
    """404 错误处理"""
    return templates.TemplateResponse(
        "404.html", {"request": request, "title": "页面未找到"}, status_code=404
    )


@app.exception_handler(500)
async def internal_exception_handler(request: Request, exc):
    """500 错误处理"""
    return templates.TemplateResponse(
        "500.html", {"request": request, "title": "服务器错误"}, status_code=500
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
