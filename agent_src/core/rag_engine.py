# rag_engine.py
import os
import logging
import re
from datetime import datetime
from typing import Union, Any, Dict, Optional
import chromadb
from chromadb.utils import embedding_functions
from chromadb import Where

logger = logging.getLogger(__name__)


class RAGEngine:
    def __init__(self, db_path="./vector_db"):
        self.client = chromadb.PersistentClient(path=db_path)

        # FIX #7: Khởi tạo embedding_fn bên trong class thay vì global
        # để tránh lỗi import-time khi thiếu dependency
        self._embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        self.collection = self.client.get_or_create_collection(
            name="ops_runbooks",
            embedding_function=self._embedding_fn  # type: ignore
        )
        self._ingest_initial_data()

    def _ingest_initial_data(self):
        kb_path = os.path.join(os.path.dirname(__file__), "..", "config", "knowledge_base")
        if not os.path.exists(kb_path):
            logger.warning(f"KB path not found: {kb_path}")
            return
        for filename in os.listdir(kb_path):
            if filename.endswith(".md"):
                file_path = os.path.join(kb_path, filename)
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                self.collection.upsert(
                    ids=[filename],
                    documents=[content],
                    metadatas=[{"source": filename}]
                )
        logger.info(f"✅ Đã nạp tri thức từ {kb_path}")

    def save_incident(
        self,
        alert_name: str,
        description: str,
        ai_analysis: str,
        resolution: str,
        outcome: str
    ):
        doc_id = f"incident_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{alert_name}"
        document = (
            f"# Incident: {alert_name}\n"
            f"Mô tả: {description}\n\n"
            f"## AI Phân tích: {ai_analysis}\n\n"
            f"## Hành động đã thực hiện: {resolution}\n\n"
            f"## Kết quả: {outcome}\n"
        )
        self.collection.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{
                "source": "incident_history",
                "alert_name": alert_name,
                "timestamp": datetime.now().isoformat(),
                "outcome": outcome
            }]
        )
        logger.info(f"✅ Đã lưu incident '{alert_name}' vào RAG DB (outcome={outcome})")

    def query_runbook(self, alert_description: str) -> str:
        try:
            total_count = self.collection.count()
            if total_count == 0:
                return "Kho tri thức đang trống."

            keywords = set(re.findall(r'\w+', alert_description.lower()))

            def hybrid_retrieve(where_clause: Where, n: int = 3) -> str:
                # FIX lỗi 2: results có thể None → guard trước khi subscript
                results = None
                try:
                    results = self.collection.query(
                        query_texts=[alert_description],
                        n_results=min(n, total_count),
                        where=where_clause  # FIX lỗi 1: truyền thẳng Where, không wrap thêm
                    )
                except Exception as e:
                    logger.warning(f"RAG query failed ({e}), retrying with n=1")
                    try:
                        results = self.collection.query(
                            query_texts=[alert_description],
                            n_results=1,
                            where=where_clause
                        )
                    except Exception as e2:
                        logger.error(f"RAG fallback query also failed: {e2}")
                        return "Không tìm thấy thông tin phù hợp."

                # FIX lỗi 2: kiểm tra None trước khi subscript
                if results is None:
                    return "Không tìm thấy thông tin phù hợp."
                
                docs = (results.get("documents") or [[]])[0]
                if not docs:
                    return "Không tìm thấy thông tin phù hợp."

                scored_docs = []
                for doc in docs:
                    score = sum(1 for kw in keywords if kw in doc.lower())
                    scored_docs.append((score, doc))

                scored_docs.sort(key=lambda x: x[0], reverse=True)
                return scored_docs[0][1]

            # FIX lỗi 1: Tạo Where dict đúng chuẩn ChromaDB và truyền trực tiếp
            runbook_filter: Where = {"source": {"$ne": "incident_history"}}
            history_filter: Where = {"source": {"$eq": "incident_history"}}

            runbook_text = hybrid_retrieve(runbook_filter)
            history_text = hybrid_retrieve(history_filter)

            return f"## Quy trình chuẩn:\n{runbook_text}\n\n## Incident tương tự trước đây:\n{history_text}"

        except Exception as e:
            logger.error(f"RAG Query Error: {e}")
            return "Lỗi khi truy xuất kho tri thức."


_rag_instance = None

def get_rag_instance() -> RAGEngine | None:
    global _rag_instance
    if _rag_instance is None:
        try:
            db_path = os.getenv("VECTOR_DB_PATH", "./vector_db")
            _rag_instance = RAGEngine(db_path=db_path)
            logger.info("✅ RAG Engine initialized successfully.")
        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG Engine: {e}")
            return None
    return _rag_instance