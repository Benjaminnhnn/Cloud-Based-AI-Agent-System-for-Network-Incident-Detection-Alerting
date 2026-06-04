import argparse
import json
import os
from typing import Any

import chromadb


def _collection_name(collection: Any) -> str:
    return str(getattr(collection, "name", collection))


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect ChromaDB collections used by the AIOps RAG engine.")
    parser.add_argument("--path", default=os.getenv("VECTOR_DB_PATH", "./vector_db"))
    parser.add_argument("--collection", help="Collection name to inspect.")
    parser.add_argument("--source", help="Filter documents by metadata source.")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    client = chromadb.PersistentClient(path=args.path)
    collections = client.list_collections()

    if not args.collection:
        print(f"ChromaDB path: {args.path}")
        for collection in collections:
            name = _collection_name(collection)
            count = client.get_collection(name=name).count()
            print(f"- {name}: {count} documents")
        return

    collection = client.get_collection(name=args.collection)
    where = {"source": args.source} if args.source else None
    result = collection.get(where=where, limit=args.limit, include=["documents", "metadatas"])
    ids = result.get("ids") or []
    documents = result.get("documents") or []
    metadatas = result.get("metadatas") or []

    print(f"ChromaDB path: {args.path}")
    print(f"Collection: {args.collection}")
    print(f"Showing: {len(ids)} documents")
    for doc_id, document, metadata in zip(ids, documents, metadatas):
        preview = " ".join(str(document).split())
        if len(preview) > 500:
            preview = preview[:497] + "..."
        print("\n" + "=" * 80)
        print(f"ID: {doc_id}")
        print("Metadata:")
        print(json.dumps(metadata or {}, ensure_ascii=False, indent=2))
        print("Document:")
        print(preview)


if __name__ == "__main__":
    main()
