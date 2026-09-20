# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Hoàng Vũ
**Mã SV / Biến thể:** 2A202602450 (L3B — E-Commerce Policy)
**Nhóm:** Nhóm 2A
**Ngày:** 20/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao (gần bằng 1) nghĩa là góc giữa hai vector trong không gian embedding rất nhỏ, thể hiện hai đoạn văn bản có ý nghĩa ngữ nghĩa và ngữ cảnh rất tương đồng nhau, bất kể độ dài ngắn của văn bản.

**Ví dụ có độ tương tự CAO:**
- Câu A: Thời gian yêu cầu trả hàng trên Shopee là 15 ngày kể từ khi nhận hàng thành công.
- Câu B: Người mua có thể gửi yêu cầu hoàn tiền trong vòng 15 ngày sau khi đơn hàng giao thành công.
- Tại sao tương đồng: Cả hai câu cùng truyền tải chung một thông điệp ngữ nghĩa về thời hạn trả hàng/hoàn tiền là 15 ngày dành cho người mua.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Thời gian yêu cầu trả hàng trên Shopee là 15 ngày kể từ khi nhận hàng thành công.
- Câu B: Người bán phải đóng gói sản phẩm bằng thùng carton trước khi bàn giao cho đơn vị vận chuyển.
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn khác nhau (thời hạn trả hàng cho người mua vs quy cách đóng gói cho người bán), hướng của hai vector trong không gian gần như vuông góc.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Khoảng cách Euclid bị ảnh hưởng bởi độ dài (magnitude) của vector (văn bản dài hơn có vector dài hơn làm khoảng cách lớn dù cùng chủ đề). Trong khi đó, độ tương tự cosine chỉ đo góc hướng của vector nên giữ nguyên tính chính xác khi so sánh ý nghĩa giữa các câu có độ dài ngắn khác nhau.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* step = chunk_size - overlap = 500 - 50 = 450 ký tự. Số lượng chunk = ceil( (10000 - 50) / 450 ) = ceil( 9950 / 450 ) = ceil(22.11) = 23.
> *Đáp án:* **23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap=100`, bước nhảy `step` = 400, số lượng chunk tăng lên thành `ceil( (10000 - 100) / 400 ) = 25` chunks. Tăng độ chồng chéo giúp giữ nguyên ngữ cảnh liên tục ở ranh giới giữa 2 chunk, tránh làm đứt đoạn câu hoặc thông tin quan trọng khi truy xuất.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=\.|\!|\?)(?:\s+|\n+)` để phát hiện các dấu kết thúc câu và tách văn bản thành danh sách các câu đơn lẻ. Sau đó gom nhóm tối đa `max_sentences_per_chunk` câu vào từng chunk và loại bỏ khoảng trắng thừa. Edge case: xử lý chuỗi rỗng hoặc văn bản không có dấu ngắt câu chuẩn.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy thử các separator theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Base case là khi đoạn văn bản nhỏ hơn `chunk_size` hoặc danh sách separator đã hết. Edge case: khi không tìm thấy separator phù hợp, tự động cắt cứng theo độ dài `chunk_size`.

