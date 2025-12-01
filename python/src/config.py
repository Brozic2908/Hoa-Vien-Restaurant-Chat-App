import os

class Config:
    # Model LLM (Yêu cầu Qwen/Qwen2.5-3B-Instruct)
    MODEL_ID = "Qwen/Qwen2.5-3B-Instruct"
    
    # Embedding Model (Nhẹ, hiệu quả cho tiếng Việt/Anh)
    EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
    
    # Qdrant settings (Local memory mode cho chấm bài)
    QDRANT_PATH = ":memory:"
    COLLECTION_NAME = "hoa_vien_data"
    
    # Paths (Tương thích với Docker volume mount trong util.sh)
    INPUT_DIR = "/nlp/input"
    OUTPUT_DIR = "/nlp/output"
    DATA_DIR = "/nlp/data"
    
    # Uncomment nếu muốn test trên vscode
    # 1. Lấy đường dẫn tuyệt đối của file config.py hiện tại
    # Ví dụ: /app/src/config.py
    # BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # # 2. "Lùi" một cấp để ra thư mục gốc của dự án (Project Root)
    # # Từ /app/src/ -> lùi về /app/
    # PYTHON_DIR = os.path.dirname(BASE_DIR)
    # ROOT_DIR = os.path.dirname(PYTHON_DIR)

    # # 3. Định nghĩa đường dẫn tới các thư mục Input/Output dựa trên ROOT_DIR
    # INPUT_DIR = os.path.join(ROOT_DIR, "input") 
    
    # # [cite_start]Yêu cầu đề bài: output/answer.txt [cite: 670]
    # OUTPUT_DIR = os.path.join(ROOT_DIR, "2211522/output")
    
    # # Đường dẫn tới thư mục data (chứa menu.json, v.v.)
    # DATA_DIR = os.path.join(PYTHON_DIR, "data")