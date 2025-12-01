import json
import os
from sentence_transformers import SentenceTransformer
from qdrant_client.models import PointStruct, VectorParams, Distance
from config import Config

class DataIngestor:
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)
        print("✅ Model đã sẵn sàng!\n")
    
    def load_menu(self, path):
        """Load dữ liệu info và menu món ăn của nhà hàng"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            docs = []
            
            # 1. Xử lý thông tin chung nhà hàng (Restaurant Info)
            info = data['restaurant']
            info_text = (
                f"Thông tin nhà hàng {info['name']} ({info['name_en']}). "
                f"Địa chỉ: {info['contact']['address']}. "
                f"Giờ mở cửa: {info['business_hours']['display']}. "
                f"SĐT: {info['contact']['phone']}. "
                f"Mô tả: {info['description']}."
            )
            docs.append({"text": info_text, "source": "info", "id": "rest_info"})
            
            # 2. Xử lý Menu (Quan trọng: Ghép description và tags vào text)
            for category in data['menu']['categories']:
                cat_name = category['name_vn']
                for item in category['items']:
                    # Lấy danh sách tags và dietary
                    tags = ", ".join(item.get('tags', []))
                    dietary = ", ".join(item.get('dietary', []))

                    # Tạo chuỗi văn bản giàu ngữ nghĩa cho Vector Embedding
                    # Kỹ thuật: Ghép hết các trường quan trọng vào 1 đoạn văn
                    content = (
                        f"Món: {item['name_vn']} ({item['name_en']}). "
                        f"Loại: {cat_name}. "
                        f"Giá: {item['price']} VND. "
                        f"Mô tả hương vị: {item.get('description', '')}. " # Lấy mô tả từ V2
                        f"Đặc điểm: {tags}, {dietary}. "
                        f"Thời gian chuẩn bị: {item.get('preparation_time', 0)} phút."
                    )
                    
                    # Lưu metadata để sau này filter nếu cần
                    metadata = {
                        "text": content,
                        "source": "menu",
                        "id": item['id'],
                        "price": item['price'],
                        "category": cat_name,
                        "tags": item.get('tags', [])
                    }
                    docs.append(metadata)

            # 3. Xử lý FAQ (Common Questions)
            for idx, qa in enumerate(data.get('common_questions', [])):
                qa_text = f"Hỏi: {qa['question']} - Trả lời: {qa['answer']}"
                docs.append({"text": qa_text, "source": "faq", "id": f"faq_{idx}"})
                
            return docs

        except FileNotFoundError:
            print("Error: Menu file not found.")
            return []

    def ingest(self):
        """Nạp dữ liệu vào Vector DB"""
        print("--- Bắt đầu nạp dữ liệu vào Vector DB ---")
        menu_data = self.load_menu(os.path.join(Config.DATA_DIR, "menu_v2.json"))

        if not menu_data: 
            print("Không có dữ liệu để nạp.")
            return
        
        # Tạo collection trong Qdrant
        if self.client.collection_exists(collection_name=Config.COLLECTION_NAME):
            self.client.delete_collection(collection_name=Config.COLLECTION_NAME)
            
        self.client.create_collection(
            collection_name=Config.COLLECTION_NAME,
            vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
        )
        
        # Vector hóa và upload
        points = []
        embeddings = self.encoder.encode([d['text'] for d in menu_data])
        # Loop tạo PointStruct (kết hợp ID + Vector + Payload)
        for i, doc in enumerate(menu_data):
            points.append(PointStruct(
                id=i,
                vector=embeddings[i].tolist(),
                payload=doc
            ))
        
        # Client.upsert -> Đẩy lên Qdrant
        self.client.upsert(
            collection_name=Config.COLLECTION_NAME,
            points=points
        )
        print(f"--- Đã nạp {len(points)} documents vào Qdrant ---")