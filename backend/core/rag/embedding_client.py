"""
本地 Embedding 客户端

使用 sentence-transformers/all-MiniLM-L6-v2 模型，首次启动自动下载权重，
后续离线运行。完全本地，零 API 调用。
"""

import logging
from typing import List

import numpy as np
from sentence_transformers import SentenceTransformer

from config.settings import rag_config

logger = logging.getLogger(__name__)


class LocalEmbeddingClient:
    """
    本地 Embedding 向量化客户端

    用法:
        client = LocalEmbeddingClient()
        vec = client.embed_text("分析报表")
        vecs = client.embed_batch(["文本1", "文本2", "文本3"])
        print(client.embedding_dim)
    """

    def __init__(
        self,
        model_name: str | None = None,
        device: str = "cpu",
    ) -> None:
        """
        初始化 Embedding 模型

        Args:
            model_name: HuggingFace 模型名称，默认 all-MiniLM-L6-v2
            device: 运行设备 ('cpu' 或 'cuda')
        """
        self._model_name = model_name or rag_config.embedding_model_name
        self._device = device

        logger.info(
            "加载 Embedding 模型: %s (device=%s) ...",
            self._model_name,
            self._device,
        )
        # 首次运行会自动下载权重并缓存到 ~/.cache/huggingface/
        self._model = SentenceTransformer(
            self._model_name,
            device=self._device,
        )
        # 获取向量维度
        self._dimension: int = self._model.get_sentence_embedding_dimension()
        logger.info(
            "Embedding 模型加载完成，向量维度: %d", self._dimension
        )

    @property
    def embedding_dim(self) -> int:
        """返回 Embedding 向量的维度"""
        return self._dimension

    @property
    def model_name(self) -> str:
        """返回当前使用的模型名称"""
        return self._model_name

    def embed_text(self, text: str) -> np.ndarray:
        """
        将单段文本转为向量

        Args:
            text: 输入文本

        Returns:
            numpy array，shape = (embedding_dim,)
        """
        if not text or not text.strip():
            logger.warning("输入文本为空，返回零向量")
            return np.zeros(self._dimension, dtype=np.float32)

        vec = self._model.encode(text, normalize_embeddings=True)
        logger.debug("单文本向量化完成，长度 %d 字符 -> 维度 %d", len(text), len(vec))
        return vec.astype(np.float32)

    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        批量将文本转为向量

        Args:
            texts: 文本列表

        Returns:
            numpy array，shape = (batch_size, embedding_dim)
        """
        if not texts:
            logger.warning("输入文本列表为空，返回空数组")
            return np.empty((0, self._dimension), dtype=np.float32)

        # 过滤空文本
        valid_texts = [t for t in texts if t and t.strip()]
        if not valid_texts:
            logger.warning("所有输入文本均为空，返回空数组")
            return np.empty((0, self._dimension), dtype=np.float32)

        vecs = self._model.encode(
            valid_texts,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        logger.debug("批量向量化完成: %d 条 -> shape %s", len(valid_texts), vecs.shape)
        return vecs.astype(np.float32)

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """
        计算两个向量的余弦相似度

        Args:
            vec_a: 向量 A
            vec_b: 向量 B

        Returns:
            余弦相似度（0~1）
        """
        # 因为 normalize_embeddings=True，点积即为余弦相似度
        dot = np.dot(vec_a, vec_b)
        return float(np.clip(dot, 0.0, 1.0))
