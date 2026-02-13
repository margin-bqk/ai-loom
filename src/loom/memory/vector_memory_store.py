"""
向量记忆存储 (VectorMemoryStore)

增强版向量存储集成，支持ChromaDB/Qdrant向量数据库，提供完整的CRUD操作、
相似性搜索、批量操作和高级查询功能。

设计目标：
1. 支持多种向量数据库后端（ChromaDB优先，Qdrant备选）
2. 提供语义相似性检索
3. 支持元数据过滤和复杂查询
4. 集成嵌入模型管理
5. 提供批量操作和性能优化
"""

import asyncio
import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from ..utils.logging_config import get_logger
from .interfaces import RetrievalError, StorageError
from .world_memory import MemoryEntity, MemoryEntityType, MemoryRelation

logger = get_logger(__name__)


class VectorStoreBackend(Enum):
    """向量存储后端类型"""

    CHROMADB = "chromadb"
    QDRANT = "qdrant"
    FAISS = "faiss"
    MEMORY = "memory"  # 内存存储，用于测试


@dataclass
class VectorStoreConfig:
    """向量存储配置"""

    backend: VectorStoreBackend = VectorStoreBackend.CHROMADB
    enabled: bool = True
    collection_name: str = "loom_memories"
    persist_directory: str = "./chroma_db"

    # 嵌入模型配置
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_provider: str = "local"  # local, openai, huggingface
    embedding_dimension: int = 384

    # OpenAI配置
    openai_api_key: Optional[str] = None
    openai_model: str = "text-embedding-ada-002"

    # Qdrant配置
    qdrant_url: Optional[str] = None
    qdrant_api_key: Optional[str] = None

    # 性能配置
    batch_size: int = 100
    cache_embeddings: bool = True
    similarity_threshold: float = 0.7

    # 高级功能
    enable_metadata_indexing: bool = True
    enable_hybrid_search: bool = False  # 混合搜索（向量+关键词）

    def __post_init__(self):
        """后初始化处理，将字符串转换为枚举值"""
        # 如果backend是字符串，转换为VectorStoreBackend枚举
        if isinstance(self.backend, str):
            try:
                self.backend = VectorStoreBackend(self.backend.lower())
            except ValueError:
                # 如果无法转换，使用默认值
                self.backend = VectorStoreBackend.CHROMADB
                logger.warning(
                    f"Unsupported backend string: {self.backend}, using default: {self.backend}"
                )


@dataclass
class VectorSearchResult:
    """向量搜索结果"""

    entity_id: str
    similarity_score: float
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None
    distance: Optional[float] = None


@dataclass
class VectorSearchQuery:
    """向量搜索查询"""

    query_text: Optional[str] = None
    query_embedding: Optional[List[float]] = None
    filters: Optional[Dict[str, Any]] = None
    limit: int = 10
    offset: int = 0
    min_similarity: float = 0.5
    include_embeddings: bool = False
    include_metadata: bool = True


