from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from config import Config

class UniMSRAG:
    def __init__(self, llm, qdrant_client):
        self.llm = llm
        self.client = qdrant_client
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)

    def planner(self, user_query):
        """
        Step 1: Knowledge Source Selection [cite: 38, 139]
        Quyết định xem câu hỏi có cần tra cứu menu/thông tin nhà hàng không.
        """
        prompt = (
            f"Câu hỏi: \"{user_query}\"\n"
            "Hãy xác định xem câu hỏi này có cần tra cứu thông tin về menu (giá, món ăn) "
            "hoặc thông tin nhà hàng (địa chỉ, giờ mở cửa) không?\n"
            "Nếu CÓ, hãy trả lời: [SEARCH]\n"
            "Nếu KHÔNG (ví dụ: chào hỏi, cảm ơn), hãy trả lời: [NO_SEARCH]"
        )
        response = self.llm.generate(prompt, max_new_tokens=10)
        if "[SEARCH]" in response:
            return "SEARCH"
        return "NO_SEARCH"

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