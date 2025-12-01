import os
from qdrant_client import QdrantClient
from ingest import DataIngestor
from llm_wrapper import LLMWrapper
from rag_engine import UniMSRAG
from config import Config

def main():
    print("="*60)
    print("CHATBOT ĐẶT MÓN ĂN - HÒA VIÊN RESTAURANT")
    print("="*60)
    
    # 1. Khởi tạo Qdrant (Local)
    print("\n[1/4] Connecting to Qdrant...")
    client = QdrantClient(Config.QDRANT_PATH)
    
    # 2. Ingest dữ liệu
    print("[2/4] Ingesting data...")
    ingestor = DataIngestor(client)
    ingestor.ingest()
    
    # 3. Khởi tạo LLM
    print("[3/4] Loading LLM...")
    try:
        llm = LLMWrapper()
    except Exception as e:
        print(f"Error loading LLM: {e}")
        return
    
    # 4. Khởi tạo RAG Engine với Order Management
    print("[4/4] Initializing RAG Engine with Order Management...")
    bot = UniMSRAG(llm, client)
    
    print("\n✅ System Ready!")
    print("="*60)
    
    # 5. Xử lý Input/Output
    input_file = os.path.join(Config.INPUT_DIR, "sentences.txt")
    output_file = os.path.join(Config.OUTPUT_DIR, "answer.txt")
    
    if not os.path.exists(input_file):
        print(f"\n⚠️  Input file not found: {input_file}")
        print("Entering interactive mode...\n")
        
        # Chế độ tương tác terminal
        print("📝 Test Cases (hoặc gõ câu hỏi của bạn):")
        print("1. Tôi muốn đặt 2 phần phở bò")
        print("2. Xem đơn hàng của tôi")
        print("3. Giá vịt quay Bắc Kinh là bao nhiêu?")
        print("4. Thêm 1 trà sữa")
        print("5. Hủy món phở bò")
        print("6. Xác nhận đặt hàng")
        print("Gõ 'exit' hoặc 'quit' để thoát\n")
        
        while True:
            query = input("👤 Bạn: ")
            if query.lower() in ["exit", "quit"]:
                print("Cảm ơn bạn đã sử dụng dịch vụ! 👋")
                break
            
            if not query.strip():
                continue
                
            print("🤖 Bot: ", end="")
            try:
                response = bot.process(query)
                print(response)
            except Exception as e:
                print(f"Lỗi: {e}")
            print()
        return
    
    # Xử lý từ file input
    print(f"\n📂 Reading from {input_file}...")
    with open(input_file, 'r', encoding='utf-8') as f:
        queries = f.readlines()
    
    results = []
    print("\n" + "="*60)
    print("PROCESSING QUERIES")
    print("="*60 + "\n")
    
    for i, q in enumerate(queries, 1):
        q = q.strip()
        if not q:
            continue
        
        print(f"[{i}] User: {q}")
        try:
            response = bot.process(q)
            print(f"Response: {response[:100]}..." if len(response) > 100 else f"Response: {response}")
            results.append(f"Q: {q}\nA: {response}\n{'-'*60}\n")
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            results.append(f"Q: {q}\nA: {error_msg}\n{'-'*60}\n")
        print()
    
    # Ghi kết quả
    os.makedirs(Config.OUTPUT_DIR, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(results)
    
    print("="*60)
    print(f"✅ Done! Results saved to: {output_file}")
    print("="*60)

if __name__ == "__main__":
    main()