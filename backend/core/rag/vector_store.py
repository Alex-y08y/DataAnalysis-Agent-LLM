"""
ChromaDB 向量存储模块

支持文档切片、清洗、向量入库、检索、元数据过滤以及集合管理。
"""

import logging
import uuid
from datetime import datetime
from typing import Any, List

import chromadb
from chromadb.config import Settings as ChromaSettings

from config.settings import rag_config
from core.rag.embedding_client import LocalEmbeddingClient

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 辅助函数：文本清洗
# ---------------------------------------------------------------------------

def clean_text(text: str) -> str:
    """
    清洗文本：去除多余空白、空行，规范化格式

    Args:
        text: 原始文本

    Returns:
        清洗后的文本
    """
    import re
    # 去除控制字符（保留换行和制表符）
    text = re.sub(r"[\\x00-\\x08\\x0b\\x0c\\x0e-\\x1f\\x7f]", "", text)
    # 将连续的多个换行替换为两个换行
    text = re.sub(r"\\n{3,}", "\\n\\n", text)
    # 去除行首尾空白
    lines = [line.strip() for line in text.split("\\n")]
    text = "\\n".join(line for line in lines if line)
    return text.strip()


def chunk_text(
    text: str,
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> List[str]:
    """
    将文本按指定大小切分为片段

    Args:
        text: 输入文本
        chunk_size: 每段最大字符数
        chunk_overlap: 相邻段重叠字符数

    Returns:
        文本片段列表
    """
    if not text:
        return []

    cleaned = clean_text(text)
    if len(cleaned) <= chunk_size:
        return [cleaned]

    chunks: List[str] = []
    start = 0
    while start < len(cleaned):
        end = start + chunk_size
        if end >= len(cleaned):
            chunks.append(cleaned[start:])
            break
        # 尽量在换行或句号处断开
        cut = cleaned.rfind("\\n", start, end)
        if cut == -1 or cut <= start:
            cut = cleaned.rfind("。", start, end)
        if cut == -1 or cut <= start:
            cut = end
        else:
            cut += 1  # 包含分隔符
        chunks.append(cleaned[start:cut])
        start = cut - chunk_overlap
    return chunks


# ---------------------------------------------------------------------------
# 向量存储类
# ---------------------------------------------------------------------------

class VectorStore:
    """
    ChromaDB 向量存储

    用法:
        store = VectorStore()
        store.add_documents([{"text": "...", "metadata": {...}}, ...])
        results = store.search("分析报表")
        store.delete_collection()
    """

    def __init__(
        self,
        collection_name: str = "data_analysis_kb",
        embedding_client: LocalEmbeddingClient | None = None,
    ) -> None:
        """
        初始化 ChromaDB 客户端与集合

        Args:
            collection_name: 集合名称
            embedding_client: Embedding 客户端实例
        """
        self._collection_name = collection_name
        self._embedding_client = embedding_client or LocalEmbeddingClient()

        persist_dir = rag_config.chroma_db_dir
        logger.info("ChromaDB 持久化目录: %s", persist_dir)

        self._chroma_client = chromadb.PersistentClient(
            path=persist_dir,
            settings=ChromaSettings(
                anonymized_telemetry=False,
                allow_reset=True,
            ),
        )

        # 获取或创建集合（使用本地 Embedding 函数）
        self._collection = self._chroma_client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(
            "向量存储初始化完成: collection=%s, 当前文档数=%d",
            collection_name,
            self._collection.count(),
        )

    # ------------------------------------------------------------------
    # 属性
    # ------------------------------------------------------------------

    @property
    def collection_name(self) -> str:
        return self._collection_name

    @property
    def count(self) -> int:
        """返回集合中的文档数量"""
        return self._collection.count()

    # ------------------------------------------------------------------
    # 文档入库
    # ------------------------------------------------------------------

    def add_documents(
        self,
        documents: List[dict[str, Any]],
        chunk_size: int | None = None,
        chunk_overlap: int | None = None,
    ) -> int:
        """
        将文档列表添加至向量库

        每个文档格式:
            {
                "text": "...",          # 文档正文
                "metadata": {           # 元数据（可选）
                    "source": "xxx",
                    "biz_line": "xxx",    # 业务线
                    "metric_type": "xx",  # 指标类型
                    "doc_time": "2025-01-01",  # 文档时间
                    ...
                }
            }

        Args:
            documents: 文档列表
            chunk_size: 切分大小（覆盖配置）
            chunk_overlap: 重叠字符数（覆盖配置）

        Returns:
            入库的切片数量
        """
        chunk_size = chunk_size or rag_config.chunk_size
        chunk_overlap = chunk_overlap or rag_config.chunk_overlap

        all_chunks: List[str] = []
        all_metadatas: List[dict] = []
        all_ids: List[str] = []

        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            if not text:
                logger.warning("跳过空文档")
                continue

            chunks = chunk_text(text, chunk_size, chunk_overlap)
            for chunk in chunks:
                chunk_id = str(uuid.uuid4())
                chunk_meta = {
                    **metadata,
                    "chunk_index": len(all_chunks),
                    "added_at": datetime.now().isoformat(),
                }
                all_chunks.append(chunk)
                all_metadatas.append(chunk_meta)
                all_ids.append(chunk_id)

        if not all_chunks:
            logger.warning("没有有效的切片可供入库")
            return 0

        # 批量计算向量
        embeddings = self._embedding_client.embed_batch(all_chunks)

        # 入库
        self._collection.add(
            documents=all_chunks,
            embeddings=embeddings.tolist(),
            metadatas=all_metadatas,
            ids=all_ids,
        )
        logger.info("入库完成: %d 个切片", len(all_chunks))
        return len(all_chunks)

    # ------------------------------------------------------------------
    # 检索
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        top_k: int | None = None,
        similarity_threshold: float | None = None,
        filter_conditions: dict[str, Any] | None = None,
    ) -> List[dict[str, Any]]:
        """
        向量检索

        Args:
            query: 查询文本
            top_k: 返回 Top-K 条结果
            similarity_threshold: 相似度阈值，低于该值的结果会被丢弃
            filter_conditions: 元数据过滤条件，e.g. {"biz_line": "电商"}

        Returns:
            检索结果列表，每项格式:
            {
                "text": "...",
                "metadata": {...},
                "similarity": 0.92,
            }
        """
        top_k = top_k or rag_config.top_k
        threshold = (
            similarity_threshold
            if similarity_threshold is not None
            else rag_config.similarity_threshold
        )

        # 查询向量
        query_vec = self._embedding_client.embed_text(query)

        results = self._collection.query(
            query_embeddings=[query_vec.tolist()],
            n_results=top_k,
            where=filter_conditions,  # ChromaDB 的 where 过滤
        )

        # 解析结果
        hits: List[dict[str, Any]] = []
        if not results["ids"] or not results["ids"][0]:
            return hits

        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]  # cosine distance

        for idx, doc_id in enumerate(ids):
            # ChromaDB 余弦距离 -> 余弦相似度
            similarity = 1.0 - distances[idx]
            if similarity < threshold:
                logger.debug("丢弃低相似度结果: %.4f < %.2f", similarity, threshold)
                continue

            hits.append({
                "id": doc_id,
                "text": documents[idx],
                "metadata": metadatas[idx],
                "similarity": round(similarity, 4),
            })

        # 按相似度降序排列
        hits.sort(key=lambda x: x["similarity"], reverse=True)
        logger.info(
            "检索完成: query='%s', 返回 %d 条（原始 %d 条，阈值 %.2f）",
            query[:50], len(hits), len(distances), threshold,
        )
        return hits

    # ------------------------------------------------------------------
    # 集合管理
    # ------------------------------------------------------------------

    def delete_collection(self) -> None:
        """删除当前集合"""
        try:
            self._chroma_client.delete_collection(self._collection_name)
            logger.warning("集合已删除: %s", self._collection_name)
        except ValueError:
            logger.warning("集合不存在，无需删除: %s", self._collection_name)

    def reset_collection(self) -> None:
        """重置集合（清空所有数据重建）"""
        self.delete_collection()
        self._collection = self._chroma_client.get_or_create_collection(
            name=self._collection_name,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info("集合已重置: %s", self._collection_name)

    def list_collections(self) -> List[str]:
        """列出所有集合名称"""
        return self._chroma_client.list_collections()

    def get_all_documents(self, limit: int = 100) -> List[dict[str, Any]]:
        """
        获取集合中的文档（分页）

        Args:
            limit: 最大返回条数

        Returns:
            文档列表 [{id, text, metadata}, ...]
        """
        results = self._collection.get(limit=limit)
        docs = []
        for i in range(len(results["ids"])):
            docs.append({
                "id": results["ids"][i],
                "text": results["documents"][i],
                "metadata": results["metadatas"][i],
            })
        return docs
