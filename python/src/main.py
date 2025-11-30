import os
from qdrant_client import QdrantClient
from ingest import DataIngestor
from llm_wrapper import LLMWrapper
from rag_engine import UniMSRAG
from config import Config

def main():
    # 1. Khởi tạo Qdrant (Local)
    client = QdrantClient(Config.QDRANT_PATH)
    
    # 2. Ingest dữ liệu (Nạp menu và info vào DB)
    # Trong môi trường thực tế, bước này có thể tách riêng, nhưng để demo chấm bài
    # ta chạy mỗi lần khởi động để đảm bảo dữ liệu có trong RAM.
    ingestor = DataIngestor(client)
    ingestor.ingest()
    
    # 3. Khởi tạo LLM
    try:
        llm = LLMWrapper()
    except Exception as e:
        print(f"Error loading LLM: {e}")
        return

    # 4. Khởi tạo RAG Engine
    bot = UniMSRAG(llm, client)
    
    # 5. Xử lý Input/Output
    input_file = os.path.join(Config.INPUT_DIR, "sentences.txt")
    output_file = os.path.join(Config.OUTPUT_DIR, "answer.txt") # Output cho phần trả lời [cite: 649]

    if not os.path.exists(input_file):
        print(f"Input file not found: {input_file}")
        # Chế độ tương tác terminal nếu không có file input
        while True:
            query = input("User: ")
            if query.lower() in ["exit", "quit"]: break
            response = bot.process(query)
            print(f"Bot: {response}")
        return

    print(f"Reading from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        queries = f.readlines()
        
    results = []
    for q in queries:
        q = q.strip()
        if not q: continue
        print(f"Processing: {q}")
        response = bot.process(q)
        results.append(f"Q: {q}\nA: {response}\n{'-'*20}\n")
        
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(results)
    
    print(f"Done. Results saved to {output_file}")

if __name__ == "__main__":
    main()