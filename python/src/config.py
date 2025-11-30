import os

class Config:
    # Model LLM (Yêu cầu VinaLLaMA-7B-Chat)
    MODEL_ID = "VinaLLaMA-7B-Chat"
    
    # Embedding Model (Nhẹ, hiệu quả cho tiếng Việt/Anh)
    EMBEDDING_MODEL = "AITeamVN/Vietnamese_Embedding"
    
    # Qdrant settings (Local memory mode cho chấm bài)
    QDRANT_PATH = ":memory:"
    COLLECTION_NAME = "hoa_vien_data"
    
    # Paths (Tương thích với Docker volume mount trong util.sh)
    # INPUT_DIR = "/nlp/input"
    # OUTPUT_DIR = "/nlp/output"
    # DATA_DIR = "/nlp/data"
    
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "../data") 
    INPUT_DIR = os.path.join(BASE_DIR, "../../input")
    OUTPUT_DIR = os.path.join(BASE_DIR, "../../2211522/output")