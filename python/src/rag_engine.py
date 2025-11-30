from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import Config

class UniMSRAG:
    """
    Đây là phần cốt lõi thực hiện logic UniMS-RAG  gồm 3 bước:
    - Knowledge Source Selection (Planner): Quyết định có cần tìm kiếm thông tin không.
    - Knowledge Retrieval (Retriever): Tìm kiếm vector.
    - Response Generation (Reader): Sinh câu trả lời.
    """
    def __init__(self, llm, qdrant_client):
        self.llm = llm
        self.client = qdrant_client
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)
    
    def planner(self, user_query):
        """
        Step 1: Knowledge Source Selection
        Cải thiện Prompt để bắt dính các câu hỏi về giờ giấc và khẩu vị.
        """
        prompt = (
            f"Câu hỏi người dùng: \"{user_query}\"\n\n"
            "Nhiệm vụ: Bạn là bộ phận phân loại câu hỏi cho RAG chatbot của nhà hàng Hòa Viên.\n"
            "Hãy quyết định xem có cần tra cứu Database (Menu/Thông tin) không.\n\n"
            "QUY TẮC BẮT BUỘC:\n"
            "1. Trả về [SEARCH] nếu câu hỏi liên quan đến:\n"
            "   - Món ăn, Menu, Giá cả.\n"
            "   - Gợi ý món ăn theo khẩu vị (cay, chua, ngọt, món nước, món khô...).\n"  # <-- Bắt case "ăn gì cay cay"
            "   - Thông tin nhà hàng (Giờ mở cửa, Địa chỉ, Hotline, Wifi).\n" # <-- Bắt case "giờ mở cửa"
            "   - Kiểm tra đơn hàng.\n"
            "2. Trả về [NO_SEARCH] CHỈ KHI câu hỏi là:\n"
            "   - Chào hỏi xã giao (Xin chào, Hello).\n"
            "   - Cảm ơn, Tạm biệt.\n"
            "   - Câu vô nghĩa hoặc không liên quan nhà hàng.\n\n"
            "Output chỉ chứa đúng 1 cụm từ: [SEARCH] hoặc [NO_SEARCH]."
        )
        
        # Tăng max_new_tokens lên một chút để LLM suy nghĩ nếu cần, dù ta chỉ lấy kết quả ngắn
        response = self.llm.generate(prompt, max_new_tokens=20)
        print(f"[1] Raw Planner Output: {response}") # In ra để debug xem nó trả lời gì
        
        # Mặc định tất cả các trường hợp còn lại đều SEARCH cho an toàn
        return "SEARCH" if "[SEARCH]" in response else "NO_SEARCH"

    def retriever(self, user_query, top_k=3):
        """
        Step 2: Knowledge Retrieval [cite: 40, 141]
        Tìm kiếm các đoạn văn bản liên quan trong Qdrant.
        """
        query_vector = self.encoder.encode(user_query).tolist()
        hits = self.client.search(
            collection_name=Config.COLLECTION_NAME,
            query_vector=query_vector,
            limit=top_k
        )
        results = [hit.payload['text'] for hit in hits]
        return results

    def reader(self, user_query, retrieved_contexts):
        """
        Step 3: Response Generation [cite: 41, 143]
        Sinh câu trả lời dựa trên ngữ cảnh đã tìm được.
        """
        context_str = "\n".join([f"- {c}" for c in retrieved_contexts])
        
        prompt = (
            "Dưới đây là thông tin từ cơ sở dữ liệu của nhà hàng Hòa Viên (Hoa Vien Restaurant):\n"
            f"{context_str}\n\n"
            "Hãy đóng vai là một nhân viên phục vụ thân thiện, chuyên nghiệp của nhà hàng Hòa Viên. "
            "Dựa vào thông tin trên, hãy trả lời câu hỏi của khách hàng.\n"
            f"Khách hàng: {user_query}\n"
            "Trả lời:"
        )
        return self.llm.generate(prompt)

    def process(self, user_query):
        # 1. Plan
        action = self.planner(user_query)
        
        # 2. Retrieve (nếu cần)
        contexts = []
        if action == "SEARCH":
            contexts = self.retriever(user_query)
        
        # 3. Generate
        if contexts:
            return self.reader(user_query, contexts)
        else:
            # Nếu không cần search, trả lời trực tiếp (chitchat)
            prompt = (
                "Bạn là nhân viên nhà hàng Hòa Viên. "
                f"Khách hàng nói: \"{user_query}\". "
                "Hãy phản hồi một cách lịch sự, ngắn gọn."
            )
            return self.llm.generate(prompt)