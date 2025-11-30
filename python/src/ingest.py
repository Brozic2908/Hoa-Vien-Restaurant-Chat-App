import json
import os
from langchain_text_splitters import RecursiveCharacterTextSplitter # Mô phỏng logic split
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance
from config import Config

class DataIngestor:
    def __init__(self, qdrant_client):
        self.client = qdrant_client
        self.encoder = SentenceTransformer(Config.EMBEDDING_MODEL)
        
    def load_menu(self, path):
        # 
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            docs = []
            for category in data:
                cat_name = category['category']
                for item in category['items']:
                    # Tạo nội dung ngữ nghĩa cho vector search
                    content = (
                        f"Món ăn: {item['name_vn']} ({item['name_en']}). "
                        f"Thuộc loại: {cat_name}. "
                        f"Giá: {item['price']} VND. "
                        f"Ghi chú: {item['note']}."
                    )
                    docs.append({"text": content, "source": "menu", "id": item['id']})
            return docs
        except FileNotFoundError:
            print("Warning: Menu file not found.")
            return []

    def load_info(self, path):
        # 
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Chia nhỏ thông tin nhà hàng thành các đoạn
            chunks = content.split('\n')
            docs = []
            for i, chunk in enumerate(chunks):
                if chunk.strip():
                    docs.append({"text": chunk.strip(), "source": "info", "id": f"info_{i}"})
            return docs
        except FileNotFoundError:
            print("Warning: Info file not found.")
            return []

    def ingest(self):
        print("--- Bắt đầu nạp dữ liệu vào Vector DB ---")
        menu_docs = self.load_menu(os.path.join(Config.DATA_DIR, 'menu.json'))
        info_docs = self.load_info(os.path.join(Config.DATA_DIR, 'restaurant_info.txt'))
        
        all_docs = menu_docs + info_docs
        
        if not all_docs:
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
        embeddings = self.encoder.encode([d['text'] for d in all_docs])
        
        for i, doc in enumerate(all_docs):
            points.append(PointStruct(
                id=i,
                vector=embeddings[i].tolist(),
                payload=doc
            ))
            
        self.client.upsert(
            collection_name=Config.COLLECTION_NAME,
            points=points
        )
        print(f"--- Đã nạp {len(points)} documents vào Qdrant ---")