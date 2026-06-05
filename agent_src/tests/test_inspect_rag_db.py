import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

from chromadb.errors import NotFoundError

from tools import inspect_rag_db


def test_missing_collection_is_reported_without_crashing(capsys) -> None:
    client = Mock()
    client.list_collections.return_value = [SimpleNamespace(name="ops_runbooks")]
    client.get_collection.side_effect = NotFoundError("missing")

    with (
        patch.object(inspect_rag_db.chromadb, "PersistentClient", return_value=client),
        patch.object(sys, "argv", ["inspect_rag_db.py", "--collection", "incident_memory"]),
    ):
        inspect_rag_db.main()

    output = capsys.readouterr().out
    assert "Collection 'incident_memory' does not exist." in output
    assert "ops_runbooks" in output
    assert "Start or restart ai-agent" in output
