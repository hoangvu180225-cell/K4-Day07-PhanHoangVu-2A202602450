## GIAI ĐOẠN 4 — HỌP NHÓM: CHỐT QUERY + PHÂN CHIẾN LƯỢC
> ⚠️ **Cả 3 người phải đồng ý trước khi ai sang Giai đoạn 5.**

**Nhóm:** Duẩn · Việt · Vũ

---

### 4.1 — Phân chiến lược chunking (bắt buộc 3 chunker khác nhau)

Lab K4-L3B yêu cầu **ít nhất 1 thành viên chunk theo heading/section** — đó là vai R3, giao cho **Vũ**.

| Thành viên | Chunker | Tham số | Ghi chú |
|-----------|---------|---------|---------|
| **Duẩn** | `RecursiveChunker` | `chunk_size=500` | Thử separator theo thứ tự ưu tiên |
| **Việt** | `SentenceChunker` | `max_sentences_per_chunk=3` | Tách theo ranh giới câu |
| **Vũ** | `HeadingChunker` (custom) | `chunk_size=500` | **Bắt buộc** — chunk theo `##` heading |

Vũ cần tự viết thêm class `HeadingChunker` vào repo của mình (không có sẵn trong `src/`). Xem gợi ý ở cuối mục này.

---

### 4.2 — 5 Benchmark Query (dùng chung cả nhóm)

> Gold answer được trích **trực tiếp từ tài liệu đã crawl** — có thể kiểm chứng.

| # | Câu hỏi | Gold answer (trích từ tài liệu) | Tài liệu nguồn | Filter bắt buộc |
|---|---------|--------------------------------|---------------|----------------|
| 1 | Người mua trên Shopee có bao nhiêu ngày để gửi yêu cầu trả hàng? | **15 ngày** kể từ khi đơn hàng được cập nhật giao hàng thành công | `shopee-return-buyer` | `{"audience": "buyer"}` |
| 2 | Người bán trên Shopee phải phản hồi yêu cầu trả hàng trong bao lâu? | **02 ngày lịch** kể từ ngày nhận thông báo | `shopee-return-seller` | `{"audience": "seller"}` |
| 3 | Sendo hoàn tiền cho người mua qua kênh nào và mất bao lâu? | Hoàn tiền 100% vào **ví Senpay**, thời gian khoảng **3–7 ngày** | `sendo-return-policy` | None |
| 4 | Tiki hỗ trợ đổi trả điện thoại bị lỗi trong bao nhiêu ngày? | **7 ngày đầu** — hình thức Đổi mới / Hoàn tiền | `tiki-return-policy` | `{"audience": "buyer"}` |
| 5 | Người bán trên Shopee có phải chịu phí vận chuyển hoàn trả khi lỗi do đơn vị vận chuyển không? | **Không** — người bán không chịu chi phí khi lỗi do đơn vị vận chuyển | `shopee-return-seller` | `{"audience": "seller"}` |

**Tại sao các câu này hợp lệ:**
- Câu 1 & 4: cần filter `buyer` — corpus có cả file buyer lẫn seller về cùng chủ đề Shopee, không filter thì retrieval có thể lấy nhầm file seller
- Câu 2 & 5: cần filter `seller` — câu hỏi không nêu rõ đối tượng, nếu không filter dễ trả về chunk của buyer
- Câu 3: không cần filter — Sendo chỉ có 1 file, không bị nhiễu

---

### 4.3 — Gợi ý HeadingChunker cho Vũ

```python
import re

class HeadingChunker:
    """Chunk theo tiêu đề ## trong Markdown. Section nào dài quá thì cắt thêm."""

    def __init__(self, chunk_size: int = 500) -> None:
        self.chunk_size = chunk_size

    def chunk(self, text: str) -> list[str]:
        if not text:
            return []
        # Tách tại mỗi dòng bắt đầu bằng ## (giữ lại heading)
        parts = re.split(r'(?=^##+ )', text, flags=re.MULTILINE)
        chunks = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            if len(part) <= self.chunk_size:
                chunks.append(part)
            else:
                # Section dài: cắt cứng, GẮN LẠI heading vào từng mảnh con
                heading_match = re.match(r'^(##+ .+)', part)
                heading = heading_match.group(1) + "\n" if heading_match else ""
                body = part[len(heading):]
                for start in range(0, len(body), self.chunk_size):
                    sub = body[start : start + self.chunk_size]
                    chunks.append((heading + sub).strip())
        return chunks
```

> **Lưu ý quan trọng:** khi section dài phải cắt, gắn lại heading vào đầu mỗi mảnh con — nếu không, mảnh thứ 2 trở đi mất ngữ cảnh "đây là mục nào".

---

### ✅ Checklist giai đoạn 4

- [ ] Duẩn báo nhóm: dùng `RecursiveChunker`
- [ ] Việt báo nhóm: dùng `SentenceChunker`
- [ ] Vũ viết xong `HeadingChunker` và báo nhóm
- [ ] Cả 3 đồng ý 5 câu query ở bảng trên
- [ ] Cả 3 copy bảng query vào `bench.py` của mình (phần `QUERIES`)

---