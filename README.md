# NLP Assignment: Chatbot Đặt Món Ăn (Hòa Viên Restaurant)

## 1. Giới thiệu

Dự án xây dựng hệ thống **Chatbot hỗ trợ đặt món ăn online** cho nhà hàng Hòa Viên, kết hợp giữa các phương pháp xử lý ngôn ngữ tự nhiên (NLP) hiện đại và quản lý hội thoại theo ngữ cảnh.

Hệ thống được thiết kế để giải quyết bài toán tương tác người - máy trong miền ngữ nghĩa hẹp (đặt món ăn), tích hợp **Large Language Model (LLM)** và kỹ thuật **Retrieval-Augmented Generation (RAG)** để đảm bảo phản hồi tự nhiên, chính xác dựa trên dữ liệu menu thực tế.

### Tính năng chính

- **Xử lý ý định (Intent Classification):** Tự động nhận diện nhu cầu khách hàng: Đặt món, Hủy món, Xem đơn hàng, Hỏi thông tin.
- **RAG (Retrieval-Augmented Generation):** Truy xuất thông tin từ cơ sở dữ liệu menu (Qdrant Vector DB) để trả lời các câu hỏi về giá, nguyên liệu, gợi ý món ăn.
- **Quản lý đơn hàng (Order Management):** Thêm, sửa, xóa món trong giỏ hàng và tính toán tổng tiền (kèm VAT).
- **Mô hình ngôn ngữ:** Sử dụng `Qwen/Qwen2.5-3B-Instruct` cho khả năng sinh ngữ tiếng Việt tốt và `AITeamVN/Vietnamese_Embedding` cho việc vector hóa dữ liệu.

---

## 2. Cấu trúc dự án

Để hệ thống hoạt động chính xác với script chấm bài, cấu trúc thư mục cần được tổ chức như sau:

```text
.
├── input/                  # Chứa file đầu vào để test
├── output/                 # Chứa file kết quả trả lời từ file test
│   └── sentences.txt       # Danh sách câu query của người dùng
├── python/                 # Mã nguồn chính và Dockerfile
│   ├── src/                # Source code Python (main.py, rag_engine.py,...)
│   ├── data/               # Dữ liệu (menu_v2.json)
│   ├── Dockerfile          # Cấu hình build Docker image
│   └── requirements.txt    # Các thư viện cần thiết
├── util.sh                 # Script hỗ trợ build và run (cần cấp quyền thực thi)
└── README.md               # File hướng dẫn này
```

---

## 3. Yêu cầu hệ thống (Prerequisites)

- **Docker:** Đã cài đặt và đang chạy (Docker Desktop hoặc Docker Engine).
- **Tài nguyên:** Do sử dụng LLM cục bộ, khuyến nghị máy có tối thiểu **8GB - 16GB RAM**.
- **Hệ điều hành:** Linux/MacOS hoặc Windows (sử dụng WSL2).

---

## 4. Hướng dẫn cài đặt và chạy (Deployment)

Hệ thống được đóng gói hoàn chỉnh bằng Docker và chạy thông qua script `util.sh`.

### Bước 1: Chuẩn bị môi trường

Đảm bảo bạn đang đứng ở thư mục gốc của dự án và file `util.sh` đã được cấp quyền thực thi:

```bash
chmod +x util.sh
```

### Bước 2: Chuẩn bị dữ liệu đầu vào

Tạo file input/sentences.txt nếu chưa có. Ví dụ nội dung:

```plaintext
Xin chào
Cho tôi xem menu
Gợi ý cho tôi món nào cay cay
Tôi muốn đặt 1 phần vịt quay Bắc Kinh
Thêm 2 ly trà sữa
Hủy món vịt quay
Xác nhận đơn hàng
```

### Bước 3: Chạy hệ thống (Chế độ Test/Submit)

Sử dụng lệnh sau để build Docker image và xử lý file input:

```Bash
./util.sh test
```

Quá trình thực hiện của script:

1. Build Docker image tên nlp222 từ thư mục python/.

2. Mount thư mục input/ vào container.

3. Chạy pipeline RAG để xử lý các câu trong sentences.txt.

4. Lưu kết quả trả lời vào thư mục [MÃ_SỐ_SV]/output/answer.txt.

### Bước 4: Kiểm tra kết quả

Sau khi chạy xong, kết quả sẽ nằm tại đường dẫn (ví dụ với MSSV 2211522 ): <code>./2211522/output/answer.txt</code>

---

## 5. Chạy chế độ Tương tác (Interactive Mode)

Nếu bạn muốn chat trực tiếp với bot qua Terminal (không dùng file input), hãy làm như sau:

1. Xóa hoặc đổi tên file input/sentences.txt (để hệ thống không tìm thấy file này).

2. Chạy lại lệnh test:

   ```bash
   ./util.sh test
   ```

3. Hệ thống sẽ chuyển sang chế độ nhập liệu thủ công:

   ```text
   👤 Bạn: Có món gà nào ngon không?
   🤖 Bot: Nhà hàng có món Gà hấp muối Đông Quang và Gà Cung Bảo rất ngon ạ...
   ```

---

## 6. Chi tiết kỹ thuật (Technical Overview)

Pipeline xử lý (rag_engine.py)

1. **Planner**: Phân loại Intent của người dùng (ORDER, SEARCH, VIEW_ORDER, etc.) sử dụng Few-shot Prompting với LLM.

2. **Order Manager**: Nếu là intent đặt món, hệ thống gọi Module quản lý đơn hàng để thêm/bớt món, tính tiền.

3. **Retriever**: Nếu là intent tìm kiếm thông tin, hệ thống vector hóa câu hỏi và tìm kiếm ngữ cảnh liên quan trong Qdrant (Vector DB).

4. **Reader (Generator)**: LLM tổng hợp thông tin từ Retriever hoặc kết quả từ Order Manager để sinh câu trả lời tự nhiên cuối cùng.

Dữ liệu (ingest.py)

Dữ liệu menu (<code>menu_v2.json</code>) được làm giàu (enrich) thông tin và vector hóa trước khi đưa vào Qdrant để đảm bảo khả năng tìm kiếm ngữ nghĩa chính xác (ví dụ: tìm "món cay" sẽ ra các món có tag "spicy").

---

## 7. Thông tin tác giả

Họ và tên: Nguyễn Lê Quốc Khánh

MSSV: 2211522

Môn học: Xử lý ngôn ngữ tự nhiên (NLP)
