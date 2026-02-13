"""
叙事工厂

提供创建叙事解释器和调度器的工厂函数，简化适配器使用。
"""

from typing import Optional

from ..utils.logging_config import get_logger
from .interfaces import (
    NarrativeArchivePersistence,
    NarrativeInterpreter,
    NarrativeScheduler,
)
from .narrative_adapter import NarrativeInterpreterAdapter, NarrativeSchedulerAdapter
from .persistence_engine import SQLitePersistence
from .session_manager import SessionManager as LegacySessionManager
from .turn_scheduler import TurnScheduler as LegacyTurnScheduler

logger = get_logger(__name__)


def create_narrative_interpreter(
    legacy_session_manager: Optional[LegacySessionManager] = None,
    persistence_engine=None,
    config_manager=None,
) -> NarrativeInterpreter:
    """创建叙事解释器实例"""
    if legacy_session_manager is None:
        # 创建默认的legacy session manager
        legacy_session_manager = LegacySessionManager(
            persistence_engine=persistence_engine, config_manager=config_manager
        )
        logger.info("Created default legacy session manager")

    # 创建适配器
    adapter = NarrativeInterpreterAdapter(legacy_session_manager)
    logger.info("Narrative interpreter created via adapter")

    return adapter


def create_narrative_scheduler(
    legacy_scheduler: Optional[LegacyTurnScheduler] = None,
    session_manager=None,
    persistence_engine=None,
    max_concurrent: int = 3,
) -> NarrativeScheduler:
    """创建叙事调度器实例"""
    if legacy_scheduler is None:
        # 创建默认的legacy scheduler
        legacy_scheduler = LegacyTurnScheduler(
            max_concurrent=max_concurrent,
            session_manager=session_manager,
            persistence_engine=persistence_engine,
        )
        logger.info("Created default legacy turn scheduler")

    # 创建适配器
    adapter = NarrativeSchedulerAdapter(legacy_scheduler)
    logger.info("Narrative scheduler created via adapter")

    return adapter


def create_narrative_persistence(
    db_path: str = "loom.db", pool_size: int = 5
) -> SQLitePersistence:
    """创建叙事持久化引擎（扩展的SQLitePersistence）"""
    persistence = SQLitePersistence(db_path=db_path, pool_size=pool_size)

    # 初始化数据库（包括叙事档案表）
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # 如果事件循环正在运行，创建任务
            asyncio.create_task(persistence.initialize())
        else:
            # 否则直接运行
            loop.run_until_complete(persistence.initialize())
    except:
        # 如果无法初始化，记录警告
        logger.warning("Could not initialize persistence engine synchronously")

    logger.info(f"Narrative persistence engine created with db={db_path}")
    return persistence


class NarrativeComponentFactory:
    """叙事组件工厂（一站式创建所有叙事组件）"""

    def __init__(self, config_manager=None):
        self.config_manager = config_manager
        self._components = {}
        logger.info("NarrativeComponentFactory initialized")

    async def get_narrative_interpreter(self) -> NarrativeInterpreter:
        """获取或创建叙事解释器"""
        if "interpreter" not in self._components:
            # 创建持久化引擎
            persistence = await self.get_persistence_engine()

            # 创建legacy session manager
            from .session_manager import SessionManager as LegacySessionManager

            legacy_manager = LegacySessionManager(
                persistence_engine=persistence, config_manager=self.config_manager
            )

            # 创建适配器
            self._components["interpreter"] = NarrativeInterpreterAdapter(
                legacy_manager
            )
            logger.info("Narrative interpreter created")

        return self._components["interpreter"]

    async def get_narrative_scheduler(self) -> NarrativeScheduler:
        """获取或创建叙事调度器"""
        if "scheduler" not in self._components:
            # 获取解释器（用于会话管理）
            interpreter = await self.get_narrative_interpreter()

            # 创建legacy scheduler
            from .turn_scheduler import TurnScheduler as LegacyTurnScheduler

            legacy_scheduler = LegacyTurnScheduler(
                max_concurrent=3,
                session_manager=(
                    interpreter.legacy_manager
                    if hasattr(interpreter, "legacy_manager")
                    else None
                ),
                persistence_engine=await self.get_persistence_engine(),
            )

            # 创建适配器
            self._components["scheduler"] = NarrativeSchedulerAdapter(legacy_scheduler)
            logger.info("Narrative scheduler created")

        return self._components["scheduler"]

    async def get_persistence_engine(self) -> SQLitePersistence:
        """获取或创建持久化引擎"""
        if "persistence" not in self._components:
            # 从配置获取数据库路径
            db_path = "loom.db"
            if self.config_manager:
                config = self.config_manager.get_config()
                db_path = f"{config.data_dir}/loom.db"

            self._components["persistence"] = create_narrative_persistence(
                db_path=db_path
            )
            await self._components["persistence"].initialize()
            logger.info(f"Persistence engine created with db={db_path}")

        return self._components["persistence"]

    async def get_all_components(self) -> dict:
        """获取所有叙事组件"""
        return {
            "interpreter": await self.get_narrative_interpreter(),
            "scheduler": await self.get_narrative_scheduler(),
            "persistence": await self.get_persistence_engine(),
        }

    async def cleanup(self):
        """清理所有组件"""
        if "persistence" in self._components:
            await self._components["persistence"].close()
            logger.info("Persistence engine closed")

        self._components.clear()
        logger.info("All narrative components cleaned up")


# 向后兼容的快捷函数
async def create_narrative_system(config_manager=None) -> dict:
    """创建完整的叙事系统（向后兼容的快捷方式）"""
    factory = NarrativeComponentFactory(config_manager)
    components = await factory.get_all_components()

    return {
        "interpreter": components["interpreter"],
        "scheduler": components["scheduler"],
        "persistence": components["persistence"],
        "factory": factory,
    }
