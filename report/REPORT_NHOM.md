# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** Nhóm 2A
**Thành viên:** Duẩn, Việt, Phan Hoàng Vũ (2A202602450)
**Ngày:** 20/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Chính sách Trả hàng & Hoàn tiền trên các sàn Thương mại Điện tử lớn tại Việt Nam (Shopee, Lazada, Tiki, Sendo, TikTok Shop).

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề chính sách đổi trả e-commerce vì đây là mảng thông tin thực tế, phức tạp và có tính phân hóa cao giữa hai đối tượng "Người mua" (Buyer) và "Người bán" (Seller). Việc xử lý tập tài liệu này đòi hỏi chiến lược chunking thông minh và gán metadata chính xác để không bị truy xuất nhầm quyền lợi giữa Buyer và Seller.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | `shopee-chinh-sach-tra-hang-hoan-tien.md` | https://help.shopee.vn/portal/4/article/77251 | 2026-09-20 / 2026-03-11 | 26,485 | `doc_id`, `audience=both`, `category=return-refund`, `language=vi` |
| 2 | `sendo-chinh-sach-doi-tra-buyer.md` | https://ginee.com/vn/insights/doi-tra-hang-sendo/ | 2026-09-20 / 2021.11 | 4,321 | `doc_id`, `audience=buyer`, `category=return-refund`, `language=vi` |
| 3 | `tiki-chinh-sach-doi-tra-buyer.md` | https://hotro.tiki.vn/knowledge-base/post/805 | 2026-09-20 / 2024-04-15 | 8,912 | `doc_id`, `audience=buyer`, `category=return-refund`, `language=vi` |
| 4 | `tiktokshop-chinh-sach-tra-hang-seller.md` | https://seller-vn.tiktok.com/university/essay?knowledge_id=6837773789234946 | 2026-09-20 / 2026.1 | 12,450 | `doc_id`, `audience=seller`, `category=return-refund`, `language=vi` |
| 5 | `lazada-quy-trinh-chi-hoan-tien-seller.md` | https://sellercenter.lazada.vn/helpcenter/s/faq/knowledge | 2026-09-20 / 2024-12-05 | 6,780 | `doc_id`, `audience=seller`, `category=return-refund`, `language=vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | `str` | `"shopee-chinh-sach-tra-hang-hoan-tien"` | Xác định chính xác tài liệu nguồn khi tổng hợp câu trả lời |
| `audience` | `str` | `"buyer"`, `"seller"`, `"both"` | Lọc chính xác thông tin dành cho Người mua hoặc Người bán, tránh nhầm lẫn điều khoản |
| `category` | `str` | `"return-refund"` | Giới hạn phân vùng chủ đề khi tích hợp vào cơ sở tri thức lớn hơn |
| `document_version` | `str` | `"2026-03-11"` | Quản lý phiên bản chính sách theo thời gian |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên tài liệu chính sách Shopee (26,485 ký tự):

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Shopee Policy | FixedSizeChunker (`fixed_size`) | 53 | 500 chars | Kém — Dễ ngắt đôi câu hoặc mất tiêu đề điều khoản |
| Shopee Policy | SentenceChunker (`by_sentences`) | 48 | 545 chars | Khá — Giữ trọn vẹn câu nhưng thiếu cấu trúc mục lớn |
| Shopee Policy | RecursiveChunker (`recursive`) | 51 | 490 chars | Tốt — Tách theo đoạn văn `\n\n` tốt hơn tách ký tự |

### Chiến lược của từng thành viên

**Thành viên 1 — Duẩn**
- **Loại chiến lược:** `RecursiveChunker` (`chunk_size=500`)
- **Mô tả & lý do chọn:** Tách ưu tiên theo đoạn `\n\n`, sau đó đến dòng `\n` và câu. Giúp các đoạn văn bản trong chính sách giữ được sự liền mạch logic theo từng mục nhỏ.

**Thành viên 2 — Việt**
- **Loại chiến lược:** `SentenceChunker` (`max_sentences_per_chunk=3`)
- **Mô tả & lý do chọn:** Tách theo ranh giới câu bằng biểu thức chính quy. Mỗi chunk chứa đúng 3 câu giúp đảm bảo độ cô đọng thông tin cho RAG.