class VectorMemoryStore:
    """向量记忆存储

    提供完整的向量存储功能，包括：
    1. 实体向量化存储
    2. 语义相似性搜索
    3. 元数据过滤查询
    4. 批量操作
    5. 向量数据库管理
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化向量记忆存储

        Args:
            config: 配置字典，支持VectorStoreConfig的所有字段
        """
        self.config = VectorStoreConfig(**config) if config else VectorStoreConfig()
        self.enabled = self.config.enabled

        # 嵌入模型
        self.embedding_model = None
        self.embedding_cache: Dict[str, List[float]] = {}

        # 向量数据库客户端
        self.client = None
        self.collection = None

        # 初始化
        if self.enabled:
            self._initialize()
        else:
            logger.info("VectorMemoryStore disabled")

    def _initialize(self):
        """初始化向量存储后端"""
        try:
            if self.config.backend == VectorStoreBackend.CHROMADB:
                self._initialize_chromadb()
            elif self.config.backend == VectorStoreBackend.QDRANT:
                self._initialize_qdrant()
            elif self.config.backend == VectorStoreBackend.FAISS:
                self._initialize_faiss()
            elif self.config.backend == VectorStoreBackend.MEMORY:
                self._initialize_memory()
            else:
                raise ValueError(
                    f"Unsupported vector store backend: {self.config.backend}"
                )

            logger.info(
                f"VectorMemoryStore initialized with backend: {self.config.backend.value}"
            )

        except ImportError as e:
            logger.error(
                f"Failed to import required package for {self.config.backend}: {e}"
            )
            self.enabled = False
        except Exception as e:
            logger.error(f"Failed to initialize VectorMemoryStore: {e}")
            self.enabled = False

    def _initialize_chromadb(self):
        """初始化ChromaDB"""
        import chromadb
        from chromadb.config import Settings

        # 创建客户端
        self.client = chromadb.Client(
            Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.config.persist_directory,
            )
        )

        # 获取或创建集合
        try:
            self.collection = self.client.get_collection(self.config.collection_name)
            logger.info(
                f"Loaded existing ChromaDB collection: {self.config.collection_name}"
            )
        except:
            self.collection = self.client.create_collection(
                name=self.config.collection_name,
                metadata={"description": "LOOM memory embeddings"},
            )
            logger.info(
                f"Created new ChromaDB collection: {self.config.collection_name}"
            )

    def _initialize_qdrant(self):
        """初始化Qdrant"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams

            # 创建客户端
            if self.config.qdrant_url:
                self.client = QdrantClient(
                    url=self.config.qdrant_url, api_key=self.config.qdrant_api_key
                )
            else:
                self.client = QdrantClient(":memory:")

            # 检查集合是否存在
            collections = self.client.get_collections().collections
            collection_names = [c.name for c in collections]

            if self.config.collection_name not in collection_names:
                # 创建新集合
                self.client.create_collection(
                    collection_name=self.config.collection_name,
                    vectors_config=VectorParams(
                        size=self.config.embedding_dimension, distance=Distance.COSINE
                    ),
                )
                logger.info(
                    f"Created new Qdrant collection: {self.config.collection_name}"
                )
            else:
                logger.info(
                    f"Loaded existing Qdrant collection: {self.config.collection_name}"
                )

        except ImportError:
            raise ImportError(
                "qdrant-client not installed. Install with: pip install qdrant-client"
            )

    def _initialize_faiss(self):
        """初始化FAISS"""
        try:
            import faiss

            # FAISS初始化逻辑
            self.index = faiss.IndexFlatL2(self.config.embedding_dimension)
            self.id_to_index = {}
            self.index_to_id = {}
            logger.info("Initialized FAISS index")
        except ImportError:
            raise ImportError(
                "faiss not installed. Install with: pip install faiss-cpu"
            )

    def _initialize_memory(self):
        """初始化内存存储（用于测试）"""
        self.memory_store = {}
        self.embeddings = {}
        # 对于内存后端，使用虚拟嵌入模型
        self.embedding_model = "dummy"
        logger.info("Initialized in-memory vector store")

    def _get_embedding_model(self):
        """获取嵌入模型（延迟加载）"""
        # 对于内存后端，使用虚拟嵌入
        if self.config.backend == VectorStoreBackend.MEMORY:
            return None

        if self.embedding_model is not None:
            return self.embedding_model

        if self.config.embedding_provider == "openai":
            self.embedding_model = self._create_openai_embedder()
        elif self.config.embedding_provider == "huggingface":
            self.embedding_model = self._create_huggingface_embedder()
        else:  # local
            self.embedding_model = self._create_local_embedder()

        return self.embedding_model

    def _create_local_embedder(self):
        """创建本地嵌入模型"""
        try:
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self.config.embedding_model)
            logger.info(f"Loaded local embedding model: {self.config.embedding_model}")
            return model
        except ImportError:
            logger.warning(
                "sentence-transformers not installed, using dummy embeddings"
            )
            return None

    def _create_openai_embedder(self):
        """创建OpenAI嵌入器"""
        try:
            import openai

            if not self.config.openai_api_key:
                logger.error("OpenAI API key not configured")
                return None

            openai.api_key = self.config.openai_api_key

            def embedder(text):
                response = openai.Embedding.create(
                    model=self.config.openai_model, input=text
                )
                return response["data"][0]["embedding"]

            logger.info(
                f"Configured OpenAI embedding model: {self.config.openai_model}"
            )
            return embedder

        except ImportError:
            logger.warning(
                "openai package not installed, falling back to local embeddings"
            )
            return self._create_local_embedder()

    def _create_huggingface_embedder(self):
        """创建HuggingFace嵌入器"""
        try:
            import torch
            import torch.nn.functional as F
            from transformers import AutoModel, AutoTokenizer

            tokenizer = AutoTokenizer.from_pretrained(self.config.embedding_model)
            model = AutoModel.from_pretrained(self.config.embedding_model)

            def embedder(text):
                inputs = tokenizer(
                    text,
                    return_tensors="pt",
                    padding=True,
                    truncation=True,
                    max_length=512,
                )
                with torch.no_grad():
                    outputs = model(**inputs)
                embeddings = outputs.last_hidden_state.mean(dim=1).squeeze()
                embeddings = F.normalize(embeddings, p=2, dim=0)
                return embeddings.tolist()

            logger.info(
                f"Loaded HuggingFace embedding model: {self.config.embedding_model}"
            )
            return embedder

        except ImportError:
            logger.warning(
                "transformers or torch not installed, falling back to local embeddings"
            )
            return self._create_local_embedder()

    async def get_embedding(self, text: str) -> List[float]:
        """获取文本嵌入向量

        Args:
            text: 输入文本

        Returns:
            嵌入向量列表

        Raises:
            RetrievalError: 嵌入生成失败
        """
        if not self.enabled:
            raise RetrievalError("VectorMemoryStore is disabled")

        # 检查缓存
        if self.config.cache_embeddings:
            cache_key = hashlib.md5(text.encode()).hexdigest()
            if cache_key in self.embedding_cache:
                return self.embedding_cache[cache_key]

        try:
            model = self._get_embedding_model()

            if model is None:
                # 返回虚拟嵌入
                embedding = [0.0] * self.config.embedding_dimension
            elif callable(model):
                # 函数型嵌入器（如OpenAI）
                embedding = model(text)
            else:
                # 模型对象（如sentence-transformers）
                embedding = model.encode(text).tolist()

            # 缓存结果
            if self.config.cache_embeddings:
                cache_key = hashlib.md5(text.encode()).hexdigest()
                self.embedding_cache[cache_key] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise RetrievalError(f"Embedding generation failed: {e}")

    def _summarize_content(self, content: Any) -> str:
        """摘要内容"""
        import json

        if isinstance(content, str):
            if len(content) > 100:
                return content[:100] + "..."
            return content
        elif isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False)[:100] + "..."
        else:
            return str(content)[:100] + "..."

    def _entity_to_text(self, entity: MemoryEntity) -> str:
        """将记忆实体转换为文本表示

        Args:
            entity: 记忆实体

        Returns:
            文本表示
        """
        text_parts = []

        # 添加类型信息
        text_parts.append(f"类型: {entity.type.value}")

        # 添加内容
        if isinstance(entity.content, dict):
            for key, value in entity.content.items():
                if isinstance(value, str):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, (int, float, bool)):
                    text_parts.append(f"{key}: {value}")
                elif isinstance(value, list):
                    text_parts.append(f"{key}: {' '.join(str(v) for v in value[:3])}")
                elif isinstance(value, dict):
                    text_parts.append(
                        f"{key}: {json.dumps(value, ensure_ascii=False)[:100]}"
                    )
        else:
            text_parts.append(str(entity.content))

        # 添加元数据
        if entity.metadata:
            for key, value in entity.metadata.items():
                if isinstance(value, str):
                    text_parts.append(f"元数据_{key}: {value}")

        return " ".join(text_parts)

    async def store_entity_with_embedding(self, entity: MemoryEntity) -> bool:
        """存储实体及其向量嵌入

        Args:
            entity: 记忆实体

        Returns:
            是否成功存储

        Raises:
            StorageError: 存储失败
        """
        if not self.enabled:
            raise StorageError("VectorMemoryStore is disabled")

        try:
            # 生成文本表示
            text_representation = self._entity_to_text(entity)

            # 生成嵌入向量
            embedding = await self.get_embedding(text_representation)

            # 准备元数据
            metadata = {
                "session_id": entity.session_id,
                "type": entity.type.value,
                "created_at": entity.created_at.isoformat(),
                "updated_at": entity.updated_at.isoformat(),
                "version": entity.version,
                "content_summary": self._summarize_content(entity.content),
            }

            # 添加自定义元数据
            if entity.metadata:
                for key, value in entity.metadata.items():
                    if isinstance(value, (str, int, float, bool)):
                        metadata[f"meta_{key}"] = str(value)

            # 存储到向量数据库
            if self.config.backend == VectorStoreBackend.CHROMADB:
                self.collection.add(
                    embeddings=[embedding],
                    documents=[text_representation],
                    metadatas=[metadata],
                    ids=[entity.id],
                )

            elif self.config.backend == VectorStoreBackend.QDRANT:
                from qdrant_client.models import PointStruct

                point = PointStruct(id=entity.id, vector=embedding, payload=metadata)
                self.client.upsert(
                    collection_name=self.config.collection_name, points=[point]
                )

            elif self.config.backend == VectorStoreBackend.FAISS:
                import numpy as np

                embedding_array = np.array([embedding], dtype=np.float32)
                self.index.add(embedding_array)
                idx = self.index.ntotal - 1
                self.id_to_index[entity.id] = idx
                self.index_to_id[idx] = entity.id

            elif self.config.backend == VectorStoreBackend.MEMORY:
                self.memory_store[entity.id] = {
                    "embedding": embedding,
                    "metadata": metadata,
                    "text": text_representation,
                }

            logger.debug(f"Stored entity {entity.id} in vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to store entity {entity.id} in vector store: {e}")
            raise StorageError(f"Failed to store entity: {e}")

    async def store_entities_batch(
        self, entities: List[MemoryEntity]
    ) -> Dict[str, bool]:
        """批量存储实体

        Args:
            entities: 记忆实体列表

        Returns:
            存储结果字典 {entity_id: success}
        """
        if not self.enabled:
            return {entity.id: False for entity in entities}

        results = {}

        # 分批处理
        for i in range(0, len(entities), self.config.batch_size):
            batch = entities[i : i + self.config.batch_size]

            try:
                # 准备批量数据
                embeddings = []
                texts = []
                metadatas = []
                ids = []

                for entity in batch:
                    text = self._entity_to_text(entity)
                    embedding = await self.get_embedding(text)

                    metadata = {
                        "session_id": entity.session_id,
                        "type": entity.type.value,
                        "created_at": entity.created_at.isoformat(),
                        "updated_at": entity.updated_at.isoformat(),
                    }

                    embeddings.append(embedding)
                    texts.append(text)
                    metadatas.append(metadata)
                    ids.append(entity.id)

                # 批量存储
                if self.config.backend == VectorStoreBackend.CHROMADB:
                    self.collection.add(
                        embeddings=embeddings,
                        documents=texts,
                        metadatas=metadatas,
                        ids=ids,
                    )

                # 标记成功
                for entity in batch:
                    results[entity.id] = True

            except Exception as e:
                logger.error(f"Failed to store batch {i//self.config.batch_size}: {e}")
                for entity in batch:
                    results[entity.id] = False

        logger.info(f"Batch stored {sum(results.values())}/{len(entities)} entities")
        return results

    async def semantic_search(
        self, query: str, filters: Optional[Dict[str, Any]] = None, limit: int = 10
    ) -> List[Tuple[str, float]]:
        """语义相似性搜索

        Args:
            query: 查询文本
            filters: 元数据过滤条件
            limit: 返回结果数量限制

        Returns:
            搜索结果列表 [(entity_id, similarity_score), ...]

        Raises:
            RetrievalError: 搜索失败
        """
        if not self.enabled:
            raise RetrievalError("VectorMemoryStore is disabled")

        try:
            # 获取查询嵌入
            query_embedding = await self.get_embedding(query)

            # 根据后端类型执行搜索
            if self.config.backend == VectorStoreBackend.CHROMADB:
                if not self.collection:
                    return []

                # ChromaDB搜索
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=limit,
                    where=filters,
                    include=["metadatas", "distances"],
                )

                if results and results["ids"]:
                    entity_ids = results["ids"][0]
                    distances = results["distances"][0]
                    # 将距离转换为相似度分数（距离越小，相似度越高）
                    similarities = [(1.0 / (1.0 + d)) for d in distances]
                    return list(zip(entity_ids, similarities))
                return []

            elif self.config.backend == VectorStoreBackend.MEMORY:
                # 内存后端：简单文本匹配
                results = []
                for entity_id, entity_data in self.memory_store.items():
                    # 简单文本匹配（实际实现应使用嵌入相似度）
                    text = entity_data.get("text", "")
                    if query.lower() in text.lower():
                        # 简单相似度分数
                        similarity = 0.8
                        results.append((entity_id, similarity))

                # 按相似度排序
                results.sort(key=lambda x: x[1], reverse=True)
                return results[:limit]

            else:
                # 其他后端
                logger.warning(
                    f"Search not implemented for backend: {self.config.backend}"
                )
                return []

        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            raise RetrievalError(f"Semantic search failed: {e}")

    async def delete_entity(self, entity_id: str) -> bool:
        """删除实体

        Args:
            entity_id: 实体ID

        Returns:
            是否成功删除

        Raises:
            StorageError: 删除失败
        """
        if not self.enabled:
            raise StorageError("VectorMemoryStore is disabled")

        try:
            if self.config.backend == VectorStoreBackend.CHROMADB:
                if self.collection:
                    self.collection.delete(ids=[entity_id])

            elif self.config.backend == VectorStoreBackend.QDRANT:
                if self.client:
                    self.client.delete(
                        collection_name=self.config.collection_name,
                        points_selector=entity_id,
                    )

            elif self.config.backend == VectorStoreBackend.FAISS:
                if entity_id in self.id_to_index:
                    idx = self.id_to_index[entity_id]
                    # FAISS不支持删除，标记为无效
                    del self.id_to_index[entity_id]
                    del self.index_to_id[idx]

            elif self.config.backend == VectorStoreBackend.MEMORY:
                if entity_id in self.memory_store:
                    del self.memory_store[entity_id]
                if entity_id in self.embeddings:
                    del self.embeddings[entity_id]

            logger.debug(f"Deleted entity {entity_id} from vector store")
            return True

        except Exception as e:
            logger.error(f"Failed to delete entity {entity_id}: {e}")
            raise StorageError(f"Failed to delete entity: {e}")
