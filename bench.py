"""
Benchmark script for Day 7 - Lab 4 (HeadingChunker & Retrieval Benchmark)
Member: Vũ
"""

import re
from pathlib import Path
from src.chunking import HeadingChunker, RecursiveChunker, SentenceChunker, FixedSizeChunker
from src.embeddings import MockEmbedder
from src.models import Document
from src.store import EmbeddingStore

DATA_DIR = Path("data/ecommerce")

QUERIES = [
    {
        "id": 1,
        "query": "Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng?",
        "gold": "15 ngày kể từ khi đơn hàng được cập nhật giao hàng thành công",
        "doc_id": "shopee-chinh-sach-tra-hang-hoan-tien",
        "filter": {"audience": "both"},
    },
    {
        "id": 2,
        "query": "Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu?",
        "gold": "02 ngày lịch kể từ ngày nhận thông báo",
        "doc_id": "shopee-chinh-sach-tra-hang-hoan-tien",
        "filter": None,
    },
    {
        "id": 3,
        "query": "Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu?",
        "gold": "ví Senpay, thời gian khoảng 3–7 ngày",
        "doc_id": "sendo-chinh-sach-doi-tra-buyer",
        "filter": None,
    },
    {
        "id": 4,
        "query": "Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày?",
        "gold": "7 ngày đầu — hình thức Đổi mới / Hoàn tiền",
        "doc_id": "tiki-chinh-sach-doi-tra-buyer",
        "filter": None,
    },
    {
        "id": 5,
        "query": "Người bán trên Shopee có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không?",
        "gold": "Không — người bán không chịu chi phí khi lỗi do đơn vị vận chuyển",
        "doc_id": "shopee-chinh-sach-tra-hang-hoan-tien",
        "filter": None,
    },
]


def load_documents_from_markdown():
    documents = []
    for md_file in sorted(DATA_DIR.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        parts = content.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            fm = dict(re.findall(r"^(\w+):\s*[\"']?([^\"'\n]+)[\"']?$", fm_text, re.MULTILINE))
            doc_id = fm.get("doc_id", md_file.stem)
            title = fm.get("title", md_file.stem)
            audience = fm.get("audience", "both")
            category = fm.get("category", "policy")
            metadata = {
                "doc_id": doc_id,
                "title": title,
                "audience": audience,
                "category": category,
                "source_url": fm.get("source_url", ""),
                "document_version": fm.get("document_version", "1.0"),
            }
            documents.append(Document(id=doc_id, content=body, metadata=metadata))
    return documents


def run_benchmark(chunker_name="HeadingChunker", chunker=None, log_lines=None):
    if chunker is None:
        chunker = HeadingChunker(chunk_size=500)

    docs = load_documents_from_markdown()
    
    chunked_docs = []
    for doc in docs:
        chunks = chunker.chunk(doc.content)
        for i, chunk_text in enumerate(chunks):
            meta = dict(doc.metadata)
            meta["chunk_index"] = i
            chunked_docs.append(Document(id=f"{doc.id}_c{i+1}", content=chunk_text, metadata=meta))

    store = EmbeddingStore(embedding_fn=MockEmbedder())
    store.add_documents(chunked_docs)

    header1 = f"\n========================================================\n  BENCHMARK EVALUATION -- Chunker: {chunker_name}\n  Total Indexed Chunks: {store.get_collection_size()}\n========================================================\n"
    print(header1)
    if log_lines is not None:
        log_lines.append(header1)

    hits = 0
    for q in QUERIES:
        q_header = f"[Query {q['id']}] {q['query']}\n  Gold Answer: {q['gold']}"
        print(q_header)
        if log_lines is not None:
            log_lines.append(q_header)
        
        filter_dict = q["filter"]
        if filter_dict:
            results = store.search_with_filter(q["query"], top_k=3, metadata_filter=filter_dict)
        else:
            results = store.search(q["query"], top_k=3)

        if results:
            top_res = results[0]
            content = top_res["content"]
            score = top_res["score"]
            meta = top_res["metadata"]
            doc_id = meta.get("doc_id", top_res["id"])
            chunk_snippet = content.replace("\n", " ")[:150]
            res_str = f"  Top Match (Score: {score:.4f}): Doc '{doc_id}'\n  Content Snippet: \"{chunk_snippet}...\"\n"
            print(res_str)
            if log_lines is not None:
                log_lines.append(res_str)
            if doc_id == q["doc_id"]:
                hits += 1
        else:
            no_res = "  NO RESULTS FOUND!\n"
            print(no_res)
            if log_lines is not None:
                log_lines.append(no_res)

    summary_str = f"--------------------------------------------------------\n  Accuracy (Doc Match): {hits}/{len(QUERIES)} ({hits/len(QUERIES)*100:.1f}%)\n--------------------------------------------------------\n"
    print(summary_str)
    if log_lines is not None:
        log_lines.append(summary_str)

    return {
        "chunker_name": chunker_name,
        "total_chunks": store.get_collection_size(),
        "hits": hits,
        "total_queries": len(QUERIES),
        "accuracy": hits / len(QUERIES),
    }


if __name__ == "__main__":
    import json
    import sys
    sys.stdout.reconfigure(encoding='utf-8')

    results = []
    log_lines = []
    print("Running Benchmark for HeadingChunker (Vu's Chunker)...")
    res1 = run_benchmark("HeadingChunker (500)", HeadingChunker(chunk_size=500), log_lines)
    results.append(res1)

    print("Comparing with standard chunkers:")
    res2 = run_benchmark("RecursiveChunker (500)", RecursiveChunker(chunk_size=500), log_lines)
    results.append(res2)

    res3 = run_benchmark("SentenceChunker (3 sents)", SentenceChunker(max_sentences_per_chunk=3), log_lines)
    results.append(res3)

    output_path = Path("report/benchmark_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    
    txt_content = "\n".join(log_lines)
    txt_file = Path("ket_qua_benchmark.txt")
    txt_file.write_text(txt_content, encoding="utf-8")
    Path("report/ket_qua_benchmark.txt").write_text(txt_content, encoding="utf-8")

    print(f"--> Saved benchmark JSON to: {output_path}")
    print(f"--> Saved benchmark TXT to: {txt_file} & report/ket_qua_benchmark.txt")