**Thành viên 3 — Vũ**
- **Loại chiến lược:** `HeadingChunker` (`chunk_size=500`) — Custom
- **Mô tả & lý do chọn:** Tách theo các dòng tiêu đề `##` trong Markdown. Đặc biệt khi section quá dài phải cắt phụ, thuật toán sẽ **tự động chèn lại tên heading vào đầu từng chunk con** giúp không bị mất ngữ cảnh của điều khoản mục lớn.
- **Code snippet:**
```python
import re

class HeadingChunker:
    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        parts = re.split(r'(?=^##+ )', text, flags=re.MULTILINE)
        chunks = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) <= self.chunk_size:
                chunks.append(part)
            else:
                heading_match = re.match(r'^(##+ .+)', part)
                heading = heading_match.group(1) + "\n" if heading_match else ""
                body = part[len(heading):]
                for start in range(0, len(body), self.chunk_size):
                    sub = body[start : start + self.chunk_size]
                    if sub.strip():
                        chunks.append((heading + sub).strip())
        return chunks
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Duẩn | `RecursiveChunker` | 9/10 | Linh hoạt, tự động xử lý mọi định dạng văn bản | Thỉnh thoảng chunk chứa 2 chủ đề nếu thiếu `\n\n` |
| Việt | `SentenceChunker` | 8.5/10 | Chunk gọn gàng, độ tương đồng cosine chuẩn | Có thể làm rời rạc bảng hoặc danh sách gạch đầu dòng |
| Vũ | `HeadingChunker` | 10/10 | Bảo toàn ngữ cảnh tiêu đề cho từng đoạn cắt phụ | Phụ thuộc vào định dạng Markdown có tiêu đề `##` |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> `HeadingChunker` (của Vũ) là chiến lược tốt nhất cho chủ đề chính sách Thương mại Điện tử. Lý do là tài liệu quy định luôn có cấu trúc phân tầng rõ ràng (Mục, Điều, Khoản). Khi cắt một section dài thành nhiều chunk nhỏ, việc lưu kèm tiêu đề mục ở đầu mỗi chunk giúp mô hình Embedding nhận diện chính xác phạm vi áp dụng mà không bị nhầm ngữ cảnh với các điều khoản khác.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng? | **15 ngày** kể từ khi đơn hàng được cập nhật giao hàng thành công | `shopee-chinh-sach-tra-hang-hoan-tien.md` (Mục 3.2) |
| 2 | Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu? | **02 ngày lịch** kể từ ngày nhận thông báo | `shopee-chinh-sach-tra-hang-hoan-tien.md` (Mục 5.1) |
| 3 | Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu? | Hoàn tiền 100% vào **ví Senpay**, thời gian khoảng **3–7 ngày** | `sendo-chinh-sach-doi-tra-buyer.md` (Mục Hoàn tiền) |
| 4 | Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày? | **7 ngày đầu** — hình thức Đổi mới / Hoàn tiền | `tiki-chinh-sach-doi-tra-buyer.md` (Mục Thiết bị điện tử) |
| 5 | Người bán trên Shopee có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không? | **Không** — người bán không chịu chi phí khi lỗi do đơn vị vận chuyển | `shopee-chinh-sach-tra-hang-hoan-tien.md` (Mục Phí vận chuyển) |

### Tổng hợp chất lượng truy xuất của nhóm

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng? | `HeadingChunker` | Có (Top-1) | Lọc `audience: buyer/both` giúp loại bỏ nhiễu seller |
| 2 | Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu? | `HeadingChunker` | Có (Top-1) | Lọc `audience: seller/both` định hướng đúng file điều khoản người bán |
| 3 | Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu? | `RecursiveChunker` / `HeadingChunker` | Có (Top-1) | Tìm kiếm chính xác thông tin kênh ví Senpay và thời gian 3-7 ngày |
| 4 | Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày? | `HeadingChunker` | Có (Top-1) | Tách theo heading giúp lấy đúng bảng mảng hàng Điện tử |
| 5 | Phí vận chuyển lỗi do đơn vị vận chuyển ai chịu? | `HeadingChunker` | Có (Top-1) | Truy xuất đúng mục Phí vận chuyển |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Metadata filtering đặc biệt quan trọng ở các câu 1, 2 và 5 liên tục đối chiếu giữa **Người mua (Buyer)** và **Người bán (Seller)**. Trong cùng một bộ tài liệu Shopee, nếu không lọc theo `audience`, truy xuất dễ bị nhầm lẫn giữa quy định thời gian trả hàng của Buyer (15 ngày) và thời gian phản hồi của Seller (2 ngày).

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
1. Cấu trúc tài liệu (Markdown Headings) quyết định hiệu quả chunking hơn là chỉ dựa vào độ dài cố định.
2. Metadata pre-filtering giúp triệt tiêu hoàn toàn nhiễu ngữ cảnh trong RAG khi làm việc với tài liệu đa đối tượng (Buyer vs Seller).
3. Độ tương tự Cosine phản ánh đúng hướng ngữ nghĩa hơn khoảng cách Euclidean trên các vector embedding văn bản.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một tập dữ liệu chính sách, các phương pháp chunking thô sơ (`FixedSize`) dẫn tới việc ngắt đôi các điều khoản quan trọng khiến Agent không thể trả lời đúng. Khi nâng cấp lên `HeadingChunker` có gắn lại ngữ cảnh tiêu đề, tỷ lệ truy xuất chính xác của nhóm đạt mức tối đa.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ chuẩn hóa dữ liệu Markdown đồng nhất ngay từ bước cào dữ liệu (Crawling phase), tạo các thẻ metadata giàu thông tin hơn (như phân loại chi tiết dòng sản phẩm: Điện tử, Thời trang, Hàng tiêu dùng) để phục vụ bài toán truy xuất phức tạp hơn.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5 / 5 |
| **Tổng phần nhóm** | **40 / 40** |
