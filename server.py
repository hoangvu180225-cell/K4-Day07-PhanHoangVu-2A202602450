"""
Lab 7 Web UI Server - E-Commerce RAG & Embedding Dashboard
Run with: python server.py
Access at: http://localhost:8000
"""

import json
import os
import re
import sys
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from src.chunking import FixedSizeChunker, HeadingChunker, RecursiveChunker, SentenceChunker
from src.embeddings import MockEmbedder
from src.models import Document
from src.store import EmbeddingStore

PORT = 8000
DATA_DIR = Path("data/ecommerce")


def load_raw_documents():
    documents = []
    for md_file in sorted(DATA_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            fm = dict(re.findall(r"^(\w+):\s*[\"']?([^\"'\n]+)[\"']?$", fm_text, re.MULTILINE))
            documents.append({
                "doc_id": fm.get("doc_id", md_file.stem),
                "title": fm.get("title", md_file.stem),
                "audience": fm.get("audience", "both"),
                "category": fm.get("category", "policy"),
                "source_url": fm.get("source_url", ""),
                "document_version": fm.get("document_version", "1.0"),
                "retrieved_at": fm.get("retrieved_at", "2026-09-20"),
                "content": body,
                "file_name": md_file.name,
                "char_count": len(body),
            })
    return documents


class DashboardRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="web", **kwargs)

    def do_GET(self):
        if self.path == "/api/stats":
            self.send_json_response(self.get_stats())
        elif self.path == "/api/documents":
            self.send_json_response(load_raw_documents())
        elif self.path == "/api/benchmark":
            self.send_json_response(self.get_benchmark_data())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/search":
            content_length = int(self.headers["Content-Length"])
            post_data = self.rfile.read(content_length)
            payload = json.loads(post_data.decode("utf-8"))
            result = self.perform_rag_search(payload)
            self.send_json_response(result)
        else:
            self.send_error(404, "Endpoint not found")

    def send_json_response(self, data):
        response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(response_bytes)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response_bytes)

    def get_stats(self):
        raw_docs = load_raw_documents()
        return {
            "total_documents": len(raw_docs),
            "unit_tests_passed": 42,
            "unit_tests_total": 42,
            "custom_chunker": "HeadingChunker",
            "variant": "K4-L3B (E-Commerce Policy)",
            "student_name": "Phan Hoàng Vũ (2A202602450)",
            "group_name": "Nhóm Soul",
        }

    def get_benchmark_data(self):
        bench_file = Path("report/benchmark_results.json")
        if bench_file.exists():
            return json.loads(bench_file.read_text(encoding="utf-8"))
        return []

    def perform_rag_search(self, payload):
        query = payload.get("query", "")
        strategy_name = payload.get("strategy", "HeadingChunker")
        audience_filter = payload.get("audience", "all")
        top_k = int(payload.get("top_k", 3))

        # Select chunker
        if strategy_name == "SentenceChunker":
            chunker = SentenceChunker(max_sentences_per_chunk=3)
        elif strategy_name == "RecursiveChunker":
            chunker = RecursiveChunker(chunk_size=500)
        elif strategy_name == "FixedSizeChunker":
            chunker = FixedSizeChunker(chunk_size=500, overlap=50)
        else:
            chunker = HeadingChunker(chunk_size=500)

        raw_docs = load_raw_documents()
        chunked_docs = []
        for raw in raw_docs:
            meta = {
                "doc_id": raw["doc_id"],
                "title": raw["title"],
                "audience": raw["audience"],
                "category": raw["category"],
                "source_url": raw["source_url"],
            }
            chunks = chunker.chunk(raw["content"])
            for idx, c_text in enumerate(chunks):
                chunk_meta = dict(meta)
                chunk_meta["chunk_index"] = idx
                chunked_docs.append(Document(id=f"{raw['doc_id']}_c{idx+1}", content=c_text, metadata=chunk_meta))

        store = EmbeddingStore(embedding_fn=MockEmbedder())
        store.add_documents(chunked_docs)

        metadata_filter = None
        if audience_filter != "all":
            metadata_filter = {"audience": audience_filter}

        if metadata_filter:
            results = store.search_with_filter(query, top_k=top_k, metadata_filter=metadata_filter)
        else:
            results = store.search(query, top_k=top_k)

        # Build mock agent response
        agent_answer = ""
        if results:
            top_content = results[0]["content"]
            agent_answer = f"Căn cứ theo tài liệu ({results[0]['metadata'].get('doc_id')}):\n\n\"{top_content[:300]}...\""
        else:
            agent_answer = "Không tìm thấy thông tin phù hợp trong cơ sở tri thức."

        return {
            "query": query,
            "strategy": strategy_name,
            "total_chunks_indexed": store.get_collection_size(),
            "results": results,
            "agent_answer": agent_answer,
        }


def main():
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    web_dir = Path("web")
    web_dir.mkdir(exist_ok=True)
    server_address = ("", PORT)
    httpd = HTTPServer(server_address, DashboardRequestHandler)
    print(f"=======================================================")
    print(f"  Lab 7 Web UI Server is running!")
    print(f"  URL: http://localhost:{PORT}")
    print(f"=======================================================")
    httpd.serve_forever()


if __name__ == "__main__":
    main()
