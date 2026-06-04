from unittest.mock import Mock

from core.rag_engine import RAGEngine, _chunk_markdown


def test_chunk_markdown_splits_by_heading_and_size() -> None:
    content = "# First\n\n" + ("a" * 80) + "\n\n## Second\n\n" + ("b" * 80)

    chunks = _chunk_markdown(content, max_chars=60)

    assert len(chunks) >= 4
    assert chunks[0][0] == "First"
    assert any(heading == "Second" for heading, _ in chunks)
    assert all(len(document) <= 60 for _, document in chunks)


def test_save_admin_solution_writes_to_incident_memory() -> None:
    engine = RAGEngine.__new__(RAGEngine)
    engine.incident_memory = Mock()

    engine.save_admin_solution(
        incident_id="abc12345",
        alert_name="WebEndpointDown",
        incident_details="frontend is down",
        admin_feedback="check logs first",
        reviewed_solution="check logs, then restart",
        review_status="revised",
    )

    kwargs = engine.incident_memory.upsert.call_args.kwargs
    assert kwargs["metadatas"][0]["source"] == "admin_feedback"
    assert kwargs["metadatas"][0]["document_type"] == "admin_feedback"
    assert "check logs, then restart" in kwargs["documents"][0]


def test_query_knowledge_keeps_standard_and_dynamic_sources_separate() -> None:
    engine = RAGEngine.__new__(RAGEngine)
    engine.standard_runbooks = Mock()
    engine.standard_runbooks.count.return_value = 1
    engine.standard_runbooks.query.return_value = {
        "documents": [["standard procedure"]],
        "metadatas": [[{"source_file": "web_endpoint_down.md"}]],
    }
    engine.incident_memory = Mock()
    engine.incident_memory.count.return_value = 1
    engine.incident_memory.query.return_value = {
        "documents": [["admin-reviewed solution"]],
        "metadatas": [[{"source": "admin_feedback"}]],
    }

    result = engine.query_knowledge("frontend web endpoint down")

    assert "Quy trình chuẩn từ runbook" in result
    assert "[Nguồn: web_endpoint_down.md]" in result
    assert "Kinh nghiệm từ incident và feedback trước đây" in result
    assert "[Nguồn: admin_feedback]" in result
