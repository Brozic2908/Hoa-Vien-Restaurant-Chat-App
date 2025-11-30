# NLP Assignment - Option 2: Chatbot with LLM/RAG

## Student ID: 2211522

## Tổng quan

Dự án xây dựng chatbot hỗ trợ đặt món cho nhà hàng Hòa Viên sử dụng kỹ thuật RAG (Retrieval-Augmented Generation) dựa trên kiến trúc UniMS-RAG.

## Mô hình

- **LLM**: Qwen/Qwen2.5-7B-Instruct (Tải tự động từ HuggingFace).
- **Embedding**: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2.
- **Vector DB**: Qdrant (In-memory mode).

## Yêu cầu phần cứng

- GPU VRAM >= 16GB (để chạy Qwen-7B ở chế độ fp16).
- Nếu chạy trên CPU hoặc GPU yếu, vui lòng đổi `MODEL_ID` trong `src/config.py` sang `Qwen/Qwen2.5-1.5B-Instruct` hoặc `Qwen/Qwen2.5-0.5B-Instruct`.

## Cấu trúc thực thi (Theo UniMS-RAG)

1. **Planner**: Phân loại intent của user (Cần tra cứu DB hay không).
2. **Retriever**: Tìm kiếm thông tin món ăn/nhà hàng trong Qdrant.
3. **Generator**: Tổng hợp thông tin và sinh câu trả lời tự nhiên.

## Cách chạy (Sử dụng util.sh)

### 1. Đảm bảo file `input/sentences.txt` tồn tại.

### 2. Chạy lệnh:

```bash
./util.sh test
```

### 3. Kết quả sẽ được lưu tại 2211522/output/answer.txt.

## Lưu ý về Docker

- Do giới hạn dung lượng nộp bài, Model không được include trong image. Docker container sẽ cần kết nối internet để tải model lần đầu tiên chạy.
