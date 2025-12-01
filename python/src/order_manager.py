import json
import os
from datetime import datetime
from typing import Dict, Optional

class OrderManager:
    """
    Quản lý đơn hàng: thêm, xóa, sửa món, xem đơn hàng
    """
    def __init__(self, menu_path: str):
        self.orders = {}  # {user_id: [list of order items]}
        self.menu_items = self._load_menu(menu_path)
    
    def _load_menu(self, path):
        """Load menu từ file JSON và tạo dict tra cứu nhanh"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Tạo dict để tra cứu nhanh món ăn
            items_dict = {}
            for category in data.get("menu", {}).get('categories', []):
                for item in category.get("items", []):
                    # Lưu cả tên tiếng Việt và tiếng Anh
                    items_dict[item['name_vn'].lower()] = {
                        'id': item['id'],
                        'name_vn': item['name_vn'],
                        'name_en': item['name_en'],
                        'price': item['price'],
                        'category': category['name_vn']
                    }
                    items_dict[item['name_en'].lower()] = items_dict[item['name_vn'].lower()]
            
            return items_dict
        except FileNotFoundError as e:
            print(f"Error loading menu: {e}")
            return {}
    
    def find_dish(self, dish_name: str) -> Optional[Dict]:
        """Tìm món ăn trong menu (fuzzy matching)"""
        dish_name_lower = dish_name.lower().strip()
        
        # Exact match
        if dish_name_lower in self.menu_items:
            return self.menu_items[dish_name_lower]
        
        # Fuzzy match - tìm món có chứa từ khóa
        for key, item in self.menu_items.items():
            if dish_name_lower in key or key in dish_name_lower:
                return item
    
        return None

    def add_item(self, user_id: str, dish_name: str, quantity: int = 1):
        """Thêm món ăn vào đơn hàng"""
        dish = self.find_dish(dish_name)
        
        if not dish:
            return {
                'success': False,
                'message': f"Xin lỗi, không tìm thấy món '{dish_name}' trong menu."
            }
        
        if user_id not in self.orders:
            self.orders[user_id] = []
        
        # Kiểm tra món đã có trong đơn chưa
        existing_item = None
        for item in self.orders[user_id]:
            if item['id'] == dish['id']:
                existing_item = dish
                break
        
        if existing_item:
            existing_item['quantity'] += quantity
            message = f"Đã tăng số lượng {dish['name_vn']} lên {existing_item['quantity']} phần."
        else:
            self.orders[user_id].append({
                'id': dish['id'],
                'name_vn': dish['name_vn'],
                'name_en': dish['name_en'],
                'price': dish['price'],
                'quantity': quantity,
                'category': dish['category']
            })
            message = f"Đã thêm {quantity} phần {dish['name_vn']} vào đơn hàng."
        
        return {
            'success': True,
            'message': message,
            'item': dish
        }

    def remove_item(self, user_id: str, dish_name: str) -> Dict:
        """Xóa món khỏi đơn hàng"""
        if user_id not in self.orders or not self.orders[user_id]:
            return {
                'success': False,
                'message': "Đơn hàng của bạn đang trống."
            }
        
        dish = self.find_dish(dish_name)
        if not dish:
            return {
                'success': False,
                'message': f"Không tìm thấy món '{dish_name}' trong đơn hàng."
            }
        
        # Tìm và xóa món
        removed = False
        for i, item in enumerate(self.orders[user_id]):
            if item['id'] == dish['id']:
                removed_item = self.orders[user_id].pop(i)
                removed = True
                break
        
        if removed:
            return {
                'success': True,
                'message': f"Đã xóa {removed_item['name_vn']} khỏi đơn hàng."
            }
        else:
            return {
                'success': False,
                'message': f"Món {dish['name_vn']} không có trong đơn hàng."
            }
    
    def update_quantity(self, user_id: str, dish_name: str, quantity: int) -> Dict:
        """Cập nhật số lượng món"""
        if user_id not in self.orders or not self.orders[user_id]:
            return {
                'success': False,
                'message': "Đơn hàng của bạn đang trống."
            }
        
        dish = self.find_dish(dish_name)
        if not dish:
            return {
                'success': False,
                'message': f"Không tìm thấy món '{dish_name}'."
            }
        
        # Tìm và cập nhật số lượng
        for item in self.orders[user_id]:
            if item['id'] == dish['id']:
                if quantity <= 0:
                    # Nếu số lượng <= 0, xóa món
                    return self.remove_item(user_id, dish_name)
                else:
                    item['quantity'] = quantity
                    return {
                        'success': True,
                        'message': f"Đã cập nhật số lượng {dish['name_vn']} thành {quantity} phần."
                    }
        
        return {
            'success': False,
            'message': f"Món {dish['name_vn']} không có trong đơn hàng."
        }
    
    def view_order(self, user_id: str) -> Dict:
        """Xem đơn hàng hiện tại"""
        if user_id not in self.orders or not self.orders[user_id]:
            return {
                'success': True,
                'message': "Đơn hàng của bạn đang trống.",
                'items': [],
                'total': 0
            }
        
        items = self.orders[user_id]
        total = sum(item['price'] * item['quantity'] for item in items)
        
        # Format thông tin đơn hàng
        order_details = []
        for item in items:
            order_details.append(
                f"- {item['name_vn']} ({item['name_en']}): "
                f"{item['quantity']} phần × {item['price']:,}đ = {item['price'] * item['quantity']:,}đ"
            )
        
        message = "Đơn hàng của bạn:\n" + "\n".join(order_details)
        message += f"\n\nTổng cộng: {total:,}đ (chưa bao gồm VAT 8%)"
        message += f"\nThành tiền: {int(total * 1.08):,}đ"
        
        return {
            'success': True,
            'message': message,
            'items': items,
            'total': total,
            'total_with_vat': int(total * 1.08)
        }
    
    def clear_order(self, user_id: str) -> Dict:
        """Xóa toàn bộ đơn hàng"""
        if user_id in self.orders:
            self.orders[user_id] = []
        
        return {
            'success': True,
            'message': "Đã xóa toàn bộ đơn hàng."
        }
    
    def _save_to_file(self, user_id, order_info):
        """Lưu đơn hàng đã xác nhận vào file log"""
        # Đường dẫn file lưu (nên để trong folder data)
        save_path = os.path.join(os.path.dirname(__file__), '../data/orders_log.jsonl')
        
        # Tạo bản ghi đơn hàng
        order_record = {
            "order_id": f"{user_id}_{int(datetime.now().timestamp())}",
            "user_id": user_id,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "items": order_info['items'],
            "total_payment": order_info['total_with_vat'],
            "status": "confirmed"
        }

        try:
            # Mode 'a' (append) để viết tiếp vào cuối file, không ghi đè đơn cũ
            with open(save_path, 'a', encoding='utf-8') as f:
                f.write(json.dumps(order_record, ensure_ascii=False) + "\n")
            print(f"Đã lưu đơn hàng")
        except Exception as e:
            print(f"Lỗi khi lưu file đơn hàng: {e}")
    
    def confirm_order(self, user_id: str, delivery_time: str = None) -> Dict:
        """Xác nhận đặt hàng"""
        if user_id not in self.orders or not self.orders[user_id]:
            return {
                'success': False,
                'message': "Đơn hàng của bạn đang trống. Vui lòng thêm món trước khi đặt hàng."
            }
        
        order_info = self.view_order(user_id)
        
        message = f"✅ Đã xác nhận đơn hàng!\n\n{order_info['message']}"
        
        if delivery_time:
            message += f"\n\n🕐 Thời gian giao: {delivery_time}"
        else:
            message += "\n\n🕐 Thời gian giao: Càng sớm càng tốt"
        
        message += "\n\nCảm ơn quý khách đã đặt hàng tại Hòa Viên! 🎉"
        
        # Lưu đơn hàng (có thể lưu vào file hoặc database)
        self._save_to_file(user_id, order_info)
        
        # Sau đó clear đơn hàng hiện tại
        self.clear_order(user_id)
        
        return {
            'success': True,
            'message': message,
            'order': order_info
        }

    def get_order_history(self, user_id: str, limit: int = 3) -> Dict:
        """Lấy lịch sử đơn hàng đã đặt từ file log"""
        # Đường dẫn file log (giống hàm _save_to_file)
        save_path = os.path.join(os.path.dirname(__file__), '../data/orders_log.jsonl')
        
        if not os.path.exists(save_path):
            return {'success': False, 'message': "Bạn chưa có lịch sử đặt hàng nào."}

        user_history = []
        try:
            with open(save_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        if not line.strip(): continue
                        record = json.loads(line.strip())
                        # Lọc theo user_id
                        if record.get('user_id') == user_id:
                            user_history.append(record)
                    except json.JSONDecodeError:
                        continue
        except Exception as e:
            return {'success': False, 'message': f"Không thể đọc lịch sử đơn hàng: {e}"}

        if not user_history:
            return {'success': False, 'message': "Bạn chưa có đơn hàng nào trong lịch sử."}

        # Sắp xếp giảm dần theo thời gian (mới nhất lên đầu)
        # Giả định timestamp string format chuẩn sort được, hoặc parse ra datetime
        user_history.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Lấy top 3
        recent_orders = user_history[:limit]

        # Format hiển thị
        message = f"📋 DANH SÁCH {len(recent_orders)} ĐƠN HÀNG GẦN NHẤT CỦA BẠN:\n"

        for i, order in enumerate(recent_orders, 1):
            # Xử lý trạng thái
            raw_status = order.get('status', 'unknown')
            
            # Format tiền tệ
            total = order.get('total_payment', 0)
            
            message += f"\n📦 Đơn hàng #{i} - {order['timestamp']}"
            message += f"\n   Trạng thái: {raw_status}"
            message += f"\n   Tổng tiền: {total:,}đ"
            
            # Liệt kê món ngắn gọn
            item_list = []
            for item in order.get('items', []):
                item_list.append(f"{item['quantity']}x {item['name_vn']}")
            message += f"\n   Chi tiết: {', '.join(item_list)}\n"
            message += "-" * 30

        return {
            'success': True, 
            'message': message,
            'orders': recent_orders
        }