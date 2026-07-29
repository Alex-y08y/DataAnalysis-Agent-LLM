import os
import re
from typing import List, Dict, Any, Optional
from tools.base_tool import BaseTool


class DocParseTool(BaseTool):
    """文档解析工具：解析 PDF/Excel/TXT/Markdown 文档，提取文本内容并切片"""

    def __init__(self):
        super().__init__(
            name="doc_parser",
            description="解析 PDF/Excel/TXT/Markdown 文档并切片"
        )
        self.chunk_size = 512
        self.chunk_overlap = 64

    def validate(self, **kwargs) -> bool:
        return "file_path" in kwargs

    def execute(self, file_path: str, chunk_size: int = 512,
                chunk_overlap: int = 64) -> Dict[str, Any]:
        """解析文档文件并返回文本切片

        Args:
            file_path: 文件路径
            chunk_size: 切片大小（字符数）
            chunk_overlap: 切片重叠大小

        Returns:
            包含 source, content, chunks, chunk_count 的字典
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        if not os.path.exists(file_path):
            return {"error": f"文件不存在: {file_path}", "chunks": [], "chunk_count": 0}

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            content = self._parse_pdf(file_path)
        elif ext in [".xlsx", ".xls"]:
            content = self._parse_excel(file_path)
        elif ext == ".txt":
            content = self._parse_txt(file_path)
        elif ext == ".md":
            content = self._parse_markdown(file_path)
        elif ext == ".csv":
            content = self._parse_csv(file_path)
        else:
            return {"error": f"不支持的文件类型: {ext}", "chunks": [], "chunk_count": 0}

        content = self._clean_text(content)
        chunks = self._chunk_text(content)

        return {
            "source": file_path,
            "content": content,
            "chunks": chunks,
            "chunk_count": len(chunks)
        }

    def _parse_pdf(self, file_path: str) -> str:
        """解析 PDF 文件"""
        try:
            from PyPDF2 import PdfReader
            reader = PdfReader(file_path)
            text = []
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text.append(page_text)
            return "\n".join(text)
        except ImportError:
            return f"[PyPDF2 not installed]"
        except Exception as e:
            return f"[PDF parse error: {str(e)}]"

    def _parse_excel(self, file_path: str) -> str:
        """解析 Excel 文件"""
        try:
            import pandas as pd
            dfs = pd.read_excel(file_path, sheet_name=None)
            text_parts = []
            for sheet_name, df in dfs.items():
                text_parts.append(f"=== Sheet: {sheet_name} ===")
                text_parts.append(df.to_string(index=False))
            return "\n".join(text_parts)
        except ImportError:
            return f"[pandas/openpyxl not installed]"
        except Exception as e:
            return f"[Excel parse error: {str(e)}]"

    def _parse_txt(self, file_path: str) -> str:
        """解析 TXT 文件"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="gbk") as f:
                return f.read()

    def _parse_markdown(self, file_path: str) -> str:
        return self._parse_txt(file_path)

    def _parse_csv(self, file_path: str) -> str:
        try:
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_string(index=False)
        except Exception as e:
            return f"[CSV parse error: {str(e)}]"

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)
        return text.strip()

    def _chunk_text(self, text: str) -> List[str]:
        if not text:
            return []
        chunks = []
        start = 0
        text_len = len(text)
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            if end < text_len:
                for sep in ["。", "！", "？", "\n", ". ", "! ", "? "]:
                    idx = text.rfind(sep, start, end)
                    if idx > start + self.chunk_size // 2:
                        end = idx + len(sep)
                        break
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            start = end - self.chunk_overlap
        return chunks

    def get_parameters(self) -> Dict:
        return {
            "file_path": {"type": "string", "description": "文件路径", "required": True},
            "chunk_size": {"type": "integer", "description": "切片大小", "required": False},
            "chunk_overlap": {"type": "integer", "description": "重叠大小", "required": False}
        }