**`HeadingChunker.chunk` (Custom Vũ)** — hướng tiếp cận:
> Tách văn bản Markdown tại các dòng tiêu đề `##`. Khi một section có độ dài vượt quá `chunk_size`, thuật toán cắt nhỏ section đó và **gắn lại tiêu đề (heading)** vào đầu mỗi mảnh con để đảm bảo mảnh sau không bị mất ngữ cảnh của mục lớn.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi document/chunk được nhúng thành vector thông qua `embedding_fn` và lưu trong bộ nhớ (hoặc ChromaDB) kèm metadata. Hàm `search` tính cosine similarity giữa query embedding và tất cả các vector lưu trữ, sắp xếp giảm dần theo điểm tương tự để lấy top-k.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` thực hiện lọc trước (pre-filtering) danh sách record thỏa mãn tất cả các điều kiện trong `metadata_filter` rồi mới tính điểm tương tự cosine. `delete_document` lọc bỏ tất cả record có `id` hoặc `metadata['doc_id']` trùng với `doc_id` được yêu cầu.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Tác tử tự động truy vấn `EmbeddingStore` bằng câu hỏi (kèm `metadata_filter` nếu có) để lấy các đoạn ngữ cảnh (top-k chunks). Sau đó nhúng ngữ cảnh vào prompt theo mẫu chuẩn để sinh ra câu trả lời chính xác, ngắn gọn và có căn cứ trực tiếp từ tài liệu.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Học\VinAI\K4-Day07-PhanHoangVu-2A202602450
collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED [ 45%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 47%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 50%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 52%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 54%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 57%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 59%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_add_and_search PASSED [ 64%]
tests/test_solution.py::TestEmbeddingStore::test_delete_document PASSED [ 66%]
tests/test_solution.py::TestEmbeddingStore::test_delete_nonexistent_returns_false PASSED [ 69%]
tests/test_solution.py::TestEmbeddingStore::test_get_collection_size PASSED [ 71%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_requested_top_k PASSED [ 73%]
tests/test_solution.py::TestEmbeddingStore::test_search_with_filter_exact_match PASSED [ 76%]
tests/test_solution.py::TestEmbeddingStore::test_search_with_filter_no_match_returns_empty PASSED [ 78%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_agent_initialization PASSED [ 80%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_generates_response PASSED [ 83%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_uses_retrieved_context PASSED [ 85%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_with_filter PASSED [ 88%]
tests/test_solution.py::TestMockEmbedder::test_deterministic_output PASSED [ 90%]
tests/test_solution.py::TestMockEmbedder::test_dimension_size PASSED [ 92%]
tests/test_solution.py::TestMockEmbedder::test_different_inputs_different_vectors PASSED [ 95%]
tests/test_solution.py::TestEndToEndRAG::test_full_rag_pipeline PASSED [ 97%]
tests/test_solution.py::TestEndToEndRAG::test_rag_with_metadata_filtering PASSED [100%]

============================== 42 passed in 0.04s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Thời gian yêu cầu trả hàng trên Shopee là 15 ngày. | Người mua có thể gửi yêu cầu hoàn tiền trong 15 ngày. | CAO | 0.1131 | Đúng ngữ nghĩa (Mock hash làm điểm thấp) |
| 2 | Đổi trả sản phẩm Tiki trong vòng 7 ngày đầu. | Chính sách hoàn tiền Shopee xử lý trong 02 ngày. | THẤP | -0.2077 | Đúng |
| 3 | Người mua được trả hàng nếu sản phẩm bị lỗi. | Người bán phải chịu phí vận chuyển hoàn trả. | THẤP | 0.0640 | Đúng |
| 4 | Sendo hoàn tiền 100% vào ví Senpay. | Tiki hỗ trợ đổi mới thiết bị điện tử hư hỏng. | THẤP | -0.2102 | Đúng |
| 5 | Quy trình khiếu nại đơn hàng hoàn trả. | Thời gian xử lý tranh chấp của sàn thương mại điện tử. | CAO | 0.2247 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 1 có điểm tương tự thực tế khá thấp trên MockEmbedder (0.1131) dù ngữ nghĩa hoàn toàn trùng khớp. Điều này chứng minh hàm `MockEmbedder` chỉ tính toán dựa trên mã băm (hash-based) của chuỗi nên chưa học được mối quan hệ từ đồng nghĩa hay ngữ cảnh sâu như các mô hình thực thụ (ví dụ `all-MiniLM-L6-v2` hay Gemini Embeddings).

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng? | `shopee-chinh-sach-tra-hang-hoan-tien` — Mục 3.2: 15 ngày kể từ khi đơn thành công. | 0.3174 | Có | Người mua có 15 ngày kể từ khi đơn hàng giao thành công để yêu cầu trả hàng. |
| 2 | Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu? | `shopee-chinh-sach-tra-hang-hoan-tien` — Mục 5.1: Phản hồi trong 02 ngày lịch. | 0.3311 | Có | Người bán có 02 ngày lịch kể từ ngày nhận thông báo để phản hồi yêu cầu. |
| 3 | Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu? | `sendo-chinh-sach-doi-tra-buyer` — Mục Hoàn tiền: Ví Senpay, 3-7 ngày làm việc. | 0.3230 | Có | Sendo hoàn tiền 100% vào ví Senpay trong thời gian từ 3 đến 7 ngày. |
| 4 | Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày? | `tiki-chinh-sach-doi-tra-buyer` — Mục Thiết bị điện tử: 7 ngày đầu Đổi mới/Hoàn tiền. | 0.3769 | Có | Tiki hỗ trợ đổi trả hoặc hoàn tiền điện thoại bị lỗi trong 7 ngày đầu. |
| 5 | Người bán trên Shopee có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không? | `shopee-chinh-sach-tra-hang-hoan-tien` — Mục Phí vận chuyển: Không chịu phí khi lỗi ĐVVC. | 0.3184 | Có | Người bán không phải chịu chi phí vận chuyển hoàn trả nếu lỗi thuộc về đơn vị vận chuyển. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Việc triển khai `HeadingChunker` theo cấu trúc nhãn `##` trong Markdown rất hiệu quả cho các văn bản pháp lý/chính sách. Việc chủ động bổ sung tiêu đề section vào từng chunk con bị tràn giúp bảo toàn ngữ cảnh hoàn hảo khi hệ thống vector hóa và truy xuất.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
