import os
import re
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer
from order_manager import OrderManager
from config import Config

class UniMSRAG:
    """
    UniMS-RAG với chức năng đặt món:
    - Knowledge Source Selection (Planner): Phân loại intent
    - Knowledge Retrieval (Retriever): Tìm kiếm thông tin
    - Response Generation (Reader): Sinh câu trả lời
    - Order Management: Quản lý đơn hàng
    """
    def __init__(self, llm, qdrant_client):
        self.llm = llm
        self.client = qdrant_client
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)
        self.order_manager = OrderManager(os.path.join(Config.DATA_DIR, 'menu_v2.json'))
        self.current_user_id = "demo_user"
    
    def planner(self, user_query):
        """
        Step 1: Knowledge Source Selection & Intent Classification
        Phân loại intent: ORDER, VIEW_ORDER, CANCEL_ITEM, INFO, ...
        """
        prompt = (
            f'Câu hỏi người dùng: "{user_query}"\n\n'
            "Nhiệm vụ: Phân loại ý định (intent) của khách hàng.\n\n"
            "CÁC INTENT:\n"
            "1. [ORDER] - Đặt món, thêm món vào đơn\n"
            "   Ví dụ: 'Tôi muốn đặt 2 phần phở', 'Cho tôi thêm trà sữa', 'Đặt vịt quay'\n"
            "   QUAN TRỌNG: Phải có TÊN MÓN CỤ THỂ, không phải mô tả chung chung\n"
            "2. [VIEW_ORDER] - Xem đơn hàng HIỆN TẠI (đang soạn, chưa xác nhận)\n"
            "   Ví dụ: 'Xem đơn hàng', 'Đơn hiện tại', 'Giỏ hàng của tôi', 'Xem lại đơn'\n"
            "   Từ khóa: 'xem', 'đơn', 'giỏ', 'hiện tại', 'đang đặt'\n"
            "   KHÔNG có từ 'đã', 'lịch sử', 'trước', 'cũ'\n\n"
            "3. [ORDER_HISTORY] - Xem LỊCH SỬ đơn hàng ĐÃ ĐẶT (quá khứ, đã hoàn thành)\n"
            "   Ví dụ: 'Tôi đã đặt gì?', 'Lịch sử đơn hàng', 'Đơn hàng trước đây', 'Các đơn cũ'\n"
            "   Từ khóa: 'ĐÃ', 'lịch sử', 'trước', 'cũ', 'hôm qua', 'tuần trước'\n"
            "   QUAN TRỌNG: Có từ 'ĐÃ' hoặc ám chỉ quá khứ → ORDER_HISTORY\n\n"
            "4. [CANCEL_ITEM] - Hủy/xóa món khỏi đơn\n"
            "   Ví dụ: 'Hủy món gà rán', 'Xóa phở bò', 'Bỏ trà sữa đi'\n"
            "5. [UPDATE_QUANTITY] - Thay đổi số lượng món\n"
            "   Ví dụ: 'Đổi thành 3 phần', 'Tăng lên 5 ly', 'Giảm còn 1'\n"
            "6. [CONFIRM_ORDER] - Xác nhận đặt hàng\n"
            "   Ví dụ: 'Xác nhận đơn', 'Đặt luôn', 'OK đặt hàng'\n"
            "7. [SEARCH] - Hỏi thông tin menu, giá cả, giờ mở cửa\n"
           "   Ví dụ: 'Giá phở bò?', 'Có món chay không?', 'Mở cửa lúc mấy giờ?'\n"
            "   'Tôi muốn ăn gì đó cay cay', 'Gợi ý món ngon', 'Món nào đặc sản?'\n"
            "   QUAN TRỌNG: Câu hỏi gợi ý/tìm món theo khẩu vị là SEARCH, không phải ORDER\n"
            "8. [NO_SEARCH] - Chào hỏi, cảm ơn\n"
            "   Ví dụ: 'Xin chào', 'Cảm ơn', 'Tạm biệt'\n\n"
            "Output CHỈ chứa 1 trong các intent trên: [ORDER], [VIEW_ORDER], [ORDER_HISTORY], "
            "[CANCEL_ITEM], [UPDATE_QUANTITY], [CONFIRM_ORDER], [SEARCH], hoặc [NO_SEARCH]"
        )
        
        response = self.llm.generate(prompt, max_new_tokens=30)
        
        # Parse intent
        if "[ORDER]" in response:
            return "ORDER"
        elif "[VIEW_ORDER]" in response:
            return "VIEW_ORDER"
        elif "[CANCEL_ITEM]" in response:
            return "CANCEL_ITEM"
        elif "[ORDER_HISTORY]" in response:
            return "ORDER_HISTORY"
        elif "[UPDATE_QUANTITY]" in response:
            return "UPDATE_QUANTITY"
        elif "[CONFIRM_ORDER]" in response:
            return "CONFIRM_ORDER"
        elif "[SEARCH]" in response:
            return "SEARCH"
        else:
            return "NO_SEARCH"
        
    def is_specific_dish_order(self, user_query):
        """
        Kiểm tra xem có phải đang đặt món CỤ THỂ không
        Return True nếu có tên món cụ thể, False nếu là câu hỏi chung chung
        """
        # Các từ khóa chung chung (không phải tên món cụ thể)
        generic_keywords = [
            'gì đó', 'gì', 'món nào', 'cái gì', 'gợi ý',
            'nên ăn', 'đặc sản', 'signature', 'ngon',
            'cay', 'ngọt', 'chua', 'mặn', 'béo', 'nhẹ',
            'nóng', 'lạnh', 'nước', 'khô'
        ]
        
        query_lower = user_query.lower()
        
        # Nếu chứa từ khóa chung chung → không phải đặt món cụ thể
        if any(keyword in query_lower for keyword in generic_keywords):
            return False
        
        # Thử tìm món trong database
        dish_name, _ = self.extract_order_info(user_query)
        if dish_name:
            dish = self.order_manager.find_dish(dish_name)
            return dish is not None
        
        return False
    
    def extract_order_info(self, user_query):
        """
        Trích xuất thông tin món ăn và số lượng từ câu query
        """
        # Extract số lượng
        quantity = 1
        quantity_match = re.search(r'(\d+)\s*(phần|ly|chai|suất|cái|con|nửa|nguyên)?', user_query.lower())
        if quantity_match:
            quantity = int(quantity_match.group(1))
            
        # Các từ khóa action cần loại bỏ
        action_words = ['đặt', 'thêm', 'cho', 'tôi', 'muốn', 'gọi', 'lấy', 'order', 
                       'món', 'phần', 'ly', 'chai', 'suất', 'vào', 'đơn', 'nhé']
        
        words = user_query.lower().split()
        dish_words = [w for w in words if w not in action_words and not w.isdigit()]
        dish_name = ' '.join(dish_words)
        
        return dish_name.strip(), quantity

    def handle_order(self, user_query):
        """Xử lý đặt món"""
        dish_name, quantity = self.extract_order_info(user_query)
        
        if not dish_name:
            return "Xin lỗi, tôi chưa hiểu bạn muốn đặt món gì. Bạn có thể nói rõ hơn được không?"
        
        result = self.order_manager.add_item(self.current_user_id, dish_name, quantity)
        
        if result['success']:
            # Thêm thông tin món vừa đặt
            response = result['message']
            response += f"\n\nGiá: {result['item']['price']:,}đ/phần"
            response += "\n\n👉 Bạn muốn gọi thêm món khác hay chốt đơn luôn ạ? (Gõ 'xem đơn' để kiểm tra hoặc 'chốt đơn' để hoàn tất)"
            return response
        else:
            # Nếu không tìm thấy món, suggest
            return result['message'] + "\n\nBạn có thể hỏi 'Có những món nào?' để xem menu đầy đủ."
    
    def handle_view_order(self):
        """Xử lý xem đơn hàng"""
        result = self.order_manager.view_order(self.current_user_id)
        if "đang trống" not in result['message']:
            result['message'] += "\n\n🔔 Bạn có muốn chốt đơn ngay không? Hãy gõ 'Xác nhận' hoặc 'Đặt hàng' để nhà hàng lên món nhé!"
        return result['message']
    
    def handle_order_history(self):
        """Xử lý xem lịch sử đơn hàng"""
        result = self.order_manager.get_order_history(self.current_user_id)
        return result['message']
    
    def handle_cancel_item(self, user_query):
        """Xử lý hủy món"""
        # Trích xuất tên món cần hủy
        cancel_words = ['hủy', 'xóa', 'bỏ', 'cancel', 'remove']
        words = user_query.lower().split()
        
        # Lọc bỏ các từ action
        dish_words = [w for w in words if w not in cancel_words and w not in ['món', 'đi', 'ra', 'khỏi', 'đơn', 'hàng']]
        dish_name = ' '.join(dish_words)
        
        if not dish_name:
            return "Bạn muốn hủy món nào? Vui lòng cho tôi biết tên món."
        
        result = self.order_manager.remove_item(self.current_user_id, dish_name)
        return result['message']
    
    def handle_confirm_order(self, user_query):
        """Xử lý xác nhận đơn hàng"""
        # Trích xuất thời gian giao hàng nếu có
        delivery_time = None
        time_match = re.search(r'(\d{1,2}):?(\d{2})?\s*(giờ|h)?', user_query)
        if time_match:
            hour = time_match.group(1)
            minute = time_match.group(2) or "00"
            delivery_time = f"{hour}:{minute}"
        
        result = self.order_manager.confirm_order(self.current_user_id, delivery_time)
        return result['message']

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
        
        # Kiểm tra xem có phải câu hỏi gợi ý món ăn không
        is_recommendation = any(keyword in user_query.lower() for keyword in 
                               ['gợi ý', 'nên ăn', 'muốn ăn', 'ăn gì', 'món nào', 
                                'cay', 'ngọt', 'chua', 'đặc sản', 'signature'])
        
        if is_recommendation:
            prompt = (
                "Dưới đây là thông tin từ cơ sở dữ liệu của nhà hàng Hòa Viên:\n"
                f"{context_str}\n\n"
                "Hãy đóng vai là nhân viên tư vấn nhiệt tình của Hòa Viên. "
                "Dựa vào thông tin trên, hãy GỢI Ý các món phù hợp với yêu cầu của khách.\n"
                "Nếu khách hỏi về khẩu vị (cay, ngọt, chua...), hãy giới thiệu 2-3 món có khẩu vị đó.\n"
                "Kết thúc bằng câu hỏi: 'Bạn có muốn đặt món nào không?'\n"
                f"Khách hàng: {user_query}\n"
                "Trả lời:"
            )
        else:
            prompt = (
                "Dưới đây là thông tin từ cơ sở dữ liệu của nhà hàng Hòa Viên:\n"
                f"{context_str}\n\n"
                "Hãy đóng vai là nhân viên phục vụ thân thiện của Hòa Viên. "
                "Dựa vào thông tin trên, hãy trả lời câu hỏi của khách hàng một cách ngắn gọn, chính xác.\n"
                f"Khách hàng: {user_query}\n"
                "Trả lời:"
            )
        return self.llm.generate(prompt, max_new_tokens=200)

    def process(self, user_query):
        """
        Xử lý query chính
        """
        # 1. Phân loại intent
        intent = self.planner(user_query)
        print(f"[Intent]: {intent}")
        
        # 2. Kiểm tra lại nếu intent là ORDER
        if intent == "ORDER":
            # Kiểm tra xem có phải đặt món cụ thể không
            if not self.is_specific_dish_order(user_query):
                # Nếu không phải đặt món cụ thể → chuyển sang SEARCH để gợi ý
                print("[Override]: Chuyển từ ORDER sang SEARCH (câu hỏi gợi ý)")
                intent = "SEARCH"
                
        # 3. Xử lý theo intent
        if intent == "ORDER":
            return self.handle_order(user_query)
        
        elif intent == "VIEW_ORDER":
            return self.handle_view_order()
        
        elif intent == "ORDER_HISTORY":
            return self.handle_order_history()
        
        elif intent == "CANCEL_ITEM":
            return self.handle_cancel_item(user_query)
        
        elif intent == "CONFIRM_ORDER":
            return self.handle_confirm_order(user_query)
        
        elif intent == "SEARCH":
            # Tìm kiếm thông tin từ database
            contexts = self.retriever(user_query)
            if contexts:
                return self.reader(user_query, contexts)
            else:
                return "Xin lỗi, tôi không tìm thấy thông tin phù hợp."
        
        else:  # NO_SEARCH - chitchat
            prompt = (
                "Bạn là nhân viên thân thiện của nhà hàng Hòa Viên. "
                f'Khách hàng nói: "{user_query}". '
                "Hãy phản hồi một cách lịch sự, ngắn gọn (1-2 câu)."
            )
            return self.llm.generate(prompt, max_new_tokens=30)